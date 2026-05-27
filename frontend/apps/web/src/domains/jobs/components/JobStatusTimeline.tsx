import { CheckCircle2, Circle, Loader2, OctagonX } from 'lucide-react';
import { motion } from 'motion/react';

import { cn } from '@applark/ui';

import { JobStatus } from '@/domains/api/generated/model/jobStatus';

type Step = { id: JobStatus; label: string };

const STEPS: readonly Step[] = [
  { id: JobStatus.pending, label: 'Queued' },
  { id: JobStatus.scraping, label: 'Scraping' },
  { id: JobStatus.extracting, label: 'Extracting' },
  { id: JobStatus.ready, label: 'Ready' },
];

const ORDER: Record<JobStatus, number> = {
  [JobStatus.pending]: 0,
  [JobStatus.scraping]: 1,
  [JobStatus.extracting]: 2,
  [JobStatus.ready]: 3,
  [JobStatus.failed]: -1,
};

export function JobStatusTimeline({ status }: { status: JobStatus }) {
  const failed = status === JobStatus.failed;
  const ready = status === JobStatus.ready;
  // When ready, every step is done. When in-progress, step at currentIndex is active.
  // When failed, mark the step where scraping happens (best guess) as the failure point.
  const currentIndex = failed ? STEPS.findIndex((s) => s.id === JobStatus.scraping) : ORDER[status];

  return (
    <ol className="flex items-center gap-2 overflow-x-auto pb-1">
      {STEPS.map((step, i) => {
        const done = ready || (!failed && i < currentIndex);
        const active = !ready && !failed && i === currentIndex;
        const upcoming = !ready && !failed && i > currentIndex;
        const isFailedStep = failed && i === currentIndex;

        return (
          <li key={step.id} className="flex shrink-0 items-center gap-2">
            <motion.span
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.2, delay: i * 0.04 }}
              className={cn(
                'flex size-7 items-center justify-center rounded-full border transition-colors',
                done && 'border-positive bg-positive/10 text-positive',
                active && 'border-warning bg-warning/10 text-warning',
                upcoming && 'border-border bg-muted text-muted-foreground',
                isFailedStep && 'border-destructive bg-destructive/10 text-destructive'
              )}
            >
              {done && <CheckCircle2 className="size-4" />}
              {active && <Loader2 className="size-4 animate-spin" />}
              {upcoming && <Circle className="size-3" />}
              {isFailedStep && <OctagonX className="size-4" />}
            </motion.span>
            <span
              className={cn(
                'text-body-small',
                done && 'text-positive',
                active && 'text-warning',
                upcoming && 'text-muted-foreground',
                isFailedStep && 'text-destructive'
              )}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && <span aria-hidden className="h-px w-6 bg-border" />}
          </li>
        );
      })}
    </ol>
  );
}
