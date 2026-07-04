import { useMemo, useState } from 'react';

import { Button } from '@/components/common/Button';
import { Spinner } from '@/components/common/Spinner';
import { PlusIcon, SearchIcon, SettingsIcon } from '@/components/icons';
import { cx } from '@/lib/cx';
import { useChatStore } from '@/stores/chatStore';
import { useUiStore } from '@/stores/uiStore';

export function Sidebar() {
  const conversations = useChatStore((s) => s.conversations);
  const currentId = useChatStore((s) => s.currentId);
  const loading = useChatStore((s) => s.loadingConversations);
  const selectConversation = useChatStore((s) => s.selectConversation);
  const newConversation = useChatStore((s) => s.newConversation);
  const openSettings = useUiStore((s) => s.openSettings);

  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return conversations;
    return conversations.filter((c) => c.title.toLowerCase().includes(q));
  }, [conversations, query]);

  return (
    <nav
      aria-label="Conversations"
      className="flex h-full w-72 flex-col border-r border-gray-200 bg-panel dark:border-white/10 dark:bg-panel-dark"
    >
      <div className="flex items-center justify-between px-4 py-4">
        <span className="text-lg font-bold text-accent">EXO</span>
        <Button variant="ghost" onClick={newConversation} className="px-3 py-1.5">
          <PlusIcon size={16} />
          New chat
        </Button>
      </div>

      <div className="px-3 pb-2">
        <div className="relative">
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <SearchIcon size={16} />
          </span>
          <input
            id="conversation-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search conversations"
            aria-label="Search conversations"
            className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-accent focus:outline-none dark:border-white/10 dark:bg-surface-dark dark:text-gray-100"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-1" role="list">
        {loading && conversations.length === 0 ? (
          <div className="flex justify-center py-6 text-gray-400">
            <Spinner label="Loading conversations" />
          </div>
        ) : filtered.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-gray-400">
            {query ? 'No matches' : 'No conversations yet'}
          </p>
        ) : (
          filtered.map((conversation) => {
            const active = conversation.id === currentId;
            return (
              <button
                key={conversation.id}
                type="button"
                role="listitem"
                aria-current={active ? 'true' : undefined}
                onClick={() => void selectConversation(conversation.id)}
                className={cx(
                  'mb-1 w-full truncate rounded-lg px-3 py-2 text-left text-sm transition-colors',
                  active
                    ? 'bg-accent/15 text-accent'
                    : 'text-gray-700 hover:bg-gray-200 dark:text-gray-200 dark:hover:bg-white/5',
                )}
                title={conversation.title}
              >
                {conversation.title}
              </button>
            );
          })
        )}
      </div>

      <div className="border-t border-gray-200 p-2 dark:border-white/10">
        <Button
          variant="ghost"
          onClick={openSettings}
          className="w-full justify-start"
          aria-label="Open settings"
        >
          <SettingsIcon size={18} />
          Settings
        </Button>
      </div>
    </nav>
  );
}
