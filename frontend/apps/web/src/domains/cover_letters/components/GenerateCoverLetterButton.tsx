import { Sparkles } from 'lucide-react';

import { Button } from '@postpilot/ui';

import {
  getGetCoverLettersQueryKey,
  useGenerateCoverLetter,
} from '@/domains/api/generated/cover-letters/cover-letters';
import { PendingFeatureCard } from '@/domains/jobs/components/PendingFeatureCard';
import { useFeatureMutationOptions } from '@/domains/jobs/hooks/useRunFeatureMutation';

export function GenerateCoverLetterButton({
  jobId,
  variant = 'primary',
  label,
}: {
  jobId: string;
  variant?: 'primary' | 'outline';
  label?: string;
}) {
  const mutation = useGenerateCoverLetter(
    useFeatureMutationOptions({
      invalidateKey: getGetCoverLettersQueryKey(jobId),
      successMessage: 'Draft ready',
      errorFallback: 'Cover letter generation failed',
    })
  );

  if (mutation.isPending) {
    return <PendingFeatureCard caption="Drafting…" className="max-w-prose" />;
  }

  return (
    <Button variant={variant} onClick={() => mutation.mutate({ jobId })}>
      <Sparkles className="size-4" />
      {label ?? 'Generate cover letter'}
    </Button>
  );
}
