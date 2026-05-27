import { Card, Skeleton } from '@postpilot/ui';

import { useGetCvDocuments } from '@/domains/api/generated/cv/cv';
import { useGetLatestInterviewPrep } from '@/domains/api/generated/interview-prep/interview-prep';
import { useGetLatestMatch } from '@/domains/api/generated/matching/matching';
import { GenerateInterviewPrepButton } from '@/domains/interview_prep/components/GenerateInterviewPrepButton';
import { InterviewPrepPanel } from '@/domains/interview_prep/components/InterviewPrepPanel';
import { DisabledButtonWithTooltip } from '@/domains/shell/components/DisabledButtonWithTooltip';

export function InterviewPrepSection({ jobId }: { jobId: string }) {
  const matchQuery = useGetLatestMatch(jobId);
  const prepQuery = useGetLatestInterviewPrep(jobId);
  const cvsQuery = useGetCvDocuments();

  const latestCv = cvsQuery.data?.[0];
  const cvChunks = latestCv?.chunks ?? [];

  const hasMatch = !!matchQuery.data;
  const prepRun = prepQuery.data;

  if (prepQuery.isLoading || matchQuery.isLoading) return <Skeleton className="h-24 w-full" />;

  if (!prepRun) {
    if (hasMatch) {
      return (
        <Card className="flex items-center justify-between gap-4 p-6">
          <div>
            <p className="text-body-default">
              A study sheet of likely questions, suggested angles, and questions to ask back — grounded in this job and
              your CV.
            </p>
            <p className="text-body-small text-muted-foreground">Uses Claude Sonnet — ~$0.05 per run.</p>
          </div>
          <GenerateInterviewPrepButton jobId={jobId} />
        </Card>
      );
    }
    return (
      <Card className="flex items-center justify-between gap-4 p-6">
        <div>
          <p className="text-body-default">
            Interview prep needs a match run first so questions can target what this team actually cares about.
          </p>
        </div>
        <DisabledButtonWithTooltip label="Generate interview prep" hint="Run match against your CV first" />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <InterviewPrepPanel run={prepRun} chunks={cvChunks} />
      <div className="flex justify-end">
        <GenerateInterviewPrepButton jobId={jobId} variant="outline" label="Re-generate" />
      </div>
    </div>
  );
}
