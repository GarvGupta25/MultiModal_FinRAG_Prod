"""Builds the final prompt: retrieved context + question, with citation instructions."""

def build_prompt(query: str, chunks: list) -> str:
    context_blocks = []
    for i, c in enumerate(chunks):
        src = c["metadata"].get("source", "unknown") if c.get("metadata") else "unknown"
        context_blocks.append(f"[Source {i+1}: {src}]\n{c['text']}")
    context = "\n\n".join(context_blocks)

    prompt = f"""You are a financial document analyst. Answer the question using ONLY the context below.
If the answer is not in the context, say so clearly. Cite sources as [Source N] inline.

Context:
{context}

Question: {query}

Answer:"""
    return prompt
