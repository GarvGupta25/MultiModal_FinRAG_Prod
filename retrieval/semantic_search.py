"""Basic semantic retrieval: embed query -> ChromaDB search."""
from embeddings.embedder import embed_query


def semantic_search(vector_store, query: str, top_k: int = 5) -> list:
    q_emb = embed_query(query)
    results = vector_store.query(q_emb, top_k=top_k)
    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]
    for i in range(len(docs)):
        hits.append({
            "id": ids[i], "text": docs[i], "metadata": metas[i],
            "score": 1 - dists[i] if dists[i] is not None else None,
        })
    return hits
