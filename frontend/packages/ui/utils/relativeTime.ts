const MIN = 60;
const HOUR = 60 * MIN;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;

export function relativeTime(value: string | Date): string {
  const date = typeof value === 'string' ? new Date(value) : value;
  const seconds = Math.max(0, (Date.now() - date.getTime()) / 1000);

  if (seconds < 10) return 'just now';
  if (seconds < MIN) return `${Math.floor(seconds)}s ago`;
  if (seconds < HOUR) return `${Math.floor(seconds / MIN)}m ago`;
  if (seconds < DAY) return `${Math.floor(seconds / HOUR)}h ago`;
  if (seconds < MONTH) return `${Math.floor(seconds / DAY)}d ago`;
  return date.toLocaleDateString();
}
