import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import resourcesToBackend from 'i18next-resources-to-backend';
import { BRAND } from '@/branding';

// 按需加载 i18n namespace：Vite import.meta.glob 为每个 (lang, ns) 生成独立 chunk。
// 仅保留 pt（Português Brasil）与 en。
const loaders = import.meta.glob<{ default: Record<string, string> }>(
  './{en,pt}/*.ts',
);

function pathFor(lang: string, ns: string): string {
  return `./${lang}/${ns}.ts`;
}

export const SUPPORTED_LANGUAGES = ['pt', 'en'] as const;
export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number];

export const LANGUAGE_DISPLAY_LABELS: Record<SupportedLanguage, string> = {
  pt: 'Português (Brasil)',
  en: 'English',
};

export const I18N_NAMESPACES = [
  'common',
  'auth',
  'dashboard',
  'errors',
  'templates',
  'assets',
] as const;

// Replace every [[brand]] placeholder in a loaded namespace with the current
// brand name. Done inside the resourcesToBackend loader so it composes with
// on-demand chunk loading. We use [[...]] rather than i18next's native {{...}}
// so the value is not treated as a runtime variable.
function applyBrandPlaceholders(value: unknown): unknown {
  if (typeof value === 'string') {
    return value.replace(/\[\[\s*brand\s*\]\]/g, () => BRAND.name);
  }
  if (Array.isArray(value)) {
    return value.map(applyBrandPlaceholders);
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      out[k] = applyBrandPlaceholders(v);
    }
    return out;
  }
  return value;
}

// Normalize detector output (pt-BR, en-US, etc.) to a supported primary tag.
function normalizeLanguage(code: string | undefined): SupportedLanguage {
  if (!code) return 'pt';
  const primary = code.toLowerCase().replace('_', '-').split('-')[0];
  if (primary === 'pt' || primary === 'en') {
    return primary;
  }
  return 'pt';
}

// 返回 init Promise，调用方（main.tsx / test setup）await 后再 render，避免首屏闪 key。
export const i18nReady = i18n
  .use(
    resourcesToBackend(async (lang: string, ns: string) => {
      const normalized = normalizeLanguage(lang);
      const loader = loaders[pathFor(normalized, ns)];
      if (!loader) {
        console.warn(`i18n: no resource for ${pathFor(normalized, ns)}, falling back`);
        return {};
      }
      const mod = await loader();
      return applyBrandPlaceholders(mod.default) as Record<string, string>;
    }),
  )
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'pt',
    supportedLngs: [...SUPPORTED_LANGUAGES],
    nonExplicitSupportedLngs: true,
    load: 'languageOnly',
    debug: false,
    interpolation: { escapeValue: false },
    defaultNS: 'common',
    ns: I18N_NAMESPACES,
    partialBundledLanguages: true,
    react: { useSuspense: false },
    detection: {
      // Prefer saved choice, then browser; normalize to pt/en
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      convertDetectedLanguage: (lng: string) => normalizeLanguage(lng),
    },
  });

export default i18n;
