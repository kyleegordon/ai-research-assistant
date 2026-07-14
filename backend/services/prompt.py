# Write this yourself — core RAG component (prompt construction)

MAX_PROMPT_TOKENS = 4096
MAX_HISTORY_TOKENS = 1024
MAX_HISTORY_TURNS = 10

def estimate_tokens(text):
    return len(text) // 3

def trim_history(history, max_tokens, max_turns):
    kept = []
    tokens_used = 0

    # walk newest -> oldest, stop at whichever limit hits first
    for turn in reversed(history[-max_turns:]):
        t = estimate_tokens(turn.content) 
        if tokens_used + t > max_tokens:
            break
        kept.insert(0, {"role": turn.role, "content": turn.content}) # re-insert at front to restore chronological order
        tokens_used += t

    return kept, tokens_used


def build_prompt(query: str, chunks: list[dict], history=[]) -> list[dict]:
    """
    1. Formats each chunk with its source citation
    2. Assembles a prompt that instructs the model to answer using only the provided context
    3. Handles context length limits (trim or drop lower-ranked chunks if needed)
    4. Returns the final prompt string
    """

    trimmed_history, _ = trim_history(history, MAX_HISTORY_TOKENS, MAX_HISTORY_TURNS)

    instruction = (
        "You are a helpful research assistant that only answers from the provided context. Answer directly with no preamble.\n"
        "If the context contains the answer, provide a direct answer with a citation in this exact format: (Source: <filename>).\n"
        "If the context does not contain the answer, state exactly \"I don't know, the information could not be found.\" \n\n"
        "\n---\n\nExample:\n"
        "Question: What is the capital of France?\n"
        "Answer: Paris is the capital of France. (Source: geography.pdf)\n\n"
    )

    system_message = { "role": "system", "content": instruction}

    no_context_msg = (
            "You have no relevant context available.\n\n"
            f"Question: {query}\n"
            "Answer: I don't know, the information could not be found."
        )
    
    # Handle empty chunks
    if not chunks:
        return [system_message] + trimmed_history + [{"role": "user", "content": no_context_msg}]

    # Format each chunk with source citation
    formatted_chunks = []
    for chunk in chunks:
        page = chunk.get('page', '')
        page_str = f", p. {page}" if page else ""
        block = f"---\nSource: {chunk['source']}{page_str}\n\"{chunk['text']}\"\n"
        formatted_chunks.append(block)

    tokens_remaining = MAX_PROMPT_TOKENS - estimate_tokens(instruction)
    context_block = "\n"
    total_chunks = 0

    for chunk in formatted_chunks:
        if tokens_remaining - estimate_tokens(chunk) <= 0:
            break
        
        context_block = f"{context_block} \n {chunk}"
        total_chunks += 1
        tokens_remaining = tokens_remaining - estimate_tokens(chunk)

    if total_chunks == 0:
        return [system_message] + trimmed_history + [{"role": "user", "content": no_context_msg}]
    
    current_message = {
        "role": "user",
        "content": context_block + f"\n\nQuestion: {query}"
    }


    return [system_message] + trimmed_history + [current_message]