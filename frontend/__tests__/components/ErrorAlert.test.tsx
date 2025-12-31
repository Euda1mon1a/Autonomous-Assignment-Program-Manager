import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { ErrorAlert } from '@/components/ErrorAlert'

describe('ErrorAlert', () => {
  describe('Error Display', () => {
    it('should render error message', () => {
      render(<ErrorAlert message="Something went wrong" />)
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('should render error title', () => {
      render(<ErrorAlert title="Error" message="Failed" />)
      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    it('should use default title when not provided', () => {
      render(<ErrorAlert message="Failed" />)
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    it('should render error icon', () => {
      const { container } = render(<ErrorAlert message="Error" />)
      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })
  })

  describe('Dismissible Functionality', () => {
    it('should render close button when dismissible', () => {
      render(<ErrorAlert message="Error" dismissible />)
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument()
    })

    it('should call onDismiss when close clicked', async () => {
      const handleDismiss = jest.fn()
      render(
        <ErrorAlert message="Error" dismissible onDismiss={handleDismiss} />
      )
      await userEvent.click(screen.getByRole('button', { name: /close/i }))
      expect(handleDismiss).toHaveBeenCalledTimes(1)
    })

    it('should not render close button when not dismissible', () => {
      render(<ErrorAlert message="Error" />)
      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
    })
  })

  describe('Error Details', () => {
    it('should render error details when provided', () => {
      render(<ErrorAlert message="Error" details="Stack trace here" />)
      expect(screen.getByText('Stack trace here')).toBeInTheDocument()
    })

    it('should toggle details visibility', async () => {
      render(<ErrorAlert message="Error" details="Details" />)
      const toggleButton = screen.getByText(/show details/i)
      await userEvent.click(toggleButton)
      expect(screen.getByText('Details')).toBeVisible()
    })
  })

  describe('Severity Variants', () => {
    it('should render error severity', () => {
      const { container } = render(<ErrorAlert message="Error" severity="error" />)
      expect(container.firstChild).toHaveClass('error')
    })

    it('should render warning severity', () => {
      const { container } = render(<ErrorAlert message="Warning" severity="warning" />)
      expect(container.firstChild).toHaveClass('warning')
    })
  })

  describe('Retry Action', () => {
    it('should render retry button when provided', () => {
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
  })
})
