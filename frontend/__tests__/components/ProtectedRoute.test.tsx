/**
 * Tests for ProtectedRoute component
 *
 * Tests authentication and authorization guard behavior including:
 * - Loading states
 * - Unauthenticated redirects
 * - Authenticated rendering
 * - Admin role requirements
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProtectedRoute } from '@/components/ProtectedRoute'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
}))

// Mock auth context - will be configured per test
const mockAuthContext = {
  isAuthenticated: false,
  isLoading: true,
  user: null as { id: string; username: string; role: string } | null,
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
}))

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset to default loading state
    mockAuthContext.isAuthenticated = false
    mockAuthContext.isLoading = true
    mockAuthContext.user = null
  })

  describe('Loading State', () => {
    it('should show loading state during auth check', () => {
      mockAuthContext.isLoading = true
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show loading indicator
      expect(screen.getByText(/checking authentication/i)).toBeInTheDocument()
      // Should have accessible loading attributes
      expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
      // Content should not be visible
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should have proper aria attributes during loading', () => {
      mockAuthContext.isLoading = true
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      const loadingContainer = screen.getByRole('status')
      expect(loadingContainer).toHaveAttribute('aria-live', 'polite')
      expect(loadingContainer).toHaveAttribute('aria-busy', 'true')
    })
  })

  describe('Unauthenticated State', () => {
    it('should redirect to /login when not authenticated', async () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should redirect to login
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })

    it('should show redirecting message when not authenticated', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show redirecting message
      expect(screen.getByText(/redirecting to login/i)).toBeInTheDocument()
      // Content should not be visible
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should not render children when not authenticated', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })
  })

  describe('Authenticated State', () => {
    it('should render children when authenticated', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'faculty',
      }

      render(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should not redirect when authenticated', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should not redirect
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should not show loading indicator when authenticated', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'coordinator',
      }

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.queryByText(/checking authentication/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/redirecting/i)).not.toBeInTheDocument()
    })

    it('should render complex children correctly', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'admin',
      }

      render(
        <ProtectedRoute>
          <div>
            <h1>Dashboard</h1>
            <p>Welcome to the protected area</p>
            <button>Action Button</button>
          </div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Welcome to the protected area')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /action button/i })).toBeInTheDocument()
    })
  })

  describe('Admin Route Protection', () => {
    it('should render children for admin user on requireAdmin route', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'adminuser',
        role: 'admin',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div data-testid="admin-content">Admin Only Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('admin-content')).toBeInTheDocument()
      expect(screen.getByText('Admin Only Content')).toBeInTheDocument()
    })

    it('should show access denied for non-admin user on requireAdmin route', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'regularuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div data-testid="admin-content">Admin Only Content</div>
        </ProtectedRoute>
      )

      // Should show access denied
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.getByText(/admin privileges are required/i)).toBeInTheDocument()
      // Admin content should not be visible
      expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
    })

    it('should show access denied for faculty user on requireAdmin route', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'facultyuser',
        role: 'faculty',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })

    it('should show access denied for coordinator user on requireAdmin route', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'coordinator',
        role: 'coordinator',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })

    it('should display return to dashboard button on access denied', async () => {
      const user = userEvent.setup()
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'regularuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      // Should show return button
      const returnButton = screen.getByRole('button', { name: /return to dashboard/i })
      expect(returnButton).toBeInTheDocument()

      // Click should navigate to home
      await user.click(returnButton)
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    it('should have proper aria attributes on access denied', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'regularuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      // Should have role="alert" for accessibility
      const alertContainer = screen.getByRole('alert')
      expect(alertContainer).toBeInTheDocument()
      expect(alertContainer).toHaveAttribute('aria-live', 'polite')
    })

    it('should render non-admin content without requireAdmin prop', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'regularuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute>
          <div data-testid="normal-content">Regular Content</div>
        </ProtectedRoute>
      )

      // Should render content for any authenticated user
      expect(screen.getByTestId('normal-content')).toBeInTheDocument()
      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument()
    })

    it('should default requireAdmin to false', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'regularuser',
        role: 'faculty',
      }

      // Render without requireAdmin prop
      render(
        <ProtectedRoute>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should render without access denied
      expect(screen.getByText('Content')).toBeInTheDocument()
      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument()
    })
  })

  describe('State Transitions', () => {
    it('should transition from loading to authenticated', () => {
      // Start in loading state
      mockAuthContext.isLoading = true
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      const { rerender } = render(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      // Should be loading
      expect(screen.getByText(/checking authentication/i)).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()

      // Transition to authenticated
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'admin',
      }

      rerender(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      // Should show content
      expect(screen.queryByText(/checking authentication/i)).not.toBeInTheDocument()
      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })

    it('should transition from loading to unauthenticated', async () => {
      // Start in loading state
      mockAuthContext.isLoading = true
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      const { rerender } = render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should be loading
      expect(screen.getByText(/checking authentication/i)).toBeInTheDocument()

      // Transition to unauthenticated
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      rerender(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should redirect
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle null user gracefully', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = null // User is null but isAuthenticated is true (edge case)

      render(
        <ProtectedRoute requireAdmin>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should show access denied since user?.role won't be 'admin'
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should handle undefined role gracefully', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: undefined as unknown as string, // Undefined role
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should show access denied since role is not 'admin'
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should handle empty string role gracefully', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: '', // Empty string role
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should show access denied since role is not 'admin'
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should handle empty children gracefully', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'admin',
      }

      // Render with null children
      render(
        <ProtectedRoute>
          {null}
        </ProtectedRoute>
      )

      // Should not crash
      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument()
      expect(screen.queryByText(/checking authentication/i)).not.toBeInTheDocument()
    })

    it('should handle multiple children', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'admin',
      }

      render(
        <ProtectedRoute>
          <div>First Child</div>
          <div>Second Child</div>
          <div>Third Child</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('First Child')).toBeInTheDocument()
      expect(screen.getByText('Second Child')).toBeInTheDocument()
      expect(screen.getByText('Third Child')).toBeInTheDocument()
    })

    it('should handle requireAdmin explicitly set to false', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin={false}>
          <div data-testid="content">Regular Content</div>
        </ProtectedRoute>
      )

      // Should render content for any authenticated user
      expect(screen.getByTestId('content')).toBeInTheDocument()
      expect(screen.queryByText(/access denied/i)).not.toBeInTheDocument()
    })

    it('should handle role case sensitivity correctly', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'Admin', // Capitalized 'Admin' instead of 'admin'
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should show access denied since role check is case-sensitive ('Admin' !== 'admin')
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should handle ADMIN in all caps', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'ADMIN', // All caps
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Content</div>
        </ProtectedRoute>
      )

      // Should show access denied since role check is case-sensitive ('ADMIN' !== 'admin')
      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should allow clinical_staff role on non-admin routes', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'clinicaluser',
        role: 'clinical_staff',
      }

      render(
        <ProtectedRoute>
          <div data-testid="content">Clinical Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('content')).toBeInTheDocument()
    })

    it('should deny clinical_staff role on admin routes', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'clinicaluser',
        role: 'clinical_staff',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText(/access denied/i)).toBeInTheDocument()
    })

    it('should allow rn role on non-admin routes', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'nurseuser',
        role: 'rn',
      }

      render(
        <ProtectedRoute>
          <div data-testid="content">RN Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('content')).toBeInTheDocument()
    })

    it('should allow lpn role on non-admin routes', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'lpnuser',
        role: 'lpn',
      }

      render(
        <ProtectedRoute>
          <div data-testid="content">LPN Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('content')).toBeInTheDocument()
    })

    it('should allow msa role on non-admin routes', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'msauser',
        role: 'msa',
      }

      render(
        <ProtectedRoute>
          <div data-testid="content">MSA Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('content')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have accessible loading indicator', () => {
      mockAuthContext.isLoading = true
      mockAuthContext.isAuthenticated = false
      mockAuthContext.user = null

      render(
        <ProtectedRoute>
          <div>Content</div>
        </ProtectedRoute>
      )

      const loadingStatus = screen.getByRole('status')
      expect(loadingStatus).toBeInTheDocument()
      expect(loadingStatus).toHaveAttribute('aria-busy', 'true')
    })

    it('should have accessible access denied message', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      // Access denied should be announced to screen readers
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()

      // Should have heading
      expect(screen.getByRole('heading', { name: /access denied/i })).toBeInTheDocument()
    })

    it('should have accessible return button', () => {
      mockAuthContext.isLoading = false
      mockAuthContext.isAuthenticated = true
      mockAuthContext.user = {
        id: '1',
        username: 'testuser',
        role: 'resident',
      }

      render(
        <ProtectedRoute requireAdmin>
          <div>Admin Content</div>
        </ProtectedRoute>
      )

      const button = screen.getByRole('button', { name: /return to dashboard/i })
      expect(button).toBeInTheDocument()
      expect(button).toBeEnabled()
    })
  })
})
