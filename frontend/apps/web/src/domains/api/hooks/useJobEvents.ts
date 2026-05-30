import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { getGetJobQueryKey, getGetJobsQueryKey } from '@/domains/api/generated/jobs/jobs';
import { JobStatus } from '@/domains/api/generated/model/jobStatus';
import { SSE_BASE } from '@/domains/api/sse';
import { useAuthStore } from '@/domains/auth/store';

type JobStatusEvent = {
  readonly job_id: string;
  readonly status: JobStatus;
  readonly error_message: string | null;
};

function isJobStatusEvent(value: unknown): value is JobStatusEvent {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.job_id === 'string' &&
    typeof v.status === 'string' &&
    (Object.values(JobStatus) as readonly string[]).includes(v.status) &&
    (v.error_message === null || typeof v.error_message === 'string')
  );
}

/**
 * Open one EventSource against `/jobs/events` for the life of the component.
 * Mount once at the app shell so events still land while the user is on
 * another route — the TanStack cache stays fresh and the next page render
 * has no extra round-trip.
 */
export function useJobEvents(): void {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);
  useEffect(() => {
    if (!accessToken) return;
    const es = new EventSource(`${SSE_BASE}/jobs/events?token=${encodeURIComponent(accessToken)}`);
    es.onmessage = (e) => {
      const parsed: unknown = JSON.parse(e.data);
      if (!isJobStatusEvent(parsed)) return;
      void queryClient.invalidateQueries({ queryKey: getGetJobsQueryKey() });
      void queryClient.invalidateQueries({ queryKey: getGetJobQueryKey(parsed.job_id) });
    };
    return () => es.close();
  }, [queryClient, accessToken]);
}
