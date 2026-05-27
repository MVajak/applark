import type { ReactNode } from 'react';
import { useState } from 'react';
import type { QueryKey } from '@tanstack/react-query';
import type { LucideIcon } from 'lucide-react';

import { Button, Card, Skeleton } from '@postpilot/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { useGetLatestMatch } from '@/domains/api/generated/matching/matching';
import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import { PendingFeatureCard } from '@/domains/jobs/components/PendingFeatureCard';
import { useFeatureMutationOptions } from '@/domains/jobs/hooks/useRunFeatureMutation';
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
  /** Caption(s) for the pending skeleton — an array rotates every few seconds. */
  pendingCaption: string | readonly string[];
  pendingClassName?: string;
  copy: {
    /** Intro shown above the run CTA when the feature is ready. */
    ready: string;
    /** Optional cost/footnote line under `ready`. */
    cost?: string;
    /** Shown when `requiresMatch` is true and no match exists yet. */
    needsMatch?: string;
    runLabel: string;
    rerunLabel: string;
    success: string;
    errorFallback: string;
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
  const [hasTriggered, setHasTriggered] = useState(false);

  const matchQuery = useGetLatestMatch(jobId);
  const latestQuery = config.useLatest(jobId);
  const cvsQuery = useGetCvDocuments();
  const chunks = cvsQuery.data?.[0]?.chunks ?? [];

  const mutation = config.useMutation(
    useFeatureMutationOptions({
      invalidateKey: config.invalidateKey(jobId),
      successMessage: config.copy.success,
      errorFallback: config.copy.errorFallback,
      onMutate: () => setHasTriggered(true),
    })
  );

  const data = latestQuery.data;
  const resultPresent = config.hasResult(data);
  // Stay pending after the mutation resolves until the latest-query refetch
  // populates a result — but bail out of the optimistic wait on error.
  const pending = mutation.isPending || (hasTriggered && !mutation.isError && !resultPresent);

  const Icon = config.icon;

  if (latestQuery.isLoading || (config.requiresMatch && matchQuery.isLoading)) {
    return <Skeleton className="h-24 w-full" />;
  }

  if (pending) {
    return <PendingFeatureCard caption={config.pendingCaption} className={config.pendingClassName} />;
  }

  if (config.hasResult(data)) {
    return (
      <div className="space-y-4">
        {config.renderResult({ result: data, chunks, jobId })}
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => mutation.mutate({ jobId })}>
            <Icon className="size-4" />
            {config.copy.rerunLabel}
          </Button>
        </div>
      </div>
    );
  }

  if (config.requiresMatch && !matchQuery.data) {
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <div>
          <p className="text-body-default">{config.copy.needsMatch}</p>
        </div>
        <DisabledButtonWithTooltip label={config.copy.runLabel} hint="Run match against your CV first" />
      </Card>
    );
  }

  return (
    <Card className="flex items-center justify-between gap-4 p-6">
      <div>
        <p className="text-body-default">{config.copy.ready}</p>
        {config.copy.cost ? <p className="text-body-small text-muted-foreground">{config.copy.cost}</p> : null}
      </div>
      <Button onClick={() => mutation.mutate({ jobId })}>
        <Icon className="size-4" />
        {config.copy.runLabel}
      </Button>
    </Card>
  );
}
