import { useQueryClient } from '@tanstack/react-query';
import { Coins } from 'lucide-react';
import { toast } from 'sonner';

import { useTranslation } from '@applark/i18n';
import { Button, Skeleton } from '@applark/ui';

import { getErrorDetail } from '@/domains/api/client';
import { getGetBillingMeQueryKey, useListPlans, useSubscribe } from '@/domains/api/generated/billing/billing';
import { PlanCard } from '@/domains/billing/components/PlanCard';
import { useCreditsModalStore } from '@/domains/billing/credits-modal-store';
import { isBillingFeature } from '@/domains/billing/hooks/useBilling';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';

export function BillingPage() {
  const { t } = useTranslation();
  const subscription = useSubscription();
  const { data: plans, isLoading } = useListPlans();
  const queryClient = useQueryClient();
  const openCreditsModal = useCreditsModalStore((s) => s.open);

  const subscribe = useSubscribe({
    mutation: {
      onSuccess: (_data, variables) => {
        void queryClient.invalidateQueries({ queryKey: getGetBillingMeQueryKey() });
        toast.success(t('billing.plans.toastSubscribed', { tier: t(`billing.tierName.${variables.data.tier}`) }));
      },
      onError: (err) => toast.error(getErrorDetail(err) ?? t('billing.errorSubscribe')),
    },
  });

  const pendingTier = subscribe.isPending ? subscribe.variables?.data.tier : undefined;
  const handleSubscribe = (tier: 'pro' | 'premium') => subscribe.mutate({ data: { tier } });

  // Premium lists only its exclusive features; the rest read as "Everything in Pro".
  const proFeatures = new Set((plans ?? []).find((p) => p.tier === 'pro')?.features ?? []);

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4 border-border/60 border-b pb-6">
        <div className="space-y-1">
          <h1 className="text-title-large-bold tracking-tight">{t('billing.title')}</h1>
          <p className="text-body-default text-muted-foreground">{t('billing.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-body-default">
            <Coins className="size-4 text-primary" />
            {t('billing.creditsChip', { count: subscription.credits })}
          </span>
          {subscription.isSubscribed ? (
            <Button variant="outline" size="sm" onClick={openCreditsModal}>
              <Coins className="size-4" />
              {t('billing.buyCredits')}
            </Button>
          ) : null}
        </div>
      </header>

      {isLoading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      ) : (
        <div className="grid items-stretch gap-4 lg:grid-cols-3">
          <PlanCard
            tier="none"
            priceUsd={0}
            featureIds={[]}
            currentTier={subscription.tier}
            pendingTier={pendingTier}
            onSubscribe={handleSubscribe}
          />
          {(plans ?? []).map((plan) => {
            const isPremium = plan.tier === 'premium';
            // Premium card shows only features Pro doesn't already include.
            const ids = (isPremium ? plan.features.filter((f) => !proFeatures.has(f)) : plan.features).filter(
              isBillingFeature
            );
            return (
              <PlanCard
                key={plan.tier}
                // Plans endpoint only returns paid tiers; map the string to BillingTier.
                tier={isPremium ? 'premium' : 'pro'}
                priceUsd={plan.price_usd}
                featureIds={ids}
                currentTier={subscription.tier}
                pendingTier={pendingTier}
                highlighted={isPremium}
                onSubscribe={handleSubscribe}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
