"""
Phase 3: the RAG API.

Usage:
    export GROQ_API_KEY="gsk_..."
    export QDRANT_URL="http://localhost:6333"
    uvicorn api:app --reload --port 8000

Test:
    curl -X POST http://localhost:8000/ask \
      -H "Content-Type: application/json" \
      -d '{"question": "What should I focus on today?"}'
"""
import os
import time
import uuid
from datetime import date
from typing import Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from retrieval import retrieve
from llm import ask_llm

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/momentum"
)
psycopg2.extras.register_uuid()

app = FastAPI(title="MomentumRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"https://momentum-rag.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def log_query(question: str, retrieved: list[dict], retrieval_ms: int,
              llm_ms: int, total_tokens: int, answer: str) -> str:
    """Writes one row to query_logs and returns its id (as a string) so the
    frontend can attach feedback to this specific query later."""
    doc_ids = [uuid.UUID(r["document_id"]) for r in retrieved]
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO query_logs
                   (question, retrieved_doc_ids, retrieval_ms, llm_ms, total_tokens, answer)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (question, doc_ids, retrieval_ms, llm_ms, total_tokens, answer),
            )
            log_id = cur.fetchone()[0]
        conn.commit()
        return str(log_id)
    finally:
        conn.close()


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    retrieval_ms: int
    llm_ms: int
    total_tokens: int
    log_id: str

class FeedbackRequest(BaseModel):
    log_id: str
    feedback: int

class CheckInRequest(BaseModel):
    date: date
    did_planned_task: bool
    motivation_level: int
    social_media_opened_count: int = 0
    reinstalled_app: bool = False
    trigger_note: Optional[str] = None


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    t0 = time.time()
    retrieved = retrieve(req.question, top_k=req.top_k)
    retrieval_ms = int((time.time() - t0) * 1000)

    result = ask_llm(req.question, retrieved)

    log_id = log_query(
        question=req.question, retrieved=retrieved, retrieval_ms=retrieval_ms,
        llm_ms=result["latency_ms"], total_tokens=result["total_tokens"],
        answer=result["answer"],
    )

    return AskResponse(
        answer=result["answer"],
        sources=[{"title": r["title"], "source_type": r["source_type"]} for r in retrieved],
        retrieval_ms=retrieval_ms,
        llm_ms=result["latency_ms"],
        total_tokens=result["total_tokens"],
        log_id=log_id,
    )


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.feedback not in (1, -1):
        return {"status": "error", "detail": "feedback must be 1 or -1"}
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE query_logs SET feedback = %s WHERE id = %s",
                (req.feedback, uuid.UUID(req.log_id)),
            )
        conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/checkins")
def create_checkin(req: CheckInRequest):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO checkins (date, did_planned_task, motivation_level,
                   social_media_opened_count, reinstalled_app, trigger_note)
                   VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                (req.date, req.did_planned_task, req.motivation_level,
                 req.social_media_opened_count, req.reinstalled_app, req.trigger_note),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": str(new_id), "status": "created"}
    finally:
        conn.close()

@app.get("/checkins/recent")
def recent_checkins(limit: int = 14):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT date, did_planned_task, motivation_level,
                   social_media_opened_count, reinstalled_app, trigger_note
                   FROM checkins ORDER BY date DESC LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {**row, "date": row["date"].isoformat()} for row in rows
        ]
    finally:
        conn.close()

 
@app.get("/goals")
def list_goals():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT id, title, description, why, status, deadline, priority, tags
                   FROM goals ORDER BY priority ASC"""
            )
            rows = cur.fetchall()
        return [
            {**row, "id": str(row["id"]),
             "deadline": row["deadline"].isoformat() if row["deadline"] else None}
            for row in rows
        ]
    finally:
        conn.close()
 
 
@app.get("/projects")
def list_projects():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT id, name, description, objective, current_focus,
                   next_step, status, technologies, tags FROM projects"""
            )
            rows = cur.fetchall()
        return [{**row, "id": str(row["id"])} for row in rows]
    finally:
        conn.close()