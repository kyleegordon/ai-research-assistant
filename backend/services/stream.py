# Write this yourself — core RAG component (streaming response)
from typing import AsyncGenerator


async def stream_response(prompt: str) -> AsyncGenerator[str, None]:
    """
    Steps to implement:
    1. Call Ollama's chat/generate endpoint with stream=True
    2. For each token/chunk received, yield it as an SSE-formatted string: f"data: {token}\\n\\n"
    3. Yield "data: [DONE]\\n\\n" when the stream ends
    """
    raise NotImplementedError
    yield  # makes this a generator
