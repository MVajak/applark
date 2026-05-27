import { ClipboardList } from 'lucide-react';

import { Button } from '@postpilot/ui';

import {
  getGetLatestInterviewPrepQueryKey,
  useGenerateInterviewPrep,
} from '@/domains/api/generated/interview-prep/interview-prep';
import { PendingFeatureCard } from '@/domains/jobs/components/PendingFeatureCard';
import { useFeatureMutationOptions } from '@/domains/jobs/hooks/useRunFeatureMutation';

const CAPTIONS = ['Reading the job posting…', 'Thinking like an interviewer…', 'Drafting questions and angles…'];

export function GenerateInterviewPrepButton({
  jobId,
  variant = 'primary',
  label,
}: {
  jobId: string;
  variant?: 'primary' | 'outline';
  label?: string;
}) {
  const mutation = useGenerateInterviewPrep(
    useFeatureMutationOptions({
      invalidateKey: getGetLatestInterviewPrepQueryKey(jobId),
      successMessage: 'Interview prep ready',
      errorFallback: 'Interview prep failed',
    })
  );

  if (mutation.isPending) {
    return <PendingFeatureCard caption={CAPTIONS} />;
  }

  return (
    <Button variant={variant} onClick={() => mutation.mutate({ jobId })}>
      <ClipboardList className="size-4" />
      {label ?? 'Generate interview prep'}
    </Button>
  );
}
