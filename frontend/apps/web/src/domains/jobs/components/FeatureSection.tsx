import type { ReactNode } from 'react';
import { useState } from 'react';
import type { QueryKey } from '@tanstack/react-query';
import { Coins, type LucideIcon } from 'lucide-react';

import { type TranslationKey, useTranslation } from '@applark/i18n';
import { Button, Card, Skeleton } from '@applark/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { useGetLatestMatch } from '@/domains/api/generated/matching/matching';
import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import { useCreditsModalStore } from '@/domains/billing/credits-modal-store';
import type { BillingFeature } from '@/domains/billing/hooks/useBilling';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';
import { PendingFeatureCard } from '@/domains/jobs/components/PendingFeatureCard';
import { useFeatureMutationOptions } from '@/domains/jobs/hooks/useFeatureMutationOptions';
import { DisabledButtonWithTooltip } from '@/domains/shell/components/DisabledButtonWithTooltip';

type FeatureMutationOptions = ReturnType<typeof useFeatureMutationOptions>;

/** Minimal structural slice of an orval mutation result that the shell needs. */
type RunMutation = {
  readonly isPending: boolean;
  readonly isError: boolean;
  readonly mutate: (variables: { jobId: string }) => void;
};

/**
 * Everything the generic `FeatureSection` needs to render one AI feature.
 * Each domain owns its own concretely-typed config; the only genuinely
 * per-domain bit is `renderResult`, into which the bespoke result panel is
 * injected.
 *
 * @typeParam TData   the latest-query payload (e.g. `CVTailorRunRead | null`)
 * @typeParam TResult the non-empty result, narrowed by `hasResult`
 */
export type FeatureSectionConfig<TData, TResult extends TData = TData> = {
  /** Icon shown on the run / re-run buttons. */
  icon: LucideIcon;
  /** Billing feature this section maps to — drives credit cost + gating. */
  creditFeature: BillingFeature;
  /** When true, the CTA is gated behind an existing match run. */
  requiresMatch: boolean;
  /** orval query hook for the latest persisted run. */
  useLatest: (jobId: string) => { readonly data: TData | undefined; readonly isLoading: boolean };
  /** orval mutation hook that runs the feature. */
  useMutation: (options: FeatureMutationOptions) => RunMutation;
  /** Query key to invalidate after a successful run. */
  invalidateKey: (jobId: string) => QueryKey;
  /** Narrows the latest-query data down to a renderable result. */
  hasResult: (data: TData | undefined) => data is TResult;
  /** Caption key(s) for the pending skeleton — an array rotates every few seconds. */
  pendingCaption: TranslationKey | readonly TranslationKey[];
  pendingClassName?: string;
  /** Translation keys for the feature's copy, resolved by this shell via `t()`. */
  copy: {
    /** Intro shown above the run CTA when the feature is ready. */
    ready: TranslationKey;
    /** Shown when `requiresMatch` is true and no match exists yet. */
    needsMatch?: TranslationKey;
    runLabel: TranslationKey;
    rerunLabel: TranslationKey;
    success: TranslationKey;
    errorFallback: TranslationKey;
  };
  renderResult: (args: { result: TResult; chunks: CVChunkRead[]; jobId: string }) => ReactNode;
};

/**
 * Generic shell for the "run an AI feature on a job → pending → result" flow.
 * Handles loading, the match gate, the empty-state CTA, optimistic pending,
 * and the result + re-run wrapper. The result body itself comes from
 * `config.renderResult`.
 */
export function FeatureSection<TData, TResult extends TData = TData>({
  config,
  jobId,
}: {
  config: FeatureSectionConfig<TData, TResult>;
  jobId: string;
}) {
  const { t } = useTranslation();
  const openCreditsModal = useCreditsModalStore((s) => s.open);
  const [hasTriggered, setHasTriggered] = useState(false);

  const subscription = useSubscription();
  const gate = subscription.featureGate(config.creditFeature);
  const cost = subscription.cost(config.creditFeature);

  const matchQuery = useGetLatestMatch(jobId);
  const latestQuery = config.useLatest(jobId);
  const cvsQuery = useGetCvDocuments();
  const chunks = cvsQuery.data?.[0]?.chunks ?? [];

  const mutation = config.useMutation(
    useFeatureMutationOptions({
      invalidateKey: config.invalidateKey(jobId),
      successMessage: t(config.copy.success),
      errorFallback: t(config.copy.errorFallback),
      onMutate: () => setHasTriggered(true),
    })
  );

  const data = latestQuery.data;
  const resultPresent = config.hasResult(data);
  // Stay pending after the mutation resolves until the latest-query refetch
  // populates a result — but bail out of the optimistic wait on error.
  const pending = mutation.isPending || (hasTriggered && !mutation.isError && !resultPresent);

  const Icon = config.icon;

  // The run / re-run CTA, gated by the per-feature subscription gate. `locked`
  // (tier doesn't unlock) and `insufficient` (can't afford) both disable the
  // button with an explanatory tooltip; `ready` fires the mutation.
  const runButton = (label: string, variant: 'default' | 'outline') => {
    switch (gate.status) {
      case 'locked':
        return <DisabledButtonWithTooltip label={label} hint={t('billing.lockedHint')} />;
      case 'insufficient':
        return <DisabledButtonWithTooltip label={label} hint={t('billing.insufficientHint', { count: gate.cost })} />;
      case 'ready':
        return (
          <Button variant={variant === 'outline' ? 'outline' : undefined} onClick={() => mutation.mutate({ jobId })}>
            <Icon className="size-4" />
            {label}
          </Button>
        );
      default: {
        const _exhaustive: never = gate;
        throw new Error(`Unhandled feature gate: ${JSON.stringify(_exhaustive)}`);
      }
    }
  };

  // Inline "Buy credits" link, shown only when the tier is unlocked but the
  // balance can't cover a run. Opens the buy-credits modal so the user can
  // top up without leaving the job.
  const buyCreditsLink =
    gate.status === 'insufficient' ? (
      <button
        type="button"
        onClick={openCreditsModal}
        className="flex items-center gap-1 text-body-small text-primary underline-offset-2 hover:underline"
      >
        <Coins className="size-3.5" />
        {t('billing.buyCredits')}
      </button>
    ) : null;

  if (latestQuery.isLoading || (config.requiresMatch && matchQuery.isLoading)) {
    return <Skeleton className="h-24 w-full" />;
  }

  if (pending) {
    // `typeof === 'string'` (not Array.isArray, which doesn't narrow readonly arrays)
    // splits the single-key vs key-array cases cleanly.
    const caption =
      typeof config.pendingCaption === 'string' ? t(config.pendingCaption) : config.pendingCaption.map((key) => t(key));
    return <PendingFeatureCard caption={caption} className={config.pendingClassName} />;
  }

  if (config.hasResult(data)) {
    return (
      <div className="space-y-4">
        {config.renderResult({ result: data, chunks, jobId })}
        <div className="flex items-center justify-end gap-3">
          {buyCreditsLink}
          {runButton(t(config.copy.rerunLabel), 'outline')}
        </div>
      </div>
    );
  }

  if (config.requiresMatch && !matchQuery.data) {
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <div>
          <p className="text-body-default">{config.copy.needsMatch ? t(config.copy.needsMatch) : null}</p>
        </div>
        <DisabledButtonWithTooltip label={t(config.copy.runLabel)} hint={t('features.needsMatchHint')} />
      </Card>
    );
  }

  return (
    <Card className="flex items-center justify-between gap-4 p-6">
      <div className="space-y-1">
        <p className="text-body-default">{t(config.copy.ready)}</p>
        {cost > 0 ? (
          <p className="flex items-center gap-1 text-body-small text-muted-foreground">
            <Coins className="size-3.5 text-primary" />
            {t('billing.cost', { count: cost })}
          </p>
        ) : null}
        {buyCreditsLink}
      </div>
      {runButton(t(config.copy.runLabel), 'default')}
    </Card>
  );
}
