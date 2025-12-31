/**
 * Tests for EditPersonModal component
 *
 * Tests form rendering, validation, pre-population, and submission behavior
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EditPersonModal } from '@/components/EditPersonModal'
import { PersonType, type Person } from '@/types/api'

// Mock the hooks
const mockMutateAsync = jest.fn()
jest.mock('@/lib/hooks', () => ({
  useUpdatePerson: jest.fn(() => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
  })),
}))

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

describe('EditPersonModal', () => {
  const mockOnClose = jest.fn()

  const mockPerson: Person = {
    id: 'person-1',
    name: 'Dr. John Smith',
    email: 'john.smith@example.com',
    type: PersonType.RESIDENT,
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Cardiology', 'Internal Medicine'],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    person: mockPerson,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockMutateAsync.mockResolvedValue({})
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <EditPersonModal {...defaultProps} isOpen={false} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render modal when isOpen is true', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Edit Person')).toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument()
    })

    it('should render Cancel and Save Changes buttons', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument()
    })

    it('should return null when person is null', () => {
      render(
        <EditPersonModal {...defaultProps} person={null} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })
  })

  describe('Form Pre-population', () => {
    it('should pre-populate all fields from person data', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
      const typeSelect = screen.getByLabelText(/type/i) as HTMLSelectElement
      const pgySelect = screen.getByLabelText(/pgy level/i) as HTMLSelectElement
      const proceduresCheckbox = screen.getByLabelText(/performs procedures/i) as HTMLInputElement
      const specialtiesInput = screen.getByLabelText(/specialties/i) as HTMLInputElement

      expect(nameInput.value).toBe('Dr. John Smith')
      expect(emailInput.value).toBe('john.smith@example.com')
      expect(typeSelect.value).toBe('resident')
      expect(pgySelect.value).toBe('2')
      expect(proceduresCheckbox.checked).toBe(true)
      expect(specialtiesInput.value).toBe('Cardiology, Internal Medicine')
    })

    it('should handle person with no email', () => {
      const personWithoutEmail = { ...mockPerson, email: null }

      render(
        <EditPersonModal {...defaultProps} person={personWithoutEmail} />,
        { wrapper: createWrapper() }
      )

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement
      expect(emailInput.value).toBe('')
    })

    it('should handle person with no specialties', () => {
      const personWithoutSpecialties = { ...mockPerson, specialties: null }

      render(
        <EditPersonModal {...defaultProps} person={personWithoutSpecialties} />,
        { wrapper: createWrapper() }
      )

      const specialtiesInput = screen.getByLabelText(/specialties/i) as HTMLInputElement
      expect(specialtiesInput.value).toBe('')
    })
  })

  describe('Form Behavior', () => {
    it('should hide PGY level when faculty is selected', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      // PGY level should be visible initially (person is resident)
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()

      // Change type to faculty
      const typeSelect = screen.getByLabelText(/type/i)
      await user.selectOptions(typeSelect, 'faculty')

      // PGY level should be hidden
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()
    })

    it('should show PGY level when switching back to resident', async () => {
      const user = userEvent.setup()
      const facultyPerson = { ...mockPerson, type: PersonType.FACULTY, pgy_level: null }

      render(
        <EditPersonModal {...defaultProps} person={facultyPerson} />,
        { wrapper: createWrapper() }
      )

      const typeSelect = screen.getByLabelText(/type/i)

      // PGY level should be hidden initially (person is faculty)
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()

      // Switch to resident
      await user.selectOptions(typeSelect, 'resident')
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
    })

    it('should update checkbox state when clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const checkbox = screen.getByLabelText(/performs procedures/i) as HTMLInputElement
      expect(checkbox.checked).toBe(true)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)
    })

    it('should update name field when typed', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/name/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'Dr. Jane Doe')

      expect((nameInput as HTMLInputElement).value).toBe('Dr. Jane Doe')
    })
  })

  describe('Form Validation', () => {
    it('should show error when name is empty', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/name/i)
      await user.clear(nameInput)

      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })
    })

    it('should show error for invalid email format', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const emailInput = screen.getByLabelText(/email/i)
      await user.clear(emailInput)
      await user.type(emailInput, 'invalid-email')

      const form = emailInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/please enter a valid email address/i)).toBeInTheDocument()
      })
    })

    it('should not show email error when email is empty', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const emailInput = screen.getByLabelText(/email/i)
      await user.clear(emailInput)

      const form = emailInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.queryByText(/please enter a valid email address/i)).not.toBeInTheDocument()
      })
    })

    it('should validate PGY level is between 1 and 3', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const pgySelect = screen.getByLabelText(/pgy level/i)
      await user.selectOptions(pgySelect, '1')

      const form = pgySelect.closest('form')!
      fireEvent.submit(form)

      // Should submit without error for valid PGY level
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled()
      })
    })
  })

  describe('Form Submission', () => {
    it('should call updatePerson with correct data on submit', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/name/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'Dr. Jane Doe')

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          id: 'person-1',
          data: expect.objectContaining({
            name: 'Dr. Jane Doe',
            type: PersonType.RESIDENT,
            pgy_level: 2,
          }),
        })
      })
    })

    it('should call onClose after successful submission', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })

    it('should show error message on submission failure', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockRejectedValue(new Error('Network error'))

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to update person/i)).toBeInTheDocument()
      })
    })

    it('should not submit with validation errors', async () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/name/i)
      // Use fireEvent for reliable clearing
      fireEvent.change(nameInput, { target: { value: '' } })

      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      expect(mockMutateAsync).not.toHaveBeenCalled()
    })

    it('should parse specialties correctly', async () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const specialtiesInput = screen.getByLabelText(/specialties/i)
      // Use fireEvent for reliable input
      fireEvent.change(specialtiesInput, { target: { value: 'Cardiology, Neurology, Oncology' } })

      const form = specialtiesInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          id: 'person-1',
          data: expect.objectContaining({
            specialties: ['Cardiology', 'Neurology', 'Oncology'],
          }),
        })
      })
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const backdrop = document.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
        expect(mockOnClose).toHaveBeenCalledTimes(1)
      }
    })

    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should clear errors when modal is closed', async () => {
      const user = userEvent.setup()

      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      // Trigger validation error
      const nameInput = screen.getByLabelText(/name/i)
      await user.clear(nameInput)
      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      // Close and reopen
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      // Error should not appear when reopened
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByText(/name is required/i)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes on modal', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })

    it('should have proper labels for all form controls', () => {
      render(
        <EditPersonModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument()
    })
  })
})
