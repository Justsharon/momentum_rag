from datetime import datetime, date
from enum import Enum
from uuid import UUID, uuid4
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeType(str, Enum):
    GOAL = "goal"
    PROJECT = "project"
    REFLECTION = "reflection"
    TASK = "task"
    WEEKLY_PLAN = "weekly_plan"
    CHECKIN = "checkin"


class KnowledgeItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    type: KnowledgeType


class GoalStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class Goal(KnowledgeItem):
    type: KnowledgeType = KnowledgeType.GOAL
    title: str
    description: str
    why: str
    status: GoalStatus = GoalStatus.NOT_STARTED
    deadline: Optional[date] = None
    priority: int = Field(ge=1, le=5)
    tags: list[str] = []


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DONE = "done"


class Project(KnowledgeItem):
    type: KnowledgeType = KnowledgeType.PROJECT
    name: str
    description: str
    objective: str
    current_focus: str
    next_step: str
    status: ProjectStatus = ProjectStatus.ACTIVE
    technologies: list[str] = []
    tags: list[str] = []


class Reflection(KnowledgeItem):
    type: KnowledgeType = KnowledgeType.REFLECTION
    date: date
    accomplishments: list[str]
    blockers: list[str]
    lessons: list[str]
    mood: int = Field(ge=1, le=10)
    energy: int = Field(ge=1, le=10)
    social_media_minutes: int = 0
    reflection: str


class TaskStatus(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


class Task(KnowledgeItem):
    type: KnowledgeType = KnowledgeType.TASK
    title: str
    description: str
    project: str
    status: TaskStatus = TaskStatus.TODO
    estimated_minutes: int
    tags: list[str] = []


class WeeklyPlan(KnowledgeItem):
    type: KnowledgeType = KnowledgeType.WEEKLY_PLAN
    week: str
    objectives: list[str]
    success_definition: str
    risks: list[str]
    planned_tasks: list[str]


class CheckIn(KnowledgeItem):
    """Daily low-friction check-in. Designed to take under 30 seconds to fill in."""
    type: KnowledgeType = KnowledgeType.CHECKIN
    date: date
    did_planned_task: bool
    motivation_level: int = Field(ge=1, le=10)
    social_media_opened_count: int = 0
    reinstalled_app: bool = False
    trigger_note: Optional[str] = None  # e.g. "bored", "after finishing X", "avoiding Y"


class Document(BaseModel):
    """Flattened, embeddable representation of any KnowledgeItem. This is what
    actually gets chunked and pushed into the vector DB — never the raw
    Goal/Reflection/CheckIn rows themselves."""
    id: UUID
    source_type: KnowledgeType
    source_id: UUID
    title: str
    text: str
    metadata: dict[str, str]