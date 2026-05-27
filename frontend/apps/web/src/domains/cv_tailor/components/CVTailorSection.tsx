import { Card, Skeleton } from '@postpilot/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { useGetLatestCvTailor } from '@/domains/api/generated/cv-tailor/cv-tailor';
import { useGetLatestMatch } from '@/domains/api/generated/matching/matching';
import { CVTailorResultPanel } from '@/domains/cv_tailor/components/CVTailorResultPanel';
import { RunCVTailorButton } from '@/domains/cv_tailor/components/RunCVTailorButton';
import { DisabledButtonWithTooltip } from '@/domains/shell/components/DisabledButtonWithTooltip';

export function CVTailorSection({ jobId }: { jobId: string }) {
  const matchQuery = useGetLatestMatch(jobId);
  const tailorQuery = useGetLatestCvTailor(jobId);
  const cvsQuery = useGetCvDocuments();

  const latestCv = cvsQuery.data?.[0];
  const cvChunks = latestCv?.chunks ?? [];

  const hasMatch = !!matchQuery.data;
  const tailorRun = tailorQuery.data;

  if (tailorQuery.isLoading || matchQuery.isLoading) return <Skeleton className="h-24 w-full" />;

  if (!tailorRun) {
    if (hasMatch) {
      return (
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-body-default">
              Specific, chunk-by-chunk suggestions for adapting your CV to this posting.
            </p>
            <p className="text-body-small text-muted-foreground">Uses Claude Sonnet — ~$0.04 per run.</p>
          </div>
          <RunCVTailorButton jobId={jobId} />
        </Card>
      );
    }
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <div>
          <p className="text-body-default">Tailor suggestions need a match run first so they can target real gaps.</p>
        </div>
        <DisabledButtonWithTooltip label="Tailor my CV" hint="Run match against your CV first" />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <CVTailorResultPanel run={tailorRun} chunks={cvChunks} />
      <div className="flex justify-end">
        <RunCVTailorButton jobId={jobId} variant="outline" label="Re-run" />
      </div>
    </div>
  );
}
