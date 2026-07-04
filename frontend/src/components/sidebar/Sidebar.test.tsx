import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { Sidebar } from './Sidebar';
import { useChatStore } from '@/stores/chatStore';
import type { Conversation } from '@/types/api';

const selectConversation = vi.fn();
const newConversation = vi.fn();

function conversation(id: string, title: string): Conversation {
  return { id, title, archived: false, created_at: '', updated_at: '' };
}

beforeEach(() => {
  selectConversation.mockReset();
  newConversation.mockReset();
  useChatStore.setState({
    conversations: [conversation('a', 'Alpha chat'), conversation('b', 'Beta chat')],
    currentId: null,
    loadingConversations: false,
    selectConversation,
    newConversation,
  });
});

describe('Sidebar', () => {
  it('lists conversations', () => {
    render(<Sidebar />);
    expect(screen.getByText('Alpha chat')).toBeInTheDocument();
    expect(screen.getByText('Beta chat')).toBeInTheDocument();
  });

  it('filters conversations by search query', async () => {
    render(<Sidebar />);
    await userEvent.type(screen.getByLabelText('Search conversations'), 'alpha');
    expect(screen.getByText('Alpha chat')).toBeInTheDocument();
    expect(screen.queryByText('Beta chat')).not.toBeInTheDocument();
  });

  it('starts a new conversation', async () => {
    render(<Sidebar />);
    await userEvent.click(screen.getByRole('button', { name: /new chat/i }));
    expect(newConversation).toHaveBeenCalled();
  });

  it('selects a conversation when clicked', async () => {
    render(<Sidebar />);
    await userEvent.click(screen.getByText('Beta chat'));
    expect(selectConversation).toHaveBeenCalledWith('b');
  });
});
