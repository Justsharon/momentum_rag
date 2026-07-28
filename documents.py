"""
Turns rows from goals/projects/reflections/tasks/weekly_plans/checkins into
flat Document objects (title + text + metadata) ready for chunking/embedding.

This is the ONLY place that knows how to translate each knowledge type into
text -- keeping it centralized means Phase 3 (retrieval) and Phase 4 (eval)
don't need to know anything about the source tables.
"""

from uuid import uuid4
from model import (
    Goal, Project, Reflection, Task, WeeklyPlan, CheckIn,
    Document, KnowledgeType,
)


def goal_to_document(g: Goal) -> Document:
    text = (
        f"Goal: {g.title}\n"
        f"Description: {g.description}\n"
        f"Why this matters: {g.why}\n"
        f"Status: {g.status.value}\n"
        f"Priority: {g.priority}/5\n"
        + (f"Deadline: {g.deadline}\n" if g.deadline else "")
        + (f"Tags: {', '.join(g.tags)}" if g.tags else "")
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.GOAL, source_id=g.id,
        title=g.title, text=text,
        metadata={"status": g.status.value, "priority": str(g.priority)},
    )


def project_to_document(p: Project) -> Document:
    text = (
        f"Project: {p.name}\n"
        f"Description: {p.description}\n"
        f"Objective: {p.objective}\n"
        f"Current focus: {p.current_focus}\n"
        f"Next step: {p.next_step}\n"
        f"Status: {p.status.value}\n"
        + (f"Technologies: {', '.join(p.technologies)}\n" if p.technologies else "")
        + (f"Tags: {', '.join(p.tags)}" if p.tags else "")
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.PROJECT, source_id=p.id,
        title=p.name, text=text, metadata={"status": p.status.value},
    )


def reflection_to_document(r: Reflection) -> Document:
    text = (
        f"Reflection for {r.date}\n"
        f"Mood: {r.mood}/10, Energy: {r.energy}/10\n"
        f"Social media minutes: {r.social_media_minutes}\n"
        f"Accomplishments: {'; '.join(r.accomplishments) or 'none noted'}\n"
        f"Blockers: {'; '.join(r.blockers) or 'none noted'}\n"
        f"Lessons: {'; '.join(r.lessons) or 'none noted'}\n"
        f"Notes: {r.reflection}"
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.REFLECTION, source_id=r.id,
        title=f"Reflection {r.date}", text=text,
        metadata={"date": str(r.date), "mood": str(r.mood)},
    )


def task_to_document(t: Task) -> Document:
    text = (
        f"Task: {t.title}\n"
        f"Project: {t.project}\n"
        f"Description: {t.description}\n"
        f"Status: {t.status.value}\n"
        f"Estimated: {t.estimated_minutes} min"
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.TASK, source_id=t.id,
        title=t.title, text=text,
        metadata={"status": t.status.value, "project": t.project},
    )


def weekly_plan_to_document(w: WeeklyPlan) -> Document:
    text = (
        f"Weekly plan: {w.week}\n"
        f"Objectives: {'; '.join(w.objectives)}\n"
        f"Success looks like: {w.success_definition}\n"
        f"Risks: {'; '.join(w.risks) or 'none noted'}\n"
        f"Planned tasks: {'; '.join(w.planned_tasks)}"
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.WEEKLY_PLAN, source_id=w.id,
        title=f"Weekly plan {w.week}", text=text, metadata={"week": w.week},
    )


def checkin_to_document(c: CheckIn) -> Document:
    text = (
        f"Check-in for {c.date}\n"
        f"Did planned task: {'yes' if c.did_planned_task else 'no'}\n"
        f"Motivation level: {c.motivation_level}/10\n"
        f"Social media opened: {c.social_media_opened_count} times\n"
        f"Reinstalled app: {'yes' if c.reinstalled_app else 'no'}\n"
        + (f"Trigger: {c.trigger_note}" if c.trigger_note else "")
    )
    return Document(
        id=uuid4(), source_type=KnowledgeType.CHECKIN, source_id=c.id,
        title=f"Check-in {c.date}", text=text,
        metadata={
            "date": str(c.date),
            "motivation": str(c.motivation_level),
            "reinstalled": str(c.reinstalled_app),
        },
    )