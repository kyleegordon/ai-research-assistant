import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File

from services.ingest import ingest_document

router = APIRouter()

UPLOAD_DIR = "./uploads"
ALLOWED_TYPES = {"application/pdf", "text/plain"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and text files are supported.")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, file.filename)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    result = ingest_document(file_path=dest, filename=file.filename)
    return {"filename": file.filename, **result}
