# Worklog — email + OTP login and per-user data scoping

Plan: `~/.claude/plans/lets-validate-how-our-mighty-puffin.md`
Decisions: dev console OTP (EmailSender abstraction) · access+refresh JWTs · dev DB reset.

---

## ✅ Backend — DONE & verified (Phases 0–2)

- **Deps/config**: added `pyjwt`, `email-validator`; `JWT_SECRET`, `OTP_PEPPER`, TTLs,
  `OTP_MAX_ATTEMPTS`, `OTP_REQUEST_LIMIT_PER_HOUR` in `config.py` + `.env.example`
  (dev-only secret defaults, override in prod).
- **`app/core/security.py`**: pyjwt access/refresh tokens (HS256, typed `TokenClaims`),
  OTP **HMAC hashing** (`hash_otp`/`verify_otp_hash`, peppered, constant-time), `AuthUser`,
  stateless `get_current_user` (HTTPBearer → 401).
- **`app/modules/auth/`**: `User` + `OtpCode` (stores `code_hash`, `attempt_count`) models,
  schemas, repository, service (request_otp w/ Redis rate-limit + invalidate-pending +
  hashed store, verify_otp w/ attempt cap + single-use, refresh), `ConsoleEmailSender`
  (logs the code in dev), router (`/auth/request-otp|verify-otp|refresh|me`) wired into v1.
- **Migrations**: `0008_auth` (users + otp_codes); `0009_user_scoping` (user_id NOT NULL FK
  on cv_documents/jobs/match_runs/cover_letter_drafts/cv_tailor_runs/interview_prep_runs;
  job-URL uniqueness now per-user). DB reset + upgraded to head.
- **Scoping**: `user_id` on the 6 models; threaded through providers/protocols,
  repositories, services, `shared/feature_context`, and **every existing route now requires
  `get_current_user`**. get-by-id is `WHERE id AND user_id` → 404 cross-user. ARQ tasks
  unchanged (operate by id on already-scoped rows).
- **Verified**: `ruff check app` clean · `pyright app` 0 errors · `pytest` 9 passed ·
  auth flow smoke (code hashed+logged, tokens issued, refresh, wrong code rejected) ·
  cross-user scoping smoke (A sees own job; B → empty list + None/404).

## ✅ Frontend — DONE & verified (Phases 3–4)
- `@applark/ui`: copied `InputOTP` (+`input-otp` dep) and the `Field` set; exported.
- Auth zustand store (persist `applark-auth`); `customAxios` request interceptor (Bearer)
  + 401 silent-refresh via a bare instance (deduped) → retry / logout+redirect; `pnpm gen:api`
  generated `useRequestOtp`/`useVerifyOtp`/`useRefresh`.
- `LoginPage` (email → 6-digit OTP → redirect), `RequireAuth` guard, router split (public
  `/login` + protected tree), `auth.*` i18n keys, logout in `AppHeader`.
- SSE: EventSource passes `?token=`; backend `/cv/events` + `/jobs/events` now require a
  `get_current_user_query` token.

## ✅ Phase 5 — verified
- Frontend: `pnpm typecheck` ✓ · `pnpm lint` ✓ · `pnpm build` ✓.
- Backend e2e (live server, curl): request-otp → 200 (code logged + stored **hashed**);
  verify-otp → tokens; `/jobs` no-token → **401**, with-token → `[]` 200; `/auth/me` → 200;
  refresh → 200; **OTP reuse → 401** (single-use); SSE no-token → 401, with-token → 200.
- Cross-user scoping smoke: A sees own job; B → empty + None/404.

## Review
Login + per-user scoping complete and verified end-to-end. The one-off `request-otp`
"hang" seen mid-verification was the network outage interrupting the run, not a code bug —
on a stable server it returns 200 in ~0.12s.

## Notes / follow-ups
- Dev DB was reset (approved) — existing jobs/CVs gone; re-seed by logging in + re-adding.
- SSE endpoints are now auth-gated, but channels are still global (an event only triggers a
  refetch against already-scoped endpoints, so no data leak) — per-user channels are a future refinement.
- Refresh tokens are stateless (not server-revocable); revisit if "log out everywhere" is needed.
- Browser click-through of the login UI not done here (no browser in this env); backend flow +
  FE build/types are proven. Run `pnpm dev` + API to click through.
- Not committed yet.
