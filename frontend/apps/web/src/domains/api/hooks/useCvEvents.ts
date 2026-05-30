import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { getGetCvDocumentQueryKey, getGetCvDocumentsQueryKey } from '@/domains/api/generated/cv/cv';
import { SSE_BASE } from '@/domains/api/sse';
import { useAuthStore } from '@/domains/auth/store';

type CvProcessingEvent = {
  readonly document_id: string;
  readonly chunks_ready: boolean;
};

function isCvProcessingEvent(value: unknown): value is CvProcessingEvent {
  if (typeof value !== 'object' || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.document_id === 'string' && typeof v.chunks_ready === 'boolean';
}

/** SSE listener for CV processing — mirrors `useJobEvents` for the CV pipeline. */
export function useCvEvents(): void {
  const queryClient = useQueryClient();
  const accessToken = useAuthStore((s) => s.accessToken);
  useEffect(() => {
    if (!accessToken) return;
    const es = new EventSource(`${SSE_BASE}/cv/events?token=${encodeURIComponent(accessToken)}`);
    es.onmessage = (e) => {
      const parsed: unknown = JSON.parse(e.data);
      if (!isCvProcessingEvent(parsed)) return;
      void queryClient.invalidateQueries({ queryKey: getGetCvDocumentsQueryKey() });
      void queryClient.invalidateQueries({ queryKey: getGetCvDocumentQueryKey(parsed.document_id) });
    };
    return () => es.close();
  }, [queryClient, accessToken]);
}
