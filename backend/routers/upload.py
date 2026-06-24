import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File

from config import UPLOAD_DIR
from services.documents import delete_document
from services.ingest import ingest_document

router = APIRouter()

ALLOWED_TYPES = {"application/pdf", "text/plain"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and text files are supported.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file is missing a filename.")

    # Strip any directory components so the stored filename (also used as the
    # ChromaDB "source" value) can never contain "/" or ".." segments.
    filename = os.path.basename(file.filename)

    # Clear any chunks from a previous ingest of this filename first: collection.add()
    # in ingest_document() keys chunks by a deterministic "{filename}_chunk_{i}" id and
    # does not upsert, so re-uploading the same filename would otherwise leave stale
    # chunks behind (unchanged content at overlapping indices, orphaned extras beyond
    # the new chunk count).
    delete_document(filename)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, filename)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = ingest_document(file_path=dest, filename=filename)
    except Exception as exc:
        # The previous version's chunks were already removed above, so a failed
        # re-index here would otherwise look like "nothing happened" instead of
        # "the old version is gone" — surface that explicitly rather than letting
        # FastAPI's generic 500 hide it.
        raise HTTPException(
            status_code=500,
            detail=(
                f'Indexing "{filename}" failed ({exc}). '
                "Its previous version was already removed, so please try uploading it again."
            ),
        ) from exc

    return {"filename": filename, **result}
