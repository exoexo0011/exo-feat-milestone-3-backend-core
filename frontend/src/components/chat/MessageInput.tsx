import { useRef, useState, type ChangeEvent, type DragEvent, type KeyboardEvent } from 'react';

import { IconButton } from '@/components/common/IconButton';
import { PaperclipIcon, SendIcon, StopIcon, XIcon } from '@/components/icons';
import { cx } from '@/lib/cx';
import { useChatStore } from '@/stores/chatStore';
import { useSettingsStore } from '@/stores/settingsStore';

const MAX_ATTACHMENT_BYTES = 100 * 1024;
const TEXT_EXTENSIONS =
  /\.(txt|md|markdown|json|ya?ml|csv|log|py|js|ts|tsx|jsx|html|css|sh|toml|ini|xml|sql)$/i;

interface Attachment {
  name: string;
  content: string;
}

function isTextual(file: File): boolean {
  return file.type.startsWith('text/') || TEXT_EXTENSIONS.test(file.name);
}

async function readAttachment(file: File): Promise<Attachment> {
  if (file.size > MAX_ATTACHMENT_BYTES) {
    return { name: file.name, content: '(file omitted: exceeds 100 KB)' };
  }
  if (!isTextual(file)) {
    return { name: file.name, content: '(binary file omitted)' };
  }
  return { name: file.name, content: await file.text() };
}

function compose(text: string, attachments: Attachment[]): string {
  if (attachments.length === 0) {
    return text;
  }
  const blocks = attachments
    .map((a) => `--- Attached file: ${a.name} ---\n\`\`\`\n${a.content}\n\`\`\``)
    .join('\n\n');
  return text ? `${text}\n\n${blocks}` : blocks;
}

export function MessageInput() {
  const sendMessage = useChatStore((s) => s.sendMessage);
  const cancelStreaming = useChatStore((s) => s.cancelStreaming);
  const sending = useChatStore((s) => s.sending);
  const sendOnEnter = useSettingsStore((s) => s.sendOnEnter);

  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [dragging, setDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const grow = (): void => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  };

  const addFiles = async (files: FileList | null): Promise<void> => {
    if (!files || files.length === 0) return;
    const read = await Promise.all(Array.from(files).map(readAttachment));
    setAttachments((prev) => [...prev, ...read]);
  };

  const submit = (): void => {
    const composed = compose(text.trim(), attachments);
    if (!composed || sending) return;
    void sendMessage(composed);
    setText('');
    setAttachments([]);
    requestAnimationFrame(grow);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    const withModifier = event.ctrlKey || event.metaKey;
    if (event.key === 'Enter') {
      if (sendOnEnter && !event.shiftKey) {
        event.preventDefault();
        submit();
      } else if (!sendOnEnter && withModifier) {
        event.preventDefault();
        submit();
      }
    }
  };

  const onDrop = (event: DragEvent<HTMLDivElement>): void => {
    event.preventDefault();
    setDragging(false);
    void addFiles(event.dataTransfer.files);
  };

  const onFileChange = (event: ChangeEvent<HTMLInputElement>): void => {
    void addFiles(event.target.files);
    event.target.value = '';
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cx(
        'border-t border-gray-200 bg-surface p-4 dark:border-white/10 dark:bg-surface-dark',
        dragging && 'ring-2 ring-inset ring-accent',
      )}
    >
      <div className="mx-auto max-w-3xl">
        {attachments.length > 0 && (
          <ul className="mb-2 flex flex-wrap gap-2" aria-label="Attachments">
            {attachments.map((attachment, index) => (
              <li
                key={`${attachment.name}-${index}`}
                className="flex items-center gap-1 rounded-md bg-panel px-2 py-1 text-xs text-gray-700 dark:bg-panel-dark dark:text-gray-200"
              >
                <PaperclipIcon size={12} />
                <span className="max-w-[12rem] truncate">{attachment.name}</span>
                <button
                  type="button"
                  aria-label={`Remove ${attachment.name}`}
                  onClick={() => setAttachments((prev) => prev.filter((_, i) => i !== index))}
                  className="text-gray-400 hover:text-gray-700 dark:hover:text-white"
                >
                  <XIcon size={12} />
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-end gap-2 rounded-2xl border border-gray-300 bg-white p-2 focus-within:border-accent dark:border-white/10 dark:bg-panel-dark">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={onFileChange}
            aria-hidden="true"
            tabIndex={-1}
          />
          <IconButton label="Attach files" onClick={() => fileInputRef.current?.click()}>
            <PaperclipIcon size={18} />
          </IconButton>

          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              grow();
            }}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder="Message EXO…"
            aria-label="Message"
            className="max-h-52 flex-1 resize-none bg-transparent py-1.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none dark:text-gray-100"
          />

          {sending ? (
            <IconButton label="Stop generating" onClick={cancelStreaming}>
              <StopIcon size={18} />
            </IconButton>
          ) : (
            <IconButton
              label="Send message"
              onClick={submit}
              disabled={!text.trim() && attachments.length === 0}
              className="text-accent hover:bg-accent/10"
            >
              <SendIcon size={18} />
            </IconButton>
          )}
        </div>
        <p className="mt-1 px-2 text-center text-xs text-gray-400">
          {sendOnEnter ? 'Enter to send · Shift+Enter for a new line' : 'Ctrl/Cmd+Enter to send'}
        </p>
      </div>
    </div>
  );
}
