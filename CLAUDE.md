## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, STOP and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes -- don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests -- then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

## Task Management
1. **Plan First:** Write plan to tasks/todo.md with checkable items
2. **Verify Plan:** Check in before starting implementation
3. **Track Progress:** Mark items complete as you go
4. **Explain Changes:** High-level summary at each step
5. **Document Results:** Add review section to tasks/todo.md
6. **Capture Lessons:** Update tasks/lessons.md after corrections

## Core Principles
- **Simplicity First:** Make every change as simple as possible. Impact minimal code.
- **No Laziness:** Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact:** Only touch what's necessary. No side effects with new bugs.

## Tech Stack

This is a monorepo: **FastAPI Python backend** in `backend/` + **React + Vite frontend** in `frontend/`. Full build spec lives in `PLAN.md` (temporary — will be removed once the project stabilizes).

**Approved libraries** (use these by default — no justification needed):

**Backend (Python 3.13, managed by `uv`):**
- FastAPI, Pydantic v2, Pydantic AI (pinned to 1.88.0)
- SQLAlchemy 2.0 async + asyncpg + PostgreSQL 16 + pgvector
- Alembic (migrations), ARQ + Redis (background jobs)
- PyMuPDF (PDF parsing), Playwright async (scraping)
- OpenAI SDK (embeddings — `text-embedding-3-small`)
- Anthropic SDK (via Pydantic AI)
- structlog, pydantic-settings, httpx

**Frontend (Node 20+, npm):**
- React 19, Vite, TypeScript 5.7+
- TanStack Query v5, axios, react-router-dom v7
- Orval (OpenAPI → TS + TanStack Query hook codegen)
- Tailwind CSS + shadcn/ui (added via the shadcn CLI)

**Dev tooling:**
- Backend: ruff, pyright, pytest + pytest-asyncio, pre-commit, dirty-equals
- Frontend: TypeScript strict mode, orval for type generation

**Adding a new library — STOP and ask the user before installing.** The proposal must include:
- What problem it solves that the approved set can't
- The two best alternatives considered and why this one wins
- Bundle / runtime cost (or wheel size + Python compatibility for backend)
- Maintenance health (last release, open issues, weekly downloads)

## Strict Python (backend)

These rules apply to all code under `backend/`. They are not suggestions.

- **Pyright strict mode** stays on. Don't loosen any flag.
- **Type hints required** on every function signature (parameters and return). Inferred return types fine for internal helpers; FastAPI routes and public service functions are explicitly typed.
- **No `Any`.** Use `object`, `Protocol`, generics, or `TypeVar`-narrowed helpers. If a third-party lib leaks `Any`, narrow it at the boundary.
- **Pydantic at every external boundary** — FastAPI request/response bodies, env vars (via `pydantic-settings`), LLM outputs (via Pydantic AI `output_type`), scraped content, HTTP responses you parse.
- **Async-first.** Routes, services, and repositories are `async def`. Don't mix sync DB calls into async paths — use SQLAlchemy 2.0 async session.
- **SQLAlchemy 2.0 `Mapped[...]` style** for all ORM models. Reserved-name gotcha: name the column `metadata_: Mapped[dict] = mapped_column("metadata", ...)`.
- **Exhaustive `match` over enums** with `case _:` raising on unknown variants. Compilation must fail when a new variant is added unhandled.
- **`ruff` formatting + linting** is the source of truth — don't fight it.
- **No bare `except:` and no `except Exception:` swallowing** — catch the specific exception or re-raise with context.
- **Each LLM module follows the four-file layout** from `PLAN.md` §9.10: `schemas.py`, `prompts.py`, `agent.py`, `service.py`. `agent.run()` is only called from `service.py`, never directly from routes or tasks.

## Strict TypeScript (frontend)

These rules apply to all code under `frontend/`. They are not suggestions.

- `tsconfig.json` `strict: true` stays on. Don't loosen any flag.
- **No `any`.** Use `unknown` and narrow with type guards or Zod.
- **No non-null assertions (`!`).** Handle the null case or prove with a real check that it can't happen.
- **No type assertions (`as Foo`)** without a one-line comment explaining why the cast is safe.
- **Prefer orval-generated types** from `src/api/generated/`. Don't hand-write types for API request/response shapes — regenerate via `npm run gen:api`. Commit the generated output.
- **Parse all non-API external data through Zod** before use: env vars, localStorage, anything not covered by orval.
- **Discriminated unions for state shapes** — e.g. `{ kind: "loading" } | { kind: "ready"; data: T } | { kind: "error"; error: E }`. No optional-flag soup.
- **Exhaustive `switch`** over discriminated unions — end with `default: { const _exhaustive: never = x; throw new Error(...) }`. Compilation must fail when a new variant is added unhandled.
- Prefer `readonly` arrays / objects when mutation isn't intended.
- Inferred return types are fine for internal functions; exported / public-API boundaries are explicitly typed.
