import { useEffect, useRef } from 'react';

import { MarkdownMessage } from '@/components/chat/MarkdownMessage';
import { MessageItem } from '@/components/chat/MessageItem';
import { ToolIndicator } from '@/components/chat/ToolIndicator';
import { Spinner } from '@/components/common/Spinner';
import { useChatStore } from '@/stores/chatStore';

function TypingIndicator() {
  return (
    <div className="flex gap-1 py-2" aria-label="Assistant is typing">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="h-2 w-2 animate-bounce rounded-full bg-gray-400"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  );
}

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const streaming = useChatStore((s) => s.streaming);
  const currentId = useChatStore((s) => s.currentId);
  const toolActivity = useChatStore((s) => s.toolActivity);
  const loading = useChatStore((s) => s.loadingMessages);

  const bottomRef = useRef<HTMLDivElement>(null);
  const isStreamingHere = streaming.active && streaming.conversationId === currentId;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, streaming.content, isStreamingHere]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400">
        <Spinner label="Loading messages" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto" role="log" aria-live="polite" aria-label="Messages">
      <div className="mx-auto flex max-w-3xl flex-col px-4 py-4">
        {messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}

        {isStreamingHere && (
          <div className="flex w-full justify-start py-3">
            <div className="max-w-[80%] rounded-2xl bg-panel px-4 py-2.5 dark:bg-panel-dark">
              {toolActivity && (
                <ToolIndicator tool={toolActivity.tool} status={toolActivity.status} />
              )}
              {streaming.content ? (
                <MarkdownMessage content={streaming.content} />
              ) : (
                <TypingIndicator />
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
