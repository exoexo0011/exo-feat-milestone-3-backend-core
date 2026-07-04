// Typed REST client for the EXO backend. Uses relative URLs so the Vite dev
// proxy (and the packaged app) route to the local FastAPI server.

import type { ChatResponse, Conversation, Message, ToolSpec } from '@/types/api';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
  } catch (cause) {
    throw new ApiError(0, `Cannot reach the backend: ${(cause as Error).message}`);
  }

  if (!response.ok) {
    const detail = await extractDetail(response);
    throw new ApiError(response.status, detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function extractDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === 'string') {
      return body.detail;
    }
    return JSON.stringify(body.detail ?? body);
  } catch {
    return response.statusText || `Request failed (${response.status})`;
  }
}

export const api = {
  health(): Promise<{ status: string; version: string; env: string }> {
    return request('/health');
  },

  listConversations(includeArchived = false): Promise<Conversation[]> {
    return request(`/chat/conversations?include_archived=${includeArchived}`);
  },

  createConversation(title = 'New chat'): Promise<Conversation> {
    return request('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  },

  listMessages(conversationId: string): Promise<Message[]> {
    return request(`/chat/conversations/${encodeURIComponent(conversationId)}/messages`);
  },

  sendMessage(conversationId: string, content: string): Promise<ChatResponse> {
    return request(`/chat/conversations/${encodeURIComponent(conversationId)}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },

  listTools(): Promise<ToolSpec[]> {
    return request('/tools');
  },
};
