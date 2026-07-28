-- MemoryRAG schema
-- One table per knowledge type (matches model.py), plus a shared `documents`
-- table used for retrieval, and a `query_logs` table used later for monitoring.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    why TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'completed', 'paused')),
    deadline DATE,
    priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
    tags TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    objective TEXT NOT NULL,
    current_focus TEXT NOT NULL,
    next_step TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'on_hold', 'done')),
    technologies TEXT[] NOT NULL DEFAULT '{}',
    tags TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS reflections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    date DATE NOT NULL,
    accomplishments TEXT[] NOT NULL DEFAULT '{}',
    blockers TEXT[] NOT NULL DEFAULT '{}',
    lessons TEXT[] NOT NULL DEFAULT '{}',
    mood INTEGER NOT NULL CHECK (mood BETWEEN 1 AND 10),
    energy INTEGER NOT NULL CHECK (energy BETWEEN 1 AND 10),
    social_media_minutes INTEGER NOT NULL DEFAULT 0,
    reflection TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    project TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'todo'
        CHECK (status IN ('todo', 'doing', 'done')),
    estimated_minutes INTEGER NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS weekly_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    week TEXT NOT NULL,
    objectives TEXT[] NOT NULL DEFAULT '{}',
    success_definition TEXT NOT NULL,
    risks TEXT[] NOT NULL DEFAULT '{}',
    planned_tasks TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS checkins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    date DATE NOT NULL,
    did_planned_task BOOLEAN NOT NULL,
    motivation_level INTEGER NOT NULL CHECK (motivation_level BETWEEN 1 AND 10),
    social_media_opened_count INTEGER NOT NULL DEFAULT 0,
    reinstalled_app BOOLEAN NOT NULL DEFAULT false,
    trigger_note TEXT
);

-- Flattened, embeddable rows. Populated by the ingestion pipeline (Phase 2)
-- from the tables above -- never populated directly.
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL,
    source_id UUID NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedded_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_source ON documents (source_type, source_id);

-- Used in Phase 6 (monitoring). Created now so the schema is complete in one file.
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    question TEXT NOT NULL,
    retrieved_doc_ids UUID[] NOT NULL DEFAULT '{}',
    retrieval_ms INTEGER,
    embedding_ms INTEGER,
    llm_ms INTEGER,
    total_tokens INTEGER,
    answer TEXT,
    feedback SMALLINT  -- 1 = thumbs up, -1 = thumbs down, NULL = no feedback
);