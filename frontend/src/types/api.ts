// Shared API types mirroring the EXO backend contracts (app/schemas).

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface Conversation {
  id: string;
  title: string;
  archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  meta: Record<string, unknown> | null;
  token_count: number | null;
  created_at: string;
}

export interface Usage {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
}

export interface ChatResponse {
  message: Message;
  provider: string;
  model: string | null;
  finish_reason: string | null;
  usage: Usage | null;
}

export interface ToolSpec {
  name: string;
  description: string;
  requires_confirmation: boolean;
  permissions: string[];
  parameters: Record<string, unknown>;
}

// --- WebSocket streaming protocol (/ws/chat) --------------------------------

export interface ChatSocketRequest {
  conversation_id: string;
  content: string;
}

export interface TokenEvent {
  type: 'token';
  delta: string;
}

export interface DoneEvent {
  type: 'done';
  message: Message;
  provider: string;
  model: string | null;
  finish_reason: string | null;
}

export interface ErrorEvent {
  type: 'error';
  detail: string;
}

// A forward-compatible tool-status frame (not yet emitted by the backend;
// the UI renders it when the chat tool-calling loop lands).
export interface ToolEvent {
  type: 'tool';
  tool: string;
  status: 'running' | 'completed' | 'failed';
  detail?: string;
}

export type ChatServerEvent = TokenEvent | DoneEvent | ErrorEvent | ToolEvent;
