# Applark

FastAPI + React side project that ingests CVs and job postings, embeds them in
pgvector, and uses Pydantic AI agents to extract structure and explain matches.

Backend lives in `backend/`, frontend in `frontend/`. Full build spec is in
`PLAN.md` (temporary — to be removed once the project stabilises).

## Local setup

Prereqs: Docker + Docker Compose, [uv](https://github.com/astral-sh/uv), Node
20+. On macOS: `brew install uv`.

```bash
# 1. Start Postgres (pgvector), Redis, Adminer
docker compose up -d

# 2. Backend Python deps + Playwright Chromium
cd backend
cp .env.example .env             # fill in ANTHROPIC_API_KEY + OPENAI_API_KEY
uv sync
uv run playwright install chromium   # one-time, required for URL scraping

# 3. Apply database migrations
uv run alembic upgrade head

# 4. Frontend deps
cd ../frontend
cp .env.example .env
npm install
```

## Running the app

```bash
# Terminal A — FastAPI
cd backend && uv run uvicorn app.main:app --reload

# Terminal B — ARQ worker (handles background CV chunking + job scraping/extraction)
cd backend && uv run arq app.workers.arq_worker.WorkerSettings

# Terminal C — Vite dev server
cd frontend && npm run dev
```

API: <http://localhost:8000/docs>. Frontend: <http://localhost:5173>. Adminer
for DB inspection: <http://localhost:8081> (postgres on host port `5434`).

## Tests

```bash
cd backend
uv run pytest                                # default; eval tests are skipped
uv run pytest tests/evals/cv/ --run-evals    # eval suite hits real Anthropic API
```
