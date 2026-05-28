import { Lightbulb } from 'lucide-react';

import { useTranslation } from '@applark/i18n';

export function QuestionsToAskBox({ items }: { items: string[] }) {
  const { t } = useTranslation();
  if (items.length === 0) return null;
  return (
    <div className="space-y-3 rounded-md border border-highlight/30 bg-highlight/10 p-5">
      <div className="flex items-center gap-2 text-body-default-bold text-highlight">
        <Lightbulb className="size-4" />
        {t('interviewPrep.questionsToAsk')}
      </div>
      <ul className="ml-4 list-disc space-y-2 text-body-default text-foreground/85">
        {items.map((q, i) => (
          <li key={i} className="leading-relaxed">
            {q}
          </li>
        ))}
      </ul>
    </div>
  );
}
