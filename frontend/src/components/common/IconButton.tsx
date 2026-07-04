import type { ButtonHTMLAttributes } from 'react';

import { cx } from '@/lib/cx';

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Accessible label; icon buttons have no visible text. */
  label: string;
}

export function IconButton({ label, className, children, ...props }: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cx(
        'inline-flex h-9 w-9 items-center justify-center rounded-lg text-gray-600',
        'transition-colors hover:bg-gray-200 hover:text-gray-900',
        'dark:text-gray-300 dark:hover:bg-panel-dark dark:hover:text-white',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
