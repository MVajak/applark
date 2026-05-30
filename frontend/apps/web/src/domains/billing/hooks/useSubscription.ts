import { type BillingFeature, type BillingTier, useBilling } from '@/domains/billing/hooks/useBilling';

/**
 * Per-feature run gate. `locked` = the tier doesn't unlock it (→ upgrade);
 * `insufficient` = unlocked but the balance can't cover a run (→ buy credits);
 * `ready` = runnable.
 */
export type FeatureGate =
  | { readonly status: 'locked' }
  | { readonly status: 'insufficient'; readonly cost: number }
  | { readonly status: 'ready'; readonly cost: number };

export type UseSubscription = {
  readonly isLoading: boolean;
  readonly tier: BillingTier;
  readonly credits: number;
  /** On any paid tier (PRO/PREMIUM) — unlocks AI intake. */
  readonly isSubscribed: boolean;
  readonly isPremium: boolean;
  /** Whether the current tier unlocks `feature` (independent of balance). */
  readonly hasFeature: (feature: BillingFeature) => boolean;
  /** Flat credit cost of one run of `feature`. */
  readonly cost: (feature: BillingFeature) => number;
  /** Whether the balance can cover one run of `feature`. */
  readonly canAfford: (feature: BillingFeature) => boolean;
  /** Combined tier + balance gate for `feature`. */
  readonly featureGate: (feature: BillingFeature) => FeatureGate;
};

/**
 * Single source of truth for subscription / entitlement checks, built on
 * {@link useBilling} (the raw billing data). Use this hook anywhere a gating
 * decision is made — the intake paywall, the per-feature run gate, upgrade
 * prompts — so the rule lives in one place rather than ad-hoc `tier === 'none'`
 * / `credits >= cost` comparisons. `useBilling` stays for pure data display.
 */
export function useSubscription(): UseSubscription {
  const billing = useBilling();

  const hasFeature = (feature: BillingFeature): boolean => billing.access(feature);
  const cost = (feature: BillingFeature): number => billing.cost(feature);
  const canAfford = (feature: BillingFeature): boolean => billing.credits >= billing.cost(feature);
  const featureGate = (feature: BillingFeature): FeatureGate => {
    if (!hasFeature(feature)) return { status: 'locked' };
    const c = cost(feature);
    return billing.credits >= c ? { status: 'ready', cost: c } : { status: 'insufficient', cost: c };
  };

  return {
    isLoading: billing.isLoading,
    tier: billing.tier,
    credits: billing.credits,
    isSubscribed: billing.tier !== 'none',
    isPremium: billing.tier === 'premium',
    hasFeature,
    cost,
    canAfford,
    featureGate,
  };
}
