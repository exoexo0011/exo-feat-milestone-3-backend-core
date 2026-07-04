import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';

import { SettingsModal } from './SettingsModal';
import { useSettingsStore } from '@/stores/settingsStore';
import { useUiStore } from '@/stores/uiStore';

beforeEach(() => {
  useUiStore.setState({ settingsOpen: true });
  useSettingsStore.setState({ theme: 'system', sendOnEnter: true });
});

describe('SettingsModal', () => {
  it('is hidden when closed', () => {
    useUiStore.setState({ settingsOpen: false });
    render(<SettingsModal />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('changes the theme when a theme option is selected', async () => {
    render(<SettingsModal />);
    await userEvent.click(screen.getByRole('radio', { name: 'Dark' }));
    expect(useSettingsStore.getState().theme).toBe('dark');
  });

  it('closes when the close button is clicked', async () => {
    render(<SettingsModal />);
    await userEvent.click(screen.getByLabelText('Close settings'));
    expect(useUiStore.getState().settingsOpen).toBe(false);
  });
});
