import { Check, Coins } from 'lucide-react';

import { useFormat } from '@applark/format';
import { useTranslation } from '@applark/i18n';
import { Badge, Button, Card, cn } from '@applark/ui';

import { type BillingFeature, type BillingTier, useBilling } from '@/domains/billing/hooks/useBilling';

type PaidTier = 'pro' | 'premium';

/**
 * One pricing card in the plans grid. The Free (`none`) tier lists the
 * always-free intake; paid tiers show their monthly price + the AI features
 * they unlock, each with its per-run credit cost. The CTA reflects whether
 * this is the current plan, a fresh subscribe, or a switch.
 */
export function PlanCard({
  tier,
  priceUsd,
  featureIds,
  currentTier,
  pendingTier,
  highlighted,
  onSubscribe,
}: {
  tier: BillingTier;
  priceUsd: number;
  featureIds: readonly BillingFeature[];
  currentTier: BillingTier;
  pendingTier: BillingTier | undefined;
  highlighted?: boolean;
  onSubscribe: (tier: PaidTier) => void;
}) {
  const { t } = useTranslation();
  const fmt = useFormat();

  const isCurrent = tier === currentTier;
  const isFree = tier === 'none';

  return (
    <Card className={cn('relative flex flex-col gap-4 p-6', highlighted && 'border-primary ring-1 ring-primary')}>
      {highlighted ? <Badge className="absolute -top-2.5 left-6">{t('billing.plans.mostPopular')}</Badge> : null}

      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <h3 className="text-title-small-bold">{t(`billing.tierName.${tier}`)}</h3>
          {isCurrent ? <Badge variant="secondary">{t('billing.plans.currentPlan')}</Badge> : null}
        </div>
        <p className="text-title-default-bold">
          {isFree ? t('billing.plans.free') : t('billing.plans.priceMonthly', { price: fmt.currency(priceUsd) })}
        </p>
        <p className="text-body-small text-muted-foreground">{t(`billing.plans.tagline.${tier}`)}</p>
      </div>

      <ul className="flex-1 space-y-2">
        {isFree ? (
          <FreeLine text={t('billing.plans.freeBrowse')} />
        ) : tier === 'premium' ? (
          <>
            <li className="text-body-small text-muted-foreground">{t('billing.plans.everythingInPro')}</li>
            {featureIds.map((id) => (
              <FeatureLine key={id} id={id} />
            ))}
          </>
        ) : (
          <>
            {/* Included with any paid plan — covered by the subscription, no credit cost. */}
            <FreeLine text={t('billing.plans.includes.cvParsing')} />
            <FreeLine text={t('billing.plans.includes.jobImport')} />
            {featureIds.map((id) => (
              <FeatureLine key={id} id={id} />
            ))}
          </>
        )}
      </ul>

      {isFree ? (
        <p className="text-body-small text-muted-foreground">
          {isCurrent ? t('billing.plans.freeCurrentNote') : t('billing.plans.freeNote')}
        </p>
      ) : (
        <Button
          variant={highlighted ? 'gradient' : 'outline'}
          disabled={isCurrent || pendingTier === tier}
          // Safe: the non-free branch only renders for paid tiers ('pro' | 'premium').
          onClick={() => onSubscribe(tier as PaidTier)}
        >
          {isCurrent
            ? t('billing.plans.currentPlan')
            : pendingTier === tier
              ? t('billing.plans.subscribing')
              : currentTier === 'none'
                ? t('billing.plans.subscribe')
                : t('billing.plans.switchTo', { tier: t(`billing.tierName.${tier}`) })}
        </Button>
      )}
    </Card>
  );
}

function FreeLine({ text }: { text: string }) {
  return (
    <li className="flex items-center gap-2 text-body-default">
      <Check className="size-4 shrink-0 text-primary" />
      {text}
    </li>
  );
}

/** A credit-costed AI feature row: name + its per-run credit cost. */
function FeatureLine({ id }: { id: BillingFeature }) {
  const { t } = useTranslation();
  const billing = useBilling();
  return (
    <li className="flex items-center justify-between gap-2">
      <span className="flex items-center gap-2 text-body-default">
        <Check className="size-4 shrink-0 text-primary" />
        {t(`billing.features.${id}`)}
      </span>
      <span className="flex items-center gap-1 text-body-small text-muted-foreground">
        <Coins className="size-3.5 text-primary" />
        {t('billing.creditsShort', { count: billing.cost(id) })}
      </span>
    </li>
  );
}
