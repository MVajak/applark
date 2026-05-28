import type { LucideIcon } from 'lucide-react';
import { ClipboardList, FileText, Sparkles, Wand2 } from 'lucide-react';

import type { TranslationKey } from '@applark/i18n';

import type { Capabilities } from '@/domains/auth/capabilities';

export type JobActionId = 'match' | 'cover-letter' | 'tailor' | 'interview-prep';

export type JobAction = {
  id: JobActionId;
  icon: LucideIcon;
  labelKey: TranslationKey;
  descriptionKey: TranslationKey;
  capability: keyof Capabilities;
};

export const JOB_ACTIONS: readonly JobAction[] = [
  {
    id: 'match',
    icon: Sparkles,
    labelKey: 'actions.match.label',
    descriptionKey: 'actions.match.description',
    capability: 'canRunMatch',
  },
  {
    id: 'cover-letter',
    icon: FileText,
    labelKey: 'actions.coverLetter.label',
    descriptionKey: 'actions.coverLetter.description',
    capability: 'canGenerateCoverLetter',
  },
  {
    id: 'tailor',
    icon: Wand2,
    labelKey: 'actions.tailor.label',
    descriptionKey: 'actions.tailor.description',
    capability: 'canTailorCV',
  },
  {
    id: 'interview-prep',
    icon: ClipboardList,
    labelKey: 'actions.interviewPrep.label',
    descriptionKey: 'actions.interviewPrep.description',
    capability: 'canGenerateInterviewPrep',
  },
] as const;

export function isJobActionId(value: string | null): value is JobActionId {
  return value === 'match' || value === 'cover-letter' || value === 'tailor' || value === 'interview-prep';
}
