import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';

import { Notifications } from './Notifications';
import { useUiStore } from '@/stores/uiStore';

beforeEach(() => {
  useUiStore.setState({ notifications: [], settingsOpen: false });
});

describe('Notifications', () => {
  it('renders active notifications', () => {
    useUiStore.setState({ notifications: [{ id: '1', kind: 'error', message: 'Boom' }] });
    render(<Notifications />);
    expect(screen.getByText('Boom')).toBeInTheDocument();
  });

  it('dismisses a notification when its close button is clicked', async () => {
    useUiStore.setState({ notifications: [{ id: '1', kind: 'info', message: 'Hello' }] });
    render(<Notifications />);

    await userEvent.click(screen.getByLabelText('Dismiss notification'));

    expect(screen.queryByText('Hello')).not.toBeInTheDocument();
    expect(useUiStore.getState().notifications).toHaveLength(0);
  });
});
