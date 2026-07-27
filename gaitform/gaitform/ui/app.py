import os
import streamlit as st
from gaitform.__main__ import run_pipeline

def _save(uploaded_file, name):
    if not uploaded_file:
        return None
    os.makedirs("uploads", exist_ok=True)
    p = os.path.join("uploads", name)
    with open(p, "wb") as fh:
        fh.write(uploaded_file.read())
    return p

def main():
    st.set_page_config(page_title="Gaitform - Premium Clinical UI", layout="wide")
    
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700;900&display=swap');
        
        @media (prefers-reduced-motion: no-preference) {
            @keyframes gradientSlide {
                0% { background-position: 0% 50%; }
                100% { background-position: 200% 50%; }
            }
            @keyframes shimmer {
                0% { left: -100%; }
                100% { left: 200%; }
            }
            @keyframes pulseStatus {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
            @keyframes scanLine {
                0% { top: -10%; opacity: 0; }
                10% { opacity: 1; }
                90% { opacity: 1; }
                100% { top: 110%; opacity: 0; }
            }
            @keyframes countUp {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        }

        /* Base Theme */
        .stApp {
            background-color: #020810 !important;
            color: #899bb5 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        .block-container { 
            padding-top: 0rem !important; 
            max-width: 1200px !important; 
        }
        [data-testid="stSidebar"], .stApp > header { display: none !important; }
        
        /* Typography */
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }
        
        /* Top Animated Line */
        .top-gradient-line {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 3px;
            background: linear-gradient(90deg, #00e5ff, #8b5cf6, #00e5ff);
            background-size: 200% 100%;
            animation: gradientSlide 4s linear infinite;
            z-index: 9999;
        }
        
        /* Hero Section */
        .hero-container {
            display: flex; justify-content: space-between; align-items: flex-start;
            padding: 3rem 0 3rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 3rem;
        }
        .hero-left { display: flex; gap: 1.5rem; align-items: center; }
        .glass-pill {
            width: 52px; height: 52px;
            border-radius: 16px;
            background: rgba(0,229,255,0.08);
            border: 1px solid rgba(0,229,255,0.2);
            backdrop-filter: blur(12px);
            display: flex; align-items: center; justify-content: center;
            position: relative;
            overflow: hidden;
        }
        .glass-pill::after {
            content: ''; position: absolute; width: 100%; height: 1px;
            background: #00e5ff; left: 0;
            animation: scanLine 6s linear infinite;
        }
        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 900; font-size: 2.4rem; color: #ffffff;
            margin: 0; line-height: 1; letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-family: 'Inter', sans-serif;
            text-transform: uppercase; font-size: 0.65rem; color: #1e3a52;
            letter-spacing: 0.15em; font-weight: 600; margin: 0; margin-top: 0.4rem;
        }
        
        /* Status Chip */
        .status-chip {
            display: flex; align-items: center; gap: 0.5rem;
            padding: 0.5rem 1rem; border-radius: 20px;
            background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05);
            font-size: 0.75rem; color: #899bb5; text-transform: uppercase; letter-spacing: 0.05em;
        }
        .status-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #10b981;
            animation: pulseStatus 2s infinite;
        }
        .status-chip.processing .status-dot {
            background: transparent;
            border: 2px solid #00e5ff;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 100% { transform: rotate(360deg); } }
        
        /* Step Track */
        .step-container {
            display: flex; flex-direction: column; align-items: center;
            height: 100%; position: relative; padding-top: 5px;
        }
        .step-circle {
            width: 32px; height: 32px; border-radius: 50%;
            border: 1px solid #00e5ff; background: #020810;
            display: flex; align-items: center; justify-content: center;
            font-family: 'Space Grotesk', sans-serif; font-size: 0.8rem; color: #00e5ff;
            font-weight: 700; z-index: 2; transition: all 0.3s ease;
        }
        .step-circle.is-filled {
            background: #00e5ff; color: #020810;
        }
        .step-line {
            width: 1px; height: calc(100% + 2rem);
            border-left: 1px dashed rgba(0,229,255,0.3);
            position: absolute; top: 37px; z-index: 1;
        }
        
        /* File Uploaders override */
        .stFileUploader { margin-bottom: 0 !important; }
        [data-testid="stFileUploadDropzone"] {
            background-color: transparent !important;
            border: 1.5px dashed rgba(0,229,255,0.15) !important;
            border-radius: 12px !important;
            padding: 2rem !important;
            min-height: 120px;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.3s ease;
        }
        [data-testid="stFileUploadDropzone"]:hover {
            border-color: rgba(0,229,255,0.5) !important;
            box-shadow: 0 0 0 4px rgba(0,229,255,0.06) !important;
        }
        [data-testid="stFileUploadDropzone"] small, [data-testid="stFileUploadDropzone"] span { display: none !important; }
        [data-testid="stFileUploadDropzone"]::before {
            content: 'Drag and drop file here';
            font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #4a5568;
            position: absolute; pointer-events: none;
        }
        [data-testid="stFileUploadDropzone"] button {
            background: rgba(0,229,255,0.05) !important;
            border: 1px solid rgba(0,229,255,0.2) !important;
            color: #00e5ff !important; border-radius: 8px !important;
            z-index: 10;
        }
        
        /* Specific accents for Left/Right */
        .right-accent [data-testid="stFileUploadDropzone"] {
            border-color: rgba(139,92,246,0.15) !important;
        }
        .right-accent [data-testid="stFileUploadDropzone"]:hover {
            border-color: rgba(139,92,246,0.5) !important;
            box-shadow: 0 0 0 4px rgba(139,92,246,0.06) !important;
        }
        .right-accent [data-testid="stFileUploadDropzone"] button {
            color: #8b5cf6 !important; border-color: rgba(139,92,246,0.2) !important;
            background: rgba(139,92,246,0.05) !important;
        }
        
        /* Hide SVG inside dropzone, replace with custom ones using CSS or let Streamlit handle the uploaded state */
        [data-testid="stFileUploadDropzone"] svg { display: none !important; }

        /* When file is uploaded (Streamlit changes DOM, we style the uploaded file section) */
        .stFileUploader section[data-testid="stUploadedFile"] {
            background: transparent !important;
            border: 1.5px solid rgba(0,229,255,0.15) !important;
            border-radius: 12px;
            padding: 1rem;
            display: flex; align-items: center;
        }
        .stFileUploader section[data-testid="stUploadedFile"] svg { display: block !important; color: #00e5ff !important; }

        /* Radio Buttons */
        .stRadio > div { flex-direction: row; gap: 2rem; margin-top: 0.5rem; }
        .stRadio label { color: #899bb5 !important; font-size: 0.85rem !important; }
        
        /* Inputs styling */
        .stNumberInput > div > div > input {
            background-color: #060f1c !important;
            border: 1px solid #0a1e35 !important;
            color: #fff !important;
            border-radius: 8px !important;
            height: 40px !important;
        }
        
        /* Main Button */
        .stButton > button {
            background-color: #020810 !important;
            border: 1.5px solid rgba(0,229,255,0.4) !important;
            color: #fff !important;
            border-radius: 14px !important;
            width: 100% !important; height: 56px !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 1.1rem !important; font-weight: 700 !important;
            transition: all 0.3s ease;
            position: relative; overflow: hidden;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .stButton > button:hover {
            background-color: rgba(0,229,255,0.06) !important;
            border-color: #00e5ff !important;
            text-shadow: 0 0 10px rgba(0,229,255,0.5);
        }
        .stButton > button::before {
            content: ''; position: absolute; top: 0; left: -100%;
            width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0,229,255,0.08), transparent);
            animation: shimmer 3s infinite;
        }
        
        /* Results Cards */
        .metric-card {
            background: #060f1c; border: 1px solid #0a1e35;
            border-radius: 12px; padding: 1.5rem;
            position: relative; overflow: hidden;
        }
        .metric-card.left-accent::before {
            content:''; position:absolute; top:0; left:0; width:100%; height:2px; background:#00e5ff;
        }
        .metric-card.right-accent::before {
            content:''; position:absolute; top:0; left:0; width:100%; height:2px; background:#8b5cf6;
        }
        .metric-value {
            font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem;
            font-weight: 700; color: #fff; margin: 0.5rem 0;
            animation: countUp 0.8s ease-out;
        }
        .metric-label { font-size: 0.75rem; color: #899bb5; text-transform: uppercase; letter-spacing: 0.05em; }
        
        .badge {
            display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        }
        .badge.ok { background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.2); }
        .badge.warn { background: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
        .badge.crit { background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid rgba(239,68,68,0.2); animation: blink 2s infinite; }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        /* Heatmap Frame */
        .heatmap-frame {
            background: #020810; border: 1px solid #0a1e35;
            border-radius: 16px; padding: 1rem;
            box-shadow: 0 0 30px rgba(0,229,255,0.05);
            transition: opacity 0.4s ease;
        }
    </style>
    """, unsafe_allow_html=True)
    
    status_text = "Analysis Complete" if getattr(st.session_state, 'done', False) else "System Ready"
    
    st.markdown(f"""
    <div class="top-gradient-line"></div>
    <div class="hero-container">
        <div class="hero-left">
            <div class="glass-pill">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00e5ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v2a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"/><path d="M19 8v3a2 2 0 0 1-2 2h-1.5a1.5 1.5 0 0 0-1.5 1.5V17a3 3 0 0 1-3 3H8a4 4 0 0 1-4-4v-5a5 5 0 0 1 5-5h10a1 1 0 0 1 1 1z"/></svg>
            </div>
            <div>
                <h1 class="hero-title">Gaitform</h1>
                <p class="hero-subtitle">AI-Driven Custom Orthotics Platform</p>
            </div>
        </div>
        <div class="status-chip" id="status-chip">
            <div class="status-dot"></div>
            <span>{status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------------
    # STEP 01
    # ---------------------------------------------------------
    col_step1, col_content1 = st.columns([1, 11])
    with col_content1:
        st.markdown("<p style='font-family: Space Grotesk; color: #e2e8f0; font-weight: 600; margin-bottom: 0.5rem;'>Kinematic Gait Video <span style='color: #4a5568;'>(Required)</span></p>", unsafe_allow_html=True)
        video_source = st.radio("Source", ["Upload File", "Select from Hub"], label_visibility="collapsed")
        video_path = None
        uploaded_video = None
        if video_source == "Upload File":
            uploaded_video = st.file_uploader("video", type=["mp4", "mov"], label_visibility="collapsed")
        else:
            st.info("Hub integration disabled for mock UI.")
            
    with col_step1:
        is_filled = "is-filled" if uploaded_video else ""
        st.markdown(f"""
        <div class="step-container">
            <div class="step-circle {is_filled}">01</div>
            <div class="step-line"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # STEP 02
    # ---------------------------------------------------------
    col_step2, col_content2 = st.columns([1, 11])
    with col_content2:
        st.markdown("<p style='font-family: Space Grotesk; color: #e2e8f0; font-weight: 600; margin-bottom: 0.5rem;'>3-D Foot Scans <span style='color: #4a5568;'>(STL)</span></p>", unsafe_allow_html=True)
        scan_source = st.radio("Scan Source", ["Upload STL", "No Scan (Procedural Placeholder)"], label_visibility="collapsed")
        
        c2_l, c2_r = st.columns(2)
        left_scan_file = None
        right_scan_file = None
        
        if scan_source == "Upload STL":
            with c2_l:
                st.markdown("<div class='left-accent'>", unsafe_allow_html=True)
                left_scan_file = st.file_uploader("Left STL", type=["stl"], label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            with c2_r:
                st.markdown("<div class='right-accent'>", unsafe_allow_html=True)
                right_scan_file = st.file_uploader("Right STL", type=["stl"], label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='opacity: 0.3; pointer-events: none;'><p style='text-decoration: line-through;'>Procedural Placeholder Active</p></div>", unsafe_allow_html=True)
            
    with col_step2:
        is_filled2 = "is-filled" if left_scan_file or right_scan_file or scan_source != "Upload STL" else ""
        st.markdown(f"""
        <div class="step-container">
            <div class="step-circle {is_filled2}">02</div>
            <div class="step-line"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # STEP 03
    # ---------------------------------------------------------
    col_step3, col_content3 = st.columns([1, 11])
    with col_content3:
        st.markdown("<p style='font-family: Space Grotesk; color: #e2e8f0; font-weight: 600; margin-bottom: 0.5rem;'>Navicular Tracking Videos</p>", unsafe_allow_html=True)
        c3_l, c3_r = st.columns(2)
        with c3_l:
            st.markdown("<div class='left-accent'>", unsafe_allow_html=True)
            l_nav_file = st.file_uploader("Left Navicular", type=["mp4"], label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        with c3_r:
            st.markdown("<div class='right-accent'>", unsafe_allow_html=True)
            r_nav_file = st.file_uploader("Right Navicular", type=["mp4"], label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
            
    with col_step3:
        is_filled3 = "is-filled" if l_nav_file or r_nav_file else ""
        st.markdown(f"""
        <div class="step-container">
            <div class="step-circle {is_filled3}">03</div>
            <div class="step-line"></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # STEP 04
    # ---------------------------------------------------------
    col_step4, col_content4 = st.columns([1, 11])
    with col_content4:
        st.markdown("<p style='font-family: Space Grotesk; color: #e2e8f0; font-weight: 600; margin-bottom: 0.5rem;'>Pressure & Patient Params</p>", unsafe_allow_html=True)
        csv_file = st.file_uploader("Upload Pressure Mat CSV", type=["csv"], label_visibility="collapsed")
        
        c4_l, c4_r = st.columns(2)
        with c4_l:
            st.markdown("<p style='font-size: 0.75rem; color: #899bb5; margin-bottom: 0.2rem; margin-top: 1rem;'>SHOE SIZE (MM)</p>", unsafe_allow_html=True)
            shoe_size_mm = st.number_input("Shoe Size (mm)", min_value=150.0, max_value=350.0, value=273.0, step=5.0, label_visibility="collapsed")
        with c4_r:
            st.markdown("<p style='font-size: 0.75rem; color: #899bb5; margin-bottom: 0.2rem; margin-top: 1rem;'>HEIGHT (M)</p>", unsafe_allow_html=True)
            patient_height_m = st.number_input("Patient Height (m)", min_value=1.0, max_value=2.5, value=1.75, step=0.01, label_visibility="collapsed")
            
    with col_step4:
        is_filled4 = "is-filled" if csv_file else ""
        st.markdown(f"""
        <div class="step-container">
            <div class="step-circle {is_filled4}">04</div>
        </div>
        """, unsafe_allow_html=True)
        
    # ---------------------------------------------------------
    # RUN BUTTON
    # ---------------------------------------------------------
    run_clicked = st.button("⚡ Run AI Pipeline — Generate Orthotics")

    if "done" not in st.session_state:
        st.session_state.done = False

    if run_clicked:
        if video_source == "Upload File" and uploaded_video is None:
            st.error("⚠️ A Kinematic Gait Video (MP4) is required to run the pipeline.")
            st.session_state.done = False
        else:
            # JS injection to change status chip
            st.components.v1.html("""
            <script>
                var chip = window.parent.document.getElementById("status-chip");
                if (chip) {
                    chip.className = "status-chip processing";
                    chip.querySelector("span").innerText = "Processing...";
                }
            </script>
            """, height=0)
            
            with st.spinner("Analyzing gait — mapping pressure — generating 3-D orthotics... (~30 s)"):
                try:
                    if video_source == "Upload File" and uploaded_video is not None:
                        video_path = _save(uploaded_video, "video.mp4")
                    else:
                        video_path = "sample_data/demo.mp4"
                        st.info("No video uploaded, using sample_data/demo.mp4 for demonstration.")
                        if not os.path.exists(video_path):
                            st.error("Sample video not found.")
                            st.stop()

                    slp = _save(left_scan_file, "scan_left.stl") if (scan_source == "Upload STL" and left_scan_file) else None
                    srp = _save(right_scan_file, "scan_right.stl") if (scan_source == "Upload STL" and right_scan_file) else None
                    nlp = _save(l_nav_file, "nav_l.mp4") if l_nav_file else None
                    nrp = _save(r_nav_file, "nav_r.mp4") if r_nav_file else None
                    pp = _save(csv_file, "pressure.csv") if csv_file else None

                    met = run_pipeline(
                        video_path=video_path,
                        height_m=patient_height_m,
                        scan_left=slp,
                        scan_right=srp,
                        shoe_size_mm=shoe_size_mm,
                        pressure_csv=pp,
                        navicular_video_left=nlp,
                        navicular_video_right=nrp,
                    )
                    st.session_state.met = met
                    st.session_state.done = True
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                    st.session_state.done = False

    # ---------------------------------------------------------
    # RESULTS SECTION
    # ---------------------------------------------------------
    if getattr(st.session_state, 'done', False):
        met = st.session_state.met
        st.markdown("<h2 style='margin-top: 3rem;'>AI Pipeline Results</h2>", unsafe_allow_html=True)
        
        res_l, res_r = st.columns([1, 1], gap="large")
        
        with res_l:
            st.markdown("<h3 style='font-size: 1.2rem; color: #fff;'>Kinematics Strip</h3>", unsafe_allow_html=True)
            
            cadence = met.get("cadence_steps_per_min")
            cadence_val = f"{cadence:.0f}" if cadence is not None else "0"
            nav_l_val = met.get("navicular_drop_L_mm", 0.0)
            nav_r_val = met.get("navicular_drop_R_mm", 0.0)
            lsi = met.get("limb_symmetry_index")
            lsi_val = f"{lsi:.1f}" if lsi is not None else "100.0"

            def nav_badge(v):
                if v > 10.0:
                    return "crit", "CRITICAL"
                elif v > 5.0:
                    return "warn", "ELEVATED"
                elif v > 0.0:
                    return "ok", "NORMAL"
                else:
                    return "ok", "NORMAL"
            
            nl_cls, nl_txt = nav_badge(nav_l_val)
            nr_cls, nr_txt = nav_badge(nav_r_val)
            
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div class="metric-card left-accent">
                    <div class="metric-label">Left Navicular Drop</div>
                    <div class="metric-value">{nav_l_val:.1f}<span style="font-size:1rem;color:#899bb5">mm</span></div>
                    <div class="badge {nl_cls}">{nl_txt}</div>
                </div>
                <div class="metric-card right-accent">
                    <div class="metric-label">Right Navicular Drop</div>
                    <div class="metric-value">{nav_r_val:.1f}<span style="font-size:1rem;color:#899bb5">mm</span></div>
                    <div class="badge {nr_cls}">{nr_txt}</div>
                </div>
                <div class="metric-card left-accent">
                    <div class="metric-label">Cadence</div>
                    <div class="metric-value">{cadence_val}<span style="font-size:1rem;color:#899bb5">spm</span></div>
                    <div class="badge ok">GAIT METRIC</div>
                </div>
                <div class="metric-card right-accent">
                    <div class="metric-label">Limb Symmetry Index</div>
                    <div class="metric-value">{lsi_val}<span style="font-size:1rem;color:#899bb5">%</span></div>
                    <div class="badge ok">GAIT METRIC</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<h3 style='font-size: 1.2rem; color: #fff; margin-top: 2rem;'>Print Plan Zones</h3>", unsafe_allow_html=True)
            
            # Build zone rows from print_instructions_left.json
            import json
            rows_html = ""
            jp = "print_instructions_left.json"
            if os.path.exists(jp):
                try:
                    with open(jp) as jf:
                        d = json.load(jf)
                    RIGIDITY_COLOR = {"firm": "#ef4444", "medium": "#f59e0b", "soft": "#10b981"}
                    INFILL_MAP = {"firm": "Gyroid 40%", "medium": "Hex 25%", "soft": "Cubic 15%"}
                    for zone in d.get("zones", []):
                        dot_color = RIGIDITY_COLOR.get(zone["target"], "#899bb5")
                        infill = INFILL_MAP.get(zone["target"], "Gyroid")
                        rows_html += f"""
                        <tr style="border-bottom: 1px solid #1a2333;">
                            <td style="padding: 1rem 0;">{zone["zone"].capitalize()}</td>
                            <td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;
                                background:{dot_color};margin-right:8px;"></span>{zone["target"].capitalize()}</td>
                            <td>{infill}</td>
                        </tr>"""
                except Exception:
                    pass
            
            if rows_html:
                st.markdown(f"""
                <table style="width:100%;text-align:left;border-collapse:collapse;
                    color:#e2e8f0;font-family:'Inter';font-size:0.9rem;">
                    <tr style="border-bottom:1px solid #2d3748;">
                        <th style="padding:1rem 0;color:#899bb5;text-transform:uppercase;">Zone</th>
                        <th style="padding:1rem 0;color:#899bb5;text-transform:uppercase;">Rigidity Target</th>
                        <th style="padding:1rem 0;color:#899bb5;text-transform:uppercase;">Infill Pattern</th>
                    </tr>
                    {rows_html}
                </table>""", unsafe_allow_html=True)
            else:
                st.info("Print plan zones details not available.")

        with res_r:
            st.markdown("<h3 style='font-size: 1.2rem; color: #fff;'>Zoning Heatmaps</h3>", unsafe_allow_html=True)
            foot_sel = st.radio("Foot", ["Left", "Right"], horizontal=True, label_visibility="collapsed")
            
            st.markdown("<div class='heatmap-frame'>", unsafe_allow_html=True)
            if foot_sel == "Left":
                hmap_l = "heatmap_left.png"
                if os.path.exists(hmap_l):
                    st.image(hmap_l, use_container_width=True)
                else:
                    st.info("Left heatmap not found.")
                stl_l = "orthotic_left.stl"
                if os.path.exists(stl_l):
                    with open(stl_l, "rb") as f:
                        st.download_button("⬇️ Download Left STL", data=f, file_name="orthotic_left.stl", key="dl_l")
                else:
                    st.info("Left orthotic STL not found.")
            else:
                hmap_r = "heatmap_right.png"
                if os.path.exists(hmap_r):
                    st.image(hmap_r, use_container_width=True)
                else:
                    st.info("Right heatmap not found.")
                stl_r = "orthotic_right.stl"
                if os.path.exists(stl_r):
                    with open(stl_r, "rb") as f:
                        st.download_button("⬇️ Download Right STL", data=f, file_name="orthotic_right.stl", key="dl_r")
                else:
                    st.info("Right orthotic STL not found.")
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------
    st.markdown("""
    <hr>
    <div style="text-align:center;color:#0d1e30;font-size:.7rem;padding:.4rem 0;">
      Gaitform &middot; AI Podiatry Platform &middot; <span style="color:#0ea5e9;">v2.3</span> &middot;
      For research use. Certified clinician oversight required for clinical deployment.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
