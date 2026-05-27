import type { ReactNode } from 'react';

import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@applark/ui';

import { coverLetterFeature } from '@/domains/cover_letters/feature';
import { cvTailorFeature } from '@/domains/cv_tailor/feature';
import { interviewPrepFeature } from '@/domains/interview_prep/feature';
import { JOB_ACTIONS, type JobActionId } from '@/domains/jobs/actions';
import { FeatureSection } from '@/domains/jobs/components/FeatureSection';
import { matchFeature } from '@/domains/matching/feature';

/** Maps each job action to its rendered feature section. */
const FEATURE_SECTIONS: Record<JobActionId, (jobId: string) => ReactNode> = {
  match: (jobId) => <FeatureSection config={matchFeature} jobId={jobId} />,
  'cover-letter': (jobId) => <FeatureSection config={coverLetterFeature} jobId={jobId} />,
  tailor: (jobId) => <FeatureSection config={cvTailorFeature} jobId={jobId} />,
  'interview-prep': (jobId) => <FeatureSection config={interviewPrepFeature} jobId={jobId} />,
};

export function FeatureDrawer({
  action,
  jobId,
  open,
  onOpenChange,
}: {
  action: JobActionId | null;
  jobId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const meta = JOB_ACTIONS.find((a) => a.id === action);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        {meta && (
          <SheetHeader>
            <SheetTitle>{meta.label}</SheetTitle>
            <SheetDescription>{meta.description}</SheetDescription>
          </SheetHeader>
        )}
        <div className="mt-4">{action && FEATURE_SECTIONS[action](jobId)}</div>
      </SheetContent>
    </Sheet>
  );
}
