'use client'

import { useState, FormEvent, useCallback, useMemo } from 'react'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { validateRequired } from '@/lib/validation'

interface LoginFormProps {
  onSuccess?: () => void
}

interface FormErrors {
  username?: string;
  password?: string;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const validateForm = useCallback((): FormErrors => {
    const errors: FormErrors = {};

    const usernameError = validateRequired(username, 'Username');
    if (usernameError) {
      errors.username = usernameError;
    }

    // Skip password complexity validation for login - backend handles it
    // Only check if password is provided
    if (!password) {
      errors.password = 'Password is required';
    }

    return errors;
  }, [username, password]);

  const formErrors = useMemo(() => validateForm(), [validateForm]);

  const isFormValid = useMemo(() => {
    return Object.keys(formErrors).length === 0 && username.trim() !== '' && password !== '';
  }, [formErrors, username, password]);

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    // Mark all fields as touched
    setTouched({ username: true, password: true });

    // Check for validation errors
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      return;
    }

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

        <div className="space-y-1">
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
            onBlur={() => handleBlur('username')}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              touched.username && formErrors.username ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter your username"
            disabled={isSubmitting}
            autoComplete="username"
          />
          {touched.username && formErrors.username && (
            <p className="text-sm text-red-600">{formErrors.username}</p>
          )}
        </div>

        <div className="space-y-1">
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
            onBlur={() => handleBlur('password')}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              touched.password && formErrors.password ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter your password"
            disabled={isSubmitting}
            autoComplete="current-password"
          />
          {touched.password && formErrors.password && (
            <p className="text-sm text-red-600">{formErrors.password}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !isFormValid}
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

      {/* Help Section */}
      <div className="mt-4 text-center text-sm text-gray-500">
        <p className="font-medium text-gray-600">Need help signing in?</p>
        <p className="mt-1">
          Contact your program administrator for account access or password reset.
        </p>
      </div>
    </div>
  )
}
