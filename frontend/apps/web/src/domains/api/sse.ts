// SSE base URL is the same axios base + /api/v1; orval generates against the
// same root, so we read VITE_API_BASE_URL directly.
export const SSE_BASE = `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/v1`;
