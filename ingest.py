"""
Phase 2: full batch ingestion + embedding pipeline.

Reads every row from Postgres, flattens each into a Document (documents.py),
embeds the text, and rebuilds the whole Qdrant collection from scratch.
Also writes each Document back into the `documents` Postgres table so
BM25/keyword search (needed for hybrid search in Phase 4) has a source of
truth that isn't the vector DB.

This is the manual/occasional full-refresh path. Day-to-day writes (a new
check-in, an edited goal) go through indexing.py's incremental upsert
instead, which is much cheaper -- run this one when you want to be sure
everything is in sync, or after bulk changes like re-running seed.py.

Usage:
    export DATABASE_URL="postgresql://user:pass@localhost:5432/momentum"
    export QDRANT_URL="http://localhost:6333"
    python ingest.py
"""

import os
import uuid

import psycopg2
import psycopg2.extras
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from embeddings import embed_documents, EMBEDDING_DIM
from chunking import chunk_text
from model import Goal, Project, Reflection, Task, WeeklyPlan, CheckIn, Document
from documents import (
    goal_to_document, project_to_document, reflection_to_document,
    task_to_document, weekly_plan_to_document, checkin_to_document,
)

psycopg2.extras.register_uuid()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/momentum"
)
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")  
COLLECTION_NAME = "momentum_documents"


# 1. Fetch every row from Postgres and convert to Document objects.

def fetch_all_documents(conn) -> list[Document]:
    docs: list[Document] = []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM goals")
        docs += [goal_to_document(Goal(**row)) for row in cur.fetchall()]

        cur.execute("SELECT * FROM projects")
        docs += [project_to_document(Project(**row)) for row in cur.fetchall()]

        cur.execute("SELECT * FROM reflections")
        docs += [reflection_to_document(Reflection(**row)) for row in cur.fetchall()]

        cur.execute("SELECT * FROM tasks")
        docs += [task_to_document(Task(**row)) for row in cur.fetchall()]

        cur.execute("SELECT * FROM weekly_plans")
        docs += [weekly_plan_to_document(WeeklyPlan(**row)) for row in cur.fetchall()]

        cur.execute("SELECT * FROM checkins")
        docs += [checkin_to_document(CheckIn(**row)) for row in cur.fetchall()]

    return docs

# 2. Write flattened Documents back to Postgres (source of truth for BM25).

def upsert_documents_table(conn, docs: list[Document]):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents")  # full-refresh for this batch path
        for d in docs:
            cur.execute(
                """INSERT INTO documents (id, source_type, source_id, title, text, metadata, embedded_at)
                   VALUES (%s,%s,%s,%s,%s,%s, now())""",
                (d.id, d.source_type.value, d.source_id, d.title, d.text, psycopg2.extras.Json(d.metadata)),
            )
    conn.commit()


# 3. Embed and push into Qdrant.

def ensure_collection(client: QdrantClient):
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def chunk_point_id(document_id: uuid.UUID, chunk_index: int) -> str:
    """Same scheme as indexing.py -- deterministic per (document, chunk),
    so this full-batch run and incremental single-item updates never
    produce colliding or duplicate points for the same underlying data."""
    return str(uuid.uuid5(document_id, str(chunk_index)))


def embed_and_upsert(docs: list[Document]):
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
    ensure_collection(client)
    client.delete_collection(COLLECTION_NAME)
    ensure_collection(client)

    doc_chunk_pairs = [(doc, chunk) for doc in docs for chunk in chunk_text(doc.text)]
    chunk_texts = [chunk for _, chunk in doc_chunk_pairs]
    vectors = embed_documents(chunk_texts)

    points = []
    chunk_index_by_doc = {}
    for (doc, chunk), vector in zip(doc_chunk_pairs, vectors):
        idx = chunk_index_by_doc.get(doc.id, 0)
        chunk_index_by_doc[doc.id] = idx + 1
        points.append(
            PointStruct(
                id=chunk_point_id(doc.id, idx),
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
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        docs = fetch_all_documents(conn)
        print(f"Fetched {len(docs)} source rows from Postgres")

        upsert_documents_table(conn, docs)
        print("Refreshed `documents` table")

        n_points = embed_and_upsert(docs)
        print(f"Embedded and upserted {n_points} chunks into Qdrant "
              f"collection '{COLLECTION_NAME}'")
    finally:
        conn.close()


if __name__ == "__main__":
    main()