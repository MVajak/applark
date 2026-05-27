import { type QueryKey, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getErrorDetail } from '@/domains/api/client';

/**
 * Build the shared `{ mutation: { onMutate, onSuccess, onError } }` config
 * that every AI feature (CoverLetter / CVTailor / InterviewPrep / Match)
 * runs through `FeatureSection`. Pass the result straight into the
 * orval-generated mutation hook.
 *
 * `onMutate` (optional) fires when the mutation starts — used to drive the
 * optimistic pending state. `onSuccess` invalidates the given query key and
 * fires a success toast. `onError` reports the FastAPI `detail` field or
 * `errorFallback`.
 */
export function useFeatureMutationOptions({
  invalidateKey,
  successMessage,
  errorFallback,
  onMutate,
}: {
  invalidateKey: QueryKey;
  successMessage: string;
  errorFallback: string;
  onMutate?: () => void;
}) {
  const queryClient = useQueryClient();
  return {
    mutation: {
      onMutate,
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: invalidateKey });
        toast.success(successMessage);
      },
      onError: (err: unknown) => {
        toast.error(getErrorDetail(err) ?? errorFallback);
      },
    },
  };
}
