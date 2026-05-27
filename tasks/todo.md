# Feature Registry refactor (frontend)

Collapse the four AI-feature "Section + Button" component pairs
(cover_letters, cv_tailor, interview_prep, matching) into one generic
`<FeatureSection>` driven by per-domain typed config objects.

## Why
- The three `*Button.tsx` files are ~95% identical (differ by ~5 config tokens).
- The three `*Section.tsx` files share the same loading/gate/empty/pending/result shell.
- `matching` re-implements the mutation/toast/pending logic inline (the "before" picture).

## Design
- `jobs/components/FeatureSection.tsx`: generic `FeatureSection<TData, TResult>` + exported
  `FeatureSectionConfig<TData, TResult>` type. Owns the match-gate query, CV-chunks query,
  the mutation, optimistic pending, and the loading/gate/empty/pending/result+rerun layout.
- `useFeatureMutationOptions`: extend with optional `onMutate` (drives optimistic pending).
- Per-domain `feature.tsx` exports a concretely-typed config (hooks + copy + `renderResult`).
  The genuinely-different result panels stay as-is, injected via `renderResult`.
- `FeatureDrawer`: a `Record<JobActionId, (jobId) => ReactNode>` registry replaces the 4-way switch.

## Tasks
- [ ] Extend `useFeatureMutationOptions` with optional `onMutate`
- [ ] Create `jobs/components/FeatureSection.tsx` (generic shell + config type)
- [ ] Create `cover_letters/feature.tsx` (drafts list + history via renderResult)
- [ ] Create `cv_tailor/feature.tsx`
- [ ] Create `interview_prep/feature.tsx`
- [ ] Create `matching/feature.tsx` (MatchResult moves here, sans its own re-run button)
- [ ] Rewrite `FeatureDrawer.tsx` to use the registry
- [ ] Delete 3 `*Button.tsx`, 3 `*Section.tsx`, and `MatchSection.tsx`
- [ ] Update the 5 affected barrels
- [ ] `pnpm typecheck` + `pnpm lint` green

## Known minor behavioral changes (acceptable, unify behavior)
- Pending now replaces the whole section (matching already did this) rather than just the CTA button.
- matching re-run button moves below the result (was embedded in MatchResult) and uses the
  feature icon instead of `RotateCcw`.
- cover-letter re-run ("Generate again") moves below the previous-drafts toggle.
- Optimistic "stay pending until refetch" now applies to all four (was matching-only),
  and is correctly cleared on error (fixes a latent stuck-pending bug in matching).

## Review

Done. All tasks complete; `pnpm typecheck`, `pnpm lint`, and `pnpm build` are green,
no `any`/`as` introduced, and no stale references to the deleted components remain.

### Outcome
- Deleted 7 files (3 `*Section.tsx`, 3 `*Button.tsx`, `MatchSection.tsx`) — 427 lines.
- Added `FeatureSection.tsx` (146) + 4 per-domain `feature.tsx` configs (203) + `onMutate`
  on the shared hook. Net ~70 fewer lines, and the duplicated shell JSX now lives in one place.
- `matching` is now on the shared mutation/pending path instead of its inline re-implementation.
- `FeatureDrawer`'s hard-coded 4-way switch is now a `Record<JobActionId, …>` registry.

### Type-safety note
The registry stays `any`-free: `FeatureSection<TData, TResult>` is generic, each domain config
is concretely typed, and `hasResult` is a type guard that narrows the `T | null` latest-query
payload to the non-null result the panel needs.