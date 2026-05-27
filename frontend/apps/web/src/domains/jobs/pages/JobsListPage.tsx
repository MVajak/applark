import { useEffect, useMemo, useState } from 'react';
import { Briefcase, Plus } from 'lucide-react';
import { motion } from 'motion/react';
import { useSearchParams } from 'react-router-dom';

import { Button, cn, Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, Skeleton } from '@postpilot/ui';

import { useGetJobs } from '@/domains/api/generated/jobs/jobs';
import { JobStatus } from '@/domains/api/generated/model/jobStatus';
import { JobCreateForm } from '@/domains/jobs/components/JobCreateForm';
import { JobListCard } from '@/domains/jobs/components/JobListCard';
import { ACTIVE_STATUSES } from '@/domains/jobs/constants';
import { EmptyState } from '@/domains/shell/components/EmptyState';

const FILTERS = [
  { id: 'all' as const, label: 'All' },
  { id: 'ready' as const, label: 'Ready', status: JobStatus.ready },
  { id: 'active' as const, label: 'In progress' },
  { id: 'failed' as const, label: 'Failed', status: JobStatus.failed },
];

type FilterId = (typeof FILTERS)[number]['id'];

export function JobsListPage() {
  const [filter, setFilter] = useState<FilterId>('all');
  const [searchParams, setSearchParams] = useSearchParams();
  const [dialogOpen, setDialogOpen] = useState(false);

  // Spotlight can deep-link to ?new=url|text to open the create dialog
  useEffect(() => {
    if (searchParams.get('new')) {
      setDialogOpen(true);
      const next = new URLSearchParams(searchParams);
      next.delete('new');
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const { data, isLoading } = useGetJobs();

  const counts = useMemo(() => {
    const jobs = data ?? [];
    return {
      all: jobs.length,
      ready: jobs.filter((j) => j.status === JobStatus.ready).length,
      active: jobs.filter((j) => ACTIVE_STATUSES.has(j.status)).length,
      failed: jobs.filter((j) => j.status === JobStatus.failed).length,
    };
  }, [data]);

  const filtered = useMemo(() => {
    const jobs = data ?? [];
    if (filter === 'all') return jobs;
    if (filter === 'ready') return jobs.filter((j) => j.status === JobStatus.ready);
    if (filter === 'active') return jobs.filter((j) => ACTIVE_STATUSES.has(j.status));
    return jobs.filter((j) => j.status === JobStatus.failed);
  }, [data, filter]);

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 border-border/60 border-b pb-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-title-large-bold tracking-tight">Jobs</h1>
          <p className="text-body-default text-muted-foreground">
            Track and tailor your applications, all in one place.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="gradient">
              <Plus className="size-4" /> Add Job
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Add job</DialogTitle>
            </DialogHeader>
            <JobCreateForm onCreated={() => setDialogOpen(false)} />
          </DialogContent>
        </Dialog>
      </header>

      <FilterBar value={filter} onChange={setFilter} counts={counts} />

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : filtered.length > 0 ? (
        <ul className="space-y-3">
          {filtered.map((job, i) => (
            <motion.li
              key={job.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.22, delay: i * 0.03, ease: 'easeOut' }}
            >
              <JobListCard job={job} />
            </motion.li>
          ))}
        </ul>
      ) : (
        <EmptyState
          icon={Briefcase}
          title={filter === 'all' ? 'No jobs yet' : 'No jobs match this filter'}
          description={
            filter === 'all'
              ? 'Add a job posting URL or paste the text — PostPilot will scrape, extract, and prepare it for matching.'
              : 'Try selecting a different filter above.'
          }
          action={
            filter === 'all' ? (
              <Button variant="gradient" onClick={() => setDialogOpen(true)}>
                <Plus className="size-4" /> Add your first job
              </Button>
            ) : undefined
          }
        />
      )}
    </div>
  );
}

function FilterBar({
  value,
  onChange,
  counts,
}: {
  value: FilterId;
  onChange: (id: FilterId) => void;
  counts: { all: number; ready: number; active: number; failed: number };
}) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {FILTERS.map((f) => {
        const active = value === f.id;
        const count = counts[f.id];
        return (
          <button
            key={f.id}
            type="button"
            onClick={() => onChange(f.id)}
            className={cn(
              'relative rounded-full px-3 py-1.5 text-body-small outline-none transition-colors',
              'focus-visible:ring-2 focus-visible:ring-ring/50',
              active ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {active && (
              <motion.span
                layoutId="job-filter-active"
                className="absolute inset-0 rounded-full bg-muted"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
            <span className="relative">
              {f.label} <span className="ml-1 text-muted-foreground tabular-nums">{count}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
