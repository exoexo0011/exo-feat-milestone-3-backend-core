import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { MessageInput } from './MessageInput';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';

const sendMessage = vi.fn();
const cancelStreaming = vi.fn();

beforeEach(() => {
  sendMessage.mockReset();
  useChatStore.setState({ sendMessage, cancelStreaming, sending: false });
  useSettingsStore.setState({ sendOnEnter: true });
});

describe('MessageInput', () => {
  it('sends the typed message on Enter', async () => {
    render(<MessageInput />);
    const textarea = screen.getByLabelText('Message');
    await userEvent.type(textarea, 'hello world');
    await userEvent.keyboard('{Enter}');
    expect(sendMessage).toHaveBeenCalledWith('hello world');
  });

  it('does not send when the input is empty', async () => {
    render(<MessageInput />);
    await userEvent.type(screen.getByLabelText('Message'), '{Enter}');
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('inserts a newline instead of sending on Shift+Enter', async () => {
    render(<MessageInput />);
    const textarea = screen.getByLabelText('Message');
    await userEvent.type(textarea, 'line one');
    await userEvent.keyboard('{Shift>}{Enter}{/Shift}');
    expect(sendMessage).not.toHaveBeenCalled();
  });

  it('shows a stop button while streaming', () => {
    useChatStore.setState({ sending: true });
    render(<MessageInput />);
    expect(screen.getByLabelText('Stop generating')).toBeInTheDocument();
  });
});
