from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.retrieval import retrieve_chunks, build_retrieval_query
from services.prompt import build_prompt
from services.stream import stream_response

router = APIRouter()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=20)
    history: list[Message] = Field(default_factory=list)


@router.post("/query")
async def query(request: QueryRequest):
    retrieval_query = build_retrieval_query(request.question, request.history)
    chunks = retrieve_chunks(query=retrieval_query, top_k=request.top_k)
    messages = build_prompt(query=request.question, chunks=chunks, history=request.history)

    return StreamingResponse(
        stream_response(messages),
        media_type="text/event-stream",
    )
