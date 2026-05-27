import { useEffect } from 'react';
import type { LucideIcon } from 'lucide-react';
import { animate, motion, useMotionValue, useTransform } from 'motion/react';

import { Card, cn } from '@applark/ui';

export function StatCard({
  icon: Icon,
  label,
  value,
  tone = 'neutral',
  loading = false,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  tone?: 'neutral' | 'positive' | 'warning' | 'destructive';
  loading?: boolean;
}) {
  const count = useMotionValue(0);
  const rounded = useTransform(count, (v) => Math.round(v).toString());

  useEffect(() => {
    const controls = animate(count, value, { duration: 0.9, ease: 'easeOut' });
    return controls.stop;
  }, [count, value]);

  return (
    <Card className="gap-3 p-5">
      <div className="flex items-center justify-between">
        <span
          className={cn(
            'flex size-9 items-center justify-center rounded-xl',
            tone === 'neutral' && 'bg-muted text-muted-foreground',
            tone === 'positive' && 'bg-positive/10 text-positive',
            tone === 'warning' && 'bg-warning/10 text-warning',
            tone === 'destructive' && 'bg-destructive/10 text-destructive'
          )}
        >
          <Icon className="size-4" />
        </span>
      </div>
      <div className="space-y-0.5">
        {loading ? (
          <span className="block h-8 w-10 animate-pulse rounded bg-muted" />
        ) : (
          <motion.span className="block text-title-large-bold tabular-nums">{rounded}</motion.span>
        )}
        <p className="text-body-small text-muted-foreground">{label}</p>
      </div>
    </Card>
  );
}
