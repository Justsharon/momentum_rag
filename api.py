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
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/momentum"
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


def partial_update(table: str, record_id: str, updates: dict):
    """Builds and runs an UPDATE for only the fields actually provided.
    `updates` keys must already be trusted column names (comes from a
    Pydantic model's own field names, never raw user input) -- this is
    what makes the f-string column interpolation below safe."""
    updates = {k: v for k, v in updates.items() if v is not None}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [uuid.UUID(record_id)]
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {table} SET {set_clause}, updated_at = now() WHERE id = %s",
                values,
            )
        conn.commit()
    finally:
        conn.close()


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
    feedback: int  # 1 = thumbs up, -1 = thumbs down


class CheckInRequest(BaseModel):
    date: date
    did_planned_task: bool
    motivation_level: int
    social_media_opened_count: int = 0
    reinstalled_app: bool = False
    trigger_note: Optional[str] = None


class GoalCreate(BaseModel):
    title: str
    description: str
    why: str
    status: str = "not_started"
    deadline: Optional[date] = None
    priority: int
    tags: list[str] = []


class GoalUpdate(BaseModel):
    # All fields optional -- only the ones the client sends get updated.
    title: Optional[str] = None
    description: Optional[str] = None
    why: Optional[str] = None
    status: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[int] = None
    tags: Optional[list[str]] = None


class ProjectCreate(BaseModel):
    name: str
    description: str
    objective: str
    current_focus: str
    next_step: str
    status: str = "active"
    technologies: list[str] = []
    tags: list[str] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    objective: Optional[str] = None
    current_focus: Optional[str] = None
    next_step: Optional[str] = None
    status: Optional[str] = None
    technologies: Optional[list[str]] = None
    tags: Optional[list[str]] = None


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


@app.post("/goals")
def create_goal(req: GoalCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO goals (title, description, why, status, deadline, priority, tags)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (req.title, req.description, req.why, req.status,
                 req.deadline, req.priority, req.tags),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": str(new_id), "status": "created"}
    finally:
        conn.close()


@app.patch("/goals/{goal_id}")
def update_goal(goal_id: str, req: GoalUpdate):
    partial_update("goals", goal_id, req.model_dump())
    return {"id": goal_id, "status": "updated"}


@app.delete("/goals/{goal_id}")
def delete_goal(goal_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM goals WHERE id = %s", (uuid.UUID(goal_id),))
        conn.commit()
        return {"id": goal_id, "status": "deleted"}
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


@app.post("/projects")
def create_project(req: ProjectCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO projects (name, description, objective, current_focus,
                   next_step, status, technologies, tags)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (req.name, req.description, req.objective, req.current_focus,
                 req.next_step, req.status, req.technologies, req.tags),
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return {"id": str(new_id), "status": "created"}
    finally:
        conn.close()


@app.patch("/projects/{project_id}")
def update_project(project_id: str, req: ProjectUpdate):
    partial_update("projects", project_id, req.model_dump())
    return {"id": project_id, "status": "updated"}


@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id = %s", (uuid.UUID(project_id),))
        conn.commit()
        return {"id": project_id, "status": "deleted"}
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