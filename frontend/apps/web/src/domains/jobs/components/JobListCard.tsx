import { Briefcase } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useFormat } from '@applark/format';
import { useTranslation } from '@applark/i18n';
import { Card } from '@applark/ui';

import type { JobListItem } from '@/domains/api/generated/model/jobListItem';
import { JobStatusBadge } from '@/domains/jobs/components/JobStatusBadge';

export function JobListCard({ job }: { job: JobListItem }) {
  const { t } = useTranslation();
  const fmt = useFormat();
  const title = job.title ?? t('jobs.untitled');
  const company = job.company ?? t('jobs.unknownCompany');

  return (
    <Link
      to={`/jobs/${job.id}`}
      className="block rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2"
    >
      <Card hoverable className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Briefcase className="size-5" />
          </div>
          <div className="min-w-0 flex-1 space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate text-title-small-bold">{title}</h3>
              <JobStatusBadge status={job.status} />
            </div>
            <div className="text-body-default text-muted-foreground">
              <span>{company}</span>
              {job.location && <span> · {job.location}</span>}
            </div>
          </div>
          <span className="shrink-0 text-body-small text-muted-foreground">{fmt.relativeTime(job.created_at)}</span>
        </div>
      </Card>
    </Link>
  );
}
