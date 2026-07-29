"""
Single shared fastembed model instance. Both query-side (retrieval.py) and
document-side (ingest.py, indexing.py) embedding go through this module so
a running API process only ever loads the ONNX model once, no matter how
many different code paths need embeddings -- this matters on memory-capped
hosts like Render's free tier.
"""

from fastembed import TextEmbedding

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384 

_model = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL)
    return _model


def embed_query(text: str) -> list[float]:
    """For search queries -- uses this model's query-specific prefix internally."""
    return list(get_model().query_embed([text]))[0].tolist()


def embed_documents(texts: list[str]) -> list[list[float]]:
    """For document/chunk text. Batched -- pass every chunk you need embedded
    in one call rather than looping, it's meaningfully faster."""
    return [v.tolist() for v in get_model().embed(texts)]