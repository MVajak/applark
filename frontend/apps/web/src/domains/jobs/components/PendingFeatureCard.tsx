import { useEffect, useState } from 'react';

import { Card, cn, Skeleton } from '@postpilot/ui';

const ROTATE_INTERVAL_MS = 3500;

/**
 * Skeleton card shown while a long-running feature mutation is in flight.
 *
 * `caption` can be a single string OR an array of strings that rotate
 * every 3.5s (used by interview prep to make the wait feel less stagnant).
 */
export function PendingFeatureCard({
  caption,
  className,
}: {
  caption: string | readonly string[];
  className?: string;
}) {
  const captions = Array.isArray(caption) ? caption : [caption as string];
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (captions.length <= 1) return;
    const id = setInterval(() => {
      setIdx((i) => Math.min(i + 1, captions.length - 1));
    }, ROTATE_INTERVAL_MS);
    return () => clearInterval(id);
  }, [captions.length]);

  return (
    <Card className={cn('space-y-3 p-6', className)}>
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-5/6" />
      <Skeleton className="h-3 w-2/3" />
      <p className="pt-2 text-body-default text-muted-foreground italic">{captions[idx]}</p>
    </Card>
  );
}
