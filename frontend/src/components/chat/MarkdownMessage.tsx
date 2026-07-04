import { memo } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';

import { CodeBlock } from '@/components/chat/CodeBlock';

const COMPONENTS: Components = {
  // Unwrap the default <pre>; CodeBlock renders its own styled container.
  pre: ({ children }) => <>{children}</>,
  code({ className, children, ...props }) {
    const isBlock = typeof className === 'string' && className.includes('language-');
    if (isBlock) {
      return <CodeBlock className={className}>{children}</CodeBlock>;
    }
    return (
      <code className="rounded bg-black/10 px-1 py-0.5 text-[0.85em] dark:bg-white/10" {...props}>
        {children}
      </code>
    );
  },
  a: ({ children, ...props }) => (
    <a {...props} target="_blank" rel="noreferrer" className="text-accent underline">
      {children}
    </a>
  ),
};

/** Renders assistant markdown with GitHub-flavoured markdown and highlighting. */
export const MarkdownMessage = memo(function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="exo-prose text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={COMPONENTS}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
