import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { getGetCvDocumentQueryKey, getGetCvDocumentsQueryKey } from '@/domains/api/generated/cv/cv';
import { getGetJobQueryKey, getGetJobsQueryKey } from '@/domains/api/generated/jobs/jobs';
import { JobStatus } from '@/domains/api/generated/model/jobStatus';

// SSE base URL is the same axios base + /api/v1; orval generates against the
// same root, so we read VITE_API_BASE_URL directly.
const SSE_BASE = `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1`;

type JobStatusEvent = {
  readonly job_id: string;
  readonly status: JobStatus;
  readonly error_message: string | null;
};

type CvProcessingEvent = {
  readonly document_id: string;
  readonly chunks_ready: boolean;
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

function isCvProcessingEvent(value: unknown): value is CvProcessingEvent {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.document_id === 'string' && typeof v.chunks_ready === 'boolean';
}

/**
 * Open one EventSource against `/jobs/events` for the life of the component.
 * Mount once at the app shell so events still land while the user is on
 * another route — the TanStack cache stays fresh and the next page render
 * has no extra round-trip.
 */
export function useJobEvents(): void {
  const queryClient = useQueryClient();
  useEffect(() => {
    const es = new EventSource(`${SSE_BASE}/jobs/events`);
    es.onmessage = (e) => {
      const parsed: unknown = JSON.parse(e.data);
      if (!isJobStatusEvent(parsed)) return;
      queryClient.invalidateQueries({ queryKey: getGetJobsQueryKey() });
      queryClient.invalidateQueries({ queryKey: getGetJobQueryKey(parsed.job_id) });
    };
    return () => es.close();
  }, [queryClient]);
}

export function useCvEvents(): void {
  const queryClient = useQueryClient();
  useEffect(() => {
    const es = new EventSource(`${SSE_BASE}/cv/events`);
    es.onmessage = (e) => {
      const parsed: unknown = JSON.parse(e.data);
      if (!isCvProcessingEvent(parsed)) return;
      queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
      queryClient.invalidateQueries({ queryKey: getGetCvDocumentQueryKey(parsed.document_id) });
    };
    return () => es.close();
  }, [queryClient]);
}
