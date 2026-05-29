import axios, { type AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from 'axios';

import { type AuthTokens, useAuthStore } from '@/domains/auth/store';

const baseURL = import.meta.env.VITE_API_BASE_URL;

const instance = axios.create({ baseURL });
// Separate, interceptor-free client for the refresh call so a 401 on refresh
// can't recurse back into the refresh logic.
const refreshClient = axios.create({ baseURL });

instance.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.set('Authorization', `Bearer ${token}`);
  }
  return config;
});

// In-flight refresh shared across concurrent 401s, so we refresh once.
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const { data } = await refreshClient.post<AuthTokens>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    useAuthStore.getState().setTokens(data);
    return data.access_token;
  } catch {
    return null;
  }
}

function redirectToLogin(): void {
  useAuthStore.getState().logout();
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login';
  }
}

instance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // Cast adds our one-shot retry flag; safe because we only read/set `_retried`.
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    const url = original?.url ?? '';
    const isAuthCall = url.includes('/auth/');

    if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
      original._retried = true;
      refreshInFlight ??= refreshAccessToken().finally(() => {
        refreshInFlight = null;
      });
      const token = await refreshInFlight;
      if (token) {
        original.headers.set('Authorization', `Bearer ${token}`);
        return instance(original);
      }
      redirectToLogin();
    }
    return Promise.reject(error);
  }
);

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
