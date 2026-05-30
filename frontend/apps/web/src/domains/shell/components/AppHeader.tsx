import { Coins, LogOut, Sparkles, User } from 'lucide-react';
import { motion, useScroll, useTransform } from 'motion/react';
import { NavLink, useNavigate } from 'react-router-dom';

import { type TranslationKey, useTranslation } from '@applark/i18n';
import {
  Avatar,
  AvatarFallback,
  Badge,
  cn,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@applark/ui';

import { useAuthStore } from '@/domains/auth/store';
import { useCreditsModalStore } from '@/domains/billing/credits-modal-store';
import { useSubscription } from '@/domains/billing/hooks/useSubscription';
import { BrandMark } from '@/domains/shell/components/BrandMark';
import { useSpotlightStore } from '@/domains/shell/spotlight-store';
import { ThemeToggle } from '@/domains/theme/components/ThemeToggle';

type NavItem = { to: string; labelKey: TranslationKey };

const NAV: readonly NavItem[] = [
  { to: '/', labelKey: 'nav.home' },
  { to: '/jobs', labelKey: 'nav.jobs' },
  { to: '/cv', labelKey: 'nav.cvs' },
];

export function AppHeader() {
  const { t } = useTranslation();
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
                {t(item.labelKey)}
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
          aria-label={t('nav.openCommandPalette')}
        >
          <span>{t('nav.search')}</span>
          <kbd className="rounded bg-muted px-1.5 py-0.5 text-body-small text-muted-foreground">⌘K</kbd>
        </button>
        <BillingChip />
        <ThemeToggle />
        <UserMenu />
      </div>
    </motion.header>
  );
}

/**
 * Always-visible credit balance. Tapping it opens the buy-credits modal —
 * a one-click top-up for subscribers; free users get the modal's
 * subscribe-first prompt. (Upgrade lives in the avatar menu.)
 */
function BillingChip() {
  const { t } = useTranslation();
  const openCreditsModal = useCreditsModalStore((s) => s.open);
  const { credits, isLoading } = useSubscription();

  if (isLoading) return null;

  return (
    <button
      type="button"
      onClick={openCreditsModal}
      aria-label={t('billing.buyCredits')}
      className="flex items-center gap-1.5 rounded-lg border border-border/60 bg-background/40 px-2.5 py-1.5 text-body-small text-foreground outline-none transition-colors hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/50"
    >
      <Coins className="size-3.5 text-primary" />
      {t('billing.creditsChip', { count: credits })}
    </button>
  );
}

function UserMenu() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const openCreditsModal = useCreditsModalStore((s) => s.open);
  const { tier, credits, isSubscribed, isPremium } = useSubscription();

  const onLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label={t('nav.userMenu')}
        className="ml-1 rounded-full outline-none transition-transform hover:scale-105 focus-visible:ring-2 focus-visible:ring-ring/50"
      >
        <Avatar className="size-9">
          <AvatarFallback className="bg-gradient-to-br from-accent-indigo to-accent-pink text-primary-foreground">
            <User className="size-4" />
          </AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-52">
        <div className="flex items-center justify-between gap-3 px-2 py-1.5">
          <Badge variant={isSubscribed ? 'default' : 'outline'}>{t(`billing.tierName.${tier}`)}</Badge>
          <span className="flex items-center gap-1.5 text-body-small text-muted-foreground">
            <Coins className="size-3.5 text-primary" />
            {t('billing.creditsChip', { count: credits })}
          </span>
        </div>
        <DropdownMenuSeparator />
        {isSubscribed && (
          <DropdownMenuItem onSelect={openCreditsModal}>
            <Coins />
            {t('billing.buyCredits')}
          </DropdownMenuItem>
        )}
        <DropdownMenuItem onSelect={() => navigate('/billing')}>
          <Sparkles />
          {isPremium ? t('billing.managePlan') : t('billing.upgrade')}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={onLogout}>
          <LogOut />
          {t('nav.logOut')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
