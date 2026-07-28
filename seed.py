"""
Seed script for MomentumRAG.

Run this once against a fresh Postgres instance (after applying schema.sql)
to populate your first real dataset. Edit the records below to reflect your
actual goals/projects/history -- these are starting examples, not fixtures
to keep as-is. Recent daily checkins matter most: even 2-3 weeks of honest
data is enough to make retrieval and evaluation meaningful.

Usage:
    export DATABASE_URL="postgresql://user:pass@localhost:5433/momentum"
    python seed.py
"""

import os
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from model import Goal, Project, Reflection, Task, WeeklyPlan, CheckIn, GoalStatus, ProjectStatus

psycopg2.extras.register_uuid()

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/momentum"
)

goals = [
    Goal(
        title="Complete LLM Zoomcamp 2026",
        description="Finish all modules and ship a working final RAG project.",
        why="Build practical RAG/LLM skills and have a portfolio project.",
        status=GoalStatus.IN_PROGRESS,
        priority=1,
        tags=["learning", "llm"],
    ),
    Goal(
        title="Rebuild a consistent daily routine",
        description="Get back to writing and working on projects daily, "
        "the way I did in the first six months of this year.",
        why="Without a direction each morning I lose the whole day.",
        status=GoalStatus.IN_PROGRESS,
        priority=1,
        tags=["habits", "motivation"],
    ),
]

projects = [
    Project(
        name="MemoryRAG",
        description="Personal memory RAG system: goals, reflections, checkins.",
        objective="Ship an end-to-end RAG app with retrieval eval, API, "
        "monitoring, and Docker for the Zoomcamp final project.",
        current_focus="Data model and seed data (Phase 1)",
        next_step="Stand up Postgres and load seed data",
        status=ProjectStatus.ACTIVE,
        technologies=["python", "postgres", "fastapi", "qdrant"],
        tags=["zoomcamp"],
    ),
]

reflections = [
    Reflection(
        date=date.today() - timedelta(days=2),
        accomplishments=["Set up the project repo"],
        blockers=["Kept opening social media instead of starting"],
        lessons=["Starting is easier right after check-in, before I open my phone"],
        mood=4,
        energy=4,
        social_media_minutes=90,
        reflection="Low motivation today. Reinstalled the app again after "
        "deleting it last week. Did manage to get the repo set up though.",
    ),
    Reflection(
        date=date.today() - timedelta(days=3),
        accomplishments=["Thought of the project I would want to have for my zoomcamp capstone"],
        blockers=["Instead of starting on a high note, I spent 10 minutes on x"],
        lessons=["Starting is easier right after check-in, before I consume any content"],
        mood=4,
        energy=4,
        social_media_minutes=20,
        reflection="High motivation, after a weeek of slight inactivity we are so back"
        "did some research and set my mind to start working on the project.",
    ),
]

checkins = [
    CheckIn(
        date=date.today() - timedelta(days=i),
        did_planned_task=(i % 3 != 0),
        motivation_level=max(2, 7 - i % 5),
        social_media_opened_count=3 + (i % 4),
        reinstalled_app=(i == 5),
        trigger_note="bored" if i % 4 == 0 else None,
    )
    for i in range(14, 0, -1)
]

def insert_goals(cur, items: list[Goal]):
    for g in items:
        cur.execute(
            """INSERT INTO goals (id, created_at, updated_at, title, description,
               why, status, deadline, priority, tags)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (g.id, g.created_at, g.updated_at, g.title, g.description, g.why,
             g.status.value, g.deadline, g.priority, g.tags),
        )


def insert_projects(cur, items: list[Project]):
    for p in items:
        cur.execute(
            """INSERT INTO projects (id, created_at, updated_at, name, description,
               objective, current_focus, next_step, status, technologies, tags)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (p.id, p.created_at, p.updated_at, p.name, p.description, p.objective,
             p.current_focus, p.next_step, p.status.value, p.technologies, p.tags),
        )


def insert_reflections(cur, items: list[Reflection]):
    for r in items:
        cur.execute(
            """INSERT INTO reflections (id, created_at, updated_at, date,
               accomplishments, blockers, lessons, mood, energy,
               social_media_minutes, reflection)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (r.id, r.created_at, r.updated_at, r.date, r.accomplishments,
             r.blockers, r.lessons, r.mood, r.energy, r.social_media_minutes,
             r.reflection),
        )


def insert_checkins(cur, items: list[CheckIn]):
    for c in items:
        cur.execute(
            """INSERT INTO checkins (id, created_at, updated_at, date,
               did_planned_task, motivation_level, social_media_opened_count,
               reinstalled_app, trigger_note)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (c.id, c.created_at, c.updated_at, c.date, c.did_planned_task,
             c.motivation_level, c.social_media_opened_count, c.reinstalled_app,
             c.trigger_note),
        )


def main():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            insert_goals(cur, goals)
            insert_projects(cur, projects)
            insert_reflections(cur, reflections)
            insert_checkins(cur, checkins)
        conn.commit()
        print(f"Seeded {len(goals)} goals, {len(projects)} projects, "
              f"{len(reflections)} reflections, {len(checkins)} checkins.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()