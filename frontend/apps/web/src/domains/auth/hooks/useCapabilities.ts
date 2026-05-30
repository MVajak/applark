import { useSubscription } from '@/domains/billing/hooks/useSubscription';

/**
 * Per-feature capability flags consumed by `ActionGrid` / route guards.
 * Derived from the signed-in user's tier via `useSubscription`: a feature is
 * enabled only when the user's tier unlocks it. Affordability (the credit
 * balance for a given run) is handled separately in `FeatureSection`.
 *
 * Add a new flag here when introducing a new gateable feature, then
 * reference it in the relevant action card / route guard.
 */

export type Capabilities = {
  canRunMatch: boolean;
  canGenerateCoverLetter: boolean;
  canTailorCV: boolean;
  canGenerateInterviewPrep: boolean;
};

export const useCapabilities = (): Capabilities => {
  const { hasFeature } = useSubscription();
  return {
    canRunMatch: hasFeature('matching'),
    canGenerateCoverLetter: hasFeature('cover_letters'),
    canTailorCV: hasFeature('cv_tailor'),
    canGenerateInterviewPrep: hasFeature('interview_prep'),
  };
};
