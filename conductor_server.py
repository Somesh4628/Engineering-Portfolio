# ==============================================================================
# SECTION 0: DEPENDENCY & ENVIRONMENT CHECK
# ==============================================================================
try:
    import os
    import uuid
    import json
    import shutil
    import subprocess
    from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
    from fastapi.responses import FileResponse, JSONResponse
    from pydantic import BaseModel
    from typing import Dict
except ImportError as e:
    print("="*60)
    print("!! MISSING REQUIRED LIBRARIES FOR CONDUCTOR SERVER !!")
    print(f"Error: {e}")
    print("\nPlease run the environment setup command to install all dependencies:")
    print("pip install --force-reinstall --no-cache-dir -r requirements.txt")
    print("\nSpecifically, the server needs: pip install fastapi uvicorn pydantic")
    print("="*60)
    exit()


# ==============================================================================
#  1. APPLICATION SETUP & STATE MANAGEMENT
# ==============================================================================

app = FastAPI(
    title="IntelliPipe Orchestration Server",
    description="The Conductor: Automates the AI model training and firmware forging pipeline.",
    version="1.2.0"
)

# In-memory dictionary to track the status of forgery tasks.
tasks_db: Dict[str, Dict] = {}

class ForgeTask(BaseModel):
    task_id: str
    status: str
    message: str
    artifact_path: str | None = None

# --- Path Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, "artifacts")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


# ==============================================================================
#  2. THE ORCHESTRATION LOGIC (BACKGROUND TASK)
# ==============================================================================

def run_forgery_pipeline(task_id: str, uploaded_blueprint_path: str):
    """
    This is the core function that runs in the background. It orchestrates
    the entire pipeline from blueprint to final firmware.
    """
    tasks_db[task_id] = {
        "status": "processing",
        "message": "Starting pipeline...",
        "artifact_path": None
    }
    
    temp_blueprint_path = os.path.join(PROJECT_ROOT, "SingleBranch_Test_v4.json")

    try:
        shutil.copy(uploaded_blueprint_path, temp_blueprint_path)

        # STEP 1: Generate Training Data
        tasks_db[task_id]["message"] = "Step 1/4: Generating training data..."
        print(f"[{task_id}] Running Data Factory...")
        
        data_process = subprocess.run(
            ["python", "config_tool.py"],
            input="3\n", text=True, capture_output=True, check=True, cwd=PROJECT_ROOT
        )
        print(f"[{task_id}] Data Factory Output:\n{data_process.stdout}")

        # STEP 2: Train AI Model
        tasks_db[task_id]["message"] = "Step 2/4: Training AI model..."
        print(f"[{task_id}] Running Oracle's Cradle (AI/ML/train_oracle.py)...")
        
        model_process = subprocess.run(
            ["python", os.path.join("AI", "ML", "train_oracle.py")],
            capture_output=True, text=True, check=True, cwd=PROJECT_ROOT
        )
        model_h_path = model_process.stdout.strip()
        print(f"[{task_id}] Model Trainer Output: {model_h_path}")
        if not os.path.exists(os.path.join(PROJECT_ROOT, model_h_path)):
            raise FileNotFoundError(f"Model training did not produce the expected model.h file at {model_h_path}")

        # STEP 3: Update Blueprint with new model path
        tasks_db[task_id]["message"] = "Step 3/4: Integrating AI model into blueprint..."
        print(f"[{task_id}] Updating blueprint with model path: {model_h_path}")
        
        with open(temp_blueprint_path, 'r') as f:
            blueprint_data = json.load(f)
        
        blueprint_data['ai_model'] = {
            "enabled": True,
            "model_file": model_h_path,
            "output_classes": ["normal", "steady_leak", "burst_leak", "clog", "sensor_drift"]
        }
        
        with open(temp_blueprint_path, 'w') as f:
            json.dump(blueprint_data, f, indent=2)
        
        # STEP 4: Forge Firmware
        tasks_db[task_id]["message"] = "Step 4/4: Forging final firmware..."
        print(f"[{task_id}] Running IntelliPipe Factory (Firmware Forge)...")
        
        forge_process = subprocess.run(
            ["python", "config_tool.py"],
            input="2\n", text=True, capture_output=True, check=True, cwd=PROJECT_ROOT
        )
        print(f"[{task_id}] Firmware Forge Output:\n{forge_process.stdout}")

        project_name = blueprint_data.get('project_details', {}).get('name', 'output')
        generated_artifact_name = f"{project_name}_FACTORY_BUILT.ino"
        generated_artifact_path = os.path.join(PROJECT_ROOT, generated_artifact_name)
        
        if not os.path.exists(generated_artifact_path):
            raise FileNotFoundError(f"Firmware forging did not produce the expected file: {generated_artifact_name}")

        final_artifact_path = os.path.join(ARTIFACTS_DIR, f"{task_id}_{generated_artifact_name}")
        shutil.move(generated_artifact_path, final_artifact_path)
        
        tasks_db[task_id] = {
            "status": "completed",
            "message": "Firmware forged successfully.",
            "artifact_path": final_artifact_path
        }
        print(f"[{task_id}] Pipeline COMPLETED successfully.")

    except subprocess.CalledProcessError as e:
        error_message = f"Pipeline failed at: {tasks_db[task_id]['message']}. Error: {e.stderr}"
        tasks_db[task_id] = {"status": "failed", "message": error_message, "artifact_path": None}
        print(f"[{task_id}] Pipeline FAILED. Error:\n{e.stderr}")
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        tasks_db[task_id] = {"status": "failed", "message": error_message, "artifact_path": None}
        print(f"[{task_id}] Pipeline FAILED with unexpected error: {str(e)}")
    finally:
        if os.path.exists(temp_blueprint_path):
            os.remove(temp_blueprint_path)

# ==============================================================================
#  3. API ENDPOINTS
# ==============================================================================

@app.post("/forge", response_model=ForgeTask)
async def forge_firmware(background_tasks: BackgroundTasks, blueprint: UploadFile = File(...)):
    if not blueprint.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .json blueprint.")

    task_id = str(uuid.uuid4())
    blueprint_path = os.path.join(UPLOADS_DIR, f"{task_id}_{blueprint.filename}")
    with open(blueprint_path, "wb") as buffer:
        shutil.copyfileobj(blueprint.file, buffer)

    background_tasks.add_task(run_forgery_pipeline, task_id, blueprint_path)

    initial_status = {
        "task_id": task_id,
        "status": "queued",
        "message": "Your forgery request has been received and is waiting to start.",
        "artifact_path": None
    }
    tasks_db[task_id] = initial_status
    return JSONResponse(status_code=202, content=initial_status)


@app.get("/status/{task_id}", response_model=ForgeTask)
async def get_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task


@app.get("/download/{task_id}")
async def download_artifact(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    
    if task["status"] != "completed" or not task["artifact_path"]:
        raise HTTPException(status_code=404, detail="Artifact not ready or task failed.")

    artifact_path = task["artifact_path"]
    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail="Artifact file not found on server.")

    return FileResponse(path=artifact_path, filename=os.path.basename(artifact_path))


@app.get("/")
async def root():
    return {"message": "IntelliPipe Orchestration Server is online. POST your blueprint to /forge to begin."}

# To run this server, use the command:
# uvicorn conductor_server:app --reload
