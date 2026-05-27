import { ExternalLink } from 'lucide-react';

import { Badge } from '@postpilot/ui';

import type { JobRead } from '@/domains/api/generated/model/jobRead';
import { RemotePolicy } from '@/domains/api/generated/model/remotePolicy';
import { Seniority } from '@/domains/api/generated/model/seniority';
import { JobStatusBadge } from '@/domains/jobs/components/JobStatusBadge';

const REMOTE_LABEL: Record<RemotePolicy, string> = {
  onsite: 'On-site',
  hybrid: 'Hybrid',
  remote: 'Remote',
  unspecified: '',
};

const SENIORITY_LABEL: Record<Seniority, string> = {
  junior: 'Junior',
  mid: 'Mid',
  senior: 'Senior',
  lead: 'Lead',
  principal: 'Principal',
  unspecified: '',
};

export function JobDetailHeader({ job }: { job: JobRead }) {
  const remoteLabel = REMOTE_LABEL[job.remote_policy];
  const seniorityLabel = SENIORITY_LABEL[job.seniority];

  return (
    <header className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-2">
          <h1 className="text-title-large-bold tracking-tight">{job.title ?? 'Untitled'}</h1>
          <div className="text-body-large text-muted-foreground">
            <span>{job.company ?? 'Unknown company'}</span>
            {job.location && <span> · {job.location}</span>}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {job.source_url && (
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Open source posting"
              className="inline-flex size-9 items-center justify-center rounded-lg border border-border text-muted-foreground outline-none transition-colors hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50"
            >
              <ExternalLink className="size-4" />
            </a>
          )}
          <JobStatusBadge status={job.status} />
        </div>
      </div>

      {(seniorityLabel || remoteLabel || job.salary_range) && (
        <div className="flex flex-wrap items-center gap-2 text-body-default">
          {seniorityLabel && <Badge variant="secondary">{seniorityLabel}</Badge>}
          {remoteLabel && <Badge variant="secondary">{remoteLabel}</Badge>}
          {job.salary_range && <Badge variant="secondary">{job.salary_range}</Badge>}
        </div>
      )}

      {job.tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {job.tech_stack.map((tech) => (
            <Badge key={tech} variant="outline" className="font-normal">
              {tech}
            </Badge>
          ))}
        </div>
      )}

      {job.summary && <p className="whitespace-pre-wrap text-body-default text-foreground/90">{job.summary}</p>}
    </header>
  );
}
