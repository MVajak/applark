import type { ComponentProps, HTMLAttributes } from 'react';
import { Command as CommandPrimitive } from 'cmdk';
import { Search } from 'lucide-react';

import { cn } from '../utils/cn';

const Command = ({ className, ...props }: ComponentProps<typeof CommandPrimitive>) => (
  <CommandPrimitive
    className={cn('flex h-full w-full flex-col overflow-hidden bg-transparent text-foreground', className)}
    {...props}
  />
);

const CommandInput = ({ className, ...props }: ComponentProps<typeof CommandPrimitive.Input>) => (
  <div className="flex items-center gap-3 border-border/50 border-b px-4" cmdk-input-wrapper="">
    <Search className="h-5 w-5 shrink-0 text-muted-foreground" />
    <CommandPrimitive.Input
      autoFocus
      className={cn(
        'flex h-14 w-full bg-transparent py-4 text-body-default outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  </div>
);

const CommandList = ({ className, ...props }: ComponentProps<typeof CommandPrimitive.List>) => (
  <CommandPrimitive.List className={cn('max-h-[320px] overflow-y-auto overflow-x-hidden p-2', className)} {...props} />
);

const CommandEmpty = (props: ComponentProps<typeof CommandPrimitive.Empty>) => (
  <CommandPrimitive.Empty className="py-8 text-center text-body-small text-muted-foreground" {...props} />
);

const CommandGroup = ({ className, ...props }: ComponentProps<typeof CommandPrimitive.Group>) => (
  <CommandPrimitive.Group
    className={cn(
      'overflow-hidden text-foreground [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-body-small [&_[cmdk-group-heading]]:text-muted-foreground',
      className
    )}
    {...props}
  />
);

const CommandSeparator = ({ className, ...props }: ComponentProps<typeof CommandPrimitive.Separator>) => (
  <CommandPrimitive.Separator className={cn('my-1 h-px bg-border/50', className)} {...props} />
);

const CommandItem = ({ className, ...props }: ComponentProps<typeof CommandPrimitive.Item>) => (
  <CommandPrimitive.Item
    className={cn(
      'relative flex cursor-pointer select-none items-center gap-3 rounded-xl px-3 py-3 text-body-default outline-none transition-colors',
      'data-[selected=true]:bg-accent/50 data-[selected=true]:text-foreground',
      'data-[disabled=true]:pointer-events-none data-[disabled=true]:opacity-50',
      '[&_svg]:h-5 [&_svg]:w-5 [&_svg]:shrink-0 [&_svg]:text-muted-foreground',
      'data-[selected=true]:[&_svg]:text-accent-foreground',
      className
    )}
    {...props}
  />
);

const CommandShortcut = ({ className, ...props }: HTMLAttributes<HTMLSpanElement>) => (
  <span
    className={cn('ml-auto rounded-md bg-muted/50 px-2 py-0.5 text-muted-foreground text-xs', className)}
    {...props}
  />
);

export {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
};
