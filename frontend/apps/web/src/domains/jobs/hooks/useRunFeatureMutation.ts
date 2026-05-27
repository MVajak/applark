import { type QueryKey, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { getErrorDetail } from '@/domains/api/client';

/**
 * Build the shared `{ mutation: { onSuccess, onError } }` config that
 * the three feature buttons (CoverLetter / CVTailor / InterviewPrep)
 * all use. Pass the result straight into the orval-generated mutation
 * hook.
 *
 * `onSuccess` invalidates the given query key and fires a success toast.
 * `onError` reports the FastAPI `detail` field or `errorFallback`.
 */
export function useFeatureMutationOptions({
  invalidateKey,
  successMessage,
  errorFallback,
}: {
  invalidateKey: QueryKey;
  successMessage: string;
  errorFallback: string;
}) {
  const queryClient = useQueryClient();
  return {
    mutation: {
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
