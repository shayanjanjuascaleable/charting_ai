import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component to catch React errors and prevent white screen crashes.
 * Falls back to a safe UI if AutoChart or any child component throws an error.
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div className="flex items-center justify-center h-64 text-muted-foreground border border-dashed border-border rounded-lg">
          <div className="text-center p-4">
            <p className="text-sm font-medium mb-2">Chart rendering error</p>
            <p className="text-xs text-muted-foreground">
              Falling back to safe rendering mode
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

