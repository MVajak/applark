import { Lightbulb } from 'lucide-react';

export function SuggestedEmphasis({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="space-y-2.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-3 text-body-default">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-warning" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}
