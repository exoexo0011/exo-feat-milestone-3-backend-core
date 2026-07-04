import { Spinner } from '@/components/common/Spinner';
import { WrenchIcon } from '@/components/icons';

interface ToolIndicatorProps {
  tool: string;
  status: 'running' | 'completed' | 'failed';
}

/** Inline indicator shown while the assistant is invoking a tool. */
export function ToolIndicator({ tool, status }: ToolIndicatorProps) {
  return (
    <div
      role="status"
      className="mb-3 inline-flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 px-3 py-1.5 text-xs text-accent"
    >
      <WrenchIcon size={14} />
      <span>
        {status === 'running' ? 'Running tool' : status === 'failed' ? 'Tool failed' : 'Used tool'}:{' '}
        <span className="font-medium">{tool}</span>
      </span>
      {status === 'running' && <Spinner className="h-3 w-3" label={`Running ${tool}`} />}
    </div>
  );
}
