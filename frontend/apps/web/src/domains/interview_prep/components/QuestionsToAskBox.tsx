import { Lightbulb } from 'lucide-react';

export function QuestionsToAskBox({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-3 rounded-md border border-highlight/30 bg-highlight/10 p-5">
      <div className="flex items-center gap-2 text-body-default-bold text-highlight">
        <Lightbulb className="size-4" />
        Questions to ask them
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
