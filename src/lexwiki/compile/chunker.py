"""Split large documents into chunks that fit LLM context windows."""

from __future__ import annotations

from lexwiki.llm.tokens import estimate_tokens


def chunk_text(text: str, max_tokens: int = 12000, overlap_tokens: int = 500) -> list[str]:
    """Split text into chunks of approximately max_tokens each.

    Tries to split on paragraph boundaries. Includes overlap between chunks
    for context continuity.
    """
    if estimate_tokens(text) <= max_tokens:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        if current_tokens + para_tokens > max_tokens and current_chunk:
            chunks.append("\n\n".join(current_chunk))

            # Keep last few paragraphs as overlap
            overlap_parts: list[str] = []
            overlap_count = 0
            for p in reversed(current_chunk):
                pt = estimate_tokens(p)
                if overlap_count + pt > overlap_tokens:
                    break
                overlap_parts.insert(0, p)
                overlap_count += pt

            current_chunk = overlap_parts
            current_tokens = overlap_count

        current_chunk.append(para)
        current_tokens += para_tokens

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks
