import { beforeEach, describe, expect, it } from 'vitest';

import { useSettingsStore } from './settingsStore';

beforeEach(() => {
  useSettingsStore.setState({ theme: 'system', sendOnEnter: true });
});

describe('settingsStore', () => {
  it('updates the theme preference', () => {
    useSettingsStore.getState().setTheme('dark');
    expect(useSettingsStore.getState().theme).toBe('dark');
  });

  it('toggles send-on-enter', () => {
    useSettingsStore.getState().setSendOnEnter(false);
    expect(useSettingsStore.getState().sendOnEnter).toBe(false);
  });
});
