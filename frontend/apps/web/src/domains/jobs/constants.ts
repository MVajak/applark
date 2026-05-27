import { JobStatus } from '@/domains/api/generated/model/jobStatus';

/** Jobs in any of these statuses are still being processed by the backend. */
export const ACTIVE_STATUSES: ReadonlySet<JobStatus> = new Set([
  JobStatus.pending,
  JobStatus.scraping,
  JobStatus.extracting,
]);
