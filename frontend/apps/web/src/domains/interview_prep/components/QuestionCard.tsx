import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

import { useTranslation } from '@applark/i18n';
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  cn,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  truncate,
} from '@applark/ui';

import type { CVChunkRead } from '@/domains/api/generated/model/cVChunkRead';
import type { InterviewQuestion } from '@/domains/api/generated/model/interviewQuestion';
import { QuestionCategory } from '@/domains/api/generated/model/questionCategory';

const CATEGORY_TINT: Record<QuestionCategory, string> = {
  technical: 'border-info/30 bg-info/10 text-info',
  system_design: 'border-creative/30 bg-creative/10 text-creative',
  behavioral: 'border-positive/30 bg-positive/10 text-positive',
  role_specific: 'border-border bg-muted/40 text-muted-foreground',
  culture_fit: 'border-warning/30 bg-warning/10 text-warning',
};

export function QuestionCard({
  question,
  chunkLookup,
}: {
  question: InterviewQuestion;
  chunkLookup: Map<string, CVChunkRead>;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const tint = CATEGORY_TINT[question.category];

  const referenced = question.referenced_cv_chunk_ids
    .map((id) => ({ id, chunk: chunkLookup.get(id) }))
    .filter((entry): entry is { id: string; chunk: CVChunkRead } => entry.chunk !== undefined);

  const orphanCount = question.referenced_cv_chunk_ids.length - referenced.length;
  const noRefs = question.referenced_cv_chunk_ids.length === 0;

  return (
    <Card className="p-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-start gap-3 rounded-2xl p-5 text-left outline-none transition-colors hover:bg-muted/30 focus-visible:ring-2 focus-visible:ring-ring/50"
      >
        <CardHeader className="flex-1 space-y-2 p-0">
          <Badge variant="outline" className={cn('font-normal', tint)}>
            {t(`interviewPrep.category.${question.category}`)}
          </Badge>
          <h3 className="text-body-large-bold">{question.question}</h3>
        </CardHeader>
        <ChevronDown
          className={cn(
            'mt-1 size-4 shrink-0 text-muted-foreground transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <CardContent className="space-y-3 px-5 pt-0 pb-5">
          <div>
            <p className="mb-1 text-body-small text-muted-foreground uppercase tracking-wide">
              {t('interviewPrep.whyLikely')}
            </p>
            <p className="text-body-default text-foreground/90">{question.why_likely}</p>
          </div>
          <div>
            <p className="mb-1 text-body-small text-muted-foreground uppercase tracking-wide">
              {t('interviewPrep.howToApproach')}
            </p>
            <p className="whitespace-pre-wrap text-body-default text-foreground/90">{question.suggested_angle}</p>
          </div>

          {noRefs ? (
            <p className="text-body-small text-muted-foreground italic">{t('interviewPrep.noDirectExperience')}</p>
          ) : (
            <div className="space-y-1.5">
              <p className="text-body-small text-muted-foreground uppercase tracking-wide">
                {t('interviewPrep.drawOn')}
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
                {orphanCount > 0 && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="inline-flex cursor-default items-center gap-1 rounded-md border border-warning/40 border-dashed bg-warning/5 px-2 py-0.5 text-body-small text-warning italic">
                        {t('interviewPrep.notInCv', { count: orphanCount })}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>{t('interviewPrep.orphanTooltip')}</TooltipContent>
                  </Tooltip>
                )}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
