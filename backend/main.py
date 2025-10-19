# main.py  (fastapi backend code)
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_dir = "uploaded_files"
os.makedirs(upload_dir, exist_ok=True)


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    fpath = os.path.join(upload_dir, file.filename)
    with open(fpath, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"message": "file uploaded", "filename": file.filename}
