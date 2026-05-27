import { Wand2 } from 'lucide-react';

import { Button } from '@postpilot/ui';

import { getGetLatestCvTailorQueryKey, useRunCvTailor } from '@/domains/api/generated/cv-tailor/cv-tailor';
import { PendingFeatureCard } from '@/domains/jobs/components/PendingFeatureCard';
import { useFeatureMutationOptions } from '@/domains/jobs/hooks/useRunFeatureMutation';

export function RunCVTailorButton({
  jobId,
  variant = 'primary',
  label,
}: {
  jobId: string;
  variant?: 'primary' | 'outline';
  label?: string;
}) {
  const mutation = useRunCvTailor(
    useFeatureMutationOptions({
      invalidateKey: getGetLatestCvTailorQueryKey(jobId),
      successMessage: 'Tailor suggestions ready',
      errorFallback: 'Tailor failed',
    })
  );

  if (mutation.isPending) {
    return <PendingFeatureCard caption="Reading your CV and identifying tweaks…" />;
  }

  return (
    <Button variant={variant} onClick={() => mutation.mutate({ jobId })}>
      <Wand2 className="size-4" />
      {label ?? 'Tailor my CV'}
    </Button>
  );
}
