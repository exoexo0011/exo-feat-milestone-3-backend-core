import { useRef, useState, type ReactNode } from 'react';

import { CheckIcon, CopyIcon } from '@/components/icons';
import { cx } from '@/lib/cx';

interface CodeBlockProps {
  className?: string;
  children: ReactNode;
}

/**
 * A fenced code block with a copy-to-clipboard button. Highlighted markup
 * (from rehype-highlight) is preserved; the raw text for copying is read from
 * the rendered element so it always matches what the user sees.
 */
export function CodeBlock({ className, children }: CodeBlockProps) {
  const codeRef = useRef<HTMLElement>(null);
  const [copied, setCopied] = useState(false);
  const language = /language-(\w+)/.exec(className ?? '')?.[1];

  const copy = async (): Promise<void> => {
    const text = codeRef.current?.textContent ?? '';
    try {
      await navigator.clipboard?.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access denied/unavailable; silently ignore.
    }
  };

  return (
    <div className="group relative my-3">
      <div className="flex items-center justify-between rounded-t-lg bg-black/40 px-3 py-1 text-xs text-gray-300">
        <span>{language ?? 'code'}</span>
        <button
          type="button"
          onClick={() => void copy()}
          aria-label={copied ? 'Copied' : 'Copy code'}
          className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-gray-300 hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          {copied ? <CheckIcon size={14} /> : <CopyIcon size={14} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="overflow-x-auto rounded-b-lg bg-[#0d1117] p-4 text-sm">
        <code ref={codeRef} className={cx('hljs', className)}>
          {children}
        </code>
      </pre>
    </div>
  );
}
