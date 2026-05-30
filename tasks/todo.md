# Worklog — tiers (PRO/PREMIUM) + pay-as-you-go AI credits

Plan: `~/.claude/plans/lets-validate-how-our-mighty-puffin.md`

Model: tier = feature access (none → no AI; PRO → match+cover; PREMIUM → all 4). Credits = pay-as-you-go
wallet, one-time packs (stub now, Stripe later), flat per-run cost. Free intake. Per-run gate =
tier!=none AND tier unlocks feature AND credits>=cost (else 403/402). Backend follows the layering default.

## Phases (each validated before moving on)
- [x] **P1** — billing config + models + migration 0010 (users.tier, users.credits, credit_ledger) + schemas + repository.
- [x] **P2** — billing service (get_status/charge/refund/subscribe/grant_pack) + BillingProvider + `/billing` router.
- [x] **P3** — gate the 4 feature services (charge→agent→refund-on-failure via provider) + central 402/403 handlers.
- [x] **P4** — FE: useBilling, capabilities-from-access, FeatureSection cost + locked/insufficient CTAs, ActionGrid gating.
- [x] **P5** — FE: billing page (subscribe + buy pack, RHF+Zod) + header credits-chip/tier + i18n + `formatCurrency`.
- [x] **P6** — validation (see Review).

## Review

**Done.** Tiers + pay-as-you-go credits shipped across backend + frontend.

Backend
- `app/modules/billing/`: `config.py` (FEATURE_COST / FEATURE_TIERS / CREDIT_PACKS — single source of truth),
  `models.py` (`credit_ledger`), `schemas.py`, `repository.py` (lock_user `FOR UPDATE` / apply_delta / set_tier),
  `service.py`, `protocols.py` (`BillingProvider`), `router.py` (`/billing`: me/packs/subscribe/checkout).
- `users.tier` + `users.credits` columns (migration `0010_billing`).
- The 4 feature services charge-before-agent + refund-on-failure **via `providers.get(BillingProvider)`** (no direct
  billing import — layering respected). Billing exceptions map to 402/403 centrally in `main.py`, so feature
  routers stay billing-free.

Frontend
- `domains/billing/`: `useBilling` (GET /billing/me; fails closed while loading), `pages/BillingPage`,
  `components/PlanPicker` (RHF+Zod tier form), `components/CreditPacks`.
- `auth/capabilities` derives from `useBilling().access`; `FeatureSection` shows "Costs N credits" + gated run
  (tier-lock → Upgrade tooltip, balance < cost → disabled + Buy-credits link); `ActionGrid` locked → Upgrade badge.
- Header: credits chip / tier badge + Buy-credits / Upgrade items. `@applark/format` gained `formatCurrency`.

Validation
- Backend: `ruff` ✓, `ruff format --check` ✓, `pyright` 0 errors ✓, `pytest` 9 passed ✓.
- Backend billing mechanics (throwaway script vs. **real dev DB**, 10/10): none-tier→403, 0-credit→402, grant pack,
  charge deducts by cost, refund restores, pro can't use premium feature (no deduction), premium unlocks, unknown
  pack errors, ledger = exact 4-row append-only audit.
- Backend HTTP contract (live server): none → subscribe PRO (access flips) → checkout (credits granted) → /me reflects.
- Frontend: `typecheck` ✓, `lint` ✓, `build` ✓. All dynamic i18n keys confirmed present.

Not done by me (needs a human at the browser)
- Live UI click-through: no headless browser is installed and Playwright wasn't added (heavy dep, not approved).
  React rendering is type-safe + driven entirely by the verified `/billing/me` contract. Full stack is left running
  (docker + API + vite + ARQ worker) for the manual journey: log in → header shows "Upgrade" + all 4 actions locked
  → `/billing` subscribe PRO (match+cover unlock, tailor/interview stay locked) → buy a pack (chip updates) → open
  Match, see "Costs 2 credits" + enabled run → run drains 2 credits.
- Nothing committed (commit on request).
