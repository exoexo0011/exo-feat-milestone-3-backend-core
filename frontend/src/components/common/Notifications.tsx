import { useEffect } from 'react';

import { IconButton } from '@/components/common/IconButton';
import { XIcon } from '@/components/icons';
import { cx } from '@/lib/cx';
import { useUiStore, type Notification } from '@/stores/uiStore';

const AUTO_DISMISS_MS = 5000;

const KIND_STYLES: Record<Notification['kind'], string> = {
  info: 'border-accent/40 bg-panel dark:bg-panel-dark',
  success: 'border-green-500/40 bg-panel dark:bg-panel-dark',
  error: 'border-red-500/50 bg-panel dark:bg-panel-dark',
};

function Toast({ notification }: { notification: Notification }) {
  const dismiss = useUiStore((state) => state.dismiss);

  useEffect(() => {
    const timer = window.setTimeout(() => dismiss(notification.id), AUTO_DISMISS_MS);
    return () => window.clearTimeout(timer);
  }, [notification.id, dismiss]);

  return (
    <div
      role={notification.kind === 'error' ? 'alert' : 'status'}
      className={cx(
        'flex items-start gap-3 rounded-lg border p-3 text-sm shadow-lg',
        'text-gray-800 dark:text-gray-100',
        KIND_STYLES[notification.kind],
      )}
    >
      <span className="flex-1">{notification.message}</span>
      <IconButton
        label="Dismiss notification"
        className="h-6 w-6"
        onClick={() => dismiss(notification.id)}
      >
        <XIcon size={14} />
      </IconButton>
    </div>
  );
}

export function Notifications() {
  const notifications = useUiStore((state) => state.notifications);

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2"
      aria-live="polite"
    >
      {notifications.map((notification) => (
        <div key={notification.id} className="pointer-events-auto">
          <Toast notification={notification} />
        </div>
      ))}
    </div>
  );
}
