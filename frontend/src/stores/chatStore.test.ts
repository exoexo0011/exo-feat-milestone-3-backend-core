import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { StreamCallbacks } from '@/api/chatSocket';
import type { ChatSocketRequest, Message } from '@/types/api';

vi.mock('@/api/client', () => ({
  ApiError: class ApiError extends Error {
    status = 0;
  },
  api: {
    createConversation: vi.fn(),
    listConversations: vi.fn().mockResolvedValue([]),
    listMessages: vi.fn().mockResolvedValue([]),
    sendMessage: vi.fn(),
  },
}));

vi.mock('@/api/chatSocket', () => ({
  streamChat: vi.fn(),
}));

import { streamChat } from '@/api/chatSocket';
import { useChatStore } from './chatStore';

function resetStore(): void {
  useChatStore.setState({
    conversations: [],
    currentId: 'conv-1',
    messages: [],
    streaming: { active: false, content: '', conversationId: null },
    toolActivity: null,
    sending: false,
  });
}

const streamMock = vi.mocked(streamChat);

beforeEach(() => {
  vi.clearAllMocks();
  resetStore();
});

describe('chatStore.sendMessage', () => {
  it('appends the user message and the streamed assistant reply', async () => {
    streamMock.mockImplementation((request: ChatSocketRequest, callbacks: StreamCallbacks) => {
      callbacks.onToken('Hel');
      callbacks.onToken('lo');
      const message: Message = {
        id: 'assistant-1',
        conversation_id: request.conversation_id,
        role: 'assistant',
        content: 'Hello',
        meta: null,
        token_count: null,
        created_at: '',
      };
      callbacks.onDone({
        type: 'done',
        message,
        provider: 'echo',
        model: null,
        finish_reason: 'stop',
      });
      return { cancel: vi.fn() };
    });

    await useChatStore.getState().sendMessage('hi there');

    const { messages, streaming, sending } = useChatStore.getState();
    expect(messages.map((m) => [m.role, m.content])).toEqual([
      ['user', 'hi there'],
      ['assistant', 'Hello'],
    ]);
    expect(streaming.active).toBe(false);
    expect(sending).toBe(false);
  });

  it('ignores empty content', async () => {
    await useChatStore.getState().sendMessage('   ');
    expect(streamMock).not.toHaveBeenCalled();
    expect(useChatStore.getState().messages).toHaveLength(0);
  });

  it('surfaces stream errors and clears the streaming state', async () => {
    streamMock.mockImplementation((_request: ChatSocketRequest, callbacks: StreamCallbacks) => {
      callbacks.onError('boom');
      return { cancel: vi.fn() };
    });

    await useChatStore.getState().sendMessage('hi');

    const { streaming, sending, messages } = useChatStore.getState();
    expect(streaming.active).toBe(false);
    expect(sending).toBe(false);
    // The optimistic user message remains.
    expect(messages).toHaveLength(1);
  });
});
