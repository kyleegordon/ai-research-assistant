# Write this yourself — core RAG component (prompt construction)

MAX_PROMPT_TOKENS = 4096

def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    1. Formats each chunk with its source citation
    2. Assembles a prompt that instructs the model to answer using only the provided context
    3. Handles context length limits (trim or drop lower-ranked chunks if needed)
    4. Returns the final prompt string
    """

    no_context_msg = (
            "You have no relevant context available.\n\n"
            f"Question: {query}\n"
            "Answer: I don't know, the information could not be found."
        )

    # Handle empty chunks
    if not chunks:
        return no_context_msg

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

    tokens_remaining = MAX_PROMPT_TOKENS - (len(instruction) //3) - (len(suffix) //3)
    context_block = "\n"
    total_chunks = 0

    for chunk in formatted_chunks:
        if tokens_remaining - (len(chunk) // 3) <= 0:
            break
        
        context_block = f"{context_block} \n {chunk}"
        total_chunks += 1
        tokens_remaining = tokens_remaining - (len(chunk) // 3)

    if total_chunks == 0:
        return no_context_msg

    prompt = instruction + context_block + suffix

    return prompt