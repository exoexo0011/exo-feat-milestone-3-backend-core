import { Component, type ErrorInfo, type ReactNode } from 'react';

import { Button } from '@/components/common/Button';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/** Catches render-time errors so a component failure never blanks the app. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error('Unhandled UI error:', error, info.componentStack);
  }

  handleReset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error) {
      return (
        <div
          role="alert"
          className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center"
        >
          <h1 className="text-xl font-semibold text-red-500">Something went wrong</h1>
          <p className="max-w-md text-sm text-gray-500">{this.state.error.message}</p>
          <Button onClick={this.handleReset}>Try again</Button>
        </div>
      );
    }
    return this.props.children;
  }
}
