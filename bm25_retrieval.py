"""
BM25 (keyword) retrieval over the `documents` table in Postgres -- the
same source-of-truth table that ingest.py refreshes on every run.

Kept as its own module (separate from retrieval.py's vector search) so
retrieval_eval.py can call each method independently and compare them.
"""

import os
import re
import psycopg2
import psycopg2.extras
from rank_bm25 import BM25Okapi

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/momentum"
)

_bm25 = None
_docs = None  # parallel list of {document_id, source_type, title, text}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _load_index():
    """Loads all documents from Postgres and builds the BM25 index once.
    Call reload_index() after re-running ingest.py so this picks up changes."""
    global _bm25, _docs
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, source_type, title, text FROM documents")
            rows = cur.fetchall()
    finally:
        conn.close()

    _docs = [
        {"document_id": str(r["id"]), "source_type": r["source_type"],
         "title": r["title"], "text": r["text"]}
        for r in rows
    ]
    tokenized_corpus = [_tokenize(d["text"]) for d in _docs]
    _bm25 = BM25Okapi(tokenized_corpus)


def reload_index():
    """Force a rebuild -- call this after re-ingesting new data."""
    global _bm25, _docs
    _bm25, _docs = None, None
    _load_index()


def retrieve_bm25(query: str, top_k: int = 5) -> list[dict]:
    if _bm25 is None:
        _load_index()

    scores = _bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(_docs, scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {**doc, "score": float(score)}
        for doc, score in ranked
    ]