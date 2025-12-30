'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'
import { ToastProvider } from '@/contexts/ToastContext'

/**
 * Global handler for unhandled promise rejections.
 *
 * This catches async errors that occur outside React Query's error handling,
 * such as errors in event handlers, timers, or third-party libraries.
 *
 * @param event - The unhandled rejection event
 */
function handleUnhandledRejection(event: PromiseRejectionEvent): void {
  // Log the error for debugging
  console.error('Unhandled promise rejection:', event.reason)

  // In development, provide more detailed logging
  if (process.env.NODE_ENV === 'development') {
    console.group('%c Unhandled Promise Rejection', 'color: #ef4444; font-weight: bold')
    console.error('Reason:', event.reason)
    console.error('Promise:', event.promise)
    if (event.reason instanceof Error) {
      console.error('Stack:', event.reason.stack)
    }
    console.error('Timestamp:', new Date().toISOString())
    console.groupEnd()
  }

  // In production, this would typically report to an error tracking service
  // Example: Sentry.captureException(event.reason)

  // Prevent the default browser behavior (console error) since we've handled it
  // Note: We still want the error logged, but we've done that above
  // Uncomment if you want to suppress the browser's default error:
  // event.preventDefault()
}

/**
 * Custom hook to set up global error handlers.
 *
 * Sets up window event listeners for unhandled promise rejections
 * that occur outside of React's error boundary and React Query's
 * error handling mechanisms.
 */
function useGlobalErrorHandlers(): void {
  useEffect(() => {
    // Add the unhandled rejection handler
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    // Cleanup on unmount
    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [])
}

export function Providers({ children }: { children: React.ReactNode }) {
  // Set up global error handlers
  useGlobalErrorHandlers()

  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>{children}</ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
