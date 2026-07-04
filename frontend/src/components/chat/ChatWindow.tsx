import { MessageInput } from '@/components/chat/MessageInput';
import { MessageList } from '@/components/chat/MessageList';
import { useChatStore } from '@/stores/chatStore';

function EmptyState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 text-center">
      <h1 className="mb-2 text-2xl font-bold text-accent">EXO</h1>
      <p className="max-w-sm text-sm text-gray-500 dark:text-gray-400">
        Your local AI desktop assistant. Ask a question, paste some code, or drop in a file to get
        started.
      </p>
    </div>
  );
}

export function ChatWindow() {
  const currentId = useChatStore((s) => s.currentId);
  const messages = useChatStore((s) => s.messages);
  const conversations = useChatStore((s) => s.conversations);
  const streaming = useChatStore((s) => s.streaming);

  const title = conversations.find((c) => c.id === currentId)?.title ?? 'New chat';
  const showEmpty = messages.length === 0 && !streaming.active;

  return (
    <main className="flex h-full flex-1 flex-col bg-surface dark:bg-surface-dark">
      <header className="flex h-14 shrink-0 items-center border-b border-gray-200 px-6 dark:border-white/10">
        <h2 className="truncate text-sm font-medium text-gray-700 dark:text-gray-200">{title}</h2>
      </header>
      {showEmpty ? <EmptyState /> : <MessageList />}
      <MessageInput />
    </main>
  );
}
