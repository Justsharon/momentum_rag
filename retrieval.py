"""
Vector retrieval against the Qdrant collection built in Phase 2.
Kept separate from api.py so Phase 4's evaluation script can import and
call `retrieve()` directly without spinning up the API.
"""

import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  
COLLECTION_NAME = "momentum_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  

_model = None
_client = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
    return _client


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Returns top_k chunks as dicts: {document_id, source_type, title, text, score}"""
    vector = _get_model().encode(query).tolist()
    hits = _get_client().query_points(
        collection_name=COLLECTION_NAME, query=vector, limit=top_k
    ).points

    return [
        {
            "document_id": h.payload["document_id"],
            "source_type": h.payload["source_type"],
            "title": h.payload["title"],
            "text": h.payload["text"],
            "score": h.score,
        }
        for h in hits
    ]