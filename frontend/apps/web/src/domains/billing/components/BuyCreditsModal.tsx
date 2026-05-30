import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { Check, Coins, Sparkles } from 'lucide-react';
import { Controller, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { z } from 'zod';

import { useFormat } from '@applark/format';
import { useTranslation } from '@applark/i18n';
import { Button, cn, Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, Skeleton } from '@applark/ui';

import { getErrorDetail } from '@/domains/api/client';
import { getGetBillingMeQueryKey, useCheckout, useListCreditPacks } from '@/domains/api/generated/billing/billing';
import { useCreditsModalStore } from '@/domains/billing/credits-modal-store';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';

const schema = z.object({ pack_id: z.string().min(1) });
type Values = z.infer<typeof schema>;

/** Pre-selected pack (the mid-tier "best value" one). */
const DEFAULT_PACK = 'plus';

/**
 * Global buy-credits modal, driven by {@link useCreditsModalStore}. Mounted
 * once in the app shell so any surface can open it. Pack selection is an
 * RHF + Zod radio; confirming runs the (stub) checkout and refreshes billing.
 */
export function BuyCreditsModal() {
  const isOpen = useCreditsModalStore((s) => s.isOpen);
  const close = useCreditsModalStore((s) => s.close);

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
    >
      <DialogContent className="sm:max-w-md">
        {/* Remounts per open (Radix unmounts on close), so the form resets cleanly. */}
        <BuyCreditsForm onDone={close} />
      </DialogContent>
    </Dialog>
  );
}

function BuyCreditsForm({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fmt = useFormat();
  const queryClient = useQueryClient();
  const { isSubscribed, credits } = useSubscription();
  const { data: packs, isLoading } = useListCreditPacks();

  const checkout = useCheckout({
    mutation: {
      onSuccess: (_data, variables) => {
        void queryClient.invalidateQueries({ queryKey: getGetBillingMeQueryKey() });
        const bought = packs?.find((p) => p.id === variables.data.pack_id);
        toast.success(t('billing.packs.toastPurchased', { count: bought?.credits ?? 0 }));
        onDone();
      },
      onError: (err) => toast.error(getErrorDetail(err) ?? t('billing.errorCheckout')),
    },
  });

  const { control, handleSubmit, watch } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { pack_id: DEFAULT_PACK },
  });

  const list = packs ?? [];
  const selected = list.find((p) => p.id === watch('pack_id'));

  // Credits are only usable on a paid tier (the backend 403s a free checkout),
  // so guide free users to subscribe first instead of into a dead end.
  if (!isSubscribed) {
    return (
      <>
        <DialogHeader>
          <DialogTitle>{t('billing.credits.title')}</DialogTitle>
          <DialogDescription>{t('billing.credits.subscribeFirst')}</DialogDescription>
        </DialogHeader>
        <Button
          variant="gradient"
          className="w-full"
          onClick={() => {
            onDone();
            navigate('/billing');
          }}
        >
          <Sparkles className="size-4" />
          {t('billing.credits.viewPlans')}
        </Button>
      </>
    );
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{t('billing.credits.title')}</DialogTitle>
        <DialogDescription>
          {t('billing.credits.subtitle')} · {t('billing.creditsChip', { count: credits })}
        </DialogDescription>
      </DialogHeader>

      {isLoading ? (
        <Skeleton className="h-44 w-full" />
      ) : (
        <form onSubmit={handleSubmit(({ pack_id }) => checkout.mutate({ data: { pack_id } }))} className="space-y-4">
          <Controller
            name="pack_id"
            control={control}
            render={({ field }) => (
              <div className="space-y-2">
                {list.map((pack) => {
                  const active = field.value === pack.id;
                  return (
                    <button
                      key={pack.id}
                      type="button"
                      onClick={() => field.onChange(pack.id)}
                      aria-pressed={active}
                      className={cn(
                        'flex w-full items-center justify-between rounded-xl border p-4 text-left outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring/50',
                        active ? 'border-primary ring-1 ring-primary' : 'border-border hover:border-foreground/30'
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <Coins className="size-4 text-primary" />
                        <span className="text-body-default-bold">
                          {t('billing.packs.credits', { count: pack.credits })}
                        </span>
                      </span>
                      <span className="flex items-center gap-2">
                        <span className="text-body-default text-muted-foreground">{fmt.currency(pack.price_usd)}</span>
                        {active ? <Check className="size-4 text-primary" /> : null}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          />
          <Button type="submit" variant="gradient" className="w-full" disabled={checkout.isPending}>
            <Coins className="size-4" />
            {checkout.isPending
              ? t('billing.packs.buying')
              : t('billing.credits.confirm', { count: selected?.credits ?? 0 })}
          </Button>
        </form>
      )}
    </>
  );
}
