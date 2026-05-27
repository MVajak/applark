import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { RotateCcw, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

import { Button, Card, Separator, Skeleton } from '@postpilot/ui';

import { getErrorDetail } from '@/domains/api/client';
import { getGetLatestMatchQueryKey, useGetLatestMatch, useRunMatch } from '@/domains/api/generated/matching/matching';
import type { MatchExplanation } from '@/domains/api/generated/model/matchExplanation';
import { GapsList } from '@/domains/matching/components/GapsList';
import { MatchScore } from '@/domains/matching/components/MatchScore';
import { MatchSummary } from '@/domains/matching/components/MatchSummary';
import { StrengthsList } from '@/domains/matching/components/StrengthsList';
import { SuggestedEmphasis } from '@/domains/matching/components/SuggestedEmphasis';

export function MatchSection({ jobId }: { jobId: string }) {
  const queryClient = useQueryClient();
  const [hasTriggered, setHasTriggered] = useState(false);

  const { data, isLoading } = useGetLatestMatch(jobId);

  const run = useRunMatch({
    mutation: {
      onMutate: () => {
        setHasTriggered(true);
      },
      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: getGetLatestMatchQueryKey(jobId),
        });
        toast.success('Match complete');
      },
      onError: (err) => {
        toast.error(getErrorDetail(err) ?? 'Match failed');
      },
    },
  });

  if (isLoading) return <Skeleton className="h-32 w-full" />;
  if (run.isPending || (hasTriggered && !data)) {
    return (
      <Card className="space-y-3 p-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
        <p className="text-body-default text-muted-foreground italic">Analysing fit — this takes a few seconds…</p>
      </Card>
    );
  }
  if (data) {
    return <MatchResult data={data} onRerun={() => run.mutate({ jobId })} pending={run.isPending} />;
  }
  return (
    <Card className="flex items-center justify-between gap-4 p-6">
      <div>
        <p className="text-body-default">See how well your CV maps onto this posting.</p>
        <p className="text-body-small text-muted-foreground">Uses Claude Sonnet — ~$0.04 per run.</p>
      </div>
      <Button onClick={() => run.mutate({ jobId })} disabled={run.isPending}>
        <Sparkles className="size-4" />
        Match against my CV
      </Button>
    </Card>
  );
}

function MatchResult({
  data,
  onRerun,
  pending,
}: {
  data: { details: MatchExplanation };
  onRerun: () => void;
  pending: boolean;
}) {
  const exp = data.details;
  return (
    <div className="space-y-4">
      <Card className="p-6">
        <MatchScore score={exp.overall_score} />
      </Card>

      <MatchSummary summary={exp.summary} />

      <Card className="space-y-6 p-6">
        <div>
          <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">Strengths</h3>
          <StrengthsList strengths={exp.strengths} />
        </div>
        <Separator />
        <div>
          <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">Gaps</h3>
          <GapsList gaps={exp.gaps} />
        </div>
        {exp.suggested_emphasis.length > 0 && (
          <>
            <Separator />
            <div>
              <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">
                Suggested emphasis
              </h3>
              <SuggestedEmphasis items={exp.suggested_emphasis} />
            </div>
          </>
        )}
      </Card>

      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={onRerun} disabled={pending}>
          <RotateCcw className="size-3" />
          {pending ? 'Re-running…' : 'Re-run match'}
        </Button>
      </div>
    </div>
  );
}
