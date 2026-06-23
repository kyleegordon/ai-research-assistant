# Write this yourself — core RAG component (streaming response)
import ollama
from typing import AsyncGenerator


async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
    """
    1. Calls Ollama's chat/generate endpoint with stream=True
    2. For each token/chunk received, yields it as an SSE-formatted string: f"data: {token}\\n\\n"
    3. Yields "data: [DONE]\\n\\n" when the stream ends
    """
    client = ollama.AsyncClient()
    async for chunk in await client.generate(model="llama3.2", prompt=prompt, stream=True):
        yield f"data: {chunk.response}\n\n"

    yield "data: [DONE]\n\n"