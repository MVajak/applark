import type { LucideIcon } from 'lucide-react';
import { ArrowRight } from 'lucide-react';
import { motion } from 'motion/react';

import { Card } from '@applark/ui';

export function QuickActionCard({
  icon: Icon,
  label,
  description,
  onClick,
}: {
  icon: LucideIcon;
  label: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 380, damping: 28 }}
      className="rounded-2xl text-left outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2"
    >
      <Card className="gap-2 p-5 transition-shadow hover:shadow-lg">
        <div className="flex items-start justify-between gap-3">
          <span className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Icon className="size-5" />
          </span>
          <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
        </div>
        <div className="space-y-0.5">
          <div className="text-title-small-bold">{label}</div>
          <p className="text-body-small text-muted-foreground">{description}</p>
        </div>
      </Card>
    </motion.button>
  );
}
