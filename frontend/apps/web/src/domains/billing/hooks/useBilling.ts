import { useGetBillingMe } from '@/domains/api/generated/billing/billing';
import type { BillingStatus } from '@/domains/api/generated/model/billingStatus';

/** The four gateable AI features, mirroring the backend `Feature` literal. */
export type BillingFeature = 'matching' | 'cover_letters' | 'cv_tailor' | 'interview_prep';

const BILLING_FEATURES: readonly BillingFeature[] = ['matching', 'cover_letters', 'cv_tailor', 'interview_prep'];

/** Narrow an API feature-id string (e.g. from `PlanRead.features`) to `BillingFeature`. */
export function isBillingFeature(value: string): value is BillingFeature {
  return (BILLING_FEATURES as readonly string[]).includes(value);
}

/** Subscription tier, mirroring the backend `Tier` literal. */
export type BillingTier = 'none' | 'pro' | 'premium';

/** Locked/zero state used while the query is in flight (safe default: deny). */
const EMPTY_STATUS: BillingStatus = { tier: 'none', credits: 0, access: {}, costs: {} };

/** Narrow the API's `string` tier to the closed `BillingTier` union. */
function asTier(value: string): BillingTier {
  return value === 'pro' || value === 'premium' ? value : 'none';
}

export type UseBilling = {
  readonly isLoading: boolean;
  readonly tier: BillingTier;
  readonly credits: number;
  /** Whether the current tier unlocks `feature` at all (independent of balance). */
  readonly access: (feature: BillingFeature) => boolean;
  /** Flat credit cost of one run of `feature`. */
  readonly cost: (feature: BillingFeature) => number;
};

/**
 * Reads the signed-in user's billing status (`GET /billing/me`). Until the
 * query resolves it reports the locked/zero state, so callers fail closed.
 */
export function useBilling(): UseBilling {
  const { data, isLoading } = useGetBillingMe();
  const status = data ?? EMPTY_STATUS;
  return {
    isLoading,
    tier: asTier(status.tier),
    credits: status.credits,
    access: (feature) => status.access[feature] ?? false,
    cost: (feature) => status.costs[feature] ?? 0,
  };
}
