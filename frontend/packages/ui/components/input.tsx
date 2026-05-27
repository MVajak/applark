import type { ComponentProps } from 'react';

import { cn } from '../utils/cn';

export const Input = ({ className, ...props }: ComponentProps<'input'>) => {
  return (
    <input
      data-slot="input"
      className={cn(
        'w-full rounded-xl border border-border bg-background/50 px-4 py-3 text-body-default text-foreground placeholder:text-muted-foreground',
        'outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary',
        'aria-invalid:border-destructive aria-invalid:ring-1 aria-invalid:ring-destructive',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-body-small-bold file:text-foreground',
        className
      )}
      {...props}
    />
  );
};
