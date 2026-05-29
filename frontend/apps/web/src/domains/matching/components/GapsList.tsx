import { useFormat } from '@applark/format';
import { useTranslation } from '@applark/i18n';
import { cn } from '@applark/ui';

import type { Gap } from '@/domains/api/generated/model/gap';

export function GapsList({ gaps }: { gaps: Gap[] }) {
  const { t } = useTranslation();
  const fmt = useFormat();
  if (gaps.length === 0) {
    return <p className="text-body-default text-muted-foreground">{t('matching.gaps.empty')}</p>;
  }
  // Highest-severity first.
  const sorted = [...gaps].sort((a, b) => b.severity - a.severity);
  return (
    <ul className="space-y-2.5">
      {sorted.map((gap, i) => (
        <li key={i} className="flex items-start gap-3">
          <span
            aria-hidden
            className={cn(
              'mt-1.5 inline-block size-2 shrink-0 rounded-full',
              gap.severity >= 0.7 ? 'bg-destructive' : 'bg-warning'
            )}
          />
          <div className="min-w-0 flex-1">
            <div className="text-body-default">{gap.requirement_text}</div>
            <div className="text-body-small text-muted-foreground">
              {t('matching.gaps.severity', { value: fmt.percent(gap.severity) })}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
