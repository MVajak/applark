import { useEffect } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';

import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@applark/ui';

import { useSpotlightStore } from '@/domains/shell/spotlight-store';
import { type Theme, useThemeStore } from '@/domains/theme/store';

export function Spotlight() {
  const isOpen = useSpotlightStore((s) => s.isOpen);
  const close = useSpotlightStore((s) => s.close);
  const navigate = useNavigate();
  const setTheme = useThemeStore((s) => s.setTheme);

  useEffect(() => {
    if (!isOpen) return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen]);

  const go = (to: string) => () => {
    close();
    navigate(to);
  };

  const pickTheme = (theme: Theme) => () => {
    close();
    setTheme(theme);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[60] bg-background/60 backdrop-blur-sm"
            onClick={close}
          />
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.98 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="fixed top-[15%] left-1/2 z-[60] w-full max-w-xl -translate-x-1/2 px-4"
          >
            <Command
              loop
              className="overflow-hidden rounded-2xl border border-border/50 bg-card shadow-2xl backdrop-blur-xl"
            >
              <CommandInput placeholder="Type a command or search…" />
              <CommandList>
                <CommandEmpty>No results found.</CommandEmpty>
                <CommandGroup heading="Navigate">
                  <CommandItem onSelect={go('/')}>Home</CommandItem>
                  <CommandItem onSelect={go('/jobs')}>Jobs</CommandItem>
                  <CommandItem onSelect={go('/cv')}>CVs</CommandItem>
                </CommandGroup>
                <CommandGroup heading="Create">
                  <CommandItem onSelect={go('/jobs?new=url')}>Add job from URL</CommandItem>
                  <CommandItem onSelect={go('/jobs?new=text')}>Add job from text</CommandItem>
                  <CommandItem onSelect={go('/cv')}>Upload CV</CommandItem>
                </CommandGroup>
                <CommandGroup heading="Theme">
                  <CommandItem onSelect={pickTheme('light')}>Light</CommandItem>
                  <CommandItem onSelect={pickTheme('dark')}>Dark</CommandItem>
                  <CommandItem onSelect={pickTheme('system')}>System</CommandItem>
                </CommandGroup>
              </CommandList>
            </Command>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
