import type { ComponentProps, ReactNode } from 'react';

import { Button, Tooltip, TooltipContent, TooltipTrigger } from '@applark/ui';

type DisabledButtonProps = Omit<ComponentProps<typeof Button>, 'disabled' | 'children'> & {
  label: ReactNode;
  hint: ReactNode;
};

/**
 * A `<Button disabled>` wrapped in a focusable `<span>` so its Tooltip
 * still fires on hover / focus. Disabled buttons don't dispatch pointer
 * or focus events natively, so the span is required.
 */
export function DisabledButtonWithTooltip({ label, hint, ...buttonProps }: DisabledButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        {/* biome-ignore lint/a11y/noNoninteractiveTabindex: focusable span lets the tooltip fire on a disabled <Button>, which natively swallows pointer/focus events */}
        <span tabIndex={0}>
          <Button disabled {...buttonProps}>
            {label}
          </Button>
        </span>
      </TooltipTrigger>
      <TooltipContent>{hint}</TooltipContent>
    </Tooltip>
  );
}
