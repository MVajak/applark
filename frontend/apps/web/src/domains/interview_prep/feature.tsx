import { ClipboardList } from 'lucide-react';

import {
  getGetLatestInterviewPrepQueryKey,
  useGenerateInterviewPrep,
  useGetLatestInterviewPrep,
} from '@/domains/api/generated/interview-prep/interview-prep';
import type { GetLatestInterviewPrep200 } from '@/domains/api/generated/model/getLatestInterviewPrep200';
import type { InterviewPrepRunRead } from '@/domains/api/generated/model/interviewPrepRunRead';
import { InterviewPrepPanel } from '@/domains/interview_prep/components/InterviewPrepPanel';
import type { FeatureSectionConfig } from '@/domains/jobs/components/FeatureSection';

const PENDING_CAPTIONS = [
  'Reading the job posting…',
  'Thinking like an interviewer…',
  'Drafting questions and angles…',
];

export const interviewPrepFeature: FeatureSectionConfig<GetLatestInterviewPrep200, InterviewPrepRunRead> = {
  icon: ClipboardList,
  requiresMatch: true,
  useLatest: useGetLatestInterviewPrep,
  useMutation: useGenerateInterviewPrep,
  invalidateKey: getGetLatestInterviewPrepQueryKey,
  hasResult: (data): data is InterviewPrepRunRead => data != null,
  pendingCaption: PENDING_CAPTIONS,
  copy: {
    ready:
      'A study sheet of likely questions, suggested angles, and questions to ask back — grounded in this job and your CV.',
    cost: 'Uses Claude Sonnet — ~$0.05 per run.',
    needsMatch: 'Interview prep needs a match run first so questions can target what this team actually cares about.',
    runLabel: 'Generate interview prep',
    rerunLabel: 'Re-generate',
    success: 'Interview prep ready',
    errorFallback: 'Interview prep failed',
  },
  renderResult: ({ result, chunks }) => <InterviewPrepPanel run={result} chunks={chunks} />,
};
