import { Lock, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { useTranslation } from '@applark/i18n';
import { Button, Card } from '@applark/ui';

/**
 * Shown in place of an intake form (CV upload / add job) for free users.
 * AI intake is a paid capability, so route them to the plans page. The
 * backend also 403s these endpoints — this is the friendly front door.
 */
export function IntakePaywall() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Card className="flex flex-col items-start gap-3 p-6">
      <div className="flex items-center gap-2 text-title-small-bold">
        <Lock className="size-5 text-primary" />
        {t('billing.intakeLocked.title')}
      </div>
      <p className="text-body-default text-muted-foreground">{t('billing.intakeLocked.body')}</p>
      <Button variant="gradient" onClick={() => navigate('/billing')}>
        <Sparkles className="size-4" />
        {t('billing.upgrade')}
      </Button>
    </Card>
  );
}
