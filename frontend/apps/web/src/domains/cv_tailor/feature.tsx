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
  pendingCaption: 'Reading your CV and identifying tweaks…',
  copy: {
    ready: 'Specific, chunk-by-chunk suggestions for adapting your CV to this posting.',
    cost: 'Uses Claude Sonnet — ~$0.04 per run.',
    needsMatch: 'Tailor suggestions need a match run first so they can target real gaps.',
    runLabel: 'Tailor my CV',
    rerunLabel: 'Re-run',
    success: 'Tailor suggestions ready',
    errorFallback: 'Tailor failed',
  },
  renderResult: ({ result, chunks }) => <CVTailorResultPanel run={result} chunks={chunks} />,
};
