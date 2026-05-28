import { StrictMode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import { useSpotlightStore } from '@/domains/shell/spotlight-store';
import { initTheme } from '@/domains/theme/store';
import { router } from '@/router';

import '@applark/i18n';
import './index.css';

initTheme();

// Global ⌘K / Ctrl+K toggles the command palette. Active in any context;
// once the palette is open, cmdk owns keyboard events from there.
window.addEventListener('keydown', (event) => {
  if (event.key === 'k' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    useSpotlightStore.getState().toggle();
  }
});

const root = document.getElementById('root');
if (!root) throw new Error('Root element #root not found');

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>
);
