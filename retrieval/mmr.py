"""Maximum Marginal Relevance -- trims a reranked list down to diverse, non-redundant chunks."""
import numpy as np
from embeddings.embedder import embed_texts


def mmr_filter(query_embedding: list, candidates: list, top_k: int = 5, lambda_param: float = 0.5) -> list:
    if not candidates:
        return []
    if len(candidates) <= top_k:
        return candidates

    texts = [c["text"] for c in candidates]
    cand_embeddings = np.array(embed_texts(texts))
    q_emb = np.array(query_embedding)

    def cos_sim(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    relevance = [cos_sim(q_emb, e) for e in cand_embeddings]
    selected_idx = []
    remaining_idx = list(range(len(candidates)))

    while len(selected_idx) < top_k and remaining_idx:
        if not selected_idx:
            best = max(remaining_idx, key=lambda i: relevance[i])
        else:
            def mmr_score(i):
                diversity = max(cos_sim(cand_embeddings[i], cand_embeddings[j]) for j in selected_idx)
                return lambda_param * relevance[i] - (1 - lambda_param) * diversity
            best = max(remaining_idx, key=mmr_score)
        selected_idx.append(best)
        remaining_idx.remove(best)

    return [candidates[i] for i in selected_idx]
