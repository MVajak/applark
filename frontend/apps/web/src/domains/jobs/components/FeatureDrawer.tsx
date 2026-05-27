import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@postpilot/ui';

import { CoverLetterSection } from '@/domains/cover_letters/components/CoverLetterSection';
import { CVTailorSection } from '@/domains/cv_tailor/components/CVTailorSection';
import { InterviewPrepSection } from '@/domains/interview_prep/components/InterviewPrepSection';
import { JOB_ACTIONS, type JobActionId } from '@/domains/jobs/actions';
import { MatchSection } from '@/domains/matching/components/MatchSection';

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
        <div className="mt-4">
          {action === 'match' && <MatchSection jobId={jobId} />}
          {action === 'cover-letter' && <CoverLetterSection jobId={jobId} />}
          {action === 'tailor' && <CVTailorSection jobId={jobId} />}
          {action === 'interview-prep' && <InterviewPrepSection jobId={jobId} />}
        </div>
      </SheetContent>
    </Sheet>
  );
}
