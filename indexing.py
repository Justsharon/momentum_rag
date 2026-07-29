"""
Incremental indexing: embed and index ONE changed row, instead of
re-running the full batch ingest.py on every write.

This matters specifically for memory on hosts like Render's free tier:
ingest.py's full run re-embeds every document in the knowledge base on
every call, which is fine as a manual/occasional operation but would be
a real problem if triggered automatically on every check-in or goal edit.
This module embeds only the one thing that changed, and reuses the
embedding model already loaded in the API process (via embeddings.py)
rather than spinning up a fresh model instance per call.

Deterministic IDs make this safe to call repeatedly:
- documents.py sets Document.id = the source row's own id (not a random
  uuid4()), so re-indexing the same goal always maps to the same document.
- Qdrant point IDs are derived from (document_id, chunk_index) via uuid5,
  so re-indexing an edited item cleanly overwrites its old chunks rather
  than accumulating duplicates.
"""

import os
import uuid

import psycopg2
import psycopg2.extras
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from embeddings import embed_documents, EMBEDDING_DIM
from chunking import chunk_text
from model import Document

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/momentum"
)
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "momentum_documents"

_client = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
        if not _client.collection_exists(COLLECTION_NAME):
            _client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )
    return _client


def _chunk_point_id(document_id: uuid.UUID, chunk_index: int) -> str:
    """Deterministic point ID -- same document + chunk index always maps to
    the same Qdrant point, so re-indexing overwrites cleanly instead of
    accumulating duplicate/stale chunks."""
    return str(uuid.uuid5(document_id, str(chunk_index)))


def _get_conn():
    return psycopg2.connect(DATABASE_URL)


def _delete_existing_chunks(document_id: uuid.UUID):
    """Removes any previously-indexed chunks for this document before
    inserting fresh ones -- needed because an edit can change how many
    chunks a document splits into, so a simple ID-overwrite alone isn't
    enough to clean up a chunk count that shrank."""
    _get_client().delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=str(document_id)))]
        ),
    )


def upsert_document(doc: Document):
    """Embeds and indexes a single Document -- both into Qdrant (for vector
    search) and the `documents` Postgres table (source of truth for BM25)."""
    _delete_existing_chunks(doc.id)

    chunks = chunk_text(doc.text)
    vectors = embed_documents(chunks)

    points = [
        PointStruct(
            id=_chunk_point_id(doc.id, i),
            vector=vector,
            payload={
                "document_id": str(doc.id),
                "source_type": doc.source_type.value,
                "source_id": str(doc.source_id),
                "title": doc.title,
                "text": chunk,
                "metadata": doc.metadata,
            },
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    _get_client().upsert(collection_name=COLLECTION_NAME, points=points)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE source_id = %s", (doc.source_id,))
            cur.execute(
                """INSERT INTO documents (id, source_type, source_id, title, text, metadata, embedded_at)
                   VALUES (%s,%s,%s,%s,%s,%s, now())""",
                (doc.id, doc.source_type.value, doc.source_id, doc.title, doc.text,
                 psycopg2.extras.Json(doc.metadata)),
            )
        conn.commit()
    finally:
        conn.close()


def delete_document(source_id: uuid.UUID):
    """Call this when the underlying goal/project/check-in row is deleted --
    otherwise it stays searchable forever even though it no longer exists."""
    _get_client().delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="source_id", match=MatchValue(value=str(source_id)))]
        ),
    )
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE source_id = %s", (source_id,))
        conn.commit()
    finally:
        conn.close()