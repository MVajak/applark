import { Outlet } from 'react-router-dom';

import { Toaster, TooltipProvider } from '@applark/ui';

import { useCvEvents } from '@/domains/api/hooks/useCvEvents';
import { useJobEvents } from '@/domains/api/hooks/useJobEvents';
import { BuyCreditsModal } from '@/domains/billing/components/BuyCreditsModal';
import { AppHeader } from '@/domains/shell/components/AppHeader';
import { Spotlight } from '@/domains/shell/components/Spotlight';

export function RootLayout() {
  // One SSE connection per stream, kept open for the life of the app so events
  // continue invalidating cache while the user is on any route.
  useJobEvents();
  useCvEvents();

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex min-h-svh flex-col bg-background text-foreground">
        <AppHeader />
        <main className="mx-auto w-full max-w-5xl flex-1 px-6 pt-24 pb-8 sm:pt-28">
          <Outlet />
        </main>
        <Toaster position="bottom-right" />
        <Spotlight />
        <BuyCreditsModal />
      </div>
    </TooltipProvider>
  );
}
