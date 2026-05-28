import { Check } from 'lucide-react';

import { useTranslation } from '@applark/i18n';

import type { MappedExperience } from '@/domains/api/generated/model/mappedExperience';

export function StrengthsList({ strengths }: { strengths: MappedExperience[] }) {
  const { t } = useTranslation();
  if (strengths.length === 0) {
    return <p className="text-body-default text-muted-foreground">{t('matching.strengths.empty')}</p>;
  }
  return (
    <ul className="space-y-4">
      {strengths.map((s, i) => (
        <li key={`${s.cv_chunk_id}-${i}`} className="flex gap-3">
          <span className="mt-0.5 inline-flex size-5 shrink-0 items-center justify-center rounded-full bg-positive/15 text-positive">
            <Check className="size-3" />
          </span>
          <div className="min-w-0 space-y-1">
            <div className="text-body-default-bold">{s.requirement_text}</div>
            <blockquote className="border-border border-l-2 pl-3 text-body-default text-foreground/85">
              {s.cv_chunk_excerpt}
            </blockquote>
            <p className="text-body-small text-muted-foreground italic">{s.why_it_matches}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
