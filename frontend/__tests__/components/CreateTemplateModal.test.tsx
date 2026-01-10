/**
 * Tests for CreateTemplateModal component
 *
 * Tests form rendering, validation, and submission behavior
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CreateTemplateModal } from '@/components/CreateTemplateModal'

// Mock the hooks
const mockMutateAsync = jest.fn()
jest.mock('@/lib/hooks', () => ({
  useCreateTemplate: jest.fn(() => ({
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
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('CreateTemplateModal', () => {
  const mockOnClose = jest.fn()

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockMutateAsync.mockResolvedValue({})
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <CreateTemplateModal {...defaultProps} isOpen={false} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render modal when isOpen is true', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Create Rotation Template')).toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/activity type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/abbreviation/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/clinic location/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/max residents/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/requires specialty/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/supervision required/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/requires procedure credential/i)).toBeInTheDocument()
    })

    it('should render Cancel and Create Template buttons', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create template/i })).toBeInTheDocument()
    })
  })

  describe('Default Values', () => {
    it('should have clinic as default activity type', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const activityTypeSelect = screen.getByLabelText(/activity type/i) as HTMLSelectElement
      expect(activityTypeSelect.value).toBe('clinic')
    })

    it('should have supervision required checked by default', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const supervisionCheckbox = screen.getByLabelText(/supervision required/i) as HTMLInputElement
      expect(supervisionCheckbox.checked).toBe(true)
    })

    it('should have supervision ratio of 4 by default', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const supervisionRatioInput = screen.getByLabelText(/supervision ratio/i) as HTMLInputElement
      expect(supervisionRatioInput.value).toBe('4')
    })

    it('should have procedure credential unchecked by default', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const procedureCheckbox = screen.getByLabelText(/requires procedure credential/i) as HTMLInputElement
      expect(procedureCheckbox.checked).toBe(false)
    })
  })

  describe('Form Interactions', () => {
    it('should update name when typed', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      await user.click(nameInput)
      await user.keyboard('Cardiology Clinic')

      await waitFor(() => {
        expect((nameInput as HTMLInputElement).value).toBe('Cardiology Clinic')
      })
    })

    it('should update activity type when selected', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const activityTypeSelect = screen.getByLabelText(/activity type/i)
      await user.selectOptions(activityTypeSelect, 'inpatient')

      expect((activityTypeSelect as HTMLSelectElement).value).toBe('inpatient')
    })

    it('should update abbreviation when typed', async () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const abbreviationInput = screen.getByPlaceholderText(/e.g., IM/i)
      fireEvent.change(abbreviationInput, { target: { value: 'CARD' } })

      expect((abbreviationInput as HTMLInputElement).value).toBe('CARD')
    })

    it('should toggle supervision required checkbox', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const checkbox = screen.getByLabelText(/supervision required/i) as HTMLInputElement
      expect(checkbox.checked).toBe(true)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)
    })

    it('should toggle procedure credential checkbox', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const checkbox = screen.getByLabelText(/requires procedure credential/i) as HTMLInputElement
      expect(checkbox.checked).toBe(false)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })

    it('should update numeric fields', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const maxResidentsInput = screen.getByLabelText(/max residents/i)
      await user.type(maxResidentsInput, '6')

      expect((maxResidentsInput as HTMLInputElement).value).toBe('6')
    })
  })

  describe('Form Validation', () => {
    it('should show error when name is empty', async () => {
      const user = userEvent.setup()

      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        const errorElement = screen.queryByText(/name is required/i)
        expect(errorElement).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should validate supervision ratio is between 1 and 10', async () => {
      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      fireEvent.change(nameInput, { target: { value: 'Test Template' } })

      const supervisionRatioInput = screen.getByLabelText(/supervision ratio/i)
      fireEvent.change(supervisionRatioInput, { target: { value: '15' } })

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/supervision ratio must be between 1 and 10/i)).toBeInTheDocument()
      })
    })

    it('should not submit form with validation errors', async () => {
      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      expect(mockMutateAsync).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('should call createTemplate with correct data on submit', async () => {
      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      fireEvent.change(nameInput, { target: { value: 'Cardiology Clinic' } })

      const abbreviationInput = screen.getByPlaceholderText(/e.g., IM/i)
      fireEvent.change(abbreviationInput, { target: { value: 'CARD' } })

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          name: 'Cardiology Clinic',
          activityType: 'clinic',
          abbreviation: 'CARD',
          requiresProcedureCredential: false,
          supervisionRequired: true,
          maxSupervisionRatio: 4,
        })
      })
    })

    it('should call onClose after successful submission', async () => {
      const user = userEvent.setup()

      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      await user.click(nameInput)
      await user.keyboard('Test Template')

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })

    it('should show error message on submission failure', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockRejectedValue(new Error('Network error'))

      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      await user.click(nameInput)
      await user.keyboard('Test Template')

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/failed to create template/i)).toBeInTheDocument()
      })
    })

    it('should include all optional fields when provided', async () => {
      const { container } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByPlaceholderText(/inpatient medicine/i)
      fireEvent.change(nameInput, { target: { value: 'Advanced Procedures' } })

      const abbreviationInput = screen.getByPlaceholderText(/e.g., IM/i)
      fireEvent.change(abbreviationInput, { target: { value: 'ADV' } })

      const clinicLocationInput = screen.getByPlaceholderText(/building a/i)
      fireEvent.change(clinicLocationInput, { target: { value: 'Building A, Room 101' } })

      const maxResidentsInput = screen.getByPlaceholderText(/e.g., 4/i)
      fireEvent.change(maxResidentsInput, { target: { value: '3' } })

      const requiresSpecialtyInput = screen.getByPlaceholderText(/cardiology/i)
      fireEvent.change(requiresSpecialtyInput, { target: { value: 'Cardiology' } })

      const procedureCheckbox = screen.getByLabelText(/requires procedure credential/i)
      fireEvent.click(procedureCheckbox)

      const form = container.querySelector('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          name: 'Advanced Procedures',
          activityType: 'clinic',
          abbreviation: 'ADV',
          clinicLocation: 'Building A, Room 101',
          maxResidents: 3,
          requiresSpecialty: 'Cardiology',
          requiresProcedureCredential: true,
          supervisionRequired: true,
          maxSupervisionRatio: 4,
        })
      })
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <CreateTemplateModal {...defaultProps} />,
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
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should reset form when closed', async () => {
      const user = userEvent.setup()

      const { rerender } = render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      // Fill in some fields
      const nameInput = screen.getByLabelText(/^name$/i)
      await user.type(nameInput, 'Test Template')

      // Close modal
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      // Reopen modal
      rerender(
        <CreateTemplateModal {...defaultProps} isOpen={false} />
      )
      rerender(
        <CreateTemplateModal {...defaultProps} isOpen={true} />
      )

      // Fields should be empty
      const nameInputAfterReopen = screen.getByLabelText(/^name$/i) as HTMLInputElement
      expect(nameInputAfterReopen.value).toBe('')
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes on modal', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })

    it('should have proper labels for all form controls', () => {
      render(
        <CreateTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/activity type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/abbreviation/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/clinic location/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/max residents/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/requires specialty/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/supervision required/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/requires procedure credential/i)).toBeInTheDocument()
    })
  })
})
