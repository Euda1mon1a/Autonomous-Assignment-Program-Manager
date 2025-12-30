/**
 * Tests for LoginForm component
 *
 * Tests form rendering, validation, submission behavior, and error handling
 * for the authentication entry point.
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginForm } from '@/components/LoginForm'

// Mock the AuthContext
const mockLogin = jest.fn()
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
  }),
}))

// Mock the validation module
jest.mock('@/lib/validation', () => ({
  validateRequired: (value: string, fieldName: string) => {
    if (!value || !value.trim()) {
      return `${fieldName} is required`
    }
    return null
  },
}))

describe('LoginForm', () => {
  const mockOnSuccess = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockLogin.mockReset()
  })

  describe('Rendering', () => {
    it('should render username and password fields', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    })

    it('should render username input with correct attributes', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      expect(usernameInput).toHaveAttribute('type', 'text')
      expect(usernameInput).toHaveAttribute('id', 'username')
      expect(usernameInput).toHaveAttribute('autocomplete', 'username')
      expect(usernameInput).toHaveAttribute('placeholder', 'Enter your username')
    })

    it('should render password input with correct attributes', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      const passwordInput = screen.getByLabelText(/password/i)
      expect(passwordInput).toHaveAttribute('type', 'password')
      expect(passwordInput).toHaveAttribute('id', 'password')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
      expect(passwordInput).toHaveAttribute('placeholder', 'Enter your password')
    })

    it('should render sign in button', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      expect(submitButton).toBeInTheDocument()
      expect(submitButton).toHaveAttribute('type', 'submit')
    })

    it('should render development credentials info section', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      expect(screen.getByText(/local dev credentials/i)).toBeInTheDocument()
      expect(screen.getByText('admin')).toBeInTheDocument()
    })

    it('should render help section', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      expect(screen.getByText(/need help signing in/i)).toBeInTheDocument()
      expect(screen.getByText(/contact your program administrator/i)).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should show username required error when empty on blur then submit', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      // Touch the username field and leave it empty
      await user.click(usernameInput)
      await user.click(passwordInput) // blur by clicking elsewhere

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument()
      })

      // Login should not be called
      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('should show password required error when empty on submit', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      // Fill username but leave password empty
      await user.type(usernameInput, 'testuser')
      await user.click(passwordInput)
      await user.click(usernameInput) // blur password field

      // Try to submit
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })

      // Login should not be called
      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('should validate both fields are required on submit with empty form', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      // Touch both fields by clicking and blurring to trigger validation
      // (The submit button is disabled when form is invalid, so we can't click it directly)
      await user.click(usernameInput)
      await user.click(passwordInput) // This blurs username
      await user.click(usernameInput) // This blurs password

      // Should show both validation errors after fields are touched
      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument()
        expect(screen.getByText(/password is required/i)).toBeInTheDocument()
      })

      // Login should not be called
      expect(mockLogin).not.toHaveBeenCalled()
    })

    it('should clear validation error when valid input is provided', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      // Trigger validation error
      await user.click(usernameInput)
      await user.click(passwordInput) // blur

      // Submit to trigger error display
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument()
      })

      // Now provide valid input
      await user.type(usernameInput, 'validuser')

      // Error should clear (or not be visible for the username field)
      await waitFor(() => {
        expect(screen.queryByText(/username is required/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Form Submission', () => {
    it('should call login with credentials on valid submission', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValueOnce({})

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'testpassword',
        })
      })
    })

    it('should call onSuccess callback after successful login', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValueOnce({})

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled()
      })
    })

    it('should work without onSuccess callback', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValueOnce({})

      // Render without onSuccess prop
      render(<LoginForm />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Should not throw
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })
    })
  })

  describe('Form Disabled State', () => {
    it('should disable form fields during submission', async () => {
      const user = userEvent.setup()
      // Make login hang so we can verify disabled state
      mockLogin.mockImplementation(() => new Promise(() => {}))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')
      await user.click(submitButton)

      // Fields should be disabled during submission
      await waitFor(() => {
        expect(usernameInput).toBeDisabled()
        expect(passwordInput).toBeDisabled()
        expect(submitButton).toBeDisabled()
      })
    })

    it('should show loading state during submission', async () => {
      const user = userEvent.setup()
      // Make login hang
      mockLogin.mockImplementation(() => new Promise(() => {}))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Should show loading text - use queryByRole with updated button text
      // The button text changes from "Sign In" to "Signing in..." during loading
      await waitFor(() => {
        const loadingButton = screen.getByRole('button')
        expect(loadingButton).toHaveTextContent(/signing in/i)
      })
    })

    it('should re-enable form after successful submission', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValueOnce({})

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled()
      })

      // Form should be usable again (not disabled)
      await waitFor(() => {
        expect(usernameInput).not.toBeDisabled()
        expect(passwordInput).not.toBeDisabled()
      })
    })

    it('should re-enable form after failed submission', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'wrongpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(usernameInput).not.toBeDisabled()
        expect(passwordInput).not.toBeDisabled()
        expect(submitButton).not.toBeDisabled()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display API error messages', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValueOnce(new Error('Invalid username or password'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'wrongpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
      })
    })

    it('should handle network errors gracefully', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValueOnce(new Error('Network error: failed to fetch'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Should show a network error message
      await waitFor(() => {
        const errorMessage = screen.getByText(/network error/i)
        expect(errorMessage).toBeInTheDocument()
      })
    })

    it('should handle 401 errors with specific message', async () => {
      const user = userEvent.setup()
      const error401 = new Error('401 Unauthorized')
      mockLogin.mockRejectedValueOnce(error401)

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'wrongpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })
    })

    it('should handle 404 errors with helpful message', async () => {
      const user = userEvent.setup()
      const error404 = new Error('404 Not Found')
      mockLogin.mockRejectedValueOnce(error404)

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/api endpoint not found/i)).toBeInTheDocument()
      })
    })

    it('should display error with alert icon', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValueOnce(new Error('Test error'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Error container should have the alert styling
      await waitFor(() => {
        const errorContainer = screen.getByText(/test error/i).closest('div')
        expect(errorContainer).toHaveClass('bg-red-50')
      })
    })

    it('should clear error on new submission attempt', async () => {
      const user = userEvent.setup()

      // First submission fails
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'wrongpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
      })

      // Second submission succeeds
      mockLogin.mockResolvedValueOnce({})

      // Clear and re-enter password
      await user.clear(passwordInput)
      await user.type(passwordInput, 'correctpassword')
      await user.click(submitButton)

      // Error should be cleared
      await waitFor(() => {
        expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument()
      })
    })

    it('should not call onSuccess when login fails', async () => {
      const user = userEvent.setup()
      mockLogin.mockRejectedValueOnce(new Error('Login failed'))

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword')

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      await user.click(submitButton)

      // Wait for error to appear
      await waitFor(() => {
        expect(screen.getByText(/login failed/i)).toBeInTheDocument()
      })

      // onSuccess should NOT have been called
      expect(mockOnSuccess).not.toHaveBeenCalled()
    })
  })

  describe('Input Interaction', () => {
    it('should update username value on input', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i) as HTMLInputElement
      await user.type(usernameInput, 'newuser')

      expect(usernameInput.value).toBe('newuser')
    })

    it('should update password value on input', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement
      await user.type(passwordInput, 'secretpass')

      expect(passwordInput.value).toBe('secretpass')
    })

    it('should handle form submission via Enter key', async () => {
      const user = userEvent.setup()
      mockLogin.mockResolvedValueOnce({})

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      await user.type(usernameInput, 'testuser')
      await user.type(passwordInput, 'testpassword{Enter}')

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({
          username: 'testuser',
          password: 'testpassword',
        })
      })
    })
  })

  describe('Accessibility', () => {
    it('should have associated labels with form inputs', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)
      const passwordInput = screen.getByLabelText(/password/i)

      // Inputs should be properly associated with labels via htmlFor/id
      expect(usernameInput).toHaveAttribute('id', 'username')
      expect(passwordInput).toHaveAttribute('id', 'password')
    })

    it('should have proper form structure', () => {
      render(<LoginForm onSuccess={mockOnSuccess} />)

      const form = document.querySelector('form')
      expect(form).toBeInTheDocument()
    })

    it('should apply error styling to invalid fields', async () => {
      const user = userEvent.setup()

      render(<LoginForm onSuccess={mockOnSuccess} />)

      const usernameInput = screen.getByLabelText(/username/i)

      // Touch the field by clicking and blurring to trigger validation error styling
      await user.click(usernameInput)
      // Blur by clicking elsewhere (password field)
      const passwordInput = screen.getByLabelText(/password/i)
      await user.click(passwordInput)

      // Now the field is touched and empty, so should show error styling
      await waitFor(() => {
        expect(usernameInput).toHaveClass('border-red-500')
      })
    })
  })
})
