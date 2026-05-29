// Locale-aware date/number formatting on top of the built-in `Intl` APIs.
// `Intl.*` constructors are expensive, so instances are memoized by locale (+ options).

const dateFormatters = new Map<string, Intl.DateTimeFormat>();
const numberFormatters = new Map<string, Intl.NumberFormat>();
const relativeFormatters = new Map<string, Intl.RelativeTimeFormat>();

function cacheKey(locale: string, opts: object | undefined): string {
  return opts ? `${locale}|${JSON.stringify(opts)}` : locale;
}

function dateFormatter(locale: string, opts: Intl.DateTimeFormatOptions): Intl.DateTimeFormat {
  const key = cacheKey(locale, opts);
  let formatter = dateFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat(locale, opts);
    dateFormatters.set(key, formatter);
  }
  return formatter;
}

function numberFormatter(locale: string, opts: Intl.NumberFormatOptions | undefined): Intl.NumberFormat {
  const key = cacheKey(locale, opts);
  let formatter = numberFormatters.get(key);
  if (!formatter) {
    formatter = new Intl.NumberFormat(locale, opts);
    numberFormatters.set(key, formatter);
  }
  return formatter;
}

function relativeFormatter(locale: string): Intl.RelativeTimeFormat {
  let formatter = relativeFormatters.get(locale);
  if (!formatter) {
    formatter = new Intl.RelativeTimeFormat(locale, { numeric: 'auto', style: 'short' });
    relativeFormatters.set(locale, formatter);
  }
  return formatter;
}

function toDate(value: string | Date): Date {
  return typeof value === 'string' ? new Date(value) : value;
}

export function formatDate(
  value: string | Date,
  locale: string,
  opts: Intl.DateTimeFormatOptions = { dateStyle: 'medium' }
): string {
  return dateFormatter(locale, opts).format(toDate(value));
}

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const RELATIVE_CUTOFF = 30 * DAY;

/** "5 min ago" / "yesterday" within ~30 days, then an absolute medium date. */
export function formatRelativeTime(value: string | Date, locale: string): string {
  const date = toDate(value);
  const deltaSeconds = (date.getTime() - Date.now()) / 1000; // negative = past
  const abs = Math.abs(deltaSeconds);

  if (abs >= RELATIVE_CUTOFF) return formatDate(date, locale);

  const rtf = relativeFormatter(locale);
  if (abs < MINUTE) return rtf.format(Math.round(deltaSeconds), 'second');
  if (abs < HOUR) return rtf.format(Math.round(deltaSeconds / MINUTE), 'minute');
  if (abs < DAY) return rtf.format(Math.round(deltaSeconds / HOUR), 'hour');
  return rtf.format(Math.round(deltaSeconds / DAY), 'day');
}

export function formatNumber(value: number, locale: string, opts?: Intl.NumberFormatOptions): string {
  return numberFormatter(locale, opts).format(value);
}

/** `value` is a 0..1 fraction (0.42 → "42%"). */
export function formatPercent(value: number, locale: string, opts?: Intl.NumberFormatOptions): string {
  return formatNumber(value, locale, { style: 'percent', maximumFractionDigits: 0, ...opts });
}
