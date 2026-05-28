import { useState } from 'react';

import { useTranslation } from '@applark/i18n';
import { Button, Card, cn } from '@applark/ui';

import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import type { CVTailorRunRead } from '@/domains/api/generated/model/cVTailorRunRead';
import type { TailorSuggestion } from '@/domains/api/generated/model/tailorSuggestion';
import { DoNotSuggestBox } from '@/domains/cv_tailor/components/DoNotSuggestBox';
import { SuggestionCard } from '@/domains/cv_tailor/components/SuggestionCard';

function ChunkBlock({ chunk, suggestions }: { chunk: CVChunkRead; suggestions: TailorSuggestion[] }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const hasSuggestions = suggestions.length > 0;
  const isLong = chunk.content.length > 220;

  return (
    <div className={cn('space-y-2 rounded-md border border-border p-4', !hasSuggestions && 'opacity-60')}>
      <div className="text-body-small text-muted-foreground uppercase tracking-wide">{chunk.chunk_type}</div>
      <p
        className={cn(
          'whitespace-pre-wrap text-body-default text-foreground/90',
          !expanded && isLong && 'line-clamp-3'
        )}
      >
        {chunk.content}
      </p>
      {isLong && (
        <Button variant="ghost" size="sm" className="h-6 px-2 text-body-small" onClick={() => setExpanded((v) => !v)}>
          {expanded ? t('cvTailor.showLess') : t('cvTailor.showMore')}
        </Button>
      )}

      {hasSuggestions ? (
        <div className="space-y-2 pt-2">
          {suggestions.map((s, i) => (
            <SuggestionCard key={`${chunk.id}-${i}`} suggestion={s} />
          ))}
        </div>
      ) : (
        <p className="pt-1 text-body-small text-muted-foreground italic">{t('cvTailor.looksGood')}</p>
      )}
    </div>
  );
}

export function CVTailorResultPanel({ run, chunks }: { run: CVTailorRunRead; chunks: CVChunkRead[] }) {
  const { t } = useTranslation();
  // Group suggestions by cv_chunk_id so each chunk renders its own.
  const byChunk = new Map<string, TailorSuggestion[]>();
  for (const s of run.suggestions) {
    const list = byChunk.get(s.cv_chunk_id) ?? [];
    list.push(s);
    byChunk.set(s.cv_chunk_id, list);
  }
  // Also collect suggestions whose cv_chunk_id doesn't match any current
  // chunk (defensive: e.g. user re-uploaded CV after running tailor).
  const orphans: TailorSuggestion[] = [];
  const knownIds = new Set(chunks.map((c) => c.id));
  for (const s of run.suggestions) {
    if (!knownIds.has(s.cv_chunk_id)) orphans.push(s);
  }

  return (
    <div className="space-y-4">
      <Card className="bg-muted/30 p-4">
        <p className="text-body-default">
          <span className="text-muted-foreground">{t('cvTailor.mostCaresAbout')}</span>
          <span className="text-foreground">{run.job_summary}</span>
        </p>
      </Card>

      <DoNotSuggestBox items={run.do_not_suggest} />

      <div className="space-y-3">
        {chunks.map((chunk) => (
          <ChunkBlock key={chunk.id} chunk={chunk} suggestions={byChunk.get(chunk.id) ?? []} />
        ))}
      </div>

      {orphans.length > 0 && (
        <div className="space-y-2">
          <p className="text-body-small text-muted-foreground">{t('cvTailor.orphans')}</p>
          {orphans.map((s, i) => (
            <SuggestionCard key={`orphan-${i}`} suggestion={s} />
          ))}
        </div>
      )}
    </div>
  );
}
