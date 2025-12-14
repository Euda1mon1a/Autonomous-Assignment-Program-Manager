'use client'

import { useState, FormEvent } from 'react'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface LoginFormProps {
  onSuccess?: () => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await login({ username, password })
      onSuccess?.()
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Invalid username or password'
      setError(errorMessage)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-red-800 text-sm">{error}</span>
          </div>
        )}

        <div>
          <label
            htmlFor="username"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Username
          </label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="input-field w-full"
            placeholder="Enter your username"
            required
            disabled={isSubmitting}
            autoComplete="username"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field w-full"
            placeholder="Enter your password"
            required
            disabled={isSubmitting}
            autoComplete="current-password"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !username || !password}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Signing in...
            </>
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      {/* Demo Account Info */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Demo Accounts</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex justify-between">
            <span className="font-mono">admin</span>
            <span className="text-gray-400">admin123</span>
          </div>
          <div className="flex justify-between">
            <span className="font-mono">coordinator</span>
            <span className="text-gray-400">coord123</span>
          </div>
          <div className="flex justify-between">
            <span className="font-mono">faculty</span>
            <span className="text-gray-400">faculty123</span>
          </div>
        </div>
      </div>
    </div>
  )
}
