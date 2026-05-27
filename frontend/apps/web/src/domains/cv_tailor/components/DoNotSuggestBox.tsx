import { AlertTriangle } from 'lucide-react';

export function DoNotSuggestBox({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2 rounded-md border border-warning/30 bg-warning/10 p-4">
      <div className="flex items-center gap-2 text-body-default-bold text-warning">
        <AlertTriangle className="size-4" />
        Honesty checks
      </div>
      <ul className="ml-4 list-disc space-y-1.5 text-body-default text-foreground/85">
        {items.map((item, i) => (
          <li key={i} className="leading-snug">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
