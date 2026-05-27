import type { LucideIcon } from 'lucide-react';
import { ArrowDown, Check, Copy, Pencil, Plus } from 'lucide-react';

import { Button, cn, copyToClipboard } from '@applark/ui';

import { SuggestionKind } from '@/domains/api/generated/model/suggestionKind';
import type { TailorSuggestion } from '@/domains/api/generated/model/tailorSuggestion';

const KIND_STYLES: Record<SuggestionKind, { label: string; icon: LucideIcon; tint: string; iconColor: string }> = {
  emphasize: {
    label: 'Make this more prominent',
    icon: Check,
    tint: 'border-positive/30 bg-positive/5',
    iconColor: 'text-positive',
  },
  rephrase: {
    label: 'Rephrase',
    icon: Pencil,
    tint: 'border-info/30 bg-info/5',
    iconColor: 'text-info',
  },
  add_detail: {
    label: 'Add detail',
    icon: Plus,
    tint: 'border-warning/30 bg-warning/5',
    iconColor: 'text-warning',
  },
  deprioritize: {
    label: 'Push this down or remove',
    icon: ArrowDown,
    tint: 'border-border bg-muted/30',
    iconColor: 'text-muted-foreground',
  },
};

export function SuggestionCard({ suggestion }: { suggestion: TailorSuggestion }) {
  const style = KIND_STYLES[suggestion.kind];
  const Icon = style.icon;

  const copy = () => {
    if (suggestion.suggested_text) void copyToClipboard(suggestion.suggested_text);
  };

  return (
    <div className={cn('space-y-2 rounded-md border p-3', style.tint)}>
      <div className="flex items-center gap-2 text-body-small-bold">
        <Icon className={cn('size-3.5', style.iconColor)} />
        <span className={style.iconColor}>{style.label}</span>
      </div>
      <p className="text-body-default text-foreground/90">{suggestion.rationale}</p>
      {suggestion.suggested_text && (
        <div className="space-y-1.5">
          <blockquote className="whitespace-pre-wrap border-border border-l-2 pl-3 text-body-default text-foreground/85 italic">
            {suggestion.suggested_text}
          </blockquote>
          <Button variant="outline" size="sm" onClick={copy} className="h-7 px-2">
            <Copy className="size-3" /> Copy suggested text
          </Button>
        </div>
      )}
    </div>
  );
}
