# Write this yourself — core RAG component (streaming response)
import ollama
from typing import AsyncGenerator

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
    """
    1. Calls Ollama's chat/generate endpoint with stream=True
    2. For each token/chunk received, yields it as an SSE-formatted string: f"data: {token}\\n\\n"
    3. Yields "data: [DONE]\\n\\n" when the stream ends
    """
    client = ollama.AsyncClient(host=OLLAMA_BASE_URL)
    async for chunk in await client.generate(model=OLLAMA_MODEL, prompt=prompt, stream=True):
        yield f"data: {chunk.response}\n\n"

    yield "data: [DONE]\n\n"