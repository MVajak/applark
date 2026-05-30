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

const PENDING_CAPTIONS = ['interviewPrep.pending.0', 'interviewPrep.pending.1', 'interviewPrep.pending.2'] as const;

export const interviewPrepFeature: FeatureSectionConfig<GetLatestInterviewPrep200, InterviewPrepRunRead> = {
  icon: ClipboardList,
  creditFeature: 'interview_prep',
  requiresMatch: true,
  useLatest: useGetLatestInterviewPrep,
  useMutation: useGenerateInterviewPrep,
  invalidateKey: getGetLatestInterviewPrepQueryKey,
  hasResult: (data): data is InterviewPrepRunRead => data != null,
  pendingCaption: PENDING_CAPTIONS,
  copy: {
    ready: 'interviewPrep.copy.ready',
    needsMatch: 'interviewPrep.copy.needsMatch',
    runLabel: 'interviewPrep.copy.runLabel',
    rerunLabel: 'interviewPrep.copy.rerunLabel',
    success: 'interviewPrep.copy.success',
    errorFallback: 'interviewPrep.copy.errorFallback',
  },
  renderResult: ({ result, chunks }) => <InterviewPrepPanel run={result} chunks={chunks} />,
};
