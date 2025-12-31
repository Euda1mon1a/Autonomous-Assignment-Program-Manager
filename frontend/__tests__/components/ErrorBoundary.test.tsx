import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { ErrorBoundary, ErrorCategory } from '@/components/ErrorBoundary'

// Component that throws an error for testing
function ThrowError({ shouldThrow = false, error }: { shouldThrow?: boolean; error?: Error }) {
  if (shouldThrow) {
    throw error || new Error('Test error')
  }
  return <div>Child component</div>
}

describe('ErrorBoundary', () => {
  // Suppress console errors during tests
  const originalError = console.error
  const originalGroup = console.group
  const originalGroupEnd = console.groupEnd

  beforeAll(() => {
    console.error = jest.fn()
    console.group = jest.fn()
    console.groupEnd = jest.fn()
  })

  afterAll(() => {
    console.error = originalError
    console.group = originalGroup
    console.groupEnd = originalGroupEnd
  })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Normal Operation', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <div>Test content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Test content')).toBeInTheDocument()
    })

    it('should render multiple children without error', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
    })
  })

  describe('Error Catching', () => {
    it('should catch errors and display fallback UI', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.queryByText('Child component')).not.toBeInTheDocument()
      expect(screen.getByText('Something Went Wrong')).toBeInTheDocument()
    })

    it('should display error message in fallback UI', () => {
      const testError = new Error('Custom error message')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={testError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument()
    })

    it('should call onError callback when error occurs', () => {
      const onErrorMock = jest.fn()

      render(
        <ErrorBoundary onError={onErrorMock}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(onErrorMock).toHaveBeenCalled()
      expect(onErrorMock.mock.calls[0][0]).toBeInstanceOf(Error)
    })
  })

  describe('Error Categorization', () => {
    it('should categorize network errors correctly', () => {
      const networkError = new Error('Failed to fetch')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={networkError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Connection Problem')).toBeInTheDocument()
      expect(screen.getByText('Unable to connect to the server.')).toBeInTheDocument()
    })

    it('should categorize validation errors correctly', () => {
      const validationError = new Error('Validation failed: invalid input')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={validationError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Validation Error')).toBeInTheDocument()
      expect(screen.getByText('The data provided is not valid.')).toBeInTheDocument()
    })

    it('should categorize auth errors correctly', () => {
      const authError = new Error('Unauthorized access')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={authError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Access Denied')).toBeInTheDocument()
      expect(screen.getByText('You do not have permission to access this resource.')).toBeInTheDocument()
    })

    it('should categorize not found errors correctly', () => {
      const notFoundError = new Error('Resource not found')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={notFoundError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Not Found')).toBeInTheDocument()
      expect(screen.getByText('The requested resource could not be found.')).toBeInTheDocument()
    })

    it('should categorize unknown errors correctly', () => {
      const unknownError = new Error('Some random error')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={unknownError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something Went Wrong')).toBeInTheDocument()
      expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument()
    })
  })

  describe('Error Details (Development Mode)', () => {
    const originalEnv = process.env.NODE_ENV

    afterEach(() => {
      process.env.NODE_ENV = originalEnv
    })

    it('should show technical details in development mode', () => {
      process.env.NODE_ENV = 'development'
      const testError = new Error('Test error message')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={testError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Technical Details (Development Only)')).toBeInTheDocument()
    })

    it('should display error name in technical details', () => {
      process.env.NODE_ENV = 'development'
      const testError = new Error('Test error')
      testError.name = 'CustomError'

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={testError} />
        </ErrorBoundary>
      )

      const details = screen.getByText('Technical Details (Development Only)')
      expect(details).toBeInTheDocument()
      // Error name should be in the details section
      expect(screen.getByText('Error Name:')).toBeInTheDocument()
    })

    it('should display error message in technical details', () => {
      process.env.NODE_ENV = 'development'
      const testError = new Error('Detailed error message')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={testError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Error Message:')).toBeInTheDocument()
    })

    it('should display stack trace in technical details', () => {
      process.env.NODE_ENV = 'development'
      const testError = new Error('Test error')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={testError} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Stack Trace:')).toBeInTheDocument()
    })
  })

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', () => {
      const customFallback = <div>Custom error message</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error message')).toBeInTheDocument()
      expect(screen.queryByText('Something Went Wrong')).not.toBeInTheDocument()
    })
  })

  describe('Retry Functionality', () => {
    it('should show "Try Again" button when error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    })

    it('should call onReset when "Try Again" button is clicked', async () => {
      const user = userEvent.setup()
      const onResetMock = jest.fn()

      render(
        <ErrorBoundary onReset={onResetMock}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await user.click(tryAgainButton)

      expect(onResetMock).toHaveBeenCalled()
    })

    it('should increment retry count when retry button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary maxRetries={3}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Error should be shown
      expect(screen.getByText('Something Went Wrong')).toBeInTheDocument()

      // No retry count initially
      expect(screen.queryByText(/retry attempt/i)).not.toBeInTheDocument()

      // Click retry
      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await user.click(tryAgainButton)

      // Should show retry count
      expect(screen.getByText(/retry attempt 1 of 3/i)).toBeInTheDocument()
    })

    it('should show retry count indicator', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary maxRetries={3}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // No retry count initially
      expect(screen.queryByText(/retry attempt/i)).not.toBeInTheDocument()

      // Click retry
      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await user.click(tryAgainButton)

      // Should show retry count
      expect(screen.getByText(/retry attempt 1 of 3/i)).toBeInTheDocument()
    })

    it('should hide retry button after max retries reached', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary maxRetries={2}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const tryAgainButton = screen.getByRole('button', { name: /try again/i })

      // Click retry twice
      await user.click(tryAgainButton)
      await user.click(screen.getByRole('button', { name: /try again/i }))

      // After 2 retries, button should be hidden
      expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument()
    })

    it('should show max retries warning after max retries reached', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary maxRetries={1}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await user.click(tryAgainButton)

      expect(screen.getByText(/maximum retry attempts reached/i)).toBeInTheDocument()
    })

    it('should default to 3 max retries when not specified', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Click retry once
      const tryAgainButton = screen.getByRole('button', { name: /try again/i })
      await user.click(tryAgainButton)

      // Should show "of 3"
      expect(screen.getByText(/retry attempt 1 of 3/i)).toBeInTheDocument()
    })
  })

  describe('Navigation Actions', () => {
    let mockHistoryBack: jest.Mock

    beforeEach(() => {
      // Mock window methods
      delete (window as any).location
      window.location = { href: '', reload: jest.fn() } as any
      mockHistoryBack = jest.fn()
      window.history = { back: mockHistoryBack } as any
    })

    it('should show "Go Home" button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /go home/i })).toBeInTheDocument()
    })

    it('should navigate to home when "Go Home" is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      await user.click(screen.getByRole('button', { name: /go home/i }))

      expect(window.location.href).toBe('/')
    })

    it('should show "Go Back" button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument()
    })

    it('should call history.back when "Go Back" is clicked', async () => {
      const user = userEvent.setup()
      const mockBack = jest.fn()
      window.history.back = mockBack

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      await user.click(screen.getByRole('button', { name: /go back/i }))

      expect(mockBack).toHaveBeenCalled()
    })

    it('should show "Refresh Page" button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /refresh page/i })).toBeInTheDocument()
    })

    it('should reload page when "Refresh Page" is clicked', async () => {
      const user = userEvent.setup()

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      await user.click(screen.getByRole('button', { name: /refresh page/i }))

      expect(window.location.reload).toHaveBeenCalled()
    })

    it('should show "Report Error" button', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /report error/i })).toBeInTheDocument()
    })
  })

  describe('Error Icons', () => {
    it('should display appropriate icon for network errors', () => {
      const networkError = new Error('Network timeout')

      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={networkError} />
        </ErrorBoundary>
      )

      // Check for orange-colored icon background
      const iconContainer = container.querySelector('.bg-orange-100')
      expect(iconContainer).toBeInTheDocument()
    })

    it('should display appropriate icon for validation errors', () => {
      const validationError = new Error('Invalid data provided')

      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={validationError} />
        </ErrorBoundary>
      )

      // Check for yellow-colored icon background
      const iconContainer = container.querySelector('.bg-yellow-100')
      expect(iconContainer).toBeInTheDocument()
    })

    it('should display appropriate icon for auth errors', () => {
      const authError = new Error('Unauthorized')

      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={authError} />
        </ErrorBoundary>
      )

      // Check for purple-colored icon background
      const iconContainer = container.querySelector('.bg-purple-100')
      expect(iconContainer).toBeInTheDocument()
    })

    it('should display appropriate icon for not found errors', () => {
      const notFoundError = new Error('404 not found')

      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={notFoundError} />
        </ErrorBoundary>
      )

      // Check for blue-colored icon background
      const iconContainer = container.querySelector('.bg-blue-100')
      expect(iconContainer).toBeInTheDocument()
    })

    it('should display appropriate icon for unknown errors', () => {
      const unknownError = new Error('Random error')

      const { container } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={unknownError} />
        </ErrorBoundary>
      )

      // Check for red-colored icon background
      const iconContainer = container.querySelector('.bg-red-100')
      expect(iconContainer).toBeInTheDocument()
    })
  })

  describe('Error Suggestions', () => {
    it('should show helpful suggestion for network errors', () => {
      const networkError = new Error('Failed to fetch')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={networkError} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/please check your internet connection/i)).toBeInTheDocument()
    })

    it('should show helpful suggestion for validation errors', () => {
      const validationError = new Error('Validation error')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={validationError} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/please check your input/i)).toBeInTheDocument()
    })

    it('should show helpful suggestion for auth errors', () => {
      const authError = new Error('Unauthorized')

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} error={authError} />
        </ErrorBoundary>
      )

      expect(screen.getByText(/please log in with appropriate credentials/i)).toBeInTheDocument()
    })
  })

  describe('Static Error Categorization Method', () => {
    it('should correctly categorize network errors', () => {
      const networkError = new Error('Failed to fetch data')
      expect(ErrorBoundary.categorizeError(networkError)).toBe(ErrorCategory.Network)
    })

    it('should correctly categorize validation errors', () => {
      const validationError = new Error('ValidationError: field is required')
      expect(ErrorBoundary.categorizeError(validationError)).toBe(ErrorCategory.Validation)
    })

    it('should correctly categorize auth errors', () => {
      const authError = new Error('Authentication failed')
      expect(ErrorBoundary.categorizeError(authError)).toBe(ErrorCategory.Auth)
    })

    it('should correctly categorize not found errors', () => {
      const notFoundError = new Error('Resource not found')
      expect(ErrorBoundary.categorizeError(notFoundError)).toBe(ErrorCategory.NotFound)
    })

    it('should default to unknown for unrecognized errors', () => {
      const randomError = new Error('Something unexpected happened')
      expect(ErrorBoundary.categorizeError(randomError)).toBe(ErrorCategory.Unknown)
    })
  })
})
