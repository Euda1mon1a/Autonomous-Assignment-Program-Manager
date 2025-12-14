'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Calendar } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { LoginForm } from '@/components/LoginForm'

export default function LoginPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading } = useAuth()

  // Redirect to home if already authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, isLoading, router])

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500">Loading...</div>
      </div>
    )
  }

  // Don't render login form if authenticated (will redirect)
  if (isAuthenticated) {
    return null
  }

  const handleLoginSuccess = () => {
    router.push('/')
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      {/* Logo */}
      <div className="flex items-center gap-3 mb-8">
        <Calendar className="w-12 h-12 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Residency Scheduler</h1>
          <p className="text-sm text-gray-500">Sign in to continue</p>
        </div>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">
          Welcome Back
        </h2>
        <LoginForm onSuccess={handleLoginSuccess} />
      </div>

      {/* Footer */}
      <p className="mt-8 text-sm text-gray-500">
        Medical Residency Scheduling System
      </p>
    </div>
  )
}
