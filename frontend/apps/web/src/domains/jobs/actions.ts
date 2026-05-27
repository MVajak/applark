import type { LucideIcon } from 'lucide-react';
import { ClipboardList, FileText, Sparkles, Wand2 } from 'lucide-react';

import type { Capabilities } from '@/domains/auth/capabilities';

export type JobActionId = 'match' | 'cover-letter' | 'tailor' | 'interview-prep';

export type JobAction = {
  id: JobActionId;
  icon: LucideIcon;
  label: string;
  description: string;
  capability: keyof Capabilities;
};

export const JOB_ACTIONS: readonly JobAction[] = [
  {
    id: 'match',
    icon: Sparkles,
    label: 'Match',
    description: 'See how your CV maps onto this posting.',
    capability: 'canRunMatch',
  },
  {
    id: 'cover-letter',
    icon: FileText,
    label: 'Cover letter',
    description: 'Draft a cover letter grounded in your strengths.',
    capability: 'canGenerateCoverLetter',
  },
  {
    id: 'tailor',
    icon: Wand2,
    label: 'Tailor CV',
    description: 'Get chunk-by-chunk suggestions to adapt your CV.',
    capability: 'canTailorCV',
  },
  {
    id: 'interview-prep',
    icon: ClipboardList,
    label: 'Interview prep',
    description: 'Likely questions, suggested angles, questions to ask.',
    capability: 'canGenerateInterviewPrep',
  },
] as const;

export function isJobActionId(value: string | null): value is JobActionId {
  return value === 'match' || value === 'cover-letter' || value === 'tailor' || value === 'interview-prep';
}
