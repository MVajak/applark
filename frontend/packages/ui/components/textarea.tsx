import type { ComponentProps } from 'react';

import { cn } from '../utils/cn';

export const Textarea = ({ className, ...props }: ComponentProps<'textarea'>) => {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'field-sizing-content min-h-16 w-full resize-none rounded-xl border border-border bg-background/50 px-4 py-3 text-body-default text-foreground placeholder:text-muted-foreground',
        'outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary',
        'aria-invalid:border-destructive aria-invalid:ring-1 aria-invalid:ring-destructive',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  );
};
