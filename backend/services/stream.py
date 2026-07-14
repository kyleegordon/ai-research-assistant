# Write this yourself — core RAG component (streaming response)
import ollama
from typing import AsyncGenerator

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_NUM_CTX

async def stream_response(messages: list[dict]) -> AsyncGenerator[str, None]:
    """
    1. Calls Ollama's chat/generate endpoint with stream=True
    2. For each token/chunk received, yields it as an SSE-formatted string: f"data: {token}\\n\\n"
    3. Yields "data: [DONE]\\n\\n" when the stream ends
    """
    client = ollama.AsyncClient(host=OLLAMA_BASE_URL)
    try:
        async for chunk in await client.chat(
            model=OLLAMA_MODEL, 
            messages=messages, 
            stream=True, 
            options={"num_ctx": OLLAMA_NUM_CTX}
            ):
            yield f"data: {chunk.message.content}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"event: error\ndata: {str(e)}\n\n"