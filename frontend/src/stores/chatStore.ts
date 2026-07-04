// Chat state: conversations, the active message list, and streaming.
//
// Streaming is driven by the WebSocket client; the live assistant text lives in
// `streaming` until the server sends the persisted message on completion.

import { create } from 'zustand';

import { api, ApiError } from '@/api/client';
import { streamChat, type StreamHandle } from '@/api/chatSocket';
import { useUiStore } from '@/stores/uiStore';
import type { Conversation, Message } from '@/types/api';

interface StreamingState {
  active: boolean;
  content: string;
  conversationId: string | null;
}

interface ToolActivity {
  tool: string;
  status: 'running' | 'completed' | 'failed';
}

interface ChatState {
  conversations: Conversation[];
  currentId: string | null;
  messages: Message[];
  streaming: StreamingState;
  toolActivity: ToolActivity | null;
  loadingConversations: boolean;
  loadingMessages: boolean;
  sending: boolean;

  init: () => Promise<void>;
  loadConversations: () => Promise<void>;
  selectConversation: (id: string) => Promise<void>;
  newConversation: () => void;
  sendMessage: (content: string) => Promise<void>;
  cancelStreaming: () => void;
}

const IDLE_STREAM: StreamingState = { active: false, content: '', conversationId: null };

// Kept outside the store: a live socket handle is not serialisable state.
let activeHandle: StreamHandle | null = null;

function tempMessage(conversationId: string, content: string): Message {
  return {
    id: `temp-${Date.now()}`,
    conversation_id: conversationId,
    role: 'user',
    content,
    meta: null,
    token_count: null,
    created_at: new Date().toISOString(),
  };
}

function deriveTitle(content: string): string {
  const trimmed = content.trim().replace(/\s+/g, ' ');
  return trimmed.length > 48 ? `${trimmed.slice(0, 48)}…` : trimmed || 'New chat';
}

function notifyError(error: unknown): void {
  const message =
    error instanceof ApiError ? error.message : 'Something went wrong. Please try again.';
  useUiStore.getState().notify('error', message);
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentId: null,
  messages: [],
  streaming: IDLE_STREAM,
  toolActivity: null,
  loadingConversations: false,
  loadingMessages: false,
  sending: false,

  async init() {
    await get().loadConversations();
    const [first] = get().conversations;
    if (first) {
      await get().selectConversation(first.id);
    }
  },

  async loadConversations() {
    set({ loadingConversations: true });
    try {
      const conversations = await api.listConversations();
      set({ conversations });
    } catch (error) {
      notifyError(error);
    } finally {
      set({ loadingConversations: false });
    }
  },

  async selectConversation(id) {
    if (get().streaming.active) {
      get().cancelStreaming();
    }
    set({ currentId: id, loadingMessages: true, messages: [] });
    try {
      const messages = await api.listMessages(id);
      // Guard against races if the user switched again mid-load.
      if (get().currentId === id) {
        set({ messages });
      }
    } catch (error) {
      notifyError(error);
    } finally {
      if (get().currentId === id) {
        set({ loadingMessages: false });
      }
    }
  },

  newConversation() {
    if (get().streaming.active) {
      get().cancelStreaming();
    }
    set({ currentId: null, messages: [] });
  },

  async sendMessage(rawContent) {
    const content = rawContent.trim();
    if (!content || get().sending) {
      return;
    }

    let conversationId = get().currentId;
    if (!conversationId) {
      try {
        const conversation = await api.createConversation(deriveTitle(content));
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          currentId: conversation.id,
          messages: [],
        }));
        conversationId = conversation.id;
      } catch (error) {
        notifyError(error);
        return;
      }
    }

    const targetId = conversationId;
    set((state) => ({
      messages: [...state.messages, tempMessage(targetId, content)],
      streaming: { active: true, content: '', conversationId: targetId },
      toolActivity: null,
      sending: true,
    }));

    activeHandle = streamChat(
      { conversation_id: targetId, content },
      {
        onToken: (delta) => {
          set((state) => ({
            streaming: { ...state.streaming, content: state.streaming.content + delta },
          }));
        },
        onTool: (event) => {
          set({ toolActivity: { tool: event.tool, status: event.status } });
        },
        onDone: (event) => {
          activeHandle = null;
          set((state) => ({
            messages:
              state.streaming.conversationId === state.currentId
                ? [...state.messages, event.message]
                : state.messages,
            streaming: IDLE_STREAM,
            toolActivity: null,
            sending: false,
          }));
          void get().loadConversations();
        },
        onError: (detail) => {
          activeHandle = null;
          useUiStore.getState().notify('error', detail);
          set({ streaming: IDLE_STREAM, toolActivity: null, sending: false });
        },
      },
    );
  },

  cancelStreaming() {
    activeHandle?.cancel();
    activeHandle = null;
    set({ streaming: IDLE_STREAM, toolActivity: null, sending: false });
  },
}));
