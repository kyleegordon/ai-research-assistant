# Write this yourself — core RAG component (prompt construction)


def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    1. Formats each chunk with its source citation
    2. Assembles a prompt that instructs the model to answer using only the provided context
    3. Handles context length limits (trim or drop lower-ranked chunks if needed)
    4. Returns the final prompt string
    """

    # Handle empty chunks
    if not chunks:
        return (
            "You have no relevant context available.\n\n"
            f"Question: {query}\n"
            "Answer: I don't know, the information could not be found."
        )

    # Format each chunk with source citation
    formatted_chunks = []
    for chunk in chunks:
        page = chunk.get('page', '')
        page_str = f", p. {page}" if page else ""
        block = f"---\nSource: {chunk['source']}{page_str}\n\"{chunk['text']}\"\n"
        formatted_chunks.append(block)

    instruction = (
        "You are a helpful research assistant that only answers from the provided context. Answer directly with no preamble.\n"
        "If the context contains the answer, provide a direct answer with a citation in this exact format: (Source: <filename>).\n"
        "If the context does not contain the answer, state exactly \"I don't know, the information could not be found.\" \n\n"
    )
    suffix = (
        "\n---\n\nExample:\n"
        "Question: What is the capital of France?\n"
        "Answer: Paris is the capital of France. (Source: geography.pdf)\n\n"
        f"\n---\n\nQuestion: {query}\nAnswer:"
    )

    context_block = "\n".join(formatted_chunks)
    prompt = instruction + context_block + suffix

    return prompt