import { useMemo } from 'react';

import { useTranslation } from '@applark/i18n';

import { formatDate, formatNumber, formatPercent, formatRelativeTime } from './intl';

/**
 * Formatters bound to the active i18n locale. Re-memoized when the language
 * changes so a future locale switch reformats everything automatically.
 */
export function useFormat() {
  const { i18n } = useTranslation();
  const locale = i18n.language;

  return useMemo(
    () => ({
      date: (value: string | Date, opts?: Intl.DateTimeFormatOptions) => formatDate(value, locale, opts),
      relativeTime: (value: string | Date) => formatRelativeTime(value, locale),
      number: (value: number, opts?: Intl.NumberFormatOptions) => formatNumber(value, locale, opts),
      percent: (value: number, opts?: Intl.NumberFormatOptions) => formatPercent(value, locale, opts),
    }),
    [locale]
  );
}
