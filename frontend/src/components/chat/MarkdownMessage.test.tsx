import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { MarkdownMessage } from './MarkdownMessage';

const writeText = vi.fn().mockResolvedValue(undefined);

beforeEach(() => {
  writeText.mockReset();
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  });
});

describe('MarkdownMessage', () => {
  it('renders markdown text', () => {
    render(<MarkdownMessage content="Hello **world**" />);
    expect(screen.getByText('world')).toBeInTheDocument();
  });

  it('renders a fenced code block with a working copy button', async () => {
    render(<MarkdownMessage content={'```js\nconst answer = 42;\n```'} />);

    const copyButton = screen.getByRole('button', { name: 'Copy code' });
    await userEvent.click(copyButton);

    await waitFor(() => expect(writeText).toHaveBeenCalledTimes(1));
    expect(writeText.mock.calls[0][0]).toContain('const answer = 42;');
  });
});
