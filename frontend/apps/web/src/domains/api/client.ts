import axios, { type AxiosRequestConfig } from 'axios';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

export const customAxios = <T>(config: AxiosRequestConfig): Promise<T> => {
  return instance(config).then(({ data }) => data);
};

/**
 * Read FastAPI's `{ detail: "..." }` error message from an axios-shaped error.
 * Handles both string-detail (`detail: "..."`) and structured-detail
 * (`detail: { message: "...", ... }`) responses.
 */
export function getErrorDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (typeof detail === 'object' && detail !== null && 'message' in detail) {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === 'string') return message;
    }
  }
  return null;
}

/**
 * Read a structured FastAPI detail object from an axios-shaped error.
 * Use when the handler raises HTTPException(detail={...}) and you need
 * fields beyond `message` (e.g. `existing_job_id`).
 */
export function getErrorDetailObject(err: unknown): Record<string, unknown> | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { data?: { detail?: unknown } } }).response;
    const detail = response?.data?.detail;
    if (typeof detail === 'object' && detail !== null && !Array.isArray(detail)) {
      return detail as Record<string, unknown>;
    }
  }
  return null;
}

/** Read the HTTP status code from an axios-shaped error. */
export function getErrorStatus(err: unknown): number | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const response = (err as { response?: { status?: unknown } }).response;
    if (typeof response?.status === 'number') return response.status;
  }
  return null;
}
