import { Badge, cn } from '@postpilot/ui';

import { JobStatus } from '@/domains/api/generated/model/jobStatus';

const STYLES: Record<JobStatus, string> = {
  ready: 'border-positive/30 bg-positive/10 text-positive',
  failed: 'border-destructive/30 bg-destructive/10 text-destructive',
  pending: 'border-warning/30 bg-warning/10 text-warning',
  scraping: 'border-warning/30 bg-warning/10 text-warning',
  extracting: 'border-warning/30 bg-warning/10 text-warning',
};

const LABELS: Record<JobStatus, string> = {
  pending: 'Pending',
  scraping: 'Scraping',
  extracting: 'Extracting',
  ready: 'Ready',
  failed: 'Failed',
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <Badge variant="outline" className={cn('font-normal', STYLES[status])}>
      {LABELS[status]}
    </Badge>
  );
}
