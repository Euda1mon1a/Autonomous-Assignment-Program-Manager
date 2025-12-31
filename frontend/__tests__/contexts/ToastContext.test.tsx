/**
 * Tests for ToastContext and ToastProvider
 *
 * Tests toast notification management, queue handling, dismissal,
 * and various toast types with options.
 */
import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ToastProvider, useToast } from '@/contexts/ToastContext'
import { getErrorMessage } from '@/lib/errors'

// Mock the error utility
jest.mock('@/lib/errors', () => ({
  getErrorMessage: jest.fn((error) => {
    if (typeof error === 'string') return error
    if (error instanceof Error) return error.message
    if (error && typeof error === 'object' && 'message' in error) {
      return String(error.message)
    }
    return 'An unexpected error occurred. Please try again.'
  }),
}))

// Mock the Toast component to simplify testing
jest.mock('@/components/Toast', () => ({
  ToastContainer: ({ toasts, onDismiss }: any) => {
    if (toasts.length === 0) return null
    return (
      <div data-testid="toast-container">
        {toasts.map((toast: any) => (
          <div
            key={toast.id}
            data-testid={`toast-${toast.type}`}
            data-toast-id={toast.id}
            role="alert"
          >
            <span data-testid="toast-message">{toast.message}</span>
            <span data-testid="toast-type">{toast.type}</span>
            {toast.duration !== undefined && (
              <span data-testid="toast-duration">{toast.duration}</span>
            )}
            {toast.persistent !== undefined && (
              <span data-testid="toast-persistent">{String(toast.persistent)}</span>
            )}
            {toast.action && (
              <button
                data-testid="toast-action"
                onClick={toast.action.onClick}
              >
                {toast.action.label}
              </button>
            )}
            <button
              data-testid="toast-dismiss"
              onClick={() => onDismiss(toast.id)}
            >
              Dismiss
            </button>
          </div>
        ))}
      </div>
    )
  },
}))

// Test component that uses the toast context
function TestConsumer({ testId = 'test-consumer' }: { testId?: string }) {
  const { toast, showSuccess, showError, dismissAll } = useToast()

  return (
    <div data-testid={testId}>
      <button
        data-testid="btn-success"
        onClick={() => toast.success('Success message')}
      >
        Success
      </button>
      <button
        data-testid="btn-error"
        onClick={() => toast.error('Error message')}
      >
        Error
      </button>
      <button
        data-testid="btn-warning"
        onClick={() => toast.warning('Warning message')}
      >
        Warning
      </button>
      <button
        data-testid="btn-info"
        onClick={() => toast.info('Info message')}
      >
        Info
      </button>
      <button
        data-testid="btn-dismiss-all"
        onClick={() => toast.dismissAll()}
      >
        Dismiss All
      </button>
      <button
        data-testid="btn-legacy-success"
        onClick={() => showSuccess('Legacy success')}
      >
        Legacy Success
      </button>
      <button
        data-testid="btn-legacy-error"
        onClick={() => showError('Legacy error')}
      >
        Legacy Error
      </button>
      <button
        data-testid="btn-dismiss-all-legacy"
        onClick={() => dismissAll()}
      >
        Dismiss All Legacy
      </button>
    </div>
  )
}

// Component to test manual dismiss
function TestDismissConsumer() {
  const { toast } = useToast()
  const [toastId, setToastId] = React.useState<string>('')

  return (
    <div>
      <button
        data-testid="create-toast"
        onClick={() => {
          const id = toast.info('Dismissable toast')
          setToastId(id)
        }}
      >
        Create Toast
      </button>
      <button
        data-testid="dismiss-toast"
        onClick={() => toast.dismiss(toastId)}
      >
        Dismiss Toast
      </button>
      <div data-testid="toast-id">{toastId}</div>
    </div>
  )
}

// Component to test toast options
function TestOptionsConsumer() {
  const { toast } = useToast()

  return (
    <div>
      <button
        data-testid="toast-custom-duration"
        onClick={() => toast.success('Custom duration', { duration: 3000 })}
      >
        Custom Duration
      </button>
      <button
        data-testid="toast-persistent"
        onClick={() => toast.warning('Persistent', { persistent: true })}
      >
        Persistent
      </button>
      <button
        data-testid="toast-with-action"
        onClick={() =>
          toast.info('With action', {
            action: {
              label: 'Undo',
              onClick: () => console.log('Action clicked'),
            },
          })
        }
      >
        With Action
      </button>
    </div>
  )
}

// Component to test queue management
function TestQueueConsumer() {
  const { toast } = useToast()

  return (
    <div>
      <button
        data-testid="add-toast"
        onClick={() => toast.success(`Toast ${Date.now()}`)}
      >
        Add Toast
      </button>
    </div>
  )
}

// Component that tests the useToast hook outside of provider
function InvalidConsumer() {
  try {
    useToast()
    return <div>No error thrown</div>
  } catch (error) {
    return <div data-testid="error-message">{(error as Error).message}</div>
  }
}

describe('ToastContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Provider Setup', () => {
    it('should render children within ToastProvider', () => {
      render(
        <ToastProvider>
          <div data-testid="child-content">Child Content</div>
        </ToastProvider>
      )

      expect(screen.getByTestId('child-content')).toBeInTheDocument()
      expect(screen.getByText('Child Content')).toBeInTheDocument()
    })

    it('should throw error when useToast is used outside ToastProvider', () => {
      // Suppress console.error for this test since we expect an error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      render(<InvalidConsumer />)

      expect(screen.getByTestId('error-message')).toHaveTextContent(
        'useToast must be used within a ToastProvider'
      )

      consoleSpy.mockRestore()
    })

    it('should provide toast context to nested components', () => {
      render(
        <ToastProvider>
          <div>
            <div>
              <TestConsumer />
            </div>
          </div>
        </ToastProvider>
      )

      expect(screen.getByTestId('test-consumer')).toBeInTheDocument()
    })

    it('should not show toast container initially', () => {
      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      expect(screen.queryByTestId('toast-container')).not.toBeInTheDocument()
    })
  })

  describe('Toast Types', () => {
    it('should show success toast', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-success'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
      })

      expect(screen.getByTestId('toast-message')).toHaveTextContent('Success message')
      expect(screen.getByTestId('toast-type')).toHaveTextContent('success')
    })

    it('should show error toast', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-error'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      expect(screen.getByTestId('toast-message')).toHaveTextContent('Error message')
      expect(screen.getByTestId('toast-type')).toHaveTextContent('error')
    })

    it('should show warning toast', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-warning'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-warning')).toBeInTheDocument()
      })

      expect(screen.getByTestId('toast-message')).toHaveTextContent('Warning message')
      expect(screen.getByTestId('toast-type')).toHaveTextContent('warning')
    })

    it('should show info toast', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-info'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-info')).toBeInTheDocument()
      })

      expect(screen.getByTestId('toast-message')).toHaveTextContent('Info message')
      expect(screen.getByTestId('toast-type')).toHaveTextContent('info')
    })
  })

  describe('Error Toast with getErrorMessage', () => {
    it('should handle string errors', async () => {
      const user = userEvent.setup()
      const mockGetErrorMessage = getErrorMessage as jest.Mock

      function TestErrorConsumer() {
        const { toast } = useToast()
        return (
          <button onClick={() => toast.error('Simple error string')}>
            Error
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestErrorConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      expect(mockGetErrorMessage).toHaveBeenCalledWith('Simple error string')
    })

    it('should handle Error objects', async () => {
      const user = userEvent.setup()
      const mockGetErrorMessage = getErrorMessage as jest.Mock

      function TestErrorConsumer() {
        const { toast } = useToast()
        return (
          <button onClick={() => toast.error(new Error('Error object message'))}>
            Error
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestErrorConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      expect(mockGetErrorMessage).toHaveBeenCalled()
      const callArg = mockGetErrorMessage.mock.calls[0][0]
      expect(callArg).toBeInstanceOf(Error)
    })

    it('should handle ApiError objects', async () => {
      const user = userEvent.setup()
      const mockGetErrorMessage = getErrorMessage as jest.Mock

      function TestErrorConsumer() {
        const { toast } = useToast()
        return (
          <button
            onClick={() =>
              toast.error({
                message: 'API error message',
                status: 404,
                detail: 'Not found',
              })
            }
          >
            Error
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestErrorConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      expect(mockGetErrorMessage).toHaveBeenCalledWith({
        message: 'API error message',
        status: 404,
        detail: 'Not found',
      })
    })

    it('should use default duration of 7000ms for error toasts', async () => {
      const user = userEvent.setup()

      function TestErrorConsumer() {
        const { toast } = useToast()
        return (
          <button onClick={() => toast.error('Error')}>
            Error
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestErrorConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-duration')).toHaveTextContent('7000')
      })
    })
  })

  describe('Toast Dismissal', () => {
    it('should dismiss a specific toast by ID', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestDismissConsumer />
        </ToastProvider>
      )

      // Create a toast
      await user.click(screen.getByTestId('create-toast'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-info')).toBeInTheDocument()
      })

      // Get the toast ID
      const toastId = screen.getByTestId('toast-id').textContent

      expect(toastId).toBeTruthy()

      // Dismiss the toast
      await user.click(screen.getByTestId('dismiss-toast'))

      await waitFor(() => {
        expect(screen.queryByTestId('toast-info')).not.toBeInTheDocument()
      })
    })

    it('should dismiss toast using dismiss button in toast', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-success'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('toast-dismiss'))

      await waitFor(() => {
        expect(screen.queryByTestId('toast-success')).not.toBeInTheDocument()
      })
    })

    it('should dismiss all toasts', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      // Create multiple toasts
      await user.click(screen.getByTestId('btn-success'))
      await user.click(screen.getByTestId('btn-error'))
      await user.click(screen.getByTestId('btn-warning'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
        expect(screen.getByTestId('toast-warning')).toBeInTheDocument()
      })

      // Dismiss all
      await user.click(screen.getByTestId('btn-dismiss-all'))

      await waitFor(() => {
        expect(screen.queryByTestId('toast-container')).not.toBeInTheDocument()
      })
    })
  })

  describe('Toast Options', () => {
    it('should accept custom duration', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestOptionsConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('toast-custom-duration'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-duration')).toHaveTextContent('3000')
      })
    })

    it('should support persistent toasts', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestOptionsConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button', { name: /persistent/i }))

      await waitFor(() => {
        // Query for the span inside the toast (not the button)
        const persistentSpan = screen.getByTestId('toast-container')
          .querySelector('[data-testid="toast-persistent"]')
        expect(persistentSpan).toHaveTextContent('true')
      })
    })

    it('should support action buttons', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestOptionsConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('toast-with-action'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-action')).toBeInTheDocument()
        expect(screen.getByTestId('toast-action')).toHaveTextContent('Undo')
      })
    })

    it('should call action onClick when action button is clicked', async () => {
      const user = userEvent.setup()
      const actionOnClick = jest.fn()

      function TestActionConsumer() {
        const { toast } = useToast()
        return (
          <button
            onClick={() =>
              toast.info('With action', {
                action: { label: 'Click me', onClick: actionOnClick },
              })
            }
          >
            Create
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestActionConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button', { name: 'Create' }))

      await waitFor(() => {
        expect(screen.getByTestId('toast-action')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('toast-action'))

      expect(actionOnClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('Queue Management (MAX_TOASTS = 3)', () => {
    it('should show maximum of 3 toasts at once', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestQueueConsumer />
        </ToastProvider>
      )

      // Add 5 toasts
      for (let i = 0; i < 5; i++) {
        await user.click(screen.getByTestId('add-toast'))
        // Small delay to ensure unique IDs
        await act(async () => {
          await new Promise((resolve) => setTimeout(resolve, 10))
        })
      }

      await waitFor(() => {
        const toasts = screen.queryAllByRole('alert')
        expect(toasts.length).toBe(3)
      })
    })

    it('should remove oldest toast when queue is full', async () => {
      const user = userEvent.setup()

      function TestQueueOrderConsumer() {
        const { toast } = useToast()
        return (
          <div>
            <button
              data-testid="toast-1"
              onClick={() => toast.success('Toast 1')}
            >
              Toast 1
            </button>
            <button
              data-testid="toast-2"
              onClick={() => toast.success('Toast 2')}
            >
              Toast 2
            </button>
            <button
              data-testid="toast-3"
              onClick={() => toast.success('Toast 3')}
            >
              Toast 3
            </button>
            <button
              data-testid="toast-4"
              onClick={() => toast.success('Toast 4')}
            >
              Toast 4
            </button>
          </div>
        )
      }

      render(
        <ToastProvider>
          <TestQueueOrderConsumer />
        </ToastProvider>
      )

      // Add first 3 toasts
      await user.click(screen.getByTestId('toast-1'))
      await user.click(screen.getByTestId('toast-2'))
      await user.click(screen.getByTestId('toast-3'))

      await waitFor(() => {
        const messages = screen.getAllByTestId('toast-message')
        expect(messages).toHaveLength(3)
        expect(messages[0]).toHaveTextContent('Toast 1')
        expect(messages[1]).toHaveTextContent('Toast 2')
        expect(messages[2]).toHaveTextContent('Toast 3')
      })

      // Add 4th toast - should remove Toast 1
      await user.click(screen.getByTestId('toast-4'))

      await waitFor(() => {
        const messages = screen.getAllByTestId('toast-message')
        expect(messages).toHaveLength(3)
        expect(messages[0]).toHaveTextContent('Toast 2')
        expect(messages[1]).toHaveTextContent('Toast 3')
        expect(messages[2]).toHaveTextContent('Toast 4')
      })
    })
  })

  describe('Legacy Methods (Deprecated)', () => {
    it('should support legacy showSuccess method', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-legacy-success'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
        expect(screen.getByTestId('toast-message')).toHaveTextContent('Legacy success')
      })
    })

    it('should support legacy showError method', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-legacy-error'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
        expect(screen.getByTestId('toast-message')).toHaveTextContent('Legacy error')
      })
    })

    it('should support legacy dismissAll method', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      await user.click(screen.getByTestId('btn-success'))
      await user.click(screen.getByTestId('btn-error'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      await user.click(screen.getByTestId('btn-dismiss-all-legacy'))

      await waitFor(() => {
        expect(screen.queryByTestId('toast-container')).not.toBeInTheDocument()
      })
    })

    it('should support legacy showToast method', async () => {
      const user = userEvent.setup()

      function TestLegacyShowToast() {
        const { showToast } = useToast()
        return (
          <button onClick={() => showToast('warning', 'Legacy warning')}>
            Show Toast
          </button>
        )
      }

      render(
        <ToastProvider>
          <TestLegacyShowToast />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-warning')).toBeInTheDocument()
        expect(screen.getByTestId('toast-message')).toHaveTextContent('Legacy warning')
      })
    })
  })

  describe('Return Values', () => {
    it('should return toast ID from success method', async () => {
      function TestReturnValue() {
        const { toast } = useToast()
        const [id, setId] = React.useState('')

        return (
          <div>
            <button
              onClick={() => {
                const toastId = toast.success('Test')
                setId(toastId)
              }}
            >
              Create
            </button>
            <div data-testid="returned-id">{id}</div>
          </div>
        )
      }

      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestReturnValue />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        const returnedId = screen.getByTestId('returned-id').textContent
        expect(returnedId).toBeTruthy()
        expect(returnedId).toMatch(/^toast-/)
      })
    })

    it('should return toast ID from all toast methods', async () => {
      function TestAllReturnValues() {
        const { toast } = useToast()
        const [ids, setIds] = React.useState<string[]>([])

        return (
          <div>
            <button
              onClick={() => {
                const id1 = toast.success('Test')
                const id2 = toast.error('Test')
                const id3 = toast.warning('Test')
                const id4 = toast.info('Test')
                setIds([id1, id2, id3, id4])
              }}
            >
              Create
            </button>
            <div data-testid="all-ids">{ids.join(',')}</div>
          </div>
        )
      }

      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestAllReturnValues />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        const allIds = screen.getByTestId('all-ids').textContent || ''
        const idArray = allIds.split(',')
        // Should have 4 IDs, but MAX_TOASTS = 3, so only 3 visible
        expect(idArray.length).toBe(4)
        idArray.forEach((id) => {
          expect(id).toMatch(/^toast-/)
        })
      })
    })
  })

  describe('Multiple Consumers', () => {
    it('should provide same toast methods to multiple consumers', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer testId="consumer-1" />
          <TestConsumer testId="consumer-2" />
        </ToastProvider>
      )

      const consumer1 = screen.getByTestId('consumer-1')
      const consumer2 = screen.getByTestId('consumer-2')

      expect(consumer1).toBeInTheDocument()
      expect(consumer2).toBeInTheDocument()

      // Trigger toast from first consumer
      await user.click(
        consumer1.querySelector('[data-testid="btn-success"]') as HTMLElement
      )

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
      })
    })

    it('should show toasts triggered from different consumers', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer testId="consumer-1" />
          <TestConsumer testId="consumer-2" />
        </ToastProvider>
      )

      const consumer1 = screen.getByTestId('consumer-1')
      const consumer2 = screen.getByTestId('consumer-2')

      // Trigger toast from first consumer
      await user.click(
        consumer1.querySelector('[data-testid="btn-success"]') as HTMLElement
      )

      // Trigger toast from second consumer
      await user.click(
        consumer2.querySelector('[data-testid="btn-error"]') as HTMLElement
      )

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })
    })

    it('should dismiss all toasts from any consumer', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer testId="consumer-1" />
          <TestConsumer testId="consumer-2" />
        </ToastProvider>
      )

      const consumer1 = screen.getByTestId('consumer-1')
      const consumer2 = screen.getByTestId('consumer-2')

      // Create toasts from both consumers
      await user.click(
        consumer1.querySelector('[data-testid="btn-success"]') as HTMLElement
      )
      await user.click(
        consumer2.querySelector('[data-testid="btn-error"]') as HTMLElement
      )

      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })

      // Dismiss all from consumer1
      await user.click(
        consumer1.querySelector('[data-testid="btn-dismiss-all"]') as HTMLElement
      )

      await waitFor(() => {
        expect(screen.queryByTestId('toast-container')).not.toBeInTheDocument()
      })
    })
  })

  describe('Edge Cases', () => {
    it('should handle rapid toast creation', async () => {
      const user = userEvent.setup()

      render(
        <ToastProvider>
          <TestConsumer />
        </ToastProvider>
      )

      // Rapidly create toasts
      await user.click(screen.getByTestId('btn-success'))
      await user.click(screen.getByTestId('btn-error'))
      await user.click(screen.getByTestId('btn-warning'))
      await user.click(screen.getByTestId('btn-info'))

      await waitFor(() => {
        const toasts = screen.queryAllByRole('alert')
        expect(toasts.length).toBe(3) // MAX_TOASTS = 3
      })
    })

    it('should handle dismissing non-existent toast ID', async () => {
      const user = userEvent.setup()

      function TestInvalidDismiss() {
        const { toast } = useToast()
        return (
          <div>
            <button
              onClick={() => {
                toast.success('Test')
                toast.dismiss('non-existent-id')
              }}
            >
              Create and Dismiss Invalid
            </button>
          </div>
        )
      }

      render(
        <ToastProvider>
          <TestInvalidDismiss />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      // Toast should still be visible since we dismissed invalid ID
      await waitFor(() => {
        expect(screen.getByTestId('toast-success')).toBeInTheDocument()
      })
    })

    it('should handle empty error messages', async () => {
      const user = userEvent.setup()

      function TestEmptyError() {
        const { toast } = useToast()
        return <button onClick={() => toast.error('')}>Error</button>
      }

      render(
        <ToastProvider>
          <TestEmptyError />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        expect(screen.getByTestId('toast-error')).toBeInTheDocument()
      })
    })

    it('should generate unique IDs for each toast', async () => {
      const user = userEvent.setup()

      function TestUniqueIds() {
        const { toast } = useToast()
        const [ids, setIds] = React.useState<string[]>([])

        return (
          <div>
            <button
              onClick={() => {
                const id1 = toast.success('Toast 1')
                const id2 = toast.success('Toast 2')
                const id3 = toast.success('Toast 3')
                setIds([id1, id2, id3])
              }}
            >
              Create
            </button>
            <div data-testid="ids">{JSON.stringify(ids)}</div>
          </div>
        )
      }

      render(
        <ToastProvider>
          <TestUniqueIds />
        </ToastProvider>
      )

      await user.click(screen.getByRole('button'))

      await waitFor(() => {
        const idsText = screen.getByTestId('ids').textContent || '[]'
        const ids = JSON.parse(idsText)
        expect(ids).toHaveLength(3)
        expect(new Set(ids).size).toBe(3) // All IDs are unique
      })
    })
  })

  describe('Context Value Stability', () => {
    it('should provide stable toast method references', async () => {
      // Track function references
      const successRefs: unknown[] = []
      const errorRefs: unknown[] = []
      const dismissRefs: unknown[] = []

      function ReferenceTracker() {
        const { toast } = useToast()

        // Track individual method references on render
        React.useLayoutEffect(() => {
          successRefs.push(toast.success)
          errorRefs.push(toast.error)
          dismissRefs.push(toast.dismiss)
        })

        return null
      }

      const { rerender } = render(
        <ToastProvider>
          <ReferenceTracker />
        </ToastProvider>
      )

      // Wait for initial render
      await waitFor(() => {
        expect(successRefs.length).toBeGreaterThan(0)
      })

      // Force rerender
      await act(async () => {
        rerender(
          <ToastProvider>
            <ReferenceTracker />
          </ToastProvider>
        )
      })

      await waitFor(() => {
        expect(successRefs.length).toBeGreaterThan(1)
      })

      // Individual toast methods should be stable across renders (useCallback)
      expect(successRefs[0]).toBe(successRefs[1])
      expect(errorRefs[0]).toBe(errorRefs[1])
      expect(dismissRefs[0]).toBe(dismissRefs[1])
    })
  })
})
