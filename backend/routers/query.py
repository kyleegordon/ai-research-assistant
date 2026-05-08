from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.retrieval import retrieve_chunks
from services.prompt import build_prompt
from services.stream import stream_response

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/query")
async def query(request: QueryRequest):
    chunks = retrieve_chunks(query=request.question, top_k=request.top_k)
    prompt = build_prompt(query=request.question, chunks=chunks)

    return StreamingResponse(
        stream_response(prompt),
        media_type="text/event-stream",
    )
