import { create } from 'zustand';

/**
 * Controls the global buy-credits modal so any surface — the header credits
 * pill, the billing page, an in-feature "not enough credits" prompt — can pop
 * it without prop-drilling. Mirrors the spotlight (⌘K) store pattern.
 */
interface CreditsModalState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}

export const useCreditsModalStore = create<CreditsModalState>((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));
