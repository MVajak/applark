import { Wand2 } from 'lucide-react';

import {
  getGetLatestCvTailorQueryKey,
  useGetLatestCvTailor,
  useRunCvTailor,
} from '@/domains/api/generated/cv-tailor/cv-tailor';
import type { CVTailorRunRead } from '@/domains/api/generated/model/cVTailorRunRead';
import type { GetLatestCvTailor200 } from '@/domains/api/generated/model/getLatestCvTailor200';
import { CVTailorResultPanel } from '@/domains/cv_tailor/components/CVTailorResultPanel';
import type { FeatureSectionConfig } from '@/domains/jobs/components/FeatureSection';

export const cvTailorFeature: FeatureSectionConfig<GetLatestCvTailor200, CVTailorRunRead> = {
  icon: Wand2,
  requiresMatch: true,
  useLatest: useGetLatestCvTailor,
  useMutation: useRunCvTailor,
  invalidateKey: getGetLatestCvTailorQueryKey,
  hasResult: (data): data is CVTailorRunRead => data != null,
  pendingCaption: 'cvTailor.pendingCaption',
  copy: {
    ready: 'cvTailor.copy.ready',
    cost: 'cvTailor.copy.cost',
    needsMatch: 'cvTailor.copy.needsMatch',
    runLabel: 'cvTailor.copy.runLabel',
    rerunLabel: 'cvTailor.copy.rerunLabel',
    success: 'cvTailor.copy.success',
    errorFallback: 'cvTailor.copy.errorFallback',
  },
  renderResult: ({ result, chunks }) => <CVTailorResultPanel run={result} chunks={chunks} />,
};
