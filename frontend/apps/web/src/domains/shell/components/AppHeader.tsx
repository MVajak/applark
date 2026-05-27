import { motion, useScroll, useTransform } from 'motion/react';
import { NavLink } from 'react-router-dom';

import { cn } from '@applark/ui';

import { BrandMark } from '@/domains/shell/components/BrandMark';
import { useSpotlightStore } from '@/domains/shell/spotlight-store';
import { ThemeToggle } from '@/domains/theme/components/ThemeToggle';

type NavItem = { to: string; label: string };

const NAV: readonly NavItem[] = [
  { to: '/', label: 'Home' },
  { to: '/jobs', label: 'Jobs' },
  { to: '/cv', label: 'CVs' },
];

export function AppHeader() {
  const { scrollY } = useScroll();
  const shadow = useTransform(scrollY, [0, 32], ['0 0 0 rgba(0,0,0,0)', '0 8px 32px rgba(0,0,0,0.08)']);
  const openSpotlight = useSpotlightStore((s) => s.open);

  return (
    <motion.header
      style={{ boxShadow: shadow }}
      className="glass fixed inset-x-3 top-3 z-50 flex h-14 items-center gap-3 rounded-2xl border border-border/60 px-3 backdrop-blur-xl sm:inset-x-6 sm:top-4 sm:h-16 sm:gap-4 sm:px-4"
    >
      <NavLink to="/" className="shrink-0 rounded-md px-1 outline-none focus-visible:ring-2 focus-visible:ring-ring/50">
        <BrandMark />
      </NavLink>

      <nav className="ml-2 flex items-center gap-1 sm:gap-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'relative rounded-lg px-3 py-1.5 text-body-default text-muted-foreground outline-none transition-colors',
                'hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50',
                isActive && 'text-foreground'
              )
            }
          >
            {({ isActive }) => (
              <>
                {item.label}
                {isActive && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-x-2 -bottom-0.5 h-0.5 rounded-full bg-gradient-to-r from-accent-indigo via-accent-pink to-accent-indigo"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="ml-auto flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => openSpotlight()}
          className="hidden items-center gap-2 rounded-lg border border-border/60 bg-background/40 px-2.5 py-1.5 text-body-small text-muted-foreground outline-none transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50 sm:flex"
          aria-label="Open command palette"
        >
          <span>Search</span>
          <kbd className="rounded bg-muted px-1.5 py-0.5 text-body-small text-muted-foreground">⌘K</kbd>
        </button>
        <ThemeToggle />
        <UserMenuPlaceholder />
      </div>
    </motion.header>
  );
}

function UserMenuPlaceholder() {
  return (
    <button
      type="button"
      aria-label="User menu (coming soon)"
      title="User menu (coming soon)"
      className="ml-1 inline-flex size-9 items-center justify-center rounded-full bg-gradient-to-br from-accent-indigo to-accent-pink text-body-small-bold text-primary-foreground outline-none transition-transform hover:scale-105 focus-visible:ring-2 focus-visible:ring-ring/50"
    >
      M
    </button>
  );
}
