// Applies the persisted theme preference to the document root and reacts to
// OS theme changes when the preference is 'system'.

import { useEffect } from 'react';

import { useSettingsStore, type ThemePreference } from '@/stores/settingsStore';

function resolve(theme: ThemePreference): 'light' | 'dark' {
  if (theme === 'system') {
    const prefersDark =
      typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? 'dark' : 'light';
  }
  return theme;
}

function apply(theme: ThemePreference): void {
  const root = document.documentElement;
  root.classList.toggle('dark', resolve(theme) === 'dark');
}

export function useTheme(): void {
  const theme = useSettingsStore((state) => state.theme);

  useEffect(() => {
    apply(theme);
    if (theme !== 'system') {
      return;
    }
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const listener = () => apply('system');
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [theme]);
}
