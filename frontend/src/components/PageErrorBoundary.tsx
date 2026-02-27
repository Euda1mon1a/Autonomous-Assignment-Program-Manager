'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw, Home, ArrowLeft } from 'lucide-react';

interface PageErrorBoundaryProps {
  error: Error & { digest?: string };
  reset: () => void;
  /** Page title shown in the error UI (e.g., "Dashboard") */
  pageTitle: string;
  /** Icon component shown next to the title */
  icon?: React.ElementType;
  /** Back link path for the "Go Back" button (defaults to /admin/dashboard) */
  backPath?: string;
}

/**
 * Reusable error boundary UI for Next.js App Router error.tsx files.
 *
 * This component is used inside each admin page's error.tsx to provide
 * page-specific error recovery without replacing the entire app layout.
 * It complements the global ErrorBoundary in the root layout by catching
 * errors at the page level and offering contextual recovery options.
 */
export function PageErrorBoundary({
  error,
  reset,
  pageTitle,
  icon: Icon = AlertTriangle,
  backPath = '/admin/dashboard',
}: PageErrorBoundaryProps) {
  useEffect(() => {
    // Log the error for debugging / future error reporting service
    console.error(`[${pageTitle}] Page error:`, error);
  }, [error, pageTitle]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <div className="max-w-lg w-full bg-slate-800/50 border border-slate-700 rounded-xl p-8 text-center">
        {/* Error Icon */}
        <div className="w-16 h-16 mx-auto mb-6 bg-red-500/20 rounded-full flex items-center justify-center">
          <Icon className="w-8 h-8 text-red-400" />
        </div>

        {/* Title */}
        <h2 className="text-xl font-semibold text-white mb-2">
          {pageTitle} Error
        </h2>

        {/* Message */}
        <p className="text-slate-400 mb-2">
          Something went wrong while loading the {pageTitle.toLowerCase()} page.
        </p>
        <p className="text-sm text-slate-500 mb-6">
          You can try again, or navigate away and come back later.
        </p>

        {/* Dev-only error details */}
        {process.env.NODE_ENV === 'development' && (
          <details className="mb-6 text-left">
            <summary className="text-sm text-slate-500 cursor-pointer hover:text-slate-300 font-medium">
              Technical Details
            </summary>
            <div className="mt-2 p-3 bg-slate-900/50 rounded-lg">
              <pre className="text-xs text-red-400 whitespace-pre-wrap break-words">
                {error.message}
              </pre>
              {error.stack && (
                <pre className="text-xs text-slate-500 mt-2 whitespace-pre-wrap break-words max-h-32 overflow-auto">
                  {error.stack}
                </pre>
              )}
              {error.digest && (
                <p className="text-xs text-slate-600 mt-2">
                  Digest: {error.digest}
                </p>
              )}
            </div>
          </details>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={reset}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
          <Link
            href={backPath}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Go Back
          </Link>
          <Link
            href="/"
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-900"
          >
            <Home className="w-4 h-4" />
            Home
          </Link>
        </div>
      </div>
    </div>
  );
}
