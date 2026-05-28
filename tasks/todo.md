# Worklog — strict router → service → repository layering

Enforce: routers/tasks call ONLY services; services own business logic + repo
access; each repository is imported only by its own module's service; cross-module
providers are backed by services (not repositories).

Plan: `~/.claude/plans/lets-validate-how-our-mighty-puffin.md`

---

## ▶️ Checklist

- [x] **core/http** — added `not_found_on(*exc_types)` (404) beside `conflict_on`.
- [x] **cv/service** — added `create_cv_document`, `list_documents`,
      `get_document_with_chunks`, `delete_document`, `get_latest_document_with_chunks`
      (CVProvider method), `reprocess_cv_document`.
- [x] **cv/router** — delegates to `cv_service`; dropped `repository`/`CVDocument`/`parser`.
- [x] **cv/tasks** — calls `cv_service.reprocess_cv_document`; dropped `repository`.
- [x] **jobs/service** — added `DuplicateJobError`/`JobNotRetriableError`,
      `_ensure_url_unique`, `create_job_from_text`/`create_job_from_url`, `list_jobs`,
      `get_job_with_requirements` (JobProvider), `delete_job`, `mark_for_retry`,
      `begin_extraction`/`begin_scrape`/`persist_scraped_text`/`scrape_job`;
      folded `status=ready` into `persist_job_extraction`.
- [x] **jobs/router** — delegates to `jobs_service`; `DuplicateJobError`→409 dict,
      `JobNotRetriableError`→409; dropped `Job` model + `repository`.
- [x] **jobs/tasks** — calls service phase helpers; dropped `repository`.
- [x] **matching/service** — added `JobNotFoundError`/`JobNotReadyError`, moved
      job None/status checks into `build_match_context`; added `get_latest_for_job`
      (MatchingProvider) + `get_history_for_job`.
- [x] **matching/router** — `not_found_on`+`conflict_on` around `run_match`;
      delegates latest/history; dropped `jobs_repository`/`repository`/`JobStatus`.
- [x] **leaf modules** — read method added to cover_letters/cv_tailor/interview_prep
      services; routers switched; `repository` imports dropped.
- [x] **providers** — `main.py` registers service modules; docstrings updated in
      `core/providers.py` + `cv/protocols.py`.
- [x] **verify** — ruff/pyright/pytest green; encapsulation greps clean; app boots.

Verification commands (from `backend/`, per prior worklog — DO NOT run `tests/evals`,
it makes real paid LLM calls):
```
uv run ruff format app && uv run ruff check app
uv run pyright app
uv run pytest tests --ignore=tests/evals -q
```

---

## Review

**Outcome:** uniform `router/task → service → repository` flow. Every router and
task now calls only its service; each `repository` is imported solely by its own
`service.py` (verified by grep — 6/6); cross-module access goes through providers
that are now backed by **services**, so no repository is reachable from outside
its module.

**Verification (all green):**
- `ruff format app` (3 files reformatted) + `ruff check app` — pass.
- `pyright app` — 0 errors, 0 warnings (strict, no `Any`).
- `pytest tests --ignore=tests/evals -q` — 9 passed. (evals skipped: real paid LLM calls.)
- `python -c "import app.main"` — app boots; providers resolve to the service
  modules; protocol methods are callable; 26 routes registered.
- Encapsulation greps: no `import repository` in any router/tasks; no
  `jobs_repository` reach in matching.

**Behavior parity:** error bodies kept byte-identical — matching 404 `"Job not
found"` (JobNotFoundError → `not_found_on`), matching 409 not-ready message
unchanged (JobNotReadyError → `conflict_on`), jobs duplicate-URL 409 still returns
`{message, existing_job_id}`, jobs retry 409 message unchanged. `status=ready` now
set inside `persist_job_extraction` (was set by a second `get_job` in each task) —
same end state, one fewer round-trip.

**Deliberate boundary choices:** session/transaction (`SessionLocal` + `commit` +
relationship `refresh` for the response) and ARQ `enqueue_job` stay in routers
(the `arq_pool` is a request dependency); only the retry *task-name decision*
moved into `jobs_service.mark_for_retry`. The PDF parse and scrape are now wrapped
by the cv/jobs services so tasks call services exclusively.

**Not committed** — left on `main` working tree for review (no commit requested).
