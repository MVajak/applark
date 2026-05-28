import { Copy } from 'lucide-react';

import { useTranslation } from '@applark/i18n';
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  cn,
  copyToClipboard,
  relativeTime,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  truncate,
} from '@applark/ui';

import type { CoverLetterDraftRead } from '@/domains/api/generated/model/coverLetterDraftRead';
import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';

const TONE_STYLES: Record<string, string> = {
  'plain-direct': 'bg-muted/40 text-muted-foreground border-border',
  'warm-personal': 'bg-warning/10 text-warning border-warning/30',
  formal: 'bg-highlight/10 text-highlight border-highlight/30',
};

export function CoverLetterDraftCard({
  draft,
  chunkLookup,
}: {
  draft: CoverLetterDraftRead;
  chunkLookup: Map<string, CVChunkRead>;
}) {
  const { t } = useTranslation();
  const referenced = draft.referenced_chunks
    .map((id) => ({ id, chunk: chunkLookup.get(id) }))
    .filter((entry): entry is { id: string; chunk: CVChunkRead } => entry.chunk !== undefined);

  return (
    <Card className="max-w-prose p-6">
      <CardHeader className="space-y-3 p-0 pb-4">
        <div className="flex items-center gap-2 text-body-small text-muted-foreground">
          {draft.tone && (
            <Badge variant="outline" className={cn('font-normal', TONE_STYLES[draft.tone])}>
              {draft.tone}
            </Badge>
          )}
          <span>{relativeTime(draft.created_at)}</span>
        </div>
        <h3 className="text-body-large-bold">{draft.subject}</h3>
      </CardHeader>

      <CardContent className="space-y-5 p-0">
        <pre className="max-w-prose whitespace-pre-wrap font-sans text-body-default text-foreground/90">
          {draft.body}
        </pre>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => copyToClipboard(draft.body, t('coverLetters.copied'))}>
            <Copy className="size-3" /> {t('coverLetters.copyBody')}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              copyToClipboard(`Subject: ${draft.subject}\n\n${draft.body}`, t('coverLetters.copiedWithSubject'))
            }
          >
            <Copy className="size-3" /> {t('coverLetters.copyWithSubject')}
          </Button>
        </div>

        {referenced.length > 0 && (
          <div className="space-y-2 border-border border-t pt-4">
            <p className="text-body-small text-muted-foreground uppercase tracking-wide">
              {t('coverLetters.referencedChunks')}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {referenced.map(({ id, chunk }) => (
                <Tooltip key={id}>
                  <TooltipTrigger asChild>
                    <span className="inline-flex cursor-default items-center gap-1 rounded-md border border-border bg-muted/40 px-2 py-0.5 text-body-small">
                      <span className="text-muted-foreground">{chunk.chunk_type}</span>
                      <span className="text-foreground/80">·</span>
                      <span>{truncate(chunk.content, 48)}</span>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-md whitespace-pre-wrap">{chunk.content}</TooltipContent>
                </Tooltip>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
