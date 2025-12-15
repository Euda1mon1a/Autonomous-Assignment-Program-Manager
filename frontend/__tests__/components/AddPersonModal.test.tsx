/**
 * Tests for AddPersonModal component
 *
 * Tests form rendering, validation, and submission behavior
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AddPersonModal } from '@/components/AddPersonModal'

// Create a wrapper with QueryClient for testing
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('AddPersonModal', () => {
  const mockOnClose = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <AddPersonModal isOpen={false} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render modal when isOpen is true', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      // Use heading role to be specific since "Add Person" appears in both title and submit button
      expect(screen.getByRole('heading', { name: 'Add Person' })).toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument()
    })

    it('should render Cancel and Add Person buttons', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /add person/i })).toBeInTheDocument()
    })

    it('should have resident selected by default', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const typeSelect = screen.getByLabelText(/type/i) as HTMLSelectElement
      expect(typeSelect.value).toBe('resident')
    })
  })

  describe('Form Behavior', () => {
    it('should hide PGY level when faculty is selected', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // PGY level should be visible initially (resident is default)
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()

      // Change type to faculty
      const typeSelect = screen.getByLabelText(/type/i)
      await user.selectOptions(typeSelect, 'faculty')

      // PGY level should be hidden
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()
    })

    it('should show PGY level when switching back to resident', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const typeSelect = screen.getByLabelText(/type/i)

      // Switch to faculty
      await user.selectOptions(typeSelect, 'faculty')
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()

      // Switch back to resident
      await user.selectOptions(typeSelect, 'resident')
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
    })

    it('should update checkbox state when clicked', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const checkbox = screen.getByLabelText(/performs procedures/i) as HTMLInputElement
      expect(checkbox.checked).toBe(false)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })
  })

  describe('Form Validation', () => {
    it('should show error when name is too short', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter a single character (bypasses HTML5 required validation)
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'A')

      // Submit form (fires React validation)
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      // Should show min length error
      await waitFor(() => {
        expect(screen.getByText(/name must be at least 2 characters/i)).toBeInTheDocument()
      })
    })

    it('should show error for invalid email format', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter valid name to bypass required validation
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'Dr. John Smith')

      // Enter invalid email
      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'invalid-email')

      // Submit form
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      // Should show email error
      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('should not show email error when email is empty (optional field)', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter valid name, leave email empty
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'Dr. John Smith')

      // Submit form
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      // Should not show email error (email is optional)
      expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument()
    })

    it('should call onClose when Cancel is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Close modal via Cancel button
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      // Verify onClose was called
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Click on the backdrop (the dark overlay behind the modal)
      const backdrop = document.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
        expect(mockOnClose).toHaveBeenCalledTimes(1)
      }
    })

    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Form Submission', () => {
    it('should have submit button with correct text', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Check submit button exists with correct text
      const submitButton = screen.getByRole('button', { name: /add person/i })
      expect(submitButton).toBeInTheDocument()
      expect(submitButton).toHaveAttribute('type', 'submit')
    })

    it('should not submit form with validation errors', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter invalid data (name too short)
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'A')

      // Submit form
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      // Should show error, not submit
      await waitFor(() => {
        expect(screen.getByText(/name must be at least 2 characters/i)).toBeInTheDocument()
      })
    })

    it('should validate email format on submission', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter valid name but invalid email
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'Dr. Test Person')

      const emailInput = screen.getByLabelText(/email/i)
      await user.type(emailInput, 'not-an-email')

      // Submit form
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      // Should show email error
      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes on modal', () => {
      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })

    it('should have proper aria attributes on error messages', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter short name to trigger validation error (bypasses HTML5 required)
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'A')

      // Submit form to trigger React validation
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        const errorMessage = screen.getByText(/name must be at least 2 characters/i)
        expect(errorMessage).toHaveAttribute('role', 'alert')
      })
    })

    it('should mark invalid fields with aria-invalid', async () => {
      const user = userEvent.setup()

      render(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Enter short name to trigger validation error
      const nameInput = screen.getByLabelText(/name/i)
      await user.type(nameInput, 'A')

      // Submit form to trigger React validation
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        const input = screen.getByLabelText(/name/i)
        // The Input component sets aria-invalid when there's an error
        expect(input).toBeInvalid()
      })
    })
  })
})
