"""
Phase 2: ingestion + embedding pipeline.

Reads every row from Postgres, flattens each into a Document (documents.py),
embeds the text with a local sentence-transformers model, and upserts into
Qdrant. Also writes each Document back into the `documents` Postgres table
so BM25/keyword search (needed for hybrid search in Phase 4) has a source
of truth that isn't the vector DB.

Usage:
    export DATABASE_URL="postgresql://user:pass@localhost:5432/momentum"
    export QDRANT_URL="http://localhost:6333"
    python ingest.py
"""

import os
import psycopg2
import psycopg2.extras
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

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
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5" 


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

# 2. Chunking. Most of your documents are short (one goal, one reflection),
#    so this only actually splits the rare long one. Simple word-count
#    chunking is enough here -- no need for anything fancier at this scale.

def chunk_text(text: str, max_words: int = 200, overlap: int = 30) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_words
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks


# 3. Write flattened Documents back to Postgres (source of truth for BM25).

def upsert_documents_table(conn, docs: list[Document]):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents")  
        for d in docs:
            cur.execute(
                """INSERT INTO documents (id, source_type, source_id, title, text, metadata, embedded_at)
                   VALUES (%s,%s,%s,%s,%s,%s, now())""",
                (d.id, d.source_type.value, d.source_id, d.title, d.text, psycopg2.extras.Json(d.metadata)),
            )
    conn.commit()

# 4. Embed and push into Qdrant.

def ensure_collection(client: QdrantClient, dim: int):
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

EMBEDDING_DIM = 384  

def embed_and_upsert(docs: list[Document]):
    model = TextEmbedding(model_name=EMBEDDING_MODEL)
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, check_compatibility=False)
    ensure_collection(client, EMBEDDING_DIM)

    # Flatten (doc, chunk) pairs first so we can embed everything in one
    # batched call -- much faster than one encode() call per chunk.
    doc_chunk_pairs = [(doc, chunk) for doc in docs for chunk in chunk_text(doc.text)]
    chunk_texts = [chunk for _, chunk in doc_chunk_pairs]
    vectors = [v.tolist() for v in model.embed(chunk_texts)]

    points = []
    for point_id, ((doc, chunk), vector) in enumerate(zip(doc_chunk_pairs, vectors)):
        points.append(
            PointStruct(
                id=point_id,
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