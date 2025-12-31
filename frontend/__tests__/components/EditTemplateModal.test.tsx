/**
 * Tests for EditTemplateModal component
 *
 * Tests form rendering, validation, pre-population, and submission behavior
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EditTemplateModal } from '@/components/EditTemplateModal'
import type { RotationTemplate } from '@/types/api'

// Mock the hooks
const mockMutateAsync = jest.fn()
jest.mock('@/lib/hooks', () => ({
  useUpdateTemplate: jest.fn(() => ({
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

describe('EditTemplateModal', () => {
  const mockOnClose = jest.fn()

  const mockTemplate: RotationTemplate = {
    id: 'template-1',
    name: 'Cardiology Clinic',
    activity_type: 'clinic',
    abbreviation: 'CARD',
    clinic_location: 'Building A, Room 101',
    max_residents: 4,
    requires_specialty: 'Cardiology',
    requires_procedure_credential: true,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    template: mockTemplate,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockMutateAsync.mockResolvedValue({})
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <EditTemplateModal {...defaultProps} isOpen={false} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render modal when isOpen is true', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Edit Rotation Template')).toBeInTheDocument()
    })

    it('should return null when template is null', () => {
      render(
        <EditTemplateModal {...defaultProps} template={null} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
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

    it('should render Cancel and Save Changes buttons', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument()
    })
  })

  describe('Form Pre-population', () => {
    it('should pre-populate all fields from template data', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/^name$/i) as HTMLInputElement
      const activityTypeSelect = screen.getByLabelText(/activity type/i) as HTMLSelectElement
      const abbreviationInput = screen.getByLabelText(/abbreviation/i) as HTMLInputElement
      const clinicLocationInput = screen.getByLabelText(/clinic location/i) as HTMLInputElement
      const maxResidentsInput = screen.getByLabelText(/max residents/i) as HTMLInputElement
      const requiresSpecialtyInput = screen.getByLabelText(/requires specialty/i) as HTMLInputElement
      const procedureCheckbox = screen.getByLabelText(/requires procedure credential/i) as HTMLInputElement
      const supervisionCheckbox = screen.getByLabelText(/supervision required/i) as HTMLInputElement
      const supervisionRatioInput = screen.getByLabelText(/supervision ratio/i) as HTMLInputElement

      expect(nameInput.value).toBe('Cardiology Clinic')
      expect(activityTypeSelect.value).toBe('clinic')
      expect(abbreviationInput.value).toBe('CARD')
      expect(clinicLocationInput.value).toBe('Building A, Room 101')
      expect(maxResidentsInput.value).toBe('4')
      expect(requiresSpecialtyInput.value).toBe('Cardiology')
      expect(procedureCheckbox.checked).toBe(true)
      expect(supervisionCheckbox.checked).toBe(true)
      expect(supervisionRatioInput.value).toBe('2')
    })

    it('should handle template with null optional fields', () => {
      const templateWithNulls: RotationTemplate = {
        ...mockTemplate,
        abbreviation: null,
        clinic_location: null,
        max_residents: null,
        requires_specialty: null,
      }

      render(
        <EditTemplateModal {...defaultProps} template={templateWithNulls} />,
        { wrapper: createWrapper() }
      )

      const abbreviationInput = screen.getByLabelText(/abbreviation/i) as HTMLInputElement
      const clinicLocationInput = screen.getByLabelText(/clinic location/i) as HTMLInputElement
      const maxResidentsInput = screen.getByLabelText(/max residents/i) as HTMLInputElement
      const requiresSpecialtyInput = screen.getByLabelText(/requires specialty/i) as HTMLInputElement

      expect(abbreviationInput.value).toBe('')
      expect(clinicLocationInput.value).toBe('')
      expect(maxResidentsInput.value).toBe('')
      expect(requiresSpecialtyInput.value).toBe('')
    })
  })

  describe('Form Interactions', () => {
    it('should update name when typed', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/^name$/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'Neurology Clinic')

      expect((nameInput as HTMLInputElement).value).toBe('Neurology Clinic')
    })

    it('should update activity type when selected', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const activityTypeSelect = screen.getByLabelText(/activity type/i)
      await user.selectOptions(activityTypeSelect, 'inpatient')

      expect((activityTypeSelect as HTMLSelectElement).value).toBe('inpatient')
    })

    it('should toggle supervision required checkbox', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
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
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const checkbox = screen.getByLabelText(/requires procedure credential/i) as HTMLInputElement
      expect(checkbox.checked).toBe(true)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)

      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)
    })

    it('should update supervision ratio', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const supervisionRatioInput = screen.getByLabelText(/supervision ratio/i)
      await user.clear(supervisionRatioInput)
      await user.type(supervisionRatioInput, '5')

      expect((supervisionRatioInput as HTMLInputElement).value).toBe('5')
    })
  })

  describe('Form Validation', () => {
    it('should show error when name is empty', async () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/^name$/i)
      // Use fireEvent to clear and set empty value
      fireEvent.change(nameInput, { target: { value: '' } })

      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })
    })

    it('should validate supervision ratio is between 1 and 10', async () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const supervisionRatioInput = screen.getByLabelText(/supervision ratio/i)
      // Use fireEvent to set an invalid value
      fireEvent.change(supervisionRatioInput, { target: { value: '15' } })

      const form = supervisionRatioInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/supervision ratio must be between 1 and 10/i)).toBeInTheDocument()
      })
    })

    it('should not submit form with validation errors', async () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/^name$/i)
      // Use fireEvent to clear the value
      fireEvent.change(nameInput, { target: { value: '' } })

      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      expect(mockMutateAsync).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it('should call updateTemplate with correct data on submit', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const nameInput = screen.getByLabelText(/^name$/i)
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Clinic')

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          id: 'template-1',
          data: expect.objectContaining({
            name: 'Updated Clinic',
            activity_type: 'clinic',
            abbreviation: 'CARD',
          }),
        })
      })
    })

    it('should call onClose after successful submission', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
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
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/failed to update template/i)).toBeInTheDocument()
      })
    })

    it('should handle empty optional fields correctly', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const abbreviationInput = screen.getByLabelText(/abbreviation/i)
      await user.clear(abbreviationInput)

      const clinicLocationInput = screen.getByLabelText(/clinic location/i)
      await user.clear(clinicLocationInput)

      const submitButton = screen.getByRole('button', { name: /save changes/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          id: 'template-1',
          data: expect.objectContaining({
            abbreviation: undefined,
            clinic_location: undefined,
          }),
        })
      })
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
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
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should clear errors when modal is closed', async () => {
      const user = userEvent.setup()

      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      // Trigger validation error
      const nameInput = screen.getByLabelText(/^name$/i)
      fireEvent.change(nameInput, { target: { value: '' } })

      const form = nameInput.closest('form')!
      fireEvent.submit(form)

      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      // Close modal
      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      // Reopen - error should be cleared
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByText(/name is required/i)).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes on modal', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })

    it('should have proper labels for all form controls', () => {
      render(
        <EditTemplateModal {...defaultProps} />,
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
