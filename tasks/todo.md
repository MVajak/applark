# Worklog — unify/genericize refactors

Resume point for the backend dedup work. Frontend work is finished; backend
items 1–2 are committed; items 3, 4, 6 are next.

---

## ✅ DONE (committed)

- **Frontend feature registry** — commit `99782bb`. Collapsed the 4 AI-feature
  Section+Button pairs into one generic `<FeatureSection>` + per-domain `feature.tsx`
  configs + a `FeatureDrawer` registry. (Full notes in git history.)
- **Backend items 1–2** — commit `b4264b9`:
  - `make_agent[T](module, output_type, *, model, max_tokens, retries=2) -> Agent[None, T]`
    in `app/core/llm.py`; all 6 `agent.py` files now call it.
    ⚠️ matching passes `retries=1` to preserve its prior behavior (Pydantic AI default).
    Open question for later: should matching get `retries=2` like the others?
  - `extract_token_usage(usage: RunUsage) -> tuple[int|None, int|None]` in `app/core/llm.py`;
    replaced the 6 copy-pasted getattr-fallback blocks in the services.

---

## ✅ DONE this session — backend items 3, 4, 6 (uncommitted)

Two new shared modules; six files trimmed (~141 lines of duplication removed).
Verification all green: `pyright app` 0 errors, `ruff check app` pass,
`ruff format --check` on all touched files pass, `pytest --ignore=tests/evals` 9 passed.

- **Item 3 + 4** → new `app/modules/feature_context.py`:
  - `build_job_dict(job: Job)` / `chunk_for_prompt(chunk: CVChunk)` — made public
    (were `_`-prefixed per-service), typed `Job`/`CVChunk` → `dict[str, object]`
    (dropped the `Any`).
  - `FeatureContext` frozen dataclass (`job`, `match_run`, `cv_doc`) +
    `gather_match_feature_context(session, job_id, *, needs_ready_subject,
    no_match_action)` — the two kwargs only shape the 409 wording, so the exact
    per-feature messages are preserved.
  - ONE shared exception pair: `NoMatchRunError` + `FeaturePrerequisitesError`
    (replaced the 3 redeclared `*PrerequisitesError`). Routers import them from here.
  - matching left untouched (keeps `build_match_context` / vector search).
- **Item 6** → new `app/core/http.py`: `conflict_on(*exc_types)` contextmanager
  maps the passed exception types → `HTTP_409_CONFLICT`. Applied in all 4 routers.
  matching's 404 + job-status-409 preflight and the bespoke GET endpoints stay as-is.
  (Note: pyright `reportDeprecated` requires `-> Generator[None]`, not `Iterator`.)

Per-service kept (as planned): `_select_chunks` (cover_letters), the
`MatchExplanation.model_validate(...)` rehydrate, and all prompt assembly.

---

## (original plan below — kept for reference)

## ▶️ RESUME HERE — backend items 3, 4, 6 (do as one batch)

Source of the plan: the three backend analyses earlier this session. The four
"run an LLM feature on a job" modules are `matching`, `cover_letters`, `cv_tailor`,
`interview_prep`. **matching is the odd one out** for items 3–4 (it produces the
match and uses pgvector search — no match dependency) so it stays out of the
shared gather helper.

### Item 3 — extract identical stateless helpers
`_build_job_dict(job)` (14 lines) and `_chunk_for_prompt(chunk)` (7 lines) are
**byte-identical** in `cover_letters/service.py`, `cv_tailor/service.py`,
`interview_prep/service.py`. Move to one shared module and import in all three.
- Placement: a new sibling module (e.g. `app/modules/feature_context.py`), NOT
  `app/core/` — these import `app.modules.cv.models.CVChunk` and job attrs, and
  core must not depend on modules (keep the layering: modules → core).

### Item 4 — shared `gather_match_feature_context`
The ~25-line gather/guard block is duplicated verbatim in cover_letters / cv_tailor /
interview_prep: load job (`get_job_with_requirements`) → status==ready check →
latest match (`get_latest_for_job`) → CV doc (`get_latest_document_with_chunks`) →
chunks-present check. Only the error wording differs.
- Add `gather_match_feature_context(session, job_id) -> FeatureContext` (dataclass:
  `job`, `match_run`, `cv_doc`) in the same shared module as item 3.
- Unify the duplicated `NoMatchRunError` + `*PrerequisitesError` (currently redeclared
  in each of the 3) into ONE shared pair; update routers' imports accordingly.
- Leave per-service: `MatchExplanation.model_validate(match_run.details)` rehydrate,
  cover_letters' `_select_chunks` (top-k strengths), and prompt assembly.
- Do NOT route matching through this — keep its `build_match_context` (vector search).

### Item 6 — shared 409 exception-mapping helper (routers)
The block `except service.XError as exc: raise HTTPException(409, str(exc)) from exc`
repeats ~7× across the 4 routers. Extract a tiny helper/contextmanager that maps a
passed-in tuple of exception types → `HTTP_409_CONFLICT` (keep the narrow except;
no broad `except Exception`).
- NOT a full router factory. matching has extra job-status pre-flight + a `/history`
  endpoint; cover_letters' GET returns a list (drafts), no `/latest`. Those stay bespoke.

### Explicitly NOT doing (over-abstraction — decided against)
- No generic `run_feature(...)` pipeline / base service class.
- No declarative `JobRunMixin` / generic repository this round (that was item 5,
  which needs a DB migration — deferred, not in this batch).
- No full router factory.
- Leave the prompt registry system alone (already clean).

---

## ⏳ PENDING DECISION (ask user)
HEAD already fails `ruff format --check` on ~21 files — pre-existing drift from when
`line-length` moved 88→100. Items 1–2 were committed WITHOUT touching it (only the 13
edited files were formatted; 16 format-only files were reverted). Offer a standalone
`chore(backend): ruff format at line-length 100` commit to clear it repo-wide.

---

## Verification (backend)
```
cd backend
uv run pyright app                 # expect 0 errors
uv run ruff check app              # expect pass
uv run pytest tests --ignore=tests/evals -q   # expect pass (incl. prompt-baseline drift test)
```
Prompts untouched ⇒ `tests/test_prompts_baselined.py` stays green. Do NOT run
`tests/evals` casually (real LLM calls, costs money).

## Restarting the local stack (background processes die on IDE/shell restart)
```
docker compose up -d                                              # infra (likely still up)
cd backend && uv run uvicorn app.main:app --reload                # API :8000
cd backend && uv run arq app.workers.arq_worker.WorkerSettings    # worker
cd frontend && pnpm dev                                           # Vite :5173
```
Health check: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health`
