// WebSocket streaming client for /ws/chat.
//
// Opens a per-turn connection, sends the request, and dispatches typed events
// to the provided callbacks. The socket URL is derived from the current origin
// so it works behind the Vite proxy and in the packaged app.

import type { ChatServerEvent, ChatSocketRequest } from '@/types/api';

export interface StreamCallbacks {
  onToken: (delta: string) => void;
  onDone: (event: Extract<ChatServerEvent, { type: 'done' }>) => void;
  onError: (detail: string) => void;
  onTool?: (event: Extract<ChatServerEvent, { type: 'tool' }>) => void;
}

export interface StreamHandle {
  /** Close the socket early (e.g. the user cancels generation). */
  cancel(): void;
}

function socketUrl(): string {
  // In tests/SSR `window` may be absent; guard defensively.
  if (typeof window === 'undefined') {
    return 'ws://127.0.0.1:8000/ws/chat';
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/chat`;
}

/**
 * Stream one assistant turn. Returns a handle to cancel the stream.
 * `WebSocketCtor` is injectable for testing.
 */
export function streamChat(
  request: ChatSocketRequest,
  callbacks: StreamCallbacks,
  WebSocketCtor: typeof WebSocket = WebSocket,
): StreamHandle {
  const socket = new WebSocketCtor(socketUrl());
  let settled = false;

  const finish = () => {
    settled = true;
    if (socket.readyState === socket.OPEN || socket.readyState === socket.CONNECTING) {
      socket.close();
    }
  };

  socket.onopen = () => {
    socket.send(JSON.stringify(request));
  };

  socket.onmessage = (event: MessageEvent<string>) => {
    let parsed: ChatServerEvent;
    try {
      parsed = JSON.parse(event.data) as ChatServerEvent;
    } catch {
      callbacks.onError('Received a malformed message from the server.');
      finish();
      return;
    }
    switch (parsed.type) {
      case 'token':
        callbacks.onToken(parsed.delta);
        break;
      case 'tool':
        callbacks.onTool?.(parsed);
        break;
      case 'done':
        callbacks.onDone(parsed);
        finish();
        break;
      case 'error':
        callbacks.onError(parsed.detail);
        finish();
        break;
    }
  };

  socket.onerror = () => {
    if (!settled) {
      callbacks.onError('The connection to the backend failed.');
    }
  };

  socket.onclose = () => {
    if (!settled) {
      callbacks.onError('The connection closed before the response completed.');
      settled = true;
    }
  };

  return {
    cancel() {
      if (!settled) {
        settled = true;
        socket.close();
      }
    },
  };
}
