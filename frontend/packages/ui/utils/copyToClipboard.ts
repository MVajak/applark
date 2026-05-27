import { toast } from 'sonner';

/**
 * Copy text to the clipboard and notify via toast. Shows the given
 * success label on success, and a generic error toast if the clipboard
 * API rejects (e.g. permissions blocked, insecure context).
 */
export async function copyToClipboard(text: string, successLabel = 'Copied'): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(successLabel);
  } catch {
    toast.error('Could not copy — clipboard permission may be blocked.');
  }
}
