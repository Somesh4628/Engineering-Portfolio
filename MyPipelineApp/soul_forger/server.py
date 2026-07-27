# Location: server.py (Complete Replacement)

# --- Cleaned-up Imports ---
import os
import json
import traceback
import h5py
import io
import re
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from .soul_engine import SystemBlueprint

# --- Basic App Setup ---
app = FastAPI(
    title="Soul Forger",
    description="A web-based UI for creating intelligent fluidic system blueprints.",
)

# --- Path Configuration ---
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
STATIC_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "static")
TEMPLATE_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, "templates")

# --- Mount Static Files and Templates ---
app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")
templates = Jinja2Templates(directory=TEMPLATE_DIRECTORY)


# --- API Endpoints (The "Routes") ---


@app.get("/", response_class=HTMLResponse)
async def serve_home_page(request: Request):
    """Serves the main index.html page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/inspect_model", response_class=JSONResponse)
async def inspect_model(model_file: UploadFile = File(...)):
    """
    Inspects an uploaded .h5 model file to determine its output shape.
    """
    try:
        file_content = await model_file.read()
        with io.BytesIO(file_content) as file_like_object:
            with h5py.File(file_like_object, "r") as hf:
                if "model_config" in hf.attrs:
                    model_config = json.loads(hf.attrs["model_config"])
                    last_layer = model_config["config"]["layers"][-1]
                    if "units" in last_layer["config"]:
                        class_count = last_layer["config"]["units"]
                        return JSONResponse(content={"class_count": class_count})
        return JSONResponse(
            content={"error": "Could not determine model output shape."},
            status_code=400,
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Invalid or corrupted H5 file: {str(e)}"},
            status_code=500,
        )


@app.post("/validate", response_class=HTMLResponse)
async def handle_validation(request: Request, blueprint_file: UploadFile = File(...)):
    """
    Receives an uploaded file, validates it using our soul_engine,
    and returns the main page with the validation result.
    """
    result_message = ""
    result_class = ""
    error_details = []

    try:
        contents = await blueprint_file.read()
        data_str = contents.decode("utf-8")
        data_dict = json.loads(data_str)

        SystemBlueprint(**data_dict)

        result_class = "success"
        result_message = (
            f"✅ SUCCESS: The blueprint '{blueprint_file.filename}' is valid."
        )

    except ValidationError as e:
        result_class = "error"
        result_message = (
            f"❌ ERROR: The blueprint '{blueprint_file.filename}' is NOT valid."
        )
        for error in e.errors():
            location = " -> ".join(map(str, error["loc"]))
            message = error["msg"]
            error_details.append(f"At '{location}': {message}")

    except Exception as e:
        result_class = "error"
        result_message = "❌ UNEXPECTED ERROR: Could not process the file."
        error_details.append(str(e))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result_class": result_class,
            "result_message": result_message,
            "error_details": error_details,
        },
    )


# AUTOMATION UPGRADE: The function signature is changed to accept the optional 'labels_file' upload.
@app.post("/create", response_class=HTMLResponse)
async def handle_creation(request: Request, labels_file: UploadFile = File(None)):
    """
    Receives form data, assembles a blueprint, optimizes it, validates it,
    assigns pins, and saves the final product.
    """
    form_data = await request.form()
    result_message = ""
    result_class = ""
    error_details = []
    optimization_report = []
    flawed_ids = []  # CAMPAIGN 15.D

    try:
        # --- Stage 1: Assemble Nodes from form data ---
        nodes_to_process = []
        i = 1
        while f"node_id_{i}" in form_data:
            is_critical = form_data.get(f"node_is_critical_{i}") == "true"
            nodes_to_process.append(
                {
                    "node_id": form_data.get(f"node_id_{i}"),
                    "type": form_data.get(f"node_type_{i}"),
                    "component_type": form_data.get(f"component_type_{i}"),
                    "label": form_data.get(f"node_label_{i}"),
                    "orientation": 0,
                    "is_critical": is_critical,
                }
            )
            i += 1

        # --- Stage 2: Assemble Pipes from form data ---
        pipes_to_process = []
        i = 1
        while f"pipe_id_{i}" in form_data:
            pipe_id = form_data.get(f"pipe_id_{i}")
            sensor_id_raw = str(form_data.get(f"pipe_sensor_id_{i}") or "").strip()
            gpio_pin_raw = str(form_data.get(f"pipe_gpio_pin_{i}") or "").strip()
            k_factor_raw = str(form_data.get(f"pipe_sensor_kfactor_{i}") or "").strip()

            sensor_id = sensor_id_raw if sensor_id_raw else f"S_{pipe_id}"

            if gpio_pin_raw:
                try:
                    gpio_pin = int(gpio_pin_raw)
                except ValueError:
                    raise ValueError(
                        f"GPIO pin '{gpio_pin_raw}' for pipe '{pipe_id}' must be an integer."
                    )
            else:
                gpio_pin = -1

            if k_factor_raw:
                try:
                    k_factor = float(k_factor_raw)
                except ValueError:
                    raise ValueError(
                        f"K-Factor '{k_factor_raw}' for pipe '{pipe_id}' must be numeric."
                    )
            else:
                k_factor = 450.0

            if k_factor <= 0:
                raise ValueError(
                    f"K-Factor for pipe '{pipe_id}' must be greater than zero."
                )

            length_raw = str(form_data.get(f"pipe_length_{i}") or "").strip()
            diameter_raw = str(form_data.get(f"pipe_diameter_{i}") or "").strip()
            try:
                length_value = float(length_raw) if length_raw else 1.0
            except ValueError:
                raise ValueError(
                    f"Length value '{length_raw}' for pipe '{pipe_id}' must be numeric."
                )
            try:
                diameter_value = float(diameter_raw) if diameter_raw else 0.01
            except ValueError:
                raise ValueError(
                    f"Diameter value '{diameter_raw}' for pipe '{pipe_id}' must be numeric."
                )

            pipes_to_process.append(
                {
                    "pipe_id": pipe_id,
                    "source_node": form_data.get(f"pipe_source_{i}"),
                    "target_node": form_data.get(f"pipe_target_{i}"),
                    "flow_sensor": {
                        "sensor_id": sensor_id,
                        "label": f"Sensor for Pipe {pipe_id}",
                        "gpio_pin": gpio_pin,
                        "k_factor_ppl": k_factor,
                    },
                    "properties": {
                        "length_m": length_value,
                        "inner_diameter_m": diameter_value,
                    },
                }
            )
            i += 1

        # --- Stage 2.5: Auto-Correct Node Types (Topological Honesty) ---
        source_node_ids = {pipe["source_node"] for pipe in pipes_to_process}
        target_node_ids = {pipe["target_node"] for pipe in pipes_to_process}
        for node in nodes_to_process:
            node_id = node["node_id"]
            is_source = node_id in source_node_ids
            is_target = node_id in target_node_ids
            if is_source and not is_target:
                node["type"] = "inlet"
            elif not is_source and is_target:
                node["type"] = "outlet"
            elif is_source and is_target:
                node["type"] = "junction"

        # --- Campaign 3 & 15 Upgrades ---
        network_info_to_process = None
        ssid = form_data.get("network_ssid")
        if ssid:
            network_info_to_process = {
                "ssid": ssid,
                "password": form_data.get("network_password", ""),
                "telemetry_endpoint": form_data.get("telemetry_endpoint"),
            }

        ai_enabled = form_data.get("ai_model_enabled") == "true"

        # --- AUTOMATION UPGRADE ---
        # Read the class names directly from the uploaded .labels.json file.
        output_classes = []
        if ai_enabled and labels_file:
            contents = await labels_file.read()
            output_classes = json.loads(contents)
            if not isinstance(output_classes, list):
                # Ensure the JSON is a list to prevent errors downstream.
                raise ValueError("Labels file is not a valid JSON list.")
        # --- END OF UPGRADE ---

        actions_to_process = []
        i = 1
        while f"action_fault_class_{i}" in form_data:
            fault_class = form_data.get(f"action_fault_class_{i}")
            recommendation = form_data.get(f"action_recommendation_{i}")
            target_node = form_data.get(f"action_target_node_{i}")
            if fault_class and recommendation:
                actions_to_process.append(
                    {
                        "fault_class": fault_class,
                        "recommendation": recommendation,
                        "target_node_id": target_node if target_node else None,
                    }
                )
            i += 1

        ai_model_to_process = {
            "enabled": ai_enabled,
            "model_file": form_data.get("ai_model_filename") or "none.h",
            "output_classes": output_classes,
            "prescriptive_actions": actions_to_process,
        }

        # --- Stage 2.8: Available Pin Pool ---
        DEFAULT_AVAILABLE_PINS = [5, 18, 19, 21, 22, 23, 25, 26]
        available_pins_input = str(form_data.get("available_pins") or "").strip()
        available_pins = []
        if available_pins_input:
            for token in available_pins_input.split(","):
                pin_token = token.strip()
                if not pin_token:
                    continue
                if not re.fullmatch(r"-?\d+", pin_token):
                    raise ValueError(
                        f"Invalid GPIO pin entry '{pin_token}'. Please provide integers separated by commas."
                    )
                available_pins.append(int(pin_token))
        if not available_pins:
            available_pins = DEFAULT_AVAILABLE_PINS

        # --- Stage 3: Assemble the complete blueprint data dictionary ---
        blueprint_data = {
            "project_details": {
                "name": form_data.get("project_name", "Untitled"),
                "version": "5.1-FactoryCompatible",
            },
            "ai_model": ai_model_to_process,
            "network_info": network_info_to_process,
            "nodes": nodes_to_process,
            "pipes": pipes_to_process,
            "available_pins": available_pins,
            "system_tuning_parameters": {
                "default_profile_id": "normal_balanced",
                "profiles": [
                    {
                        "id": "normal_balanced",
                        "label": "Normal (Balanced)",
                        "update_interval_ms": 1000,
                        "median_window_size": 5,
                        "ema_alpha": 0.4,
                        "calibration_sample_count": 20,
                        "deviation_std_dev_factor": 1.5,
                        "calibration_min_start_flow_lps": 0.1,
                        "calib_start_confirm_cycles": 3,
                        "leak_confirmation_cycles": 4,
                        "drift_confirmation_cycles": 10,
                        "max_consecutive_faults": 10,
                        "near_zero_flow_lps": 0.05,
                        "max_realistic_flow_lps": 20.0,
                        "stuck_sensor_cycles": 15,
                        "max_log_events": 20,
                        "debug_validity_level": 1,
                    }
                ],
            },
        }

        # --- Step 4: Create, Optimize, and Finalize Blueprint ---
        new_blueprint = SystemBlueprint(**blueprint_data)  # type: ignore[arg-type]
        new_blueprint.complete_and_optimize()
        new_blueprint.assign_pins()

        # --- Step 5: Save the fully compliant blueprint to a file ---
        output_filename = (
            f"{new_blueprint.project_details.name.replace(' ', '_').lower()}.json"
        )
        full_output_path = os.path.join(SCRIPT_DIRECTORY, output_filename)
        new_blueprint.to_file(full_output_path)

        result_class = "success"
        result_message = (
            f"✅ SUCCESS: Blueprint '{output_filename}' created and optimized!"
        )
        optimization_report = new_blueprint.optimization_report

    except ValidationError as e:
        result_class = "error"
        result_message = "❌ LOGICAL ERROR: Your design is invalid. Please check your connections and rules."

        # --- CAMPAIGN 15.D UPGRADE: Parse error messages to find flawed component IDs ---
        for error in e.errors():
            location = " -> ".join(map(str, error.get("loc", "")))
            msg = error.get("msg", "")
            error_details.append(f"At '{location}': {msg}")

            # Use regex to find IDs like 'node_id' or 'pipe_id' in the error message
            match = re.search(r"'([^']*)'", msg)
            if match:
                flawed_ids.append(match.group(1))

    except Exception:
        result_class = "error"
        result_message = (
            "❌ UNEXPECTED SERVER ERROR: An error occurred during creation."
        )
        traceback.print_exc()
        error_details.append("Check the server console for details.")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result_class": result_class,
            "result_message": result_message,
            "error_details": error_details,
            "optimization_report": optimization_report,
            "flawed_ids_json": json.dumps(
                flawed_ids
            ),  # Pass flawed IDs as a JSON string
        },
    )
