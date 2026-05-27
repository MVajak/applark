import { cn } from '@applark/ui';

type Variant = 'icon' | 'wordmark' | 'full';

export function BrandMark({ variant = 'full', className }: { variant?: Variant; className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      {(variant === 'icon' || variant === 'full') && <BrandIcon />}
      {(variant === 'wordmark' || variant === 'full') && (
        <span className="text-title-small-bold tracking-tight">Applark</span>
      )}
    </span>
  );
}

function BrandIcon() {
  return (
    <svg viewBox="0 0 24 24" className="size-6" aria-hidden role="img">
      <title>Applark</title>
      <defs>
        <linearGradient id="applark-brand" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="var(--color-accent-indigo)" />
          <stop offset="55%" stopColor="var(--color-accent-pink)" />
          <stop offset="100%" stopColor="var(--color-accent-indigo)" />
        </linearGradient>
      </defs>
      <path d="M12 2 L20 12 L12 22 L4 12 Z" fill="url(#applark-brand)" opacity="0.9" />
      <path d="M12 7 L15 12 L12 17 L9 12 Z" fill="var(--color-background)" opacity="0.85" />
    </svg>
  );
}
