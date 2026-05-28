# Worklog — i18n (English-only, ready for more languages)

Goal: real i18n support, English only now, structured so a second language = one
JSON tree. Library: react-i18next (matches portfolio-ui) + type-safe keys. Packaged
as a `@applark/i18n` workspace package. Plan:
`~/.claude/plans/lets-validate-how-our-mighty-puffin.md`

---

## ✅ Done

- [x] **`packages/i18n` (`@applark/i18n`)** — flat package mirroring `@applark/ui`
      (consumed as TS source via workspace symlink). `config.ts` (i18next init +
      `LanguageDetector` + the `CustomTypeOptions` augmentation), `index.ts`
      (side-effect init + re-exports `useTranslation`/`Trans`/`i18n`/`SUPPORTED_LANGUAGES`/
      `Language`/`TranslationKey`), `locales/en/translation.json`.
      Deps: i18next ^26, react-i18next ^17, i18next-browser-languagedetector ^8.
- [x] **Wiring** — `@applark/i18n` added to `@applark/web`; `import '@applark/i18n'`
      in `main.tsx`; `resolveJsonModule` added to `tsconfig.app.json`.
- [x] **Type-safe keys** — `t('bad.key')` is a compile error (proven: typecheck
      rejected a widened `string`). Module augmentation crosses the package boundary
      via source consumption. No `any`.
- [x] **Full migration** — all ~250 strings across shell/home/spotlight/theme, jobs
      (pages, forms, enum→label maps, `actions`, `FeatureSection`), cv, and the 4
      feature configs + result panels now go through `t()`.
- [x] **Module-level registries** (NAV, FILTERS, JOB_ACTIONS, STEPS, feature
      `copy`/`pendingCaption`, enum maps) hold `TranslationKey`s, resolved by the
      consuming component. Enum→label uses template-literal keys, e.g.
      `t(\`jobs.status.${status}\`)`.
- [x] **Non-React caller** — `JobCreateForm.handleDuplicate` uses `i18n.t(...)` directly.

## Verification (all green)
- `pnpm typecheck` (recursive: i18n + ui + web) — passes.
- `pnpm lint` (Biome) — clean (`lint:fix` organized the new imports).
- `pnpm build` (`tsc -b && vite build`) — bundles; JSON catalog resolves at build.
- Greps: no hardcoded toasts / placeholders / aria-labels / JSX copy remain. Only
  literal left is `BrandMark`'s "Applark" wordmark (brand logo — intentionally not
  translated; `common.appName` covers the Hero heading).

## Adding a language later (the whole point)
1. `packages/i18n/locales/<lng>/translation.json` (copy `en`, translate values).
2. One line in `config.ts` `resources` + add `<lng>` to `SUPPORTED_LANGUAGES`.
3. (Optional) a switcher calling `i18n.changeLanguage(code)` — none added now since
   English-only.

## Notes / deferred
- No visible language switcher (English-only by request); detector + `supportedLngs`
  make adding one trivial.
- No date/number localization yet (none in the app today) — use `Intl` with
  `i18n.language` when needed.
- `vite build` chunk-size warning is pre-existing (single bundle), unrelated to i18n.

## Review
Clean, typed, fully migrated. `@applark/i18n` owns init + catalog + the typed hook so
the app depends only on `@applark/i18n`. Not committed — awaiting go-ahead.
