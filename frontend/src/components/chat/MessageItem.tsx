import { useState } from 'react';

import { MarkdownMessage } from '@/components/chat/MarkdownMessage';
import { CheckIcon, CopyIcon } from '@/components/icons';
import { cx } from '@/lib/cx';
import type { Message } from '@/types/api';

function CopyMessageButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async (): Promise<void> => {
    try {
      await navigator.clipboard?.writeText(content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // ignore
    }
  };
  return (
    <button
      type="button"
      onClick={() => void copy()}
      aria-label={copied ? 'Copied message' : 'Copy message'}
      className="opacity-0 transition-opacity focus-visible:opacity-100 group-hover:opacity-100"
    >
      {copied ? <CheckIcon size={15} /> : <CopyIcon size={15} />}
    </button>
  );
}

export function MessageItem({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  return (
    <div className={cx('group flex w-full gap-3 py-3', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cx(
          'max-w-[80%] rounded-2xl px-4 py-2.5',
          isUser
            ? 'bg-accent text-white'
            : 'bg-panel text-gray-900 dark:bg-panel-dark dark:text-gray-100',
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
            {message.content}
          </p>
        ) : (
          <>
            <MarkdownMessage content={message.content} />
            <div className="mt-1 flex justify-end text-gray-400">
              <CopyMessageButton content={message.content} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
