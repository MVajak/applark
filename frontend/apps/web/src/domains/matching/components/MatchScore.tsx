import { cn } from '@applark/ui';

function bandColor(score: number): {
  stroke: string;
  text: string;
  label: string;
} {
  if (score >= 0.7)
    return {
      stroke: 'stroke-positive',
      text: 'text-positive',
      label: 'Strong fit',
    };
  if (score >= 0.4)
    return {
      stroke: 'stroke-warning',
      text: 'text-warning',
      label: 'Partial fit',
    };
  return {
    stroke: 'stroke-destructive',
    text: 'text-destructive',
    label: 'Weak fit',
  };
}

export function MatchScore({ score }: { score: number }) {
  const clamped = Math.max(0, Math.min(1, score));
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped);
  const band = bandColor(clamped);
  const percent = Math.round(clamped * 100);

  return (
    <div className="flex items-center gap-4">
      <div className="relative size-28">
        <svg className="size-full -rotate-90" viewBox="0 0 100 100" aria-hidden>
          <circle cx="50" cy="50" r={radius} className="fill-none stroke-muted" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r={radius}
            className={cn('fill-none transition-all', band.stroke)}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn('text-title-default-bold tabular-nums', band.text)}>{percent}%</span>
        </div>
      </div>
      <div>
        <div className={cn('font-medium', band.text)}>{band.label}</div>
        <div className="text-body-small text-muted-foreground">overall score</div>
      </div>
    </div>
  );
}
