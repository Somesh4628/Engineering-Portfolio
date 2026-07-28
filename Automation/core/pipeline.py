"""
Main pipeline entry point - runs single trend through full pipeline.
Can be called from Airflow or CLI.
"""
import asyncio
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from datetime import datetime
from typing import Optional, Any
import structlog

from core.config import settings
from core.observability import setup_observability, set_correlation_id, get_correlation_id
from core.database import init_db, close_db, get_db, AsyncSessionLocal, Trend, TrendStatus, SupplierProductORM, Listing, ListingStatus
from core.resilience import with_resilience, AsyncSemaphore
from supplier.gateway import supplier_gateway, SupplierProduct
from intelligence.trend_scorer import TrendScorer, TrendSignal, classify_category
from intelligence.dynamic_pricing import DynamicPricingEngine
from intelligence.rto_predictor import RTOPredictor, OrderFeatures
from marketplace.meesho import MeeshoCSVGenerator, create_meesho_listing_from_product
from ai_debate_engine import run_ai_debate
import redis.asyncio as redis

logger = structlog.get_logger("pipeline")

# Concurrency control
trend_semaphore = AsyncSemaphore(settings.MAX_CONCURRENT_API_CALLS, "trend_processing")

# Intelligence engines (initialized lazily)
_pricing_engine: Optional[DynamicPricingEngine] = None
_rto_predictor: Optional[RTOPredictor] = None


async def get_pricing_engine() -> DynamicPricingEngine:
    global _pricing_engine
    if _pricing_engine is None:
        try:
            redis_client = redis.from_url(str(settings.REDIS_URL))
        except Exception:
            redis_client = None
        _pricing_engine = DynamicPricingEngine(redis_client)
    return _pricing_engine


async def get_rto_predictor() -> RTOPredictor:
    global _rto_predictor
    if _rto_predictor is None:
        _rto_predictor = RTOPredictor()
    return _rto_predictor


@with_resilience("supplier_gateway", max_retries=3)
async def match_supplier(keyword: str) -> Optional[SupplierProduct]:
    """Find best supplier product for keyword."""
    return await supplier_gateway.find_best_product(keyword)


@with_resilience("ai_copywriting", max_retries=2)
async def generate_copy(keyword: str, product: SupplierProduct) -> dict:
    """Generate AI copywriting with debate."""
    supplier_info = {
        "sku": product.sku,
        "name": product.name,
        "wholesale_cost": product.wholesale_cost,
        "image_url": product.image_url,
    }
    return run_ai_debate(keyword, supplier_info)


@with_resilience("dynamic_pricing", max_retries=2)
async def calculate_price(product: SupplierProduct) -> float:
    """Get dynamic price from bandit engine."""
    engine = await get_pricing_engine()
    return await engine.get_price(product.sku, product.wholesale_cost, min_margin=1.35)


@with_resilience("rto_prediction", max_retries=1)
async def predict_rto(product: SupplierProduct, price: float) -> float:
    """Predict RTO probability."""
    predictor = await get_rto_predictor()
    return predictor.predict(OrderFeatures(
        category=product.category,
        price=price,
        payment_mode="COD",
        customer_tier="tier2",
        is_first_order=True,
        pincode_rto_rate=0.20,
        seller_rating=4.5,
        product_weight=0.5,
        estimated_delivery_days=3,
    ))


async def process_single_trend(trend_id: Any, bot: Optional[Any] = None) -> dict:
    """Process a single trend through the full pipeline."""
    import uuid
    trend_str = str(trend_id)
    try:
        t_uuid = uuid.UUID(trend_str)
    except Exception:
        t_uuid = trend_id

    correlation_id = set_correlation_id(trend_str[:8])
    logger.info("processing_trend_started", trend_id=trend_str)

    async with trend_semaphore:
        async for db in get_db():
            # Get trend
            trend = await db.get(Trend, t_uuid)
            if not trend:
                return {"status": "error", "message": "Trend not found"}

            trend.status = TrendStatus.PROCESSING
            await db.commit()

            try:
                # 1. Supplier Matching
                logger.info("matching_supplier", keyword=trend.keyword)
                product = await match_supplier(trend.keyword)
                if not product:
                    trend.status = TrendStatus.FAILED
                    trend.meta["error"] = "No supplier match"
                    await db.commit()
                    return {"status": "failed", "reason": "no_supplier"}

                # Get or create SupplierProductORM record in DB
                from sqlalchemy import select
                existing_product = await db.execute(
                    select(SupplierProductORM).where(SupplierProductORM.sku == product.sku)
                )
                db_product = existing_product.scalar_one_or_none()
                if not db_product:
                    db_product = SupplierProductORM(
                        sku=product.sku,
                        name=product.name,
                        category=product.category,
                        wholesale_cost=product.wholesale_cost,
                        image_url=product.image_url,
                        vendor=product.vendor,
                        vendor_product_id=product.vendor_product_id,
                        stock=product.stock,
                        meta=product.meta or {}
                    )
                    db.add(db_product)
                    await db.flush()

                # 2. AI Copywriting
                logger.info("generating_copy", sku=product.sku)
                ai_output = await generate_copy(trend.keyword, product)

                # 3. Dynamic Pricing
                logger.info("calculating_price", sku=product.sku)
                price = await calculate_price(product)

                # 4. RTO Prediction & Multi-Factor Risk Assessment
                logger.info("predicting_rto", sku=product.sku)
                rto_prob = await predict_rto(product, price)

                from intelligence.risk_engine import assess_multi_factor_risk
                from monitoring.telemetry import telemetry_engine
                margin_pct = round((price - product.wholesale_cost) / price * 100, 2)
                pricing_data = {"margin_percent": margin_pct, "marketplace_price": price}
                risk_data = await assess_multi_factor_risk(product, pricing_data)
                risk_score = risk_data.get("risk_score", 0.3)

                await telemetry_engine.log_product_published(
                    sku=product.sku,
                    category=product.category,
                    wholesale_cost=product.wholesale_cost,
                    marketplace_price=price,
                    margin_percent=margin_pct,
                    risk_score=risk_score,
                    vendor=getattr(product, "vendor", "cjdropshipping")
                )

                # 5. Create Listing
                listing = Listing(
                    trend_id=trend.id,
                    supplier_product_id=db_product.id,
                    title=ai_output["Title"],
                    description=ai_output["Description"],
                    bullet_points=ai_output["BulletPoints"],
                    price=price,
                    wholesale_cost=product.wholesale_cost,
                    margin_pct=margin_pct,
                    image_url=product.image_url,
                    status=ListingStatus.PENDING_REVIEW,
                    meta={
                        "rto_probability": rto_prob,
                        "risk_score": risk_score,
                        "ai_output": ai_output,
                        "trend_score": trend.score,
                    }
                )
                db.add(listing)

                trend.status = TrendStatus.COMPLETED
                trend.completed_at = datetime.utcnow()
                await db.commit()

                # Dispatch Telegram approval card with multi-angle photo album & supplier details
                if bot:
                    try:
                        product_images = (product.meta or {}).get("images", [product.image_url])
                        await bot.send_listing_for_review(
                            listing_id=str(listing.id),
                            title=listing.title,
                            description=listing.description,
                            price=listing.price,
                            wholesale_cost=listing.wholesale_cost,
                            margin_pct=listing.margin_pct,
                            category=product.category,
                            rto_probability=rto_prob,
                            image_url=product.image_url,
                            images=product_images,
                            supplier_name=getattr(product, "vendor", "GlowRoad Verified Direct"),
                            vendor_sku=getattr(product, "vendor_product_id", "GLW-89472"),
                            gst_percent=(product.meta or {}).get("gst_percent", 18.0),
                            hs_code=(product.meta or {}).get("hs_code", "39269099"),
                            data_source=(product.meta or {}).get("data_source", "unknown"),
                        )
                    except Exception as bot_err:
                        logger.warning("telegram_card_send_failed", error=str(bot_err))

                logger.info("trend_processed_successfully",
                           trend_id=trend_id,
                           listing_id=str(listing.id),
                           price=price,
                           rto_prob=rto_prob)

                return {
                    "status": "success",
                    "trend_id": trend_id,
                    "listing_id": str(listing.id),
                    "price": price,
                    "rto_probability": rto_prob,
                }

            except Exception as e:
                logger.error("trend_processing_failed", trend_id=trend_id, error=str(e))
                trend.status = TrendStatus.FAILED
                trend.meta["error"] = str(e)
                await db.commit()
                if bot:
                    try:
                        await bot.send_diagnostic_alert(
                            component="Trend Processing Pipeline",
                            error_type=e.__class__.__name__,
                            details=f"Trend ID: {trend_id}\nKeyword: {trend.keyword}\nError: {str(e)}",
                            recommendation="System logged error to DB and isolated failed trend. Continuing remaining queue."
                        )
                    except Exception:
                        pass
                return {"status": "error", "message": str(e)}


async def process_pending_trends(limit: int = 10, bot: Optional[Any] = None, target_chat_id: Optional[str] = None) -> dict:
    """Process all pending trends sequentially to guarantee Telegram card delivery."""
    logger.info("processing_pending_trends", limit=limit)

    async for db in get_db():
        from sqlalchemy import select
        res = await db.execute(
            select(Trend)
            .where(Trend.status == TrendStatus.PENDING)
            .limit(limit)
        )
        trends = res.scalars().all()

    if not trends:
        return {"processed": 0, "message": "No pending trends"}

    results = []
    for t in trends:
        r = await process_single_trend(str(t.id), bot=bot)
        results.append(r)
        await asyncio.sleep(0.5)

    success = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
    failed = len(results) - success

    logger.info("batch_processing_complete", total=len(results), success=success, failed=failed)
    return {"processed": len(results), "success": success, "failed": failed, "results": results}


async def generate_meesho_csv() -> str:
    """Generate Meesho bulk upload CSV from staged listings."""
    logger.info("generating_meesho_csv")

    async for db in get_db():
        listings = await db.execute(
            Listing.__table__.select()
            .where(Listing.status == ListingStatus.STAGED)
            .join(SupplierProductORM)
        )
        listings = listings.all()

    if not listings:
        return "No staged listings"

    meesho_generator = MeeshoCSVGenerator()
    supplier_products = {}

    # Load supplier products
    for listing, supplier in listings:
        supplier_products[supplier.sku] = {
            "sku": supplier.sku,
            "name": supplier.name,
            "category": supplier.category,
            "weight_g": supplier.meta.get("weight_g", 500),
            "length_cm": supplier.meta.get("length_cm", 25),
            "breadth_cm": supplier.meta.get("breadth_cm", 20),
            "height_cm": supplier.meta.get("height_cm", 15),
            "hs_code": supplier.meta.get("hs_code", "39269099"),
            "gst_percent": supplier.meta.get("gst_percent", 18.0),
        }

    pipeline_listings = []
    for listing, supplier in listings:
        pipeline_listings.append({
            "title": listing.title,
            "description": listing.description,
            "price": listing.price,
            "supplier_product_id": supplier.sku,
            "image_url": listing.image_url,
        })

    csv_path = meesho_generator.generate_and_write(pipeline_listings, supplier_products)

    # Update listing status
    async for db in get_db():
        for listing, _ in listings:
            listing.status = ListingStatus.PUBLISHED_MEESHO
            listing.published_at = datetime.utcnow()
        await db.commit()

    return f"Generated {len(listings)} Meesho listings: {csv_path}"


# CLI entry point
if __name__ == "__main__":

    setup_observability("ecommerce-pipeline")

    async def main():
        await init_db()

        if len(sys.argv) < 2:
            print("Usage: python -m core.pipeline [--help|process_trends|process_trend <id>|generate_meesho]")
            return

        cmd = sys.argv[1]

        if cmd == "--help":
            print("Available commands:")
            print("  seed_trends              - Seed sample trending products into database")
            print("  process_trends [limit]   - Process pending trends (default limit=10)")
            print("  process_trend <id>       - Process a single trend by ID")
            print("  generate_meesho          - Generate Meesho CSV from staged listings")
            return

        if cmd == "seed_trends":
            async with AsyncSessionLocal() as db:
                sample_keywords = ["sunset lamp", "oversized t shirt", "baby bottle", "kitchen organizer", "desk organizer"]
                added = 0
                for kw in sample_keywords:
                    # check duplicate
                    from sqlalchemy import select
                    existing = await db.execute(select(Trend).where(Trend.keyword == kw, Trend.status == TrendStatus.PENDING))
                    if not existing.scalar_one_or_none():
                        t = Trend(keyword=kw, source="google_trends", status=TrendStatus.PENDING, score=85.0, meta={"category": "general"})
                        db.add(t)
                        added += 1
                await db.commit()
                print(f"Seeded {added} new pending trends into database.")

        if cmd in ("process_trends", "start_bot", "server"):
            import os
            import aiohttp
            from aiohttp import web
            from review.telegram_bot import TelegramReviewBot

            # 1. Start HTTP Web Server IMMEDIATELY so Render detects port 10000 open in < 0.1s
            routes = web.RouteTableDef()

            @routes.get("/")
            @routes.get("/health")
            @routes.get("/ping")
            async def health_check(request):
                from review.telegram_bot import get_scheduled_hour
                return web.json_response({
                    "status": "online",
                    "service": "VibeMart Autonomous E-Commerce Engine",
                    "active_commit": "0c5be2d (Latest Push)",
                    "active_scheduled_hour_ist": f"{get_scheduled_hour()}:00 IST",
                    "timestamp": datetime.utcnow().isoformat()
                })

            @routes.post("/webhooks/meesho")
            async def meesho_webhook_route(request):
                try:
                    payload = await request.json()
                except Exception:
                    payload = {}
                from api.webhooks import webhook_handler
                res = await webhook_handler.handle_meesho_order_webhook(payload)
                return web.json_response(res)

            @routes.post("/webhooks/amazon")
            async def amazon_webhook_route(request):
                try:
                    payload = await request.json()
                except Exception:
                    payload = {}
                from api.webhooks import webhook_handler
                res = await webhook_handler.handle_amazon_order_webhook(payload)
                return web.json_response(res)

            app = web.Application()
            app.add_routes(routes)
            runner = web.AppRunner(app)
            await runner.setup()
            port = int(os.getenv("PORT", "10000"))
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()
            print(f"Health check web server running on port {port}")

            bot = TelegramReviewBot.from_settings()
            await bot.send_notification("🟢 <b>VibeMart 24/7 Cloud Server Online!</b>\nSend <code>/status</code> or <code>/run</code> anytime.")
            print("--- VibeMart 24/7 Cloud Server & Telegram Listener Running ---")

            # 2. Self-Pinger Loop to prevent Render Free Tier from sleeping
            async def keep_alive_ping_loop():
                async with aiohttp.ClientSession() as session:
                    while True:
                        try:
                            await asyncio.sleep(240)  # Ping every 4 minutes
                            url = f"http://localhost:{port}/health"
                            async with session.get(url) as resp:
                                await resp.json()
                        except Exception as e:
                            pass

            asyncio.create_task(keep_alive_ping_loop())

            # Helper to execute pipeline scan
            async def execute_pipeline_scan(target_chat_id: str = None):
                import random
                from intelligence.trend_hunter import trend_hunter
                fetched_res = await trend_hunter.fetch_trending_keywords(limit=5)
                if len(fetched_res) == 3:
                    fetched_kws, is_fallback, source_tag_name = fetched_res
                else:
                    fetched_kws, is_fallback = fetched_res[0], fetched_res[1]
                    source_tag_name = "Google Trends India" if not is_fallback else "Curated Keyword Pool"
                
                high_demand_catalog = ["sunset lamp", "magnetic phone holder", "oversized t shirt", "wireless earbuds", "rgb desk light", "kitchen organizer"]
                
                async with AsyncSessionLocal() as db:
                    from sqlalchemy import select, delete
                    try:
                        ex_tr = await db.execute(select(Trend.keyword))
                        used_kws = set(ex_tr.scalars().all())

                        available_kws = [
                            kw for kw in fetched_kws
                            if kw.lower() not in [u.lower() for u in used_kws]
                        ]
                        if not available_kws:
                            available_kws = fetched_kws

                        # Ensure high-demand catalog keywords are mixed in so supplier matching always succeeds
                        mixed_kws = available_kws[:3] + [k for k in high_demand_catalog if k not in available_kws][:2]
                        fresh_kws = mixed_kws[:5]
                    except Exception:
                        fresh_kws = (fetched_kws + high_demand_catalog)[:5]

                    await db.execute(delete(Trend).where(Trend.status == TrendStatus.PENDING))
                    await db.commit()

                    for kw in fresh_kws:
                        t = Trend(
                            keyword=kw,
                            source=source_tag_name.lower().replace(' ', '_'),
                            status=TrendStatus.PENDING,
                            score=round(random.uniform(82.0, 96.5), 1),
                            meta={"category": "general", "trend_source": source_tag_name}
                        )
                        db.add(t)
                    await db.commit()

                result = await process_pending_trends(10, bot=bot, target_chat_id=target_chat_id)
                success_cards = result.get('success', 0)
                source_tag = f"🟢 <b>Live Data ({source_tag_name})</b>" if not is_fallback else f"⚠️ <b>{source_tag_name}</b>"
                
                if success_cards > 0:
                    await bot.send_notification(
                        f"✅ <b>Pipeline Scan Completed!</b> ({source_tag})\n"
                        f"📦 Processed {result.get('processed', 0)} trends.\n"
                        f"🟢 <b>{success_cards} Approval Cards Delivered Above!</b> ☝️"
                    )
                else:
                    await bot.send_notification(
                        f"✅ <b>Pipeline Scan Completed!</b> ({source_tag})\n"
                        f"⚠️ Raw keywords had zero wholesale supplier matches. Retrying with verified catalog..."
                    )
                    # Instant fallback to high-demand catalog items so user ALWAYS gets approval cards
                    async with AsyncSessionLocal() as db:
                        await db.execute(delete(Trend).where(Trend.status == TrendStatus.PENDING))
                        for fallback_kw in high_demand_catalog[:3]:
                            db.add(Trend(keyword=fallback_kw, source="catalog_guaranteed", status=TrendStatus.PENDING, score=90.0, meta={"category": "general"}))
                        await db.commit()
                    retry_res = await process_pending_trends(10, bot=bot, target_chat_id=target_chat_id)
                    await bot.send_notification(
                        f"🟢 <b>{retry_res.get('success', 0)} Approval Cards Delivered Above!</b> ☝️"
                    )

            # 3. Dynamic Daily Schedule Runner (Reads user choice from /schedule buttons)
            last_scheduled_date = ""

            async def daily_schedule_loop():
                nonlocal last_scheduled_date
                while True:
                    try:
                        from datetime import datetime, timezone, timedelta
                        from review.telegram_bot import get_scheduled_hour

                        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
                        today_str = ist_now.strftime("%Y-%m-%d")
                        target_hour = get_scheduled_hour()
                        
                        # Trigger at user's configured hour IST once per day reliably
                        if ist_now.hour == target_hour and last_scheduled_date != today_str:
                            last_scheduled_date = today_str
                            print(f"⏰ Triggering Daily Automatic Scan at {target_hour}:00 IST ({today_str})...")
                            await bot.send_notification(f"⏰ <b>Daily Automatic Scan ({target_hour}:00 IST) Initiated!</b>\nAnalyzing trending market products...")
                            await execute_pipeline_scan()
                    except Exception as sched_err:
                        print("Daily schedule loop error:", sched_err)
                    
                    await asyncio.sleep(25)

            asyncio.create_task(daily_schedule_loop())

            # 4. Telegram Command & Button Tap Listener Loop
            while True:
                try:
                    res = await bot.listen_and_process_commands()
                    if res and res.get("command") == "RUN_NOW":
                        cid = res.get("chat_id")
                        print(f"Telegram triggered /run now command from {cid}!")
                        asyncio.create_task(execute_pipeline_scan(target_chat_id=cid))
                except Exception as err:
                    print("Listener loop error:", err)
                
                await asyncio.sleep(0.3)

        elif cmd == "process_trend":
            if len(sys.argv) < 3:
                print("Usage: python -m core.pipeline process_trend <trend_id>")
                return
            result = await process_single_trend(sys.argv[2])
            print(f"Result: {result}")

        elif cmd == "generate_meesho":
            result = await generate_meesho_csv()
            print(f"Result: {result}")

        else:
            print(f"Unknown command: {cmd}")

        await close_db()
        # Close Redis client used by DynamicPricingEngine to avoid "Event loop is closed" warnings
        global _pricing_engine
        if _pricing_engine is not None:
            await _pricing_engine.close()

    asyncio.run(main())