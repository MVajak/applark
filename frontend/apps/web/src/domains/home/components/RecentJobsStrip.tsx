import { ArrowUpRight, Briefcase } from 'lucide-react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';

import { useTranslation } from '@applark/i18n';
import { Card, relativeTime } from '@applark/ui';

import type { JobListItem } from '@/domains/api/generated/model/jobListItem';
import { JobStatusBadge } from '@/domains/jobs/components/JobStatusBadge';

export function RecentJobsStrip({ jobs }: { jobs: JobListItem[] }) {
  const { t } = useTranslation();
  if (jobs.length === 0) return null;

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {jobs.map((job, i) => (
        <motion.div
          key={job.id}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25, delay: 0.05 * i, ease: 'easeOut' }}
        >
          <Link
            to={`/jobs/${job.id}`}
            className="block rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2"
          >
            <Card hoverable className="gap-2.5 p-4">
              <div className="flex items-start justify-between gap-2">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Briefcase className="size-4" />
                </span>
                <ArrowUpRight className="size-4 shrink-0 text-muted-foreground" />
              </div>
              <div className="min-w-0 space-y-1">
                <div className="truncate text-body-default-bold">{job.title ?? t('jobs.untitled')}</div>
                <div className="truncate text-body-small text-muted-foreground">
                  {job.company ?? t('jobs.unknownCompany')}
                </div>
              </div>
              <div className="flex items-center justify-between gap-2 pt-1">
                <JobStatusBadge status={job.status} />
                <span className="text-body-small text-muted-foreground">{relativeTime(job.created_at)}</span>
              </div>
            </Card>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}
