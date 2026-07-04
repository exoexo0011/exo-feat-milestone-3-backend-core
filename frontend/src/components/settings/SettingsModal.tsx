import { useEffect, useRef } from 'react';

import { IconButton } from '@/components/common/IconButton';
import { MonitorIcon, MoonIcon, SunIcon, XIcon } from '@/components/icons';
import { cx } from '@/lib/cx';
import { useSettingsStore, type ThemePreference } from '@/stores/settingsStore';
import { useUiStore } from '@/stores/uiStore';

const THEMES: Array<{ value: ThemePreference; label: string; Icon: typeof SunIcon }> = [
  { value: 'light', label: 'Light', Icon: SunIcon },
  { value: 'dark', label: 'Dark', Icon: MoonIcon },
  { value: 'system', label: 'System', Icon: MonitorIcon },
];

export function SettingsModal() {
  const open = useUiStore((s) => s.settingsOpen);
  const close = useUiStore((s) => s.closeSettings);
  const theme = useSettingsStore((s) => s.theme);
  const setTheme = useSettingsStore((s) => s.setTheme);
  const sendOnEnter = useSettingsStore((s) => s.sendOnEnter);
  const setSendOnEnter = useSettingsStore((s) => s.setSendOnEnter);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      dialogRef.current?.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4"
      onClick={close}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-2xl outline-none dark:bg-panel-dark"
      >
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Settings</h2>
          <IconButton label="Close settings" onClick={close}>
            <XIcon size={18} />
          </IconButton>
        </div>

        <section className="mb-6">
          <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Theme</h3>
          <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Theme">
            {THEMES.map(({ value, label, Icon }) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={theme === value}
                onClick={() => setTheme(value)}
                className={cx(
                  'flex flex-col items-center gap-2 rounded-lg border p-3 text-sm transition-colors',
                  theme === value
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-gray-200 text-gray-600 hover:bg-gray-100 dark:border-white/10 dark:text-gray-300 dark:hover:bg-white/5',
                )}
              >
                <Icon size={20} />
                {label}
              </button>
            ))}
          </div>
        </section>

        <section>
          <label className="flex items-center justify-between text-sm text-gray-700 dark:text-gray-300">
            <span>Send message on Enter</span>
            <input
              type="checkbox"
              checked={sendOnEnter}
              onChange={(e) => setSendOnEnter(e.target.checked)}
              className="h-4 w-4 accent-accent"
            />
          </label>
          <p className="mt-1 text-xs text-gray-400">
            When off, use Ctrl/Cmd+Enter to send and Enter for a new line.
          </p>
        </section>
      </div>
    </div>
  );
}
