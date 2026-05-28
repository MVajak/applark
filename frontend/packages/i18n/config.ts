import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import en from './locales/en/translation.json';

export const SUPPORTED_LANGUAGES = ['en'] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];
export type TranslationKey = import('i18next').ParseKeys;

// Type-safe keys: `t('...')` autocompletes against the English catalog and a
// non-existent key is a compile error. Kept in this module (rather than a loose
// .d.ts) so it's always part of the import graph wherever `@applark/i18n` is used.
declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'translation';
    resources: { translation: typeof en };
  }
}

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en } },
    fallbackLng: 'en',
    supportedLngs: [...SUPPORTED_LANGUAGES],
    interpolation: { escapeValue: false },
    detection: { caches: ['localStorage'] },
  });

export default i18n;
