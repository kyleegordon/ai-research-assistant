# Write this yourself — core RAG component (prompt construction)


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Steps to implement:
    1. Format each chunk with its source citation
    2. Assemble a prompt that instructs the model to answer using only the provided context
    3. Handle context length limits (trim or drop lower-ranked chunks if needed)
    4. Return the final prompt string
    """
    raise NotImplementedError
