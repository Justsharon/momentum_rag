"""
Hybrid retrieval: combines vector search (retrieval.py) and BM25
(bm25_retrieval.py) using Reciprocal Rank Fusion (RRF). RRF is used instead
of a weighted score blend because vector cosine scores and BM25 scores
live on completely different scales -- RRF only needs each method's
*rank order*, so there's nothing to normalize or tune.
"""

from retrieval import retrieve as retrieve_vector
from bm25_retrieval import retrieve_bm25

RRF_K = 60  # standard default from the original RRF paper


def retrieve_hybrid(query: str, top_k: int = 5, fetch_k: int = 20) -> list[dict]:
    vector_hits = retrieve_vector(query, top_k=fetch_k)
    bm25_hits = retrieve_bm25(query, top_k=fetch_k)

    fused_scores: dict[str, float] = {}
    doc_lookup: dict[str, dict] = {}

    for rank, hit in enumerate(vector_hits):
        doc_id = hit["document_id"]
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (RRF_K + rank + 1)
        doc_lookup[doc_id] = hit

    for rank, hit in enumerate(bm25_hits):
        doc_id = hit["document_id"]
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (RRF_K + rank + 1)
        doc_lookup.setdefault(doc_id, hit)

    ranked_ids = sorted(fused_scores, key=fused_scores.get, reverse=True)[:top_k]

    return [
        {**doc_lookup[doc_id], "score": fused_scores[doc_id]}
        for doc_id in ranked_ids
    ]