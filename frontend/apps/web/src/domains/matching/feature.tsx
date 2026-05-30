import { Sparkles } from 'lucide-react';

import { useTranslation } from '@applark/i18n';
import { Card, Separator } from '@applark/ui';

import { getGetLatestMatchQueryKey, useGetLatestMatch, useRunMatch } from '@/domains/api/generated/matching/matching';
import type { GetLatestMatch200 } from '@/domains/api/generated/model/getLatestMatch200';
import type { MatchExplanation } from '@/domains/api/generated/model/matchExplanation';
import type { MatchRunRead } from '@/domains/api/generated/model/matchRunRead';
import type { FeatureSectionConfig } from '@/domains/jobs/components/FeatureSection';
import { GapsList } from '@/domains/matching/components/GapsList';
import { MatchScore } from '@/domains/matching/components/MatchScore';
import { MatchSummary } from '@/domains/matching/components/MatchSummary';
import { StrengthsList } from '@/domains/matching/components/StrengthsList';
import { SuggestedEmphasis } from '@/domains/matching/components/SuggestedEmphasis';

function MatchResult({ exp }: { exp: MatchExplanation }) {
  const { t } = useTranslation();
  return (
    <>
      <Card className="p-6">
        <MatchScore score={exp.overall_score} />
      </Card>

      <MatchSummary summary={exp.summary} />

      <Card className="space-y-6 p-6">
        <div>
          <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">
            {t('matching.result.strengths')}
          </h3>
          <StrengthsList strengths={exp.strengths} />
        </div>
        <Separator />
        <div>
          <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">
            {t('matching.result.gaps')}
          </h3>
          <GapsList gaps={exp.gaps} />
        </div>
        {exp.suggested_emphasis.length > 0 && (
          <>
            <Separator />
            <div>
              <h3 className="mb-3 text-body-default-bold text-muted-foreground uppercase tracking-wide">
                {t('matching.result.suggestedEmphasis')}
              </h3>
              <SuggestedEmphasis items={exp.suggested_emphasis} />
            </div>
          </>
        )}
      </Card>
    </>
  );
}

export const matchFeature: FeatureSectionConfig<GetLatestMatch200, MatchRunRead> = {
  icon: Sparkles,
  creditFeature: 'matching',
  // Match is itself the prerequisite for the other features, so it is never gated.
  requiresMatch: false,
  useLatest: useGetLatestMatch,
  useMutation: useRunMatch,
  invalidateKey: getGetLatestMatchQueryKey,
  hasResult: (data): data is MatchRunRead => data != null,
  pendingCaption: 'matching.pendingCaption',
  copy: {
    ready: 'matching.copy.ready',
    runLabel: 'matching.copy.runLabel',
    rerunLabel: 'matching.copy.rerunLabel',
    success: 'matching.copy.success',
    errorFallback: 'matching.copy.errorFallback',
  },
  renderResult: ({ result }) => <MatchResult exp={result.details} />,
};
