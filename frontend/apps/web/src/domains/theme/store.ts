import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

interface ThemeState {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
}

const getSystemTheme = (): ResolvedTheme => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const resolve = (theme: Theme): ResolvedTheme => (theme === 'system' ? getSystemTheme() : theme);

const applyTheme = (resolved: ResolvedTheme) => {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  if (resolved === 'dark') root.classList.add('dark');
  else root.classList.remove('dark');
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'system',
      resolvedTheme: getSystemTheme(),
      setTheme: (theme: Theme) => {
        const resolved = resolve(theme);
        applyTheme(resolved);
        set({ theme, resolvedTheme: resolved });
      },
    }),
    {
      name: 'applark-theme',
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = resolve(state.theme);
          state.resolvedTheme = resolved;
          applyTheme(resolved);
        }
      },
    }
  )
);

/**
 * Call once at app startup BEFORE React mounts so the dark class is on
 * documentElement before first paint (no FOUC).
 *
 * Also wires a matchMedia listener so the resolved theme updates live when
 * the user is on `system` and flips their OS appearance.
 */
export function initTheme(): void {
  if (typeof window === 'undefined') return;
  const store = useThemeStore.getState();
  applyTheme(store.resolvedTheme);

  const media = window.matchMedia('(prefers-color-scheme: dark)');
  media.addEventListener('change', () => {
    const current = useThemeStore.getState();
    if (current.theme !== 'system') return;
    const resolved: ResolvedTheme = media.matches ? 'dark' : 'light';
    applyTheme(resolved);
    useThemeStore.setState({ resolvedTheme: resolved });
  });
}
