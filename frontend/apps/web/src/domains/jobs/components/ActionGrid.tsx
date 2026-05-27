import { motion } from 'motion/react';

import { Badge, Card } from '@postpilot/ui';

import { useCapabilities } from '@/domains/auth/capabilities';
import { JOB_ACTIONS, type JobAction, type JobActionId } from '@/domains/jobs/actions';

export function ActionGrid({ onSelect }: { onSelect: (action: JobActionId) => void }) {
  const capabilities = useCapabilities();

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {JOB_ACTIONS.map((action, i) => (
        <ActionCard
          key={action.id}
          action={action}
          enabled={capabilities[action.capability]}
          index={i}
          onSelect={() => onSelect(action.id)}
        />
      ))}
    </div>
  );
}

function ActionCard({
  action,
  enabled,
  index,
  onSelect,
}: {
  action: JobAction;
  enabled: boolean;
  index: number;
  onSelect: () => void;
}) {
  const Icon = action.icon;

  if (!enabled) {
    return (
      <Card aria-disabled className="cursor-not-allowed gap-3 p-5 opacity-60">
        <CardInner action={action} icon={<Icon className="size-8 text-muted-foreground" />} />
        <Badge variant="outline" className="w-fit">
          Coming soon
        </Badge>
      </Card>
    );
  }

  return (
    <motion.button
      type="button"
      onClick={onSelect}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04, ease: 'easeOut' }}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.98 }}
      className="group rounded-2xl text-left outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2"
    >
      <Card className="gap-3 p-5 transition-shadow group-hover:shadow-lg">
        <CardInner action={action} icon={<Icon className="size-8 text-primary" />} />
      </Card>
    </motion.button>
  );
}

function CardInner({ action, icon }: { action: JobAction; icon: React.ReactNode }) {
  return (
    <>
      <div className="flex items-start justify-between">{icon}</div>
      <div className="space-y-1">
        <div className="text-title-small-bold">{action.label}</div>
        <p className="text-body-small text-muted-foreground">{action.description}</p>
      </div>
    </>
  );
}
