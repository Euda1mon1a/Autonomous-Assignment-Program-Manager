'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Loader2, ShieldX } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

/**
 * ProtectedRoute component that handles route protection and authorization.
 *
 * - If not authenticated, redirects to /login
 * - If requireAdmin and user is not admin, shows forbidden message
 * - Shows loading spinner while checking auth state
 */
export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Wait for auth check to complete
    if (isLoading) return

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
      router.push('/login')
    }
  }, [isAuthenticated, isLoading, router])

  // Show loading spinner while checking auth
  if (isLoading) {
    return (
      <div
        className="flex flex-col items-center justify-center min-h-[60vh]"
        aria-live="polite"
        aria-busy="true"
        role="status"
      >
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" aria-hidden="true" />
        <p className="mt-3 text-gray-600">Checking authentication...</p>
      </div>
    )
  }

  // Not authenticated - will redirect via useEffect
  if (!isAuthenticated) {
    return (
      <div
        className="flex flex-col items-center justify-center min-h-[60vh]"
        aria-live="polite"
        aria-busy="true"
        role="status"
      >
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" aria-hidden="true" />
        <p className="mt-3 text-gray-600">Redirecting to login...</p>
      </div>
    )
  }

  // Check admin requirement
  if (requireAdmin && user?.role !== 'admin') {
    return (
      <div
        className="flex flex-col items-center justify-center min-h-[60vh]"
        aria-live="polite"
        role="alert"
      >
        <div className="text-center">
          <ShieldX className="w-16 h-16 text-red-500 mx-auto mb-4" aria-hidden="true" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p className="text-gray-600 mb-6">
            You do not have permission to access this page.
            <br />
            Admin privileges are required.
          </p>
          <button
            onClick={() => router.push('/')}
            className="btn-primary"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    )
  }

  // User is authenticated and has required permissions
  return <>{children}</>
}
