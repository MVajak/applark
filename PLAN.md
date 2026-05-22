# Postpilot — Build Plan

A concrete, paste-into-Claude-Code spec for Postpilot, a FastAPI + React side project that
ingests CVs and job postings, embeds them in pgvector, and uses Pydantic AI
agents to extract structure and explain matches.

---

## 0. Top-level decisions

- **Monorepo**, single git repo, `backend/` and `frontend/` at the root
- **Python 3.13**, managed by **uv**
- **FastAPI** + **Pydantic v2** + **Pydantic AI** (Anthropic Claude)
- **SQLAlchemy 2.0 async** + **asyncpg** + **PostgreSQL 16** + **pgvector**
- **Alembic** for migrations
- **ARQ** + **Redis** for background jobs
- **PyMuPDF** for PDF parsing
- **Playwright** (async) for scraping JS-heavy job pages
- **OpenAI `text-embedding-3-small`** (1536-d, multilingual) for embeddings
- **React + Vite + TypeScript + TanStack Query** on the frontend
- **Orval** for OpenAPI → TS + TanStack Query hooks codegen
- **Railway** (backend, Postgres, Redis) + **Vercel** (frontend)

No auth in v1. Single-user. Add auth later.

---

## 1. Monorepo layout

```
postpilot/
├── README.md
├── docker-compose.yml
├── .gitignore
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .python-version             # 3.13
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── .env.example
│   ├── .pre-commit-config.yaml
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── evals/                  # labeled agent eval cases
│   │       ├── cv/
│   │       ├── jobs/
│   │       ├── matching/
│   │       ├── cover_letters/
│   │       ├── cv_tailor/
│   │       └── interview_prep/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── redis.py
│       │   ├── llm.py              # Pydantic AI model factories + caching
│       │   ├── embeddings.py
│       │   ├── logging.py
│       │   └── exceptions.py
│       ├── api/
│       │   └── v1/
│       │       └── router.py
│       ├── modules/
│       │   ├── cv/
│       │   │   ├── router.py
│       │   │   ├── schemas.py
│       │   │   ├── models.py
│       │   │   ├── service.py
│       │   │   ├── repository.py
│       │   │   ├── parser.py       # PyMuPDF wrapper
│       │   │   ├── prompts.py      # SYSTEM_PROMPT + EXAMPLES
│       │   │   ├── agent.py
│       │   │   └── tasks.py
│       │   ├── jobs/
│       │   │   ├── router.py
│       │   │   ├── schemas.py
│       │   │   ├── models.py
│       │   │   ├── service.py
│       │   │   ├── repository.py
│       │   │   ├── scraper.py      # Playwright
│       │   │   ├── prompts.py
│       │   │   ├── agent.py
│       │   │   └── tasks.py
│       │   ├── matching/
│       │   │   ├── router.py
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   ├── prompts.py
│       │   │   └── agent.py
│       │   ├── cover_letters/      # NEW
│       │   │   ├── router.py
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   ├── prompts.py
│       │   │   └── agent.py
│       │   ├── cv_tailor/          # NEW
│       │   │   ├── router.py
│       │   │   ├── schemas.py
│       │   │   ├── service.py
│       │   │   ├── prompts.py
│       │   │   └── agent.py
│       │   └── interview_prep/     # NEW
│       │       ├── router.py
│       │       ├── schemas.py
│       │       ├── service.py
│       │       ├── prompts.py
│       │       └── agent.py
│       └── workers/
│           └── arq_worker.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── orval.config.ts
    ├── .env.example
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   ├── client.ts
        │   └── generated/
        ├── modules/
        │   ├── cv/
        │   ├── jobs/
        │   ├── matching/
        │   ├── cover_letters/
        │   ├── cv_tailor/
        │   └── interview_prep/
        └── shared/
            ├── components/
            └── lib/
```

---

## 2. Pinned versions

`backend/pyproject.toml`:

```toml
[project]
name = "postpilot"
version = "0.1.0"
requires-python = ">=3.13,<3.14"
dependencies = [
    "fastapi>=0.136.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.6.0",
    "pydantic-ai==1.88.0",          # PINNED — library still evolves quickly
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pgvector>=0.3.6",
    "arq>=0.26.3",
    "redis>=5.2.0",
    "pymupdf>=1.25.0",
    "playwright>=1.50.0",
    "httpx>=0.28.0",
    "openai>=1.55.0",
    "anthropic>=0.40.0",
    "structlog>=24.4.0",
    "python-multipart>=0.0.18",
]

[dependency-groups]
dev = [
    "ruff>=0.8.0",
    "pyright>=1.1.390",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "aiosqlite>=0.20.0",
    "pre-commit>=4.0.0",
    "dirty-equals>=0.8.0",
]
```

Frontend `package.json` highlights:

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.62.0",
    "react-router-dom": "^7.0.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "orval": "^7.3.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "gen:api": "orval --config orval.config.ts"
  }
}
```

---

## 3. Bootstrap commands

```bash
git init
mkdir backend frontend

# backend
cd backend
uv init --name postpilot --python 3.13
uv sync
uv run alembic init migrations
uv run pre-commit install

# frontend
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install
npm install @tanstack/react-query axios react-router-dom
npm install -D orval

# at repo root
docker compose up -d
```

---

## 4. docker-compose.yml

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: postpilot
      POSTGRES_USER: postpilot
      POSTGRES_PASSWORD: dev
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postpilot"]
      interval: 5s

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  adminer:
    image: adminer
    ports: ["8080:8080"]

volumes:
  pgdata:
```

---

## 5. Environment variables

`backend/.env.example`:

```bash
DATABASE_URL=postgresql+asyncpg://postpilot:dev@localhost:5432/postpilot
REDIS_URL=redis://localhost:6379/0

ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:5173"]

EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

LLM_MODEL_FAST=anthropic:claude-haiku-4-5
LLM_MODEL_SMART=anthropic:claude-sonnet-4-6
```

`frontend/.env.example`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 6. Database schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================
-- CV module
-- =====================

CREATE TYPE cv_document_kind AS ENUM ('cv', 'cover_letter');

CREATE TABLE cv_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind cv_document_kind NOT NULL,
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    storage_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE cv_chunk_type AS ENUM (
    'summary', 'experience', 'skill', 'education',
    'project', 'language', 'other'
);

CREATE TABLE cv_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES cv_documents(id) ON DELETE CASCADE,
    chunk_type cv_chunk_type NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    chunk_index INTEGER NOT NULL,
    embedding VECTOR(1536),
    embedding_model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX cv_chunks_document_id_idx ON cv_chunks(document_id);
CREATE INDEX cv_chunks_chunk_type_idx ON cv_chunks(chunk_type);
CREATE INDEX cv_chunks_embedding_idx ON cv_chunks
    USING hnsw (embedding vector_cosine_ops);

-- =====================
-- Jobs module
-- =====================

CREATE TYPE job_source_kind AS ENUM ('url', 'pasted');
CREATE TYPE job_status AS ENUM (
    'pending', 'scraping', 'extracting', 'ready', 'failed'
);
CREATE TYPE remote_policy AS ENUM (
    'onsite', 'hybrid', 'remote', 'unspecified'
);
CREATE TYPE seniority AS ENUM (
    'junior', 'mid', 'senior', 'lead', 'principal', 'unspecified'
);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT UNIQUE,
    source_kind job_source_kind NOT NULL,
    raw_text TEXT NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    remote_policy remote_policy DEFAULT 'unspecified',
    seniority seniority DEFAULT 'unspecified',
    tech_stack TEXT[] NOT NULL DEFAULT '{}',
    salary_range TEXT,
    summary TEXT,
    raw_extraction JSONB,
    embedding VECTOR(1536),
    embedding_model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX jobs_status_idx ON jobs(status);
CREATE INDEX jobs_company_idx ON jobs(company);
CREATE INDEX jobs_created_at_idx ON jobs(created_at DESC);
CREATE INDEX jobs_embedding_idx ON jobs
    USING hnsw (embedding vector_cosine_ops);

CREATE TYPE requirement_category AS ENUM (
    'required', 'nice_to_have', 'responsibility'
);

CREATE TABLE job_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    category requirement_category NOT NULL,
    embedding VECTOR(1536),
    embedding_model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX job_requirements_job_id_idx ON job_requirements(job_id);
CREATE INDEX job_requirements_embedding_idx ON job_requirements
    USING hnsw (embedding vector_cosine_ops);

-- =====================
-- Matching module
-- =====================

CREATE TABLE match_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    overall_score DOUBLE PRECISION NOT NULL,
    summary TEXT NOT NULL,
    details JSONB NOT NULL,
    llm_model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX match_runs_job_id_idx ON match_runs(job_id);
CREATE INDEX match_runs_score_idx ON match_runs(overall_score DESC);

-- =====================
-- Cover letters (NEW)
-- =====================

CREATE TABLE cover_letter_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    match_run_id UUID REFERENCES match_runs(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    referenced_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    tone TEXT,
    llm_model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX cover_letter_drafts_job_id_idx ON cover_letter_drafts(job_id);

-- =====================
-- CV tailor (NEW)
-- =====================

CREATE TABLE cv_tailor_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    job_summary TEXT NOT NULL,
    suggestions JSONB NOT NULL,
    do_not_suggest JSONB NOT NULL,
    llm_model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX cv_tailor_runs_job_id_idx ON cv_tailor_runs(job_id);

-- =====================
-- Interview prep (NEW)
-- =====================

CREATE TABLE interview_prep_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    role_overview TEXT NOT NULL,
    likely_areas_of_focus JSONB NOT NULL,
    questions JSONB NOT NULL,
    questions_to_ask_them JSONB NOT NULL,
    llm_model TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX interview_prep_runs_job_id_idx ON interview_prep_runs(job_id);
```

### Alembic gotcha for pgvector

In `migrations/env.py`:

```python
from pgvector.sqlalchemy import Vector  # noqa: F401
```

Include `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` as the first
operation in the initial migration's `upgrade()`.

---

## 7. SQLAlchemy models

```python
# app/core/database.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**Reserved name gotcha:** SQLAlchemy reserves `metadata` on the Base class.
Name the column `metadata_` in Python with `"metadata"` as the DB alias:

```python
metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
```

Mirror the SQL DDL into one `models.py` per module. Pattern: UUID PK,
`Mapped[...]` columns, `Vector(1536)` for embeddings, cascading FKs.

---

## 8. Pydantic schemas — the cross-stack contract

Each module's `schemas.py` Pydantic models are simultaneously:
- LLM structured-output schemas (what Pydantic AI agents return)
- FastAPI request/response shapes
- Source of TS types on the frontend via orval

This is the FastAPI superpower — one definition flows through the stack.

---

## 9. Agent design principles

The rules every agent in this project follows. Pulled from Anthropic's official
prompting docs, Pydantic AI testing docs, and 2026 production patterns.

### 9.1 The "new employee" rule

If a smart colleague with no project context would be confused by your prompt,
Claude will be too. Read every prompt aloud and ask: would this make sense to
someone seeing this codebase for the first time?

### 9.2 Explain the why, not just the what

Don't say "no marketing language." Say "no marketing language because the user
is screening real opportunities and needs honest signal — promotional fluff
makes their filtering harder."

Claude generalizes well from explanations.

### 9.3 Tell Claude what to do, not what not to do

Bad: "Don't paraphrase the CV."
Good: "Quote the candidate's exact wording in `content`."

### 9.4 Structure prompts with XML

Use these consistent tags across all agents:

- `<role>` — what the agent is
- `<task>` — what it does
- `<rules>` — constraints
- `<examples>` containing `<example>` — few-shot demonstrations
- `<input>` — the data being processed (in user messages)

### 9.5 Few-shot examples — 3 to 5, always

Every agent in this project ships with 3-5 examples in its `prompts.py`. They
cover:

1. One typical case
2. One messy / edge case
3. One case where some fields are missing or unclear

Examples live in `prompts.py` next to the system prompt as a Python string,
wrapped in `<examples>` and `<example>` tags.

### 9.6 Long inputs go FIRST in the user message

Queries at the end of a prompt can improve response quality by up to 30% on
long-doc tasks. The user prompt looks like:

```
<cv>
... entire raw CV text ...
</cv>

Now extract the structured chunks per the rules in the system prompt.
```

NOT:

```
Extract the structured chunks from this CV:

... entire raw CV text ...
```

### 9.7 Pydantic Field descriptions are prompt engineering

Field descriptions are injected into the JSON schema sent to the model. They
are part of the prompt, not docs:

```python
tech_stack: list[str] = Field(
    description=(
        "Technologies, languages, frameworks, libraries, tools, cloud "
        "providers mentioned as required or used. Lowercase. Deduplicated. "
        "Exclude soft skills like 'communication'."
    )
)
```

Not just `description="The tech stack"`.

### 9.8 Model selection per agent

- **Fast model** (Haiku 4.5) — pure extraction agents (CV chunker, job
  extractor). Their job is structured parsing.
- **Smart model** (Sonnet 4.6) — agents that need reasoning (match explainer,
  cover letter drafter, CV tailor, interview prep). They make judgment calls.

Strings come from env vars (`LLM_MODEL_FAST`, `LLM_MODEL_SMART`) so you can
swap models project-wide via env, not code.

### 9.9 Separate deterministic work from LLM work

Vector similarity, ranking, filtering, deduplication — all deterministic. Do
them in Python before invoking the agent. The agent should only do the
language-shaped part: explain, draft, judge.

Pattern: `service.py` does deterministic prep, then calls `agent.run(...)` with
a pre-shaped input.

### 9.10 Four-file layout per LLM module

Every module with an LLM follows this exact structure:

```
modules/<name>/
├── schemas.py   # Pydantic output types
├── prompts.py   # SYSTEM_PROMPT + EXAMPLES strings
├── agent.py     # Agent(model=..., output_type=..., system_prompt=...)
└── service.py   # run_X(input) -> Output — handles retries, logging, persistence
```

`agent.run()` is never called directly from routes or tasks. Everything goes
through `service.py` so error handling, token logging, and DB persistence live
in one place.

### 9.11 Testing without burning API budget

Set up the safety net on day one:

```python
# tests/conftest.py
import pydantic_ai
pydantic_ai.models.ALLOW_MODEL_REQUESTS = False
```

For unit tests, override with `TestModel`:

```python
import pytest
from pydantic_ai.models.test import TestModel
from app.modules.cv.agent import cv_extractor

@pytest.fixture
def mock_cv_extractor():
    with cv_extractor.override(model=TestModel()):
        yield
```

Agent-quality evals are SEPARATE from unit tests, live in `tests/evals/<module>/`,
and DO hit the real API. Each eval case is a JSON file with input + expected
fields. Run with `pytest tests/evals/` locally before prompt changes, and in
CI on PRs that touch `prompts.py`. Aim for 5-10 cases per agent in v1.

### 9.12 Track usage on every run

Every `service.py` wrapper records `input_tokens`, `output_tokens`, and
`llm_model` to the result table. This lets you see cost-per-job-extracted,
cost-per-match, etc. Pydantic AI exposes usage on the run result.

### 9.13 Prompt caching for stable prefixes

System prompts + examples are stable across calls. Anthropic's prompt caching
has a 5-minute default TTL; cached prefix reads are ~90% cheaper. Mark the
system prompt as cacheable in the Anthropic model client. Only pays off for
prompts above ~1k tokens, but our 3-5-example system prompts easily clear
that bar.

### 9.14 Versioning prompts

System prompts live in `prompts.py` files — code, not config. Changing a prompt
is a git commit, code-reviewable, blameable. Do NOT put prompts in a database
or external config service for a side project. Diff visibility is more
valuable than runtime editability.

When a prompt change measurably improves the eval set, note it in the commit
message ("matches: prompt rev 3 raises eval pass 6/10 → 9/10").

### 9.15 No aggressive language

Claude 4.6+ is more responsive to system prompts. Avoid "CRITICAL: YOU MUST..."
style — that compensated for under-following in older models, now it causes
over-triggering. Normal "Do X when Y" wording works best.

---

## 10. Existing agents (refactored to follow the principles)

### 10.1 CV chunker

```python
# app/modules/cv/prompts.py

SYSTEM_PROMPT = """<role>
You parse CVs and resumes into semantically meaningful chunks for later
retrieval and matching against job postings.
</role>

<task>
Given the raw text of a CV, split it into discrete chunks. Each chunk
represents one self-contained piece of the candidate's history that should be
retrievable on its own when matching against a job posting requirement.
</task>

<rules>
- Chunk types: summary, experience, skill, education, project, language, other.
  Use 'other' only when nothing else fits.
- One real-world entry = one chunk. Do NOT split one role into multiple chunks
  by bullet point. Keep all of a role's responsibilities and achievements
  together in a single experience chunk, because matching compares full
  responsibilities against requirements, not individual bullets.
- Quote the candidate's exact wording in `content`. The matching step compares
  the candidate's actual language against job requirements; paraphrasing loses
  the specific terminology that drives good matches.
- For experience chunks, populate metadata with: company, role, start_date,
  end_date. Use the dates as written by the candidate.
- For education chunks, populate metadata with: institution, degree, year.
- For project chunks, populate metadata with: name, technologies.
- If a section header has no real content under it, skip it. Do not produce
  empty chunks.
- The candidate's full name goes in `candidate_name`. Spoken languages go in
  `languages_spoken` (lowercase).
</rules>

<examples>
{EXAMPLES}
</examples>
"""

EXAMPLES = """
<example>
<input>
Jane Doe — Senior Frontend Engineer
jane@example.com

Summary
Frontend engineer with 8 years of experience in React and TypeScript,
specializing in design systems and large-scale applications.

Experience
Acme Corp — Senior Frontend Engineer (Jan 2022 — present)
- Led migration from Webpack to Vite, cutting build times by 60%
- Designed the company's first cross-product design system

Tools — TypeScript, React, Vite, Tailwind, Playwright
</input>
<output>
{
  "candidate_name": "Jane Doe",
  "languages_spoken": [],
  "chunks": [
    {
      "chunk_type": "summary",
      "content": "Frontend engineer with 8 years of experience in React and TypeScript, specializing in design systems and large-scale applications.",
      "metadata": {}
    },
    {
      "chunk_type": "experience",
      "content": "Led migration from Webpack to Vite, cutting build times by 60%. Designed the company's first cross-product design system",
      "metadata": {
        "company": "Acme Corp",
        "role": "Senior Frontend Engineer",
        "start_date": "Jan 2022",
        "end_date": "present"
      }
    },
    {
      "chunk_type": "skill",
      "content": "TypeScript, React, Vite, Tailwind, Playwright",
      "metadata": {}
    }
  ]
}
</output>
</example>

<example>
<!-- Edge case: messy formatting from PDF, sparse content -->
<input>
JOHN  SMITH

  Lead   developer   at   StartupX,  building   internal   tools.
2019 - 2023
Mostly Python and Go.
</input>
<output>
{
  "candidate_name": "JOHN SMITH",
  "languages_spoken": [],
  "chunks": [
    {
      "chunk_type": "experience",
      "content": "Lead developer at StartupX, building internal tools. Mostly Python and Go.",
      "metadata": {
        "company": "StartupX",
        "role": "Lead developer",
        "start_date": "2019",
        "end_date": "2023"
      }
    }
  ]
}
</output>
</example>

<example>
<!-- Edge case: multilingual, mixed structure -->
<input>
Carl-Hillar S.
Folk Dance Researcher
Native: Estonian. Fluent: English, German.
Lives in Tallinn.

University of Tartu (2020), MA in Ethnology

Research project — "Estonian Folk Dance Genealogy" (2021-2023)
Used Python pandas for archive analysis.
</input>
<output>
{
  "candidate_name": "Carl-Hillar S.",
  "languages_spoken": ["estonian", "english", "german"],
  "chunks": [
    {
      "chunk_type": "education",
      "content": "University of Tartu (2020), MA in Ethnology",
      "metadata": {
        "institution": "University of Tartu",
        "degree": "MA in Ethnology",
        "year": "2020"
      }
    },
    {
      "chunk_type": "project",
      "content": "Estonian Folk Dance Genealogy (2021-2023). Used Python pandas for archive analysis.",
      "metadata": {
        "name": "Estonian Folk Dance Genealogy",
        "technologies": ["python", "pandas"]
      }
    }
  ]
}
</output>
</example>
"""
```

```python
# app/modules/cv/agent.py
from pydantic_ai import Agent
from app.core.config import settings
from app.modules.cv.schemas import CVExtraction
from app.modules.cv.prompts import SYSTEM_PROMPT, EXAMPLES

cv_extractor: Agent[None, CVExtraction] = Agent(
    model=settings.LLM_MODEL_FAST,
    output_type=CVExtraction,
    system_prompt=SYSTEM_PROMPT.format(EXAMPLES=EXAMPLES),
)
```

Caller passes the CV text in the user prompt with `<cv>` tags:

```python
# app/modules/cv/service.py (snippet)
user_message = f"<cv>\n{raw_text}\n</cv>\n\nExtract structured chunks per the rules above."
result = await cv_extractor.run(user_message)
extraction = result.output  # CVExtraction
# Persist tokens: result.usage().request_tokens, .response_tokens
```

### 10.2 Job extractor

Same four-file structure. System prompt has the same `<role>`, `<task>`,
`<rules>`, `<examples>` skeleton. Three examples covering typical, noisy
(extracted from a SPA with extra UI text), and partial-info cases. User
message wraps the raw posting in `<job_posting>` tags.

Key rules:
- Use null, never invent.
- Lowercase tech stack, no soft skills.
- Split requirements into one-clause-each items.
- Plain summary, no marketing language ("rockstar", "ninja", "passionate").
- Mark requirement category clearly.

### 10.3 Match explainer

Uses `LLM_MODEL_SMART` (Sonnet). User message has THREE sections:

```
<job>
... structured job extraction as JSON ...
</job>

<candidate_chunks>
... top-k relevant CV chunks with similarity scores ...
</candidate_chunks>

<requirement_matches>
... pre-computed deterministic mapping of requirements → chunks ...
</requirement_matches>

Now produce a MatchExplanation per the rules in the system prompt.
```

The deterministic vector search runs FIRST in `service.py`. The agent only
explains the matches.

Rules:
- Honest scoring — 0.4 for partial match, not 0.8.
- Cite specific chunks for each strength.
- Gap severity proportional to required vs nice-to-have.
- Don't invent experiences.
- Quote the relevant chunk excerpt and requirement text in the explanation.

---

## 11. New agents

### 11.1 Cover letter drafter

```python
# app/modules/cover_letters/schemas.py
from pydantic import BaseModel, Field
from uuid import UUID

class CoverLetterDraft(BaseModel):
    """A drafted cover letter grounded in the candidate's real CV chunks."""

    subject: str = Field(
        description=(
            "Email subject line. Specific to the role and company, not generic. "
            "Format: 'Application: <role> — <candidate name>'"
        )
    )
    body: str = Field(
        description=(
            "Full cover letter body, 250-350 words. Plain text with paragraph "
            "breaks. End with 'Best regards,\\n<name>'. No salutation block "
            "at the very top — the user adds that."
        )
    )
    referenced_cv_chunk_ids: list[UUID] = Field(
        description=(
            "IDs of CV chunks whose content is referenced or paraphrased in "
            "the body. Used to verify the letter is grounded in real experience."
        )
    )
    tone: str = Field(
        description=(
            "Short label for the chosen tone: 'plain-direct', 'warm-personal', "
            "or 'formal'. Match the tone of the job posting."
        )
    )
```

```python
# app/modules/cover_letters/prompts.py

SYSTEM_PROMPT = """<role>
You draft cover letters for a job candidate. The letters are sent to real
hiring teams, so they must be honest, specific, and grounded in the
candidate's actual experience.
</role>

<task>
Given a structured job posting and a set of the candidate's relevant CV
chunks, draft a cover letter that:
1. Opens with a specific reason for applying to THIS role at THIS company —
   not boilerplate.
2. Names 2-3 concrete experiences from the candidate's CV that match
   requirements in the posting.
3. Closes with a clear ask (interview, conversation, next steps).
</task>

<rules>
- Every claim about the candidate must trace to a CV chunk in the input.
  Record the chunk IDs used in `referenced_cv_chunk_ids`. Never invent.
- Match the tone of the posting. Scrappy startup → conversational. Bank or
  government → formal. Tech mid-sized → plain-direct.
- Plain language. No "I am writing to express my enthusiasm for...". No
  "rockstar", "passionate", "guru", "ninja", "thrilled". No generic claims
  like "hardworking team player".
- Specific over general. "I led a Webpack→Vite migration that cut build times
  60%" beats "I have experience with modern frontend tooling."
- 250-350 words. Long enough to be substantive, short enough that a hiring
  manager will actually read it.
- If the candidate is a weak fit, write a letter that is honest about the fit
  and emphasizes transferable strengths. Don't oversell.
</rules>

<examples>
{EXAMPLES}
</examples>
"""

EXAMPLES = """
<example>
<input>
<job>{"title": "Senior Frontend Engineer", "company": "Bubblydoo", "location": "Antwerp, Belgium", "tech_stack": ["typescript", "next.js", "tailwind"], "summary": "Small product team building tools for designers. Hybrid in Antwerp."}</job>
<chunks>[{"id": "c1", "content": "Led migration from Webpack to Vite at Katana MRP, reducing build times 60% and CI minutes 40%", "metadata": {"company": "Katana MRP", "role": "Senior Frontend Engineer"}}, {"id": "c2", "content": "Planned and shipped a 170-ticket ingredient booking feature as feature lead, including Miro architecture diagrams and weekly cross-team syncs", "metadata": {"company": "Katana MRP"}}]</chunks>
</input>
<output>
{
  "subject": "Application: Senior Frontend Engineer — Mihkel",
  "body": "Hi Bubblydoo team,\\n\\nYour Antwerp role caught my eye because of the size — a small product team building tools for designers is where I do my best work, and it matches the kind of ownership I had at Katana MRP.\\n\\nA couple of concrete things from my experience. At Katana I led a Webpack-to-Vite migration that cut build times by 60% and CI minutes by 40% — the kind of unglamorous platform work that compounds across the team. I also planned and shipped a 170-ticket ingredient booking feature end-to-end as feature lead, including the architecture in Miro and the weekly cross-team syncs. Both pieces taught me that on a small product team the value isn't only the code you write but the clarity you bring to everyone else's work.\\n\\nMy brother is in Brussels, so relocating to Antwerp is something I've already started thinking about seriously rather than as a hypothetical.\\n\\nHappy to share more in a conversation if there's interest.\\n\\nBest regards,\\nMihkel",
  "referenced_cv_chunk_ids": ["c1", "c2"],
  "tone": "plain-direct"
}
</output>
</example>

<example>
<!-- Weak-fit case: backend role, frontend candidate -->
<input>
<job>{"title": "Senior Backend Engineer", "company": "Finary", "tech_stack": ["go", "postgresql", "kubernetes"], "summary": "Building distributed systems for personal finance."}</job>
<chunks>[{"id": "c3", "content": "Built a JWT/OTP auth flow from scratch at ObsidianOS", "metadata": {"company": "ObsidianOS"}}, {"id": "c4", "content": "Designed PostgreSQL schemas and SQL import pipelines for the LottoLens data platform across multiple lottery types", "metadata": {"company": "LottoLens"}}]</chunks>
</input>
<output>
{
  "subject": "Application: Senior Backend Engineer — Mihkel",
  "body": "Hi Finary team,\\n\\nI want to be straight up front: my primary depth is on the frontend, not backend. But I do have backend experience that's relevant to what you're building, and it's been the part of my work I most want to grow.\\n\\nAt ObsidianOS I built a JWT/OTP auth flow from scratch — the kind of work where you really need to understand the system end-to-end. For LottoLens I designed PostgreSQL schemas and SQL import pipelines across multiple lottery data types, which gave me a feel for the data-modeling decisions that look small at first but get expensive when you get them wrong.\\n\\nWhat I'd be honest about: I haven't shipped production Go, and Kubernetes is something I've used as a consumer but not operated. If the role would consider someone closer to the boundary between full-stack and backend, I'd love to discuss what that might look like. If it really needs deep backend depth from day one, I understand.\\n\\nBest regards,\\nMihkel",
  "referenced_cv_chunk_ids": ["c3", "c4"],
  "tone": "plain-direct"
}
</output>
</example>

<example>
<!-- Formal corporate posting, larger company -->
<input>
<job>{"title": "Frontend Engineer", "company": "Qonto", "tech_stack": ["typescript", "react", "ember.js"], "summary": "European business banking. Building tooling for SMB owners across multiple countries."}</job>
<chunks>[{"id": "c5", "content": "8 years building React applications, including a year as feature lead at Katana MRP", "metadata": {}}, {"id": "c6", "content": "Strong TypeScript across all recent projects, type-safe API patterns with TanStack Query", "metadata": {}}]</chunks>
</input>
<output>
{
  "subject": "Application: Frontend Engineer — Mihkel",
  "body": "Dear Qonto hiring team,\\n\\nI'm applying for the Frontend Engineer role because the combination of European fintech and multi-country tooling is exactly the kind of problem I'd like to work on next.\\n\\nMy background is eight years building React applications, including a year as feature lead at Katana MRP where I owned a 170-ticket effort end-to-end. Across recent projects I've worked with strong TypeScript and type-safe API patterns built on TanStack Query, which I'd guess maps closely to the level of rigor a banking product expects.\\n\\nI noticed the stack includes Ember.js alongside React. I haven't worked in Ember in production, but I'm comfortable with framework transitions — the migration work I led at Katana taught me that the meaningful part isn't usually the framework, it's the team patterns around it.\\n\\nI'd welcome the opportunity to discuss the role.\\n\\nBest regards,\\nMihkel",
  "referenced_cv_chunk_ids": ["c5", "c6"],
  "tone": "formal"
}
</output>
</example>
"""
```

### 11.2 CV tailor

```python
# app/modules/cv_tailor/schemas.py
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field

class SuggestionKind(str, Enum):
    emphasize = "emphasize"           # this chunk should be more prominent
    rephrase = "rephrase"             # specific wording change to match JD terms
    add_detail = "add_detail"         # this chunk needs more specificity
    deprioritize = "deprioritize"     # this chunk doesn't fit, push down

class TailorSuggestion(BaseModel):
    kind: SuggestionKind
    cv_chunk_id: UUID = Field(
        description="The existing CV chunk this suggestion applies to"
    )
    rationale: str = Field(
        description=(
            "One sentence: why this change helps for THIS specific job. "
            "Reference the job requirement or tech stack item that drove it."
        )
    )
    suggested_text: str | None = Field(
        description=(
            "For 'rephrase' or 'add_detail' suggestions, the proposed new "
            "wording. Null for emphasize/deprioritize."
        )
    )

class CVTailorResult(BaseModel):
    job_summary: str = Field(
        description="One sentence framing what this job most cares about"
    )
    suggestions: list[TailorSuggestion] = Field(
        description="3-7 specific, actionable suggestions. Quality over quantity."
    )
    do_not_suggest: list[str] = Field(
        description=(
            "Things the candidate should NOT add even if tempting — claims "
            "that would overstate fit. Each item is one sentence."
        )
    )
```

```python
# app/modules/cv_tailor/prompts.py

SYSTEM_PROMPT = """<role>
You help a job candidate tailor their existing CV for a specific job posting.
You don't rewrite the CV — you suggest specific changes the candidate should
make based on what THIS job emphasizes.
</role>

<task>
Given a structured job posting and the candidate's existing CV chunks,
produce a small set of high-leverage, specific suggestions: which chunks to
emphasize, which wording to rephrase, what details to add (drawn from what
the candidate already has), and what to deprioritize.

Also produce a `do_not_suggest` list — honest limits on the fit that the
candidate should NOT try to paper over.
</task>

<rules>
- Suggestions reference ONLY chunks that exist in the input by their UUID.
  Never reference a chunk that wasn't provided.
- Each suggestion ties to a specific JD requirement or tech stack item.
  State which one in `rationale`.
- 'add_detail' suggestions don't invent new facts — they ask the candidate
  to elaborate on something already present (e.g. "your Katana feature lead
  chunk mentions Miro and weekly syncs, but doesn't mention the 170-ticket
  scope — adding that number would land harder").
- 'rephrase' suggestions match the JD's terminology. If the JD says "design
  systems" and the candidate's chunk says "component library", suggest the
  rephrase.
- 3-7 suggestions max. Quality over quantity.
- `do_not_suggest` is for honest fit limits ("this is a backend-heavy role,
  do not claim Go experience based on having read about it").
</rules>

<examples>
{EXAMPLES}
</examples>
"""

EXAMPLES = """
<!-- 3 examples following the pattern: input → output JSON.
     One typical case (good fit, minor tweaks).
     One messy case (medium fit, multiple terminology rephrases).
     One stretch case (weak fit, focus is on do_not_suggest and transferable angles).
-->
"""
```

### 11.3 Interview prep

```python
# app/modules/interview_prep/schemas.py
from enum import Enum
from pydantic import BaseModel, Field

class QuestionCategory(str, Enum):
    technical = "technical"
    behavioral = "behavioral"
    system_design = "system_design"
    role_specific = "role_specific"
    culture_fit = "culture_fit"

class InterviewQuestion(BaseModel):
    category: QuestionCategory
    question: str = Field(
        description="The full question as the interviewer would ask it"
    )
    why_likely: str = Field(
        description=(
            "One sentence: why this question is likely for THIS specific role. "
            "Reference a requirement, tech stack item, or company trait."
        )
    )
    suggested_angle: str = Field(
        description=(
            "How the candidate should approach answering. Reference specific "
            "CV chunks where they have relevant experience to draw on."
        )
    )
    referenced_cv_chunk_ids: list[str] = Field(
        description=(
            "CV chunks the candidate can draw on. May be empty if they lack "
            "direct experience for this question."
        )
    )

class InterviewPrepResult(BaseModel):
    role_overview: str = Field(
        description="2-3 sentence summary of what to expect from this interview"
    )
    likely_areas_of_focus: list[str] = Field(
        description="3-5 short phrases naming what they'll probably probe"
    )
    questions: list[InterviewQuestion] = Field(
        description="8-12 questions distributed across categories"
    )
    questions_to_ask_them: list[str] = Field(
        description=(
            "3-5 thoughtful questions the candidate should ask the interviewer. "
            "Specific to this company/role, not generic."
        )
    )
```

```python
# app/modules/interview_prep/prompts.py

SYSTEM_PROMPT = """<role>
You generate realistic interview prep for a candidate, grounded in the
specific job posting and their actual CV.
</role>

<task>
Given a structured job posting and the candidate's CV chunks, produce:
- A short overview of what the candidate should expect from this interview.
- 3-5 likely areas of focus the interviewers will probe.
- 8-12 questions across technical, behavioral, system design, role-specific,
  and culture-fit categories. Distribution depends on the role: a senior
  engineering role weights more on technical and system design; a lead role
  weights more on behavioral.
- 3-5 thoughtful questions the candidate should ask the interviewer back —
  specific to this company/role.
</task>

<rules>
- Every question has both `why_likely` (grounded in the JD) and
  `suggested_angle` (grounded in the candidate's chunks).
- Don't invent CV chunks. `referenced_cv_chunk_ids` can be empty if the
  candidate lacks direct experience for a question; the `suggested_angle`
  should then honestly say "you don't have direct experience here — frame it
  as something you'd approach by..."
- Questions to ask back must be specific to the company/role, not generic
  ("what does career growth look like at the company"). Use details from
  the job posting.
- For technical questions, name the actual technology from the JD's tech
  stack — don't ask abstract "how would you optimize a slow query" when the
  JD specifies PostgreSQL.
</rules>

<examples>
{EXAMPLES}
</examples>
"""

EXAMPLES = """
<!-- 3 examples covering:
     One senior frontend role (heavy on tech + system design questions)
     One lead/manager role (heavy on behavioral + culture-fit)
     One stretch role (heavy on candidate framing transferable experience)
-->
"""
```

---

## 12. API endpoints

All prefixed with `/api/v1`. Tag routers so orval produces organized output:
`APIRouter(prefix="/jobs", tags=["jobs"])`.

| Module | Method | Path | Body | Returns |
|---|---|---|---|---|
| cv | POST | `/cv/documents` | multipart file + form kind | `CVDocumentRead` (202) |
| cv | GET | `/cv/documents` | — | `list[CVDocumentRead]` |
| cv | GET | `/cv/documents/{id}` | — | `CVDocumentRead` |
| cv | DELETE | `/cv/documents/{id}` | — | `204` |
| jobs | POST | `/jobs/from-url` | `CreateJobFromUrl` | `JobRead` (202) |
| jobs | POST | `/jobs/from-text` | `CreateJobFromText` | `JobRead` (202) |
| jobs | GET | `/jobs` | query: status, limit, offset | `list[JobListItem]` |
| jobs | GET | `/jobs/{id}` | — | `JobRead` |
| jobs | DELETE | `/jobs/{id}` | — | `204` |
| jobs | POST | `/jobs/{id}/retry` | — | `JobRead` |
| matching | POST | `/matching/{job_id}/run` | — | `MatchRunRead` |
| matching | GET | `/matching/{job_id}/latest` | — | `MatchRunRead \| null` |
| matching | GET | `/matching/{job_id}/history` | — | `list[MatchRunRead]` |
| cover_letters | POST | `/cover-letters/{job_id}/generate` | — | `CoverLetterDraft` |
| cover_letters | GET | `/cover-letters/{job_id}` | — | `list[CoverLetterDraft]` |
| cv_tailor | POST | `/cv-tailor/{job_id}/run` | — | `CVTailorResult` |
| cv_tailor | GET | `/cv-tailor/{job_id}/latest` | — | `CVTailorResult \| null` |
| interview_prep | POST | `/interview-prep/{job_id}/generate` | — | `InterviewPrepResult` |
| interview_prep | GET | `/interview-prep/{job_id}/latest` | — | `InterviewPrepResult \| null` |

---

## 13. ARQ background jobs

```python
# app/workers/arq_worker.py
from arq.connections import RedisSettings
from app.core.config import settings
from app.modules.cv.tasks import chunk_and_embed_cv
from app.modules.jobs.tasks import scrape_and_extract_job, extract_job

class WorkerSettings:
    functions = [chunk_and_embed_cv, scrape_and_extract_job, extract_job]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_tries = 3
    job_timeout = 120
```

The three new agents (cover letter, CV tailor, interview prep) run
synchronously from their POST endpoints — one Sonnet call each, fast enough
the user can wait. No ARQ task needed.

---

## 14. Frontend orval config

```typescript
// frontend/orval.config.ts
import { defineConfig } from 'orval';

export default defineConfig({
  postpilot: {
    input: { target: 'http://localhost:8000/api/v1/openapi.json' },
    output: {
      mode: 'tags-split',
      target: 'src/api/generated/endpoints.ts',
      schemas: 'src/api/generated/model',
      client: 'react-query',
      httpClient: 'axios',
      mock: true,
      prettier: true,
      override: {
        mutator: { path: 'src/api/client.ts', name: 'customAxios' },
        query: { useQuery: true, options: { staleTime: 30_000 } },
      },
    },
  },
});
```

Run `npm run gen:api` whenever the backend changes. Commit `src/api/generated/`.

---

## 15. Build order

### M0 — Bootstrap (half a day)

- [ ] Init repo, paste pyproject.toml, `uv sync`
- [ ] Init Vite frontend
- [ ] Compose up postgres + redis
- [ ] FastAPI hello-world at `/api/v1/health`
- [ ] Alembic initial migration with `CREATE EXTENSION vector`
- [ ] Confirm `/docs` works
- [ ] Set `ALLOW_MODEL_REQUESTS=False` in `tests/conftest.py`

### M1 — CV module (1-2 evenings)

- [ ] Tables for cv_documents + cv_chunks
- [ ] POST `/cv/documents` accepts PDF, extracts text via PyMuPDF
- [ ] Four files: `cv/prompts.py`, `cv/agent.py`, `cv/service.py`, `cv/tasks.py`
- [ ] System prompt with 3 few-shot examples (typical, messy, multilingual)
- [ ] `chunk_and_embed_cv` ARQ task
- [ ] GET endpoints
- [ ] Upload your CV; verify chunks look right
- [ ] 5 eval cases in `tests/evals/cv/`

### M2 — Jobs module (1-2 evenings)

- [ ] Tables for jobs + job_requirements
- [ ] POST `/jobs/from-text` first (skip scraping)
- [ ] Job extractor agent following the four-file structure + 3 examples
- [ ] POST `/jobs/from-url` with Playwright scraper
- [ ] GET endpoints
- [ ] Paste 3-5 real postings, verify extraction
- [ ] 5 eval cases in `tests/evals/jobs/`

### M3 — Matching (1 evening)

- [ ] match_runs table
- [ ] Deterministic vector search in `matching/service.py` (no LLM)
- [ ] Match explainer agent (Sonnet) + 3 examples
- [ ] POST `/matching/{job_id}/run`
- [ ] Score one of your real applications, sanity check the explanation

### M4 — Frontend (2-3 evenings)

- [ ] `npm run gen:api` working against running backend
- [ ] Pages: CV upload, jobs list, job detail, match view
- [ ] Enough Tailwind/shadcn for it to look decent

### M5 — Cover letter drafter (1 evening)

- [ ] cover_letter_drafts table
- [ ] Agent files + 3 examples (typical fit, weak fit, formal posting)
- [ ] Endpoint + UI to view/copy the draft

### M6 — CV tailor (1 evening)

- [ ] cv_tailor_runs table
- [ ] Agent files + 3 examples
- [ ] Endpoint + UI showing suggestions inline next to chunks

### M7 — Interview prep (1 evening)

- [ ] interview_prep_runs table
- [ ] Agent files + 3 examples
- [ ] Endpoint + UI showing question list

### M8 — Deploy

- [ ] Railway: backend from `backend/`, add PG + Redis
- [ ] Railway: second service for the ARQ worker
- [ ] Vercel: frontend from `frontend/`
- [ ] CORS allowlist updated on backend
- [ ] Confirm prompt caching is hitting

---

## 16. Deployment notes

**Railway:**
- New project, Root Directory `backend`
- Add Postgres plugin (pgvector via `CREATE EXTENSION vector`)
- Add Redis plugin
- Add a second service for the ARQ worker — same image, command:
  `arq app.workers.arq_worker.WorkerSettings`
- Env vars from `.env.example`

**Vercel:**
- New project, Root Directory `frontend`
- Build: `npm run build`, Output: `dist`
- Env vars: `VITE_API_BASE_URL=https://<railway-domain>/api/v1`

---

## Appendix A: Sources for agent design principles

The principles in section 9 come from these sources. Open them when you want
to go deeper on any specific point.

- [Anthropic Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — official, authoritative. Sections used: clarity, examples, XML structure, long context, tool use, model behavior in 4.6+.
- [Anthropic Prompt Caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — TTL, pricing, what's cacheable.
- [Pydantic AI Testing docs](https://ai.pydantic.dev/testing/) — TestModel, FunctionModel, `Agent.override`, `ALLOW_MODEL_REQUESTS`.
- [Pydantic AI Anthropic Provider](https://ai.pydantic.dev/models/anthropic/) — Claude integration specifics.
- [Production-Ready LLM Agents: Offline Evaluation](https://towardsdatascience.com/production-ready-llm-agents-a-comprehensive-framework-for-offline-evaluation/) — eval harness patterns.
- [Pydantic AI Production Tutorial (April 2026)](https://dev.to/jahanzaibai/pydantic-ai-tutorial-how-i-build-type-safe-ai-agents-that-actually-work-in-production-3bcp) — patterns from production deployments.
- [Pydantic AI Practical Tutorial (April 2026)](https://jangwook.net/en/blog/en/pydantic-ai-type-safe-agent-tutorial-2026/) — version pinning, testing patterns.

## Appendix B: Suggested Claude Code prompts

Paste this PLAN.md into the repo root as `docs/PLAN.md`. Then use prompts like:

- "Read docs/PLAN.md. Bootstrap the backend per section 3 — pyproject.toml,
  uv sync, alembic init. Don't write any business logic yet."
- "Read docs/PLAN.md sections 6 and 7. Create the initial Alembic migration
  with all the SQL from section 6, then create the SQLAlchemy models per
  section 7."
- "Read docs/PLAN.md section 9 (agent design principles) and section 10.1.
  Implement the CV chunker following the four-file pattern. Use the system
  prompt and three examples from section 10.1 verbatim."
- "Add 2 more few-shot examples to app/modules/cv_tailor/prompts.py per the
  rules in section 9.5. One messy/medium-fit case, one stretch case."
- "Read docs/PLAN.md section 9.11. Set up `tests/conftest.py` with the
  ALLOW_MODEL_REQUESTS guard and a TestModel fixture for the cv_extractor."

Keep PLAN.md as the single reference. When you change a decision, update it.
