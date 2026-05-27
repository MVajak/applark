import type { ComponentProps } from 'react';
import { Slot, Slottable } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '../utils/cn';

const buttonVariants = cva(
  'inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 whitespace-nowrap rounded-full text-body-default-bold outline-none transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 [&_svg:not([class*="size-"])]:size-4 [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'border border-border bg-background text-foreground hover:bg-accent',
        ghost: 'border-border bg-transparent text-foreground hover:bg-accent',
        link: 'text-foreground underline-offset-4 hover:underline',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        gradient:
          'bg-[length:200%_auto] bg-gradient-to-r from-accent-indigo via-accent-pink to-accent-indigo text-primary-foreground shadow-md hover:bg-[position:100%] hover:shadow-lg',
      },
      size: {
        xs: 'h-7 gap-1 px-3 text-body-small-bold [&_svg:not([class*="size-"])]:size-3',
        sm: 'h-9 px-4',
        md: 'h-10 px-4',
        lg: 'h-11 px-8',
        icon: 'size-10',
        'icon-sm': 'size-9',
        'icon-lg': 'size-11',
      },
      loading: {
        true: 'opacity-50',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps extends ComponentProps<'button'>, VariantProps<typeof buttonVariants> {
  loading?: boolean;
  asChild?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
}

export { buttonVariants };

export const Button = ({
  variant,
  size,
  loading = false,
  iconLeft,
  iconRight,
  asChild = false,
  children,
  className,
  ...props
}: ButtonProps) => {
  const Component = asChild ? Slot : 'button';

  return (
    <Component
      data-slot="button"
      className={cn(
        buttonVariants({
          variant,
          size,
          loading,
        }),
        className
      )}
      {...props}
    >
      {iconLeft}
      <Slottable>{children}</Slottable>
      {iconRight}
    </Component>
  );
};
