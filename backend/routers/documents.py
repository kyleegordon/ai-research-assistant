from fastapi import APIRouter, HTTPException

from services.documents import list_documents, delete_document

router = APIRouter()


@router.get("/documents")
async def get_documents():
    return {"documents": list_documents()}


@router.delete("/documents/{filename}")
async def remove_document(filename: str):
    deleted = delete_document(filename)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No document found with filename '{filename}'.")
    return {"filename": filename, "chunks_deleted": deleted}
