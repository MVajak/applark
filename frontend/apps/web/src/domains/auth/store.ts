import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (tokens: AuthTokens) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: (tokens) => set({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }),
      logout: () => set({ accessToken: null, refreshToken: null }),
    }),
    {
      name: 'applark-auth',
      partialize: (state) => ({ accessToken: state.accessToken, refreshToken: state.refreshToken }),
    }
  )
);

/** Read-only check used by route guards; tokens live in localStorage via persist. */
export function isAuthenticated(): boolean {
  return useAuthStore.getState().accessToken !== null;
}
