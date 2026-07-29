"""
Vector retrieval against the Qdrant collection built in Phase 2.
Kept separate from api.py so Phase 4's evaluation script can import and
call `retrieve()` directly without spinning up the API.

Uses fastembed (ONNX Runtime) instead of sentence-transformers (PyTorch) --
torch's memory footprint alone exceeds Render's free-tier 512MB limit.
fastembed's default model is the same 384 dimensions as before, so the
existing Qdrant collection config doesn't need to change, but the actual
embeddings differ from the old model -- re-run ingest.py after this change.
"""

import os
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  
COLLECTION_NAME = "momentum_documents"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

_model = None
_client = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
    return _client


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """Returns top_k chunks as dicts: {document_id, source_type, title, text, score}"""
    # query_embed (not embed) applies this model's query-specific prefix
    # internally -- BGE models are trained asymmetrically for queries vs docs.
    vector = list(_get_model().query_embed([query]))[0].tolist()
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