'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

/**
 * Error categories for better error handling and user messaging
 */
export enum ErrorCategory {
  Network = 'NetworkError',
  Validation = 'ValidationError',
  Auth = 'AuthError',
  NotFound = 'NotFoundError',
  Unknown = 'UnknownError',
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
  maxRetries?: number;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
  errorCategory: ErrorCategory;
}

interface ErrorCategoryConfig {
  icon: ReactNode;
  title: string;
  message: string;
  suggestion: string;
  bgColor: string;
  iconColor: string;
}

/**
 * Enhanced React Error Boundary component that catches render errors
 * and displays categorized, user-friendly error messages with recovery options.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
      errorCategory: ErrorCategory.Unknown,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorCategory = ErrorBoundary.categorizeError(error);
    return {
      hasError: true,
      error,
      errorCategory,
    };
  }

  /**
   * Categorize error based on error type and message
   */
  static categorizeError(error: Error): ErrorCategory {
    const errorMessage = error.message.toLowerCase();
    const errorName = error.name.toLowerCase();

    // Network errors
    if (
      errorName.includes('network') ||
      errorMessage.includes('network') ||
      errorMessage.includes('fetch') ||
      errorMessage.includes('connection') ||
      errorMessage.includes('timeout') ||
      error instanceof TypeError && errorMessage.includes('failed to fetch')
    ) {
      return ErrorCategory.Network;
    }

    // Authentication/Authorization errors
    if (
      errorName.includes('auth') ||
      errorMessage.includes('unauthorized') ||
      errorMessage.includes('forbidden') ||
      errorMessage.includes('authentication') ||
      errorMessage.includes('permission')
    ) {
      return ErrorCategory.Auth;
    }

    // Validation errors
    if (
      errorName.includes('validation') ||
      errorMessage.includes('validation') ||
      errorMessage.includes('invalid') ||
      errorMessage.includes('required')
    ) {
      return ErrorCategory.Validation;
    }

    // Not found errors
    if (
      errorMessage.includes('not found') ||
      errorMessage.includes('404') ||
      errorName.includes('notfound')
    ) {
      return ErrorCategory.NotFound;
    }

    // Default to unknown
    return ErrorCategory.Unknown;
  }

  /**
   * Get error configuration based on category
   */
  getErrorConfig(): ErrorCategoryConfig {
    const { errorCategory } = this.state;

    const configs: Record<ErrorCategory, ErrorCategoryConfig> = {
      [ErrorCategory.Network]: {
        icon: (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"
            />
          </svg>
        ),
        title: 'Connection Problem',
        message: 'Unable to connect to the server.',
        suggestion: 'Please check your internet connection and try again.',
        bgColor: 'bg-orange-100',
        iconColor: 'text-orange-600',
      },
      [ErrorCategory.Validation]: {
        icon: (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
        ),
        title: 'Validation Error',
        message: 'The data provided is not valid.',
        suggestion: 'Please check your input and try again.',
        bgColor: 'bg-yellow-100',
        iconColor: 'text-yellow-600',
      },
      [ErrorCategory.Auth]: {
        icon: (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
            />
          </svg>
        ),
        title: 'Access Denied',
        message: 'You do not have permission to access this resource.',
        suggestion: 'Please log in with appropriate credentials or contact support.',
        bgColor: 'bg-purple-100',
        iconColor: 'text-purple-600',
      },
      [ErrorCategory.NotFound]: {
        icon: (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        ),
        title: 'Not Found',
        message: 'The requested resource could not be found.',
        suggestion: 'Please check the URL or navigate back to the home page.',
        bgColor: 'bg-blue-100',
        iconColor: 'text-blue-600',
      },
      [ErrorCategory.Unknown]: {
        icon: (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        ),
        title: 'Something Went Wrong',
        message: 'An unexpected error occurred.',
        suggestion: 'Please try again or contact support if the problem persists.',
        bgColor: 'bg-red-100',
        iconColor: 'text-red-600',
      },
    };

    return configs[errorCategory];
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Store error info in state
    this.setState({ errorInfo });

    // Log error details to console in development
    if (process.env.NODE_ENV === 'development') {
      console.group('%c Error Boundary Caught Error', 'color: #ef4444; font-weight: bold');
      console.error('Error:', error);
      console.error('Error Name:', error.name);
      console.error('Error Message:', error.message);
      console.error('Error Stack:', error.stack);
      console.error('Component Stack:', errorInfo.componentStack);
      console.error('Category:', this.state.errorCategory);
      console.groupEnd();
    } else {
      // In production, prepare for error reporting service
      console.error('Error occurred:', {
        message: error.message,
        name: error.name,
        category: this.state.errorCategory,
        timestamp: new Date().toISOString(),
        // Future: send to error reporting service (Sentry, LogRocket, etc.)
      });
    }

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  componentWillUnmount(): void {
    // Clean up any pending retry timeout
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  handleReset = (): void => {
    const { retryCount } = this.state;
    const maxRetries = this.props.maxRetries ?? 3;

    if (retryCount >= maxRetries) {
      console.warn(`Max retry attempts (${maxRetries}) reached`);
      return;
    }

    // Call optional reset callback
    if (this.props.onReset) {
      this.props.onReset();
    }

    // Reset error state and increment retry count
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: retryCount + 1,
    });
  };

  handleAutoRetry = (): void => {
    const { retryCount } = this.state;
    const maxRetries = this.props.maxRetries ?? 3;

    if (retryCount >= maxRetries) {
      return;
    }

    // Exponential backoff: 1s, 2s, 4s, 8s...
    const delay = Math.min(1000 * Math.pow(2, retryCount), 8000);

    console.log(`Auto-retry in ${delay}ms (attempt ${retryCount + 1}/${maxRetries})`);

    this.retryTimeoutId = setTimeout(() => {
      this.handleReset();
    }, delay);
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleRefresh = (): void => {
    window.location.reload();
  };

  handleGoBack = (): void => {
    window.history.back();
  };

  handleReportError = (): void => {
    const { error, errorInfo, errorCategory } = this.state;

    console.group('%c Error Report', 'color: #3b82f6; font-weight: bold');
    console.log('Category:', errorCategory);
    console.log('Error:', error);
    console.log('Error Info:', errorInfo);
    console.log('Timestamp:', new Date().toISOString());
    console.log('User Agent:', navigator.userAgent);
    console.log('URL:', window.location.href);
    console.groupEnd();

    alert('Error details have been logged to the console. In production, this would be sent to an error reporting service.');
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Allow custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, retryCount } = this.state;
      const maxRetries = this.props.maxRetries ?? 3;
      const config = this.getErrorConfig();
      const canRetry = retryCount < maxRetries;

      // Default error UI with categorization
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
            {/* Error Icon */}
            <div className={`w-16 h-16 mx-auto mb-4 ${config.bgColor} rounded-full flex items-center justify-center`}>
              <div className={config.iconColor}>
                {config.icon}
              </div>
            </div>

            {/* Error Title */}
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {config.title}
            </h2>

            {/* Error Message */}
            <p className="text-gray-600 mb-2">
              {config.message}
            </p>

            {/* Suggestion */}
            <p className="text-sm text-gray-500 mb-6">
              {config.suggestion}
            </p>

            {/* Retry Count Indicator */}
            {retryCount > 0 && (
              <p className="text-xs text-gray-400 mb-4">
                Retry attempt {retryCount} of {maxRetries}
              </p>
            )}

            {/* Development Error Details */}
            {process.env.NODE_ENV === 'development' && error && (
              <details className="mb-6 text-left">
                <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700 font-medium">
                  Technical Details (Development Only)
                </summary>
                <div className="mt-2 p-3 bg-gray-100 rounded-lg">
                  <div className="mb-2">
                    <span className="text-xs font-semibold text-gray-700">Error Name:</span>
                    <pre className="text-xs text-gray-600 mt-1">{error.name}</pre>
                  </div>
                  <div className="mb-2">
                    <span className="text-xs font-semibold text-gray-700">Error Message:</span>
                    <pre className="text-xs text-gray-600 mt-1">{error.message}</pre>
                  </div>
                  {error.stack && (
                    <div>
                      <span className="text-xs font-semibold text-gray-700">Stack Trace:</span>
                      <pre className="text-xs text-gray-600 mt-1 overflow-auto max-h-32">
                        {error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* Action Buttons */}
            <div className="space-y-3">
              {/* Primary Actions */}
              <div className="flex gap-3">
                {canRetry && (
                  <button
                    onClick={this.handleReset}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 font-medium"
                  >
                    Try Again
                  </button>
                )}
                <button
                  onClick={this.handleGoHome}
                  className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 font-medium"
                >
                  Go Home
                </button>
              </div>

              {/* Secondary Actions */}
              <div className="flex gap-3">
                <button
                  onClick={this.handleGoBack}
                  className="flex-1 px-3 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 text-sm"
                >
                  Go Back
                </button>
                <button
                  onClick={this.handleRefresh}
                  className="flex-1 px-3 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 text-sm"
                >
                  Refresh Page
                </button>
                <button
                  onClick={this.handleReportError}
                  className="flex-1 px-3 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 text-sm"
                >
                  Report Error
                </button>
              </div>
            </div>

            {/* Max Retries Reached Warning */}
            {!canRetry && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-xs text-yellow-800">
                  Maximum retry attempts reached. Please try refreshing the page or contact support.
                </p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
