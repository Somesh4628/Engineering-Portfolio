from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil

app = FastAPI(title="Gaitform Mobile Hub")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Gaitform Mobile Hub. Use /api/upload to upload files."}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = file.filename if file.filename else "uploaded"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": filename, "message": "Upload successful"}


@app.get("/api/uploads")
async def list_uploads():
    if not os.path.exists(UPLOAD_DIR):
        return {"uploads": []}
    files = os.listdir(UPLOAD_DIR)
    return {"uploads": files}


@app.get("/api/uploads/{filename}")
async def get_upload(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
