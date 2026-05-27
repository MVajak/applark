/**
 * Capability flags for per-feature gating. Today every flag is true.
 * When auth lands, this hook will read from a user context that
 * resolves capabilities per signed-in user.
 *
 * Add a new flag here when introducing a new gateable feature, then
 * reference it in the relevant action card / route guard.
 */

export type Capabilities = {
  canRunMatch: boolean;
  canGenerateCoverLetter: boolean;
  canTailorCV: boolean;
  canGenerateInterviewPrep: boolean;
};

export const useCapabilities = (): Capabilities => ({
  canRunMatch: true,
  canGenerateCoverLetter: true,
  canTailorCV: true,
  canGenerateInterviewPrep: true,
});
