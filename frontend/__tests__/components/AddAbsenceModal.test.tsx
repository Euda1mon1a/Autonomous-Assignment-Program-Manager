import { render, screen, waitFor, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AddAbsenceModal } from '@/components/AddAbsenceModal'
import { useCreateAbsence, usePeople } from '@/lib/hooks'
import { createWrapper, mockResponses } from '../utils/test-utils'

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  useCreateAbsence: jest.fn(),
  usePeople: jest.fn(),
}))

describe('AddAbsenceModal', () => {
  const mockOnClose = jest.fn()
  const mockMutateAsync = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useCreateAbsence as jest.Mock).mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
    })
    ;(usePeople as jest.Mock).mockReturnValue({
      data: mockResponses.listPeople,
      isLoading: false,
      isError: false,
    })
  })

  describe('Modal Visibility', () => {
    it('should render modal when isOpen is true', () => {
      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('heading', { name: 'Add Absence' })).toBeInTheDocument()
    })

    it('should not render modal when isOpen is false', () => {
      render(
        <AddAbsenceModal isOpen={false} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByText('Add Absence')).not.toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    beforeEach(() => {
      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )
    })

    it('should render person selector', () => {
      expect(screen.getByLabelText(/person/i)).toBeInTheDocument()
    })

    it('should render absence type dropdown', () => {
      expect(screen.getByLabelText(/absence type/i)).toBeInTheDocument()
    })

    it('should render start date field', () => {
      const dateInputs = screen.getAllByDisplayValue('')
      const dateTypeInputs = dateInputs.filter(input => input.getAttribute('type') === 'date')
      expect(dateTypeInputs.length).toBeGreaterThanOrEqual(2) // At least start and end date
    })

    it('should render end date field', () => {
      const dateInputs = screen.getAllByDisplayValue('')
      const dateTypeInputs = dateInputs.filter(input => input.getAttribute('type') === 'date')
      expect(dateTypeInputs.length).toBeGreaterThanOrEqual(2) // At least start and end date
    })

    it('should render notes field', () => {
      const notesField = screen.getByPlaceholderText(/optional notes about this absence/i)
      expect(notesField).toBeInTheDocument()
      expect(notesField.tagName).toBe('TEXTAREA')
    })

    it('should populate person selector with people data', () => {
      const personSelect = screen.getByLabelText(/person/i)
      const options = within(personSelect).getAllByRole('option')

      // Should have default "Select a person" option + 2 mock people
      expect(options.length).toBeGreaterThanOrEqual(2)
      expect(screen.getByRole('option', { name: /dr. john smith/i })).toBeInTheDocument()
    })

    it('should show loading state for person selector', () => {
      ;(usePeople as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
      })

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('option', { name: /loading/i })).toBeInTheDocument()
    })
  })

  describe('Absence Type Options', () => {
    beforeEach(() => {
      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )
    })

    it('should show all absence type options', () => {
      const absenceTypeSelect = screen.getByLabelText(/absence type/i)
      const options = within(absenceTypeSelect).getAllByRole('option')

      // Component now has 11 absence type options (vacation, conference, sick, medical, convalescent, parental leave, family emergency, emergency leave, bereavement, deployment, tdy)
      expect(options.length).toBe(11)
      expect(screen.getByRole('option', { name: /vacation/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /deployment/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /tdy/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /medical leave/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /family emergency/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /conference/i })).toBeInTheDocument()
    })

    it('should have vacation selected by default', () => {
      const absenceTypeSelect = screen.getByLabelText(/absence type/i) as HTMLSelectElement
      expect(absenceTypeSelect.value).toBe('vacation')
    })
  })

  describe('Military-Specific Fields', () => {
    it('should show deployment orders checkbox when deployment is selected', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Initially not visible
      expect(screen.queryByLabelText(/has deployment orders/i)).not.toBeInTheDocument()

      // Select deployment
      const absenceTypeSelect = screen.getByLabelText(/absence type/i)
      await user.selectOptions(absenceTypeSelect, 'deployment')

      // Should now be visible
      expect(screen.getByLabelText(/has deployment orders/i)).toBeInTheDocument()
    })

    it('should hide deployment orders checkbox when switching away from deployment', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Select deployment
      const absenceTypeSelect = screen.getByLabelText(/absence type/i)
      await user.selectOptions(absenceTypeSelect, 'deployment')
      expect(screen.getByLabelText(/has deployment orders/i)).toBeInTheDocument()

      // Switch to vacation
      await user.selectOptions(absenceTypeSelect, 'vacation')
      expect(screen.queryByLabelText(/has deployment orders/i)).not.toBeInTheDocument()
    })

    it('should show TDY location field when TDY is selected', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Initially not visible
      expect(screen.queryByLabelText(/tdy location/i)).not.toBeInTheDocument()

      // Select TDY
      const absenceTypeSelect = screen.getByLabelText(/absence type/i)
      await user.selectOptions(absenceTypeSelect, 'tdy')

      // Should now be visible
      expect(screen.getByLabelText(/tdy location/i)).toBeInTheDocument()
    })

    it('should hide TDY location field when switching away from TDY', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Select TDY
      const absenceTypeSelect = screen.getByLabelText(/absence type/i)
      await user.selectOptions(absenceTypeSelect, 'tdy')
      expect(screen.getByLabelText(/tdy location/i)).toBeInTheDocument()

      // Switch to medical
      await user.selectOptions(absenceTypeSelect, 'medical')
      expect(screen.queryByLabelText(/tdy location/i)).not.toBeInTheDocument()
    })

    it('should not show military fields for non-military absence types', () => {
      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Default is vacation, so no military fields should be visible
      expect(screen.queryByLabelText(/has deployment orders/i)).not.toBeInTheDocument()
      expect(screen.queryByLabelText(/tdy location/i)).not.toBeInTheDocument()
    })
  })

  describe('Date Range Validation', () => {
    it('should show error when person is not selected', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /add absence/i })
      await user.click(submitButton)

      expect(await screen.findByText(/please select a person/i)).toBeInTheDocument()
      expect(mockMutateAsync).not.toHaveBeenCalled()
    })

    it('should show error when start date is not provided', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Select person but not dates
      const personSelect = screen.getByLabelText(/person/i)
      await user.selectOptions(personSelect, 'person-1')

      const submitButton = screen.getByRole('button', { name: /add absence/i })
      await user.click(submitButton)

      expect(await screen.findByText(/start date is required/i)).toBeInTheDocument()
      expect(mockMutateAsync).not.toHaveBeenCalled()
    })

    it('should show error when end date is not provided', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Select person and start date but not end date
      const personSelect = screen.getByLabelText(/person/i)
      await user.selectOptions(personSelect, 'person-1')

      // Mock DatePicker would need special handling, let's just test the validation logic
      // by submitting without end date
      const submitButton = screen.getByRole('button', { name: /add absence/i })
      await user.click(submitButton)

      expect(await screen.findByText(/end date is required/i)).toBeInTheDocument()
      expect(mockMutateAsync).not.toHaveBeenCalled()
    })

    it('should validate that end date is not before start date', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const personSelect = screen.getByLabelText(/person/i)
      await user.selectOptions(personSelect, 'person-1')

      // Set dates where end is before start
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement

      await user.type(startDateInput, '2024-12-31')
      await user.type(endDateInput, '2024-12-01')

      const submitButton = screen.getByRole('button', { name: /add absence/i })
      await user.click(submitButton)

      expect(await screen.findByText(/end date must be on or after start date/i)).toBeInTheDocument()
      expect(mockMutateAsync).not.toHaveBeenCalled()
    })
  })

  describe('Form Submission', () => {
    it.skip('should submit with correct data for vacation', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockResolvedValue({})

      const { container } = render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill form
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const dateInputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement

      // Use fireEvent.change for date inputs (more reliable than typing)
      fireEvent.change(startDateInput, { target: { value: '2024-12-01' } })
      fireEvent.change(endDateInput, { target: { value: '2024-12-07' } })

      const notesField = screen.getByPlaceholderText(/optional notes about this absence/i)
      await user.type(notesField, 'Holiday vacation')

      // Submit
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          person_id: 'person-1',
          absence_type: 'vacation',
          start_date: '2024-12-01',
          end_date: '2024-12-07',
          notes: 'Holiday vacation',
        })
      })
    })

    it('should submit with deployment orders when checked', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockResolvedValue({})

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill form with deployment type
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      await user.selectOptions(screen.getByLabelText(/absence type/i), 'deployment')
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement
      await user.type(startDateInput, '2024-12-01')
      await user.type(endDateInput, '2025-06-01')
      await user.click(screen.getByLabelText(/has deployment orders/i))

      // Submit
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            absence_type: 'deployment',
            deployment_orders: true,
          })
        )
      })
    })

    it.skip('should submit with TDY location when provided', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockResolvedValue({})

      const { container } = render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill form with TDY type
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      await user.selectOptions(screen.getByLabelText(/absence type/i), 'tdy')
      const dateInputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement

      // Use fireEvent.change for date inputs (more reliable than typing)
      fireEvent.change(startDateInput, { target: { value: '2024-12-01' } })
      fireEvent.change(endDateInput, { target: { value: '2024-12-14' } })

      await user.type(screen.getByLabelText(/tdy location/i), 'Fort Bragg, NC')

      // Submit
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            absence_type: 'tdy',
            tdy_location: 'Fort Bragg, NC',
          })
        )
      })
    })

    it('should show loading state during submission', async () => {
      ;(useCreateAbsence as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn().mockImplementation(() => new Promise(() => {})),
        isPending: true,
      })

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /creating/i })
      expect(submitButton).toBeDisabled()
      expect(submitButton).toHaveTextContent('Creating...')
    })

    it('should call onClose after successful submission', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockResolvedValue({})

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill minimum required fields
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement
      await user.type(startDateInput, '2024-12-01')
      await user.type(endDateInput, '2024-12-07')

      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })

    it('should reset form after successful submission', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockResolvedValue({})

      const { rerender } = render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill and submit form
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement
      await user.type(startDateInput, '2024-12-01')
      await user.type(endDateInput, '2024-12-07')
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })

      // Reopen modal
      rerender(<AddAbsenceModal isOpen={true} onClose={mockOnClose} />)

      // Form should be reset
      const absenceTypeSelect = screen.getByLabelText(/absence type/i) as HTMLSelectElement
      expect(absenceTypeSelect.value).toBe('vacation')
    })
  })

  describe('Preselected Person', () => {
    it('should preselect person when preselectedPersonId is provided', () => {
      render(
        <AddAbsenceModal
          isOpen={true}
          onClose={mockOnClose}
          preselectedPersonId="person-1"
        />,
        { wrapper: createWrapper() }
      )

      const personSelect = screen.getByLabelText(/person/i) as HTMLSelectElement
      expect(personSelect.value).toBe('person-1')
    })

    it('should disable person selector when preselectedPersonId is provided', () => {
      render(
        <AddAbsenceModal
          isOpen={true}
          onClose={mockOnClose}
          preselectedPersonId="person-1"
        />,
        { wrapper: createWrapper() }
      )

      const personSelect = screen.getByLabelText(/person/i)
      expect(personSelect).toBeDisabled()
    })

    it('should update person when preselectedPersonId changes', () => {
      const { rerender } = render(
        <AddAbsenceModal
          isOpen={true}
          onClose={mockOnClose}
          preselectedPersonId="person-1"
        />,
        { wrapper: createWrapper() }
      )

      let personSelect = screen.getByLabelText(/person/i) as HTMLSelectElement
      expect(personSelect.value).toBe('person-1')

      // Change preselected person
      rerender(
        <AddAbsenceModal
          isOpen={true}
          onClose={mockOnClose}
          preselectedPersonId="person-2"
        />
      )

      personSelect = screen.getByLabelText(/person/i) as HTMLSelectElement
      expect(personSelect.value).toBe('person-2')
    })
  })

  describe('Error Handling', () => {
    it('should display error message when submission fails', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockRejectedValue(new Error('API Error'))

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill and submit form
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement
      await user.type(startDateInput, '2024-12-01')
      await user.type(endDateInput, '2024-12-07')
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      expect(await screen.findByText(/failed to create absence/i)).toBeInTheDocument()
    })

    it('should not close modal when submission fails', async () => {
      const user = userEvent.setup()
      mockMutateAsync.mockRejectedValue(new Error('API Error'))

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date')
      const startDateInput = dateInputs[0] as HTMLInputElement
      const endDateInput = dateInputs[1] as HTMLInputElement
      await user.type(startDateInput, '2024-12-01')
      await user.type(endDateInput, '2024-12-07')
      await user.click(screen.getByRole('button', { name: /add absence/i }))

      await waitFor(() => {
        expect(screen.getByText(/failed to create absence/i)).toBeInTheDocument()
      })

      expect(mockOnClose).not.toHaveBeenCalled()
    })
  })

  describe('Cancel Button', () => {
    it('should call onClose when cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      await user.click(screen.getByRole('button', { name: /cancel/i }))

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should reset form when cancel is clicked', async () => {
      const user = userEvent.setup()

      const { rerender } = render(
        <AddAbsenceModal isOpen={true} onClose={mockOnClose} />,
        { wrapper: createWrapper() }
      )

      // Fill form
      await user.selectOptions(screen.getByLabelText(/person/i), 'person-1')
      const notesField = screen.getByPlaceholderText(/optional notes about this absence/i)
      await user.type(notesField, 'Test notes')

      // Cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }))

      // Reopen modal
      rerender(<AddAbsenceModal isOpen={true} onClose={mockOnClose} />)

      // Form should be reset
      const notesInput = screen.getByPlaceholderText(/optional notes about this absence/i) as HTMLTextAreaElement
      expect(notesInput.value).toBe('')
    })
  })
})
