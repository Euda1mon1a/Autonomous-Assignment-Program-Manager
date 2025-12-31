/**
 * Tests for Login Page
 *
 * Tests page rendering, authentication state handling, loading states,
 * redirect behavior, and integration with LoginForm component.
 */
import React from 'react'
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import LoginPage from '@/app/login/page'

// Mock dependencies
const mockPush = jest.fn()
const mockUseAuth = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

// Mock LoginForm component to test integration
const mockOnSuccess = jest.fn()
jest.mock('@/components/LoginForm', () => ({
  LoginForm: ({ onSuccess }: { onSuccess?: () => void }) => {
    // Store the callback so we can test it
    mockOnSuccess.mockImplementation(onSuccess || (() => {}))
    return (
      <div data-testid="login-form">
        <button
          data-testid="mock-login-button"
          onClick={() => {
            if (onSuccess) onSuccess()
          }}
        >
          Mock Login
        </button>
      </div>
    )
  },
}))

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Default: not authenticated, not loading
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: jest.fn(),
      logout: jest.fn(),
    })
  })

  describe('Rendering', () => {
    it('should render the page when not authenticated', () => {
      render(<LoginPage />)

      expect(screen.getByText('Residency Scheduler')).toBeInTheDocument()
      expect(screen.getByText('Sign in to continue')).toBeInTheDocument()
    })

    it('should render the logo icon', () => {
      render(<LoginPage />)

      // Calendar icon is rendered via lucide-react
      // The icon is part of the same container as the text, not a sibling
      const logoSection = screen.getByText('Residency Scheduler').closest('div')
      expect(logoSection).toBeInTheDocument()
      // The logoSection should contain both the icon and text
      expect(logoSection?.parentElement).toHaveClass('flex', 'items-center', 'gap-3')
    })

    it('should render welcome message', () => {
      render(<LoginPage />)

      expect(screen.getByText('Welcome Back')).toBeInTheDocument()
    })

    it('should render LoginForm component', () => {
      render(<LoginPage />)

      expect(screen.getByTestId('login-form')).toBeInTheDocument()
    })

    it('should render footer text', () => {
      render(<LoginPage />)

      expect(screen.getByText('Medical Residency Scheduling System')).toBeInTheDocument()
    })

    it('should have proper styling classes for the container', () => {
      const { container } = render(<LoginPage />)

      const mainDiv = container.querySelector('.min-h-screen')
      expect(mainDiv).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center', 'bg-gray-50')
    })

    it('should render login card with proper styling', () => {
      const { container } = render(<LoginPage />)

      const loginCard = screen.getByText('Welcome Back').closest('div')
      expect(loginCard).toHaveClass('bg-white', 'rounded-lg', 'shadow-sm', 'border')
    })
  })

  describe('Loading State', () => {
    it('should show loading spinner when auth is loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('should show loading with proper styling', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const { container } = render(<LoginPage />)

      // The outer container has the styling
      const loadingContainer = container.querySelector('.min-h-screen')
      expect(loadingContainer).toHaveClass('flex', 'items-center', 'justify-center', 'bg-gray-50')
    })

    it('should show animated loading text', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      const loadingText = screen.getByText('Loading...')
      expect(loadingText).toHaveClass('animate-pulse', 'text-gray-500')
    })

    it('should not show login form while loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
    })

    it('should not show branding while loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(screen.queryByText('Residency Scheduler')).not.toBeInTheDocument()
      expect(screen.queryByText('Welcome Back')).not.toBeInTheDocument()
    })
  })

  describe('Authentication Redirect', () => {
    it('should redirect to home when already authenticated', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: '1', username: 'testuser', role: 'admin' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('should not render login form when authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: '1', username: 'testuser', role: 'admin' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      const { container } = render(<LoginPage />)

      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
      expect(container.firstChild).toBeNull()
    })

    it('should only redirect once when authenticated', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: '1', username: 'testuser', role: 'admin' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledTimes(1)
      })
    })

    it('should not redirect when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should not redirect while loading', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  describe('LoginForm Integration', () => {
    it('should pass onSuccess callback to LoginForm', () => {
      render(<LoginPage />)

      expect(screen.getByTestId('login-form')).toBeInTheDocument()
      expect(mockOnSuccess).toBeDefined()
    })

    it('should redirect to home when LoginForm onSuccess is called', async () => {
      const user = userEvent.setup()

      render(<LoginPage />)

      // Simulate successful login by clicking the mock login button
      const mockLoginButton = screen.getByTestId('mock-login-button')
      await user.click(mockLoginButton)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('should handle onSuccess callback correctly', async () => {
      const user = userEvent.setup()

      render(<LoginPage />)

      const mockLoginButton = screen.getByTestId('mock-login-button')
      await user.click(mockLoginButton)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
        expect(mockPush).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('State Transitions', () => {
    it('should transition from loading to login form', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const { rerender } = render(<LoginPage />)

      // Initially loading
      expect(screen.getByText('Loading...')).toBeInTheDocument()
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()

      // Update to not loading
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      rerender(<LoginPage />)

      // Should now show login form
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      expect(screen.getByTestId('login-form')).toBeInTheDocument()
    })

    it('should transition from login form to redirect', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const { rerender } = render(<LoginPage />)

      // Initially showing login form
      expect(screen.getByTestId('login-form')).toBeInTheDocument()

      // Update to authenticated
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: '1', username: 'testuser', role: 'admin' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      rerender(<LoginPage />)

      // Should redirect
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })

      // Should not show login form
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
    })

    it('should handle loading to authenticated transition', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      const { rerender } = render(<LoginPage />)

      // Initially loading
      expect(screen.getByText('Loading...')).toBeInTheDocument()

      // Update to authenticated
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: { id: '1', username: 'testuser', role: 'admin' },
        login: jest.fn(),
        logout: jest.fn(),
      })

      rerender(<LoginPage />)

      // Should redirect immediately
      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })

      // Should not show loading or login form
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
      expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle null user when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      expect(screen.getByTestId('login-form')).toBeInTheDocument()
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('should handle user object when authenticated', async () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        user: {
          id: 'user-123',
          username: 'john.doe',
          email: 'john@example.com',
          role: 'coordinator',
        },
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/')
      })
    })

    it('should not break if useAuth returns undefined functions', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        user: null,
        login: undefined,
        logout: undefined,
      })

      // Should not throw
      expect(() => render(<LoginPage />)).not.toThrow()
    })
  })

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<LoginPage />)

      const mainHeading = screen.getByRole('heading', { name: /residency scheduler/i })
      expect(mainHeading).toBeInTheDocument()
      expect(mainHeading.tagName).toBe('H1')

      const subHeading = screen.getByRole('heading', { name: /welcome back/i })
      expect(subHeading).toBeInTheDocument()
      expect(subHeading.tagName).toBe('H2')
    })

    it('should have descriptive text for screen readers', () => {
      render(<LoginPage />)

      expect(screen.getByText('Sign in to continue')).toBeInTheDocument()
      expect(screen.getByText('Medical Residency Scheduling System')).toBeInTheDocument()
    })

    it('should have proper semantic structure', () => {
      const { container } = render(<LoginPage />)

      // Main container should be a div with proper classes
      const mainContainer = container.querySelector('.min-h-screen')
      expect(mainContainer).toBeInTheDocument()
    })

    it('should have accessible loading state', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        user: null,
        login: jest.fn(),
        logout: jest.fn(),
      })

      render(<LoginPage />)

      const loadingText = screen.getByText('Loading...')
      expect(loadingText).toBeInTheDocument()
      expect(loadingText).toHaveClass('text-gray-500')
    })
  })

  describe('Visual Styling', () => {
    it('should apply correct background color to page', () => {
      const { container } = render(<LoginPage />)

      const mainDiv = container.querySelector('.bg-gray-50')
      expect(mainDiv).toHaveClass('min-h-screen')
    })

    it('should apply correct styling to login card', () => {
      render(<LoginPage />)

      const welcomeHeading = screen.getByText('Welcome Back')
      const loginCard = welcomeHeading.closest('div')

      expect(loginCard).toHaveClass('bg-white', 'rounded-lg', 'shadow-sm', 'border', 'border-gray-200')
    })

    it('should center content vertically and horizontally', () => {
      const { container } = render(<LoginPage />)

      const mainDiv = container.querySelector('.min-h-screen')
      expect(mainDiv).toHaveClass('flex', 'items-center', 'justify-center')
    })

    it('should have proper padding on mobile', () => {
      const { container } = render(<LoginPage />)

      const mainDiv = container.querySelector('.min-h-screen')
      expect(mainDiv).toHaveClass('px-4')
    })

    it('should limit login card width', () => {
      const { container } = render(<LoginPage />)

      // Find the div with max-w-md class
      const loginCardContainer = container.querySelector('.max-w-md')
      expect(loginCardContainer).toBeInTheDocument()
      expect(loginCardContainer).toHaveClass('w-full', 'max-w-md')
    })

    it('should have proper spacing for logo section', () => {
      render(<LoginPage />)

      const logoSection = screen.getByText('Residency Scheduler').closest('div')?.parentElement
      expect(logoSection).toHaveClass('flex', 'items-center', 'gap-3', 'mb-8')
    })
  })

  describe('Component Composition', () => {
    it('should render all major sections', () => {
      render(<LoginPage />)

      // Logo section
      expect(screen.getByText('Residency Scheduler')).toBeInTheDocument()
      expect(screen.getByText('Sign in to continue')).toBeInTheDocument()

      // Login card
      expect(screen.getByText('Welcome Back')).toBeInTheDocument()
      expect(screen.getByTestId('login-form')).toBeInTheDocument()

      // Footer
      expect(screen.getByText('Medical Residency Scheduling System')).toBeInTheDocument()
    })

    it('should render sections in correct order', () => {
      const { container } = render(<LoginPage />)

      const sections = container.querySelectorAll('.min-h-screen > *')

      // Logo should be first
      expect(sections[0]).toContainElement(screen.getByText('Residency Scheduler'))

      // Login card should be second
      expect(sections[1]).toContainElement(screen.getByText('Welcome Back'))

      // Footer should be last
      expect(sections[2]).toContainElement(screen.getByText('Medical Residency Scheduling System'))
    })
  })
})
