import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { ErrorAlert } from '@/components/ErrorAlert'

describe('ErrorAlert', () => {
  describe('Error Display', () => {
    it('should render error message', () => {
      render(<ErrorAlert message="Something went wrong" />)
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should render error icon', () => {
      const { container } = render(<ErrorAlert message="Error" />)
      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })

    it('should have alert role for accessibility', () => {
      render(<ErrorAlert message="Error occurred" />)
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })

  describe('Dismiss Functionality', () => {
    it('should render dismiss button when onDismiss provided', () => {
      const handleDismiss = jest.fn()
      render(<ErrorAlert message="Error" onDismiss={handleDismiss} />)
      expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
    })

    it('should call onDismiss when dismiss button clicked', async () => {
      const handleDismiss = jest.fn()
      render(<ErrorAlert message="Error" onDismiss={handleDismiss} />)
      await userEvent.click(screen.getByRole('button', { name: /dismiss/i }))
      expect(handleDismiss).toHaveBeenCalledTimes(1)
    })

    it('should not render dismiss button when onDismiss not provided', () => {
      render(<ErrorAlert message="Error" />)
      expect(screen.queryByRole('button', { name: /dismiss/i })).not.toBeInTheDocument()
    })
  })

  describe('Retry Functionality', () => {
    it('should render retry button when onRetry provided', () => {
      const handleRetry = jest.fn()
      render(<ErrorAlert message="Error" onRetry={handleRetry} />)
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    it('should call onRetry when retry clicked', async () => {
      const handleRetry = jest.fn()
      render(<ErrorAlert message="Error" onRetry={handleRetry} />)
      await userEvent.click(screen.getByRole('button', { name: /retry/i }))
      expect(handleRetry).toHaveBeenCalledTimes(1)
    })

    it('should not render retry button when onRetry not provided', () => {
      render(<ErrorAlert message="Error" />)
      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
    })
  })

  describe('Error Object Handling', () => {
    it('should handle Error object', () => {
      const error = new Error('Test error message')
      render(<ErrorAlert message={error} />)
      // getErrorMessage should extract a user-friendly message
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('should handle unknown error type', () => {
      render(<ErrorAlert message={{ custom: 'error' }} />)
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })
  })
})
