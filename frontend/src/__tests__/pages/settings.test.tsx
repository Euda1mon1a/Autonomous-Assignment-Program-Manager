/**
 * Settings Page Tests
 *
 * Comprehensive tests for the settings page including form rendering,
 * loading states, error states, form validation, save functionality,
 * and holiday management integration.
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SettingsPage from '@/app/settings/page'
import * as api from '@/lib/api'

// Mock dependencies
jest.mock('@/lib/api')
jest.mock('@/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))
jest.mock('@/components/HolidayEditModal', () => ({
  HolidayEditModal: ({
    isOpen,
    onClose,
    onSave,
    holidays,
  }: {
    isOpen: boolean
    onClose: () => void
    onSave: (holidays: any[]) => void
    holidays: any[]
  }) => {
    if (!isOpen) return null
    return (
      <div data-testid="holiday-modal">
        <h2>Holiday Modal</h2>
        <button onClick={onClose}>Close Modal</button>
        <button
          onClick={() => {
            onSave([
              ...holidays,
              { id: 'custom-1', name: 'Test Holiday', date: '2024-12-31', isCustom: true },
            ])
            onClose()
          }}
        >
          Add Test Holiday
        </button>
      </div>
    )
  },
}))

const mockedApi = api as jest.Mocked<typeof api>

// Mock settings data
const mockSettings = {
  academicYear: {
    startDate: '2024-07-01',
    endDate: '2025-06-30',
    blockDuration: 28,
  },
  acgme: {
    maxWeeklyHours: 80,
    pgy1SupervisionRatio: 2,
    pgy23SupervisionRatio: 4,
  },
  scheduling: {
    defaultAlgorithm: 'greedy' as const,
  },
  holidays: [],
}

const mockSettingsWithHolidays = {
  ...mockSettings,
  holidays: [
    { id: 'holiday-1', name: 'New Years Day', date: '2025-01-01', isCustom: false },
    { id: 'holiday-2', name: 'Independence Day', date: '2024-07-04', isCustom: false },
    { id: 'holiday-3', name: 'Christmas', date: '2024-12-25', isCustom: false },
  ],
}

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient()
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('SettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  describe('Loading State', () => {
    it('should show loading spinner while fetching settings', () => {
      // Mock a pending query
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      renderWithProviders(<SettingsPage />)

      expect(screen.getByText(/loading settings\.\.\./i)).toBeInTheDocument()
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('should show loading state with proper ARIA attributes', () => {
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      renderWithProviders(<SettingsPage />)

      const loadingElement = screen.getByText(/loading settings\.\.\./i).parentElement
      expect(loadingElement).toHaveAttribute('aria-live', 'polite')
      expect(loadingElement).toHaveAttribute('aria-busy', 'true')
    })
  })

  describe('Rendering', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should render page header', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /^settings$/i })).toBeInTheDocument()
      })
      expect(screen.getByText(/configure application settings/i)).toBeInTheDocument()
    })

    it('should render all settings sections', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Academic Year')).toBeInTheDocument()
      })
      expect(screen.getByText('ACGME Settings')).toBeInTheDocument()
      expect(screen.getByText('Scheduling Algorithm')).toBeInTheDocument()
      expect(screen.getByText('Holidays')).toBeInTheDocument()
    })

    it('should render all academic year fields', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/start date/i)).toBeInTheDocument()
      })
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
    })

    it('should render all ACGME settings fields', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      })
      expect(screen.getByLabelText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy-2\/3 supervision ratio/i)).toBeInTheDocument()
    })

    it('should render scheduling algorithm field', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
      })
    })

    it('should render save button', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save settings/i })).toBeInTheDocument()
      })
    })

    it('should have save button disabled by default when no changes', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        const saveButton = screen.getByRole('button', { name: /save settings/i })
        expect(saveButton).toBeDisabled()
      })
    })
  })

  describe('Default Values', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should display fetched academic year values', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        const startDateInput = screen.getByLabelText(/start date/i) as HTMLInputElement
        expect(startDateInput.value).toBe('2024-07-01')
      })

      const endDateInput = screen.getByLabelText(/end date/i) as HTMLInputElement
      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement

      expect(endDateInput.value).toBe('2025-06-30')
      expect(blockDurationInput.value).toBe('28')
    })

    it('should display fetched ACGME values', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
        expect(maxHoursInput.value).toBe('80')
      })

      const pgy1Select = screen.getByLabelText(/pgy-1 supervision ratio/i) as HTMLSelectElement
      const pgy23Select = screen.getByLabelText(/pgy-2\/3 supervision ratio/i) as HTMLSelectElement

      expect(pgy1Select.value).toBe('2')
      expect(pgy23Select.value).toBe('4')
    })

    it('should display fetched algorithm value', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        const algorithmSelect = screen.getByLabelText(/default algorithm/i) as HTMLSelectElement
        expect(algorithmSelect.value).toBe('greedy')
      })
    })
  })

  describe('Error States', () => {
    it('should display load error message when API fails', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network error'))

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/could not load settings from server/i)).toBeInTheDocument()
      })
      expect(screen.getByText(/using defaults/i)).toBeInTheDocument()
    })

    it('should still render form when load fails', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network error'))

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save settings/i })).toBeInTheDocument()
      })
    })

    it('should display save error message when save fails', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.get.mockResolvedValue(mockSettings)
      const saveError = new api.ApiError('Save failed', 500)
      mockedApi.put.mockRejectedValue(saveError)

      renderWithProviders(<SettingsPage />)

      // Wait for form to load
      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Make a change
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Check for error message
      await waitFor(() => {
        expect(screen.getByText(/failed to save settings/i)).toBeInTheDocument()
      })
    })

    it('should show error with proper styling and icon', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network error'))

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        const errorDiv = screen.getByText(/could not load settings/i).closest('div')
        expect(errorDiv).toHaveClass('bg-yellow-50')
      })
    })
  })

  describe('Success State', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
      mockedApi.put.mockResolvedValue(mockSettings)
    })

    it('should display success message after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Make a change
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Check for success message
      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument()
      })
    })

    it('should auto-hide success message after 3 seconds', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Make a change and save
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Success message should appear
      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument()
      })

      // Fast-forward time by 3 seconds
      jest.advanceTimersByTime(3000)

      // Success message should disappear
      await waitFor(() => {
        expect(screen.queryByText(/settings saved successfully/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Form Interactions', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should update start date when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/start date/i)).toBeInTheDocument()
      })

      const startDateInput = screen.getByLabelText(/start date/i) as HTMLInputElement
      await user.clear(startDateInput)
      await user.type(startDateInput, '2025-07-01')

      expect(startDateInput.value).toBe('2025-07-01')
    })

    it('should update end date when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/end date/i)).toBeInTheDocument()
      })

      const endDateInput = screen.getByLabelText(/end date/i) as HTMLInputElement
      await user.clear(endDateInput)
      await user.type(endDateInput, '2026-06-30')

      expect(endDateInput.value).toBe('2026-06-30')
    })

    it('should update block duration when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(blockDurationInput.value).toBe('30')
    })

    it('should update max weekly hours when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      })

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
      await user.clear(maxHoursInput)
      await user.type(maxHoursInput, '75')

      expect(maxHoursInput.value).toBe('75')
    })

    it('should update PGY-1 supervision ratio when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = screen.getByLabelText(/pgy-1 supervision ratio/i) as HTMLSelectElement
      await user.selectOptions(supervisionSelect, '1')

      expect(supervisionSelect.value).toBe('1')
    })

    it('should update PGY-2/3 supervision ratio when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/pgy-2\/3 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = screen.getByLabelText(
        /pgy-2\/3 supervision ratio/i
      ) as HTMLSelectElement
      await user.selectOptions(supervisionSelect, '2')

      expect(supervisionSelect.value).toBe('2')
    })

    it('should update algorithm when changed', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
      })

      const algorithmSelect = screen.getByLabelText(/default algorithm/i) as HTMLSelectElement
      await user.selectOptions(algorithmSelect, 'cp_sat')

      expect(algorithmSelect.value).toBe('cp_sat')
    })
  })

  describe('Change Tracking', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should show "unsaved changes" indicator when fields are modified', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()
    })

    it('should enable save button when changes are made', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const saveButton = screen.getByRole('button', { name: /save settings/i })
      expect(saveButton).toBeDisabled()

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(saveButton).not.toBeDisabled()
    })

    it('should track changes across multiple fields', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Change multiple fields
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i)
      await user.clear(maxHoursInput)
      await user.type(maxHoursInput, '75')

      const algorithmSelect = screen.getByLabelText(/default algorithm/i)
      await user.selectOptions(algorithmSelect, 'cp_sat')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /save settings/i })).not.toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
      mockedApi.put.mockResolvedValue(mockSettings)
    })

    it('should call API with updated settings when save button is clicked', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Make a change
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(mockedApi.put).toHaveBeenCalledWith(
          '/settings',
          expect.objectContaining({
            academicYear: expect.objectContaining({
              blockDuration: 30,
            }),
          })
        )
      })
    })

    it('should show saving state while submitting', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.put.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)))

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
    })

    it('should clear unsaved changes indicator after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()
      })
    })

    it('should disable save button after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save settings/i })).toBeDisabled()
      })
    })

    it('should submit all updated fields correctly', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      // Update multiple fields
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i)
      await user.clear(maxHoursInput)
      await user.type(maxHoursInput, '75')

      const algorithmSelect = screen.getByLabelText(/default algorithm/i)
      await user.selectOptions(algorithmSelect, 'cp_sat')

      // Submit
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(mockedApi.put).toHaveBeenCalledWith(
          '/settings',
          expect.objectContaining({
            academicYear: expect.objectContaining({ blockDuration: 30 }),
            acgme: expect.objectContaining({ maxWeeklyHours: 75 }),
            scheduling: expect.objectContaining({ defaultAlgorithm: 'cp_sat' }),
          })
        )
      })
    })
  })

  describe('Algorithm Options', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should have all algorithm options available', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
      })

      const algorithmSelect = screen.getByLabelText(/default algorithm/i)
      const options = algorithmSelect.querySelectorAll('option')

      expect(options).toHaveLength(3)
      expect(options[0].textContent).toContain('Greedy')
      expect(options[1].textContent).toContain('Min Conflicts')
      expect(options[2].textContent).toContain('CP-SAT')
    })

    it('should show algorithm descriptions', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/greedy is fastest, cp-sat finds optimal solution/i)).toBeInTheDocument()
    })
  })

  describe('Supervision Ratio Options', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should have PGY-1 supervision ratio options', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = screen.getByLabelText(/pgy-1 supervision ratio/i)
      const options = supervisionSelect.querySelectorAll('option')

      expect(options).toHaveLength(2)
      expect(options[0].value).toBe('2')
      expect(options[1].value).toBe('1')
    })

    it('should have PGY-2/3 supervision ratio options', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/pgy-2\/3 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = screen.getByLabelText(/pgy-2\/3 supervision ratio/i)
      const options = supervisionSelect.querySelectorAll('option')

      expect(options).toHaveLength(3)
      expect(options[0].value).toBe('4')
      expect(options[1].value).toBe('3')
      expect(options[2].value).toBe('2')
    })
  })

  describe('Holiday Management', () => {
    it('should show "No holidays configured" when there are no holidays', async () => {
      mockedApi.get.mockResolvedValue(mockSettings)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/no holidays configured/i)).toBeInTheDocument()
      })
    })

    it('should display holiday count', async () => {
      mockedApi.get.mockResolvedValue(mockSettingsWithHolidays)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/3 configured/i)).toBeInTheDocument()
      })
    })

    it('should display holidays within academic year', async () => {
      mockedApi.get.mockResolvedValue(mockSettingsWithHolidays)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Independence Day')).toBeInTheDocument()
      })
      expect(screen.getByText('Christmas')).toBeInTheDocument()
      expect(screen.getByText(/new years day/i)).toBeInTheDocument()
    })

    it('should open holiday modal when "Edit" button is clicked', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.get.mockResolvedValue(mockSettingsWithHolidays)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Independence Day')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      expect(screen.getByTestId('holiday-modal')).toBeInTheDocument()
    })

    it('should open holiday modal when "Add Holidays" button is clicked', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.get.mockResolvedValue(mockSettings)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/no holidays configured/i)).toBeInTheDocument()
      })

      const addButton = screen.getByRole('button', { name: /add holidays/i })
      await user.click(addButton)

      expect(screen.getByTestId('holiday-modal')).toBeInTheDocument()
    })

    it('should close holiday modal when close button is clicked', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.get.mockResolvedValue(mockSettingsWithHolidays)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Independence Day')).toBeInTheDocument()
      })

      // Open modal
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      expect(screen.getByTestId('holiday-modal')).toBeInTheDocument()

      // Close modal
      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(screen.queryByTestId('holiday-modal')).not.toBeInTheDocument()
    })

    it('should update holidays and mark as having changes when holiday is added via modal', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.get.mockResolvedValue(mockSettings)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/no holidays configured/i)).toBeInTheDocument()
      })

      // Open modal
      const addButton = screen.getByRole('button', { name: /add holidays/i })
      await user.click(addButton)

      // Add holiday via modal
      const addHolidayButton = screen.getByRole('button', { name: /add test holiday/i })
      await user.click(addHolidayButton)

      // Modal should close and unsaved changes should appear
      await waitFor(() => {
        expect(screen.queryByTestId('holiday-modal')).not.toBeInTheDocument()
      })
      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /save settings/i })).not.toBeDisabled()
    })

    it('should limit displayed holidays to 5 and show remaining count', async () => {
      const manyHolidays = {
        ...mockSettings,
        holidays: [
          { id: '1', name: 'Holiday 1', date: '2024-07-01', isCustom: false },
          { id: '2', name: 'Holiday 2', date: '2024-08-01', isCustom: false },
          { id: '3', name: 'Holiday 3', date: '2024-09-01', isCustom: false },
          { id: '4', name: 'Holiday 4', date: '2024-10-01', isCustom: false },
          { id: '5', name: 'Holiday 5', date: '2024-11-01', isCustom: false },
          { id: '6', name: 'Holiday 6', date: '2024-12-01', isCustom: false },
          { id: '7', name: 'Holiday 7', date: '2025-01-01', isCustom: false },
        ],
      }
      mockedApi.get.mockResolvedValue(manyHolidays)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Holiday 1')).toBeInTheDocument()
      })

      // Should show first 5 holidays
      expect(screen.getByText('Holiday 1')).toBeInTheDocument()
      expect(screen.getByText('Holiday 2')).toBeInTheDocument()
      expect(screen.getByText('Holiday 3')).toBeInTheDocument()
      expect(screen.getByText('Holiday 4')).toBeInTheDocument()
      expect(screen.getByText('Holiday 5')).toBeInTheDocument()

      // Should show remaining count
      expect(screen.getByText(/\+ 2 more holidays/i)).toBeInTheDocument()
    })

    it('should show "Custom" badge for custom holidays', async () => {
      const settingsWithCustomHoliday = {
        ...mockSettings,
        holidays: [
          { id: 'custom-1', name: 'Company Retreat', date: '2024-08-15', isCustom: true },
        ],
      }
      mockedApi.get.mockResolvedValue(settingsWithCustomHoliday)

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Company Retreat')).toBeInTheDocument()
      })

      expect(screen.getByText('Custom')).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should enforce min value for block duration', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement
      expect(blockDurationInput.min).toBe('1')
    })

    it('should enforce max value for block duration', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      })

      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement
      expect(blockDurationInput.max).toBe('365')
    })

    it('should enforce min value for max weekly hours', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      })

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
      expect(maxHoursInput.min).toBe('1')
    })

    it('should enforce max value for max weekly hours', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      })

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
      expect(maxHoursInput.max).toBe('168')
    })
  })

  describe('Accessibility', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should have proper form structure', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save settings/i })).toBeInTheDocument()
      })

      const form = screen.getByRole('button', { name: /save settings/i }).closest('form')
      expect(form).toBeInTheDocument()
    })

    it('should have labels for all inputs', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByLabelText(/start date/i)).toBeInTheDocument()
      })

      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy-2\/3 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
    })

    it('should have section headings with proper hierarchy', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /^settings$/i, level: 1 })).toBeInTheDocument()
      })

      expect(screen.getByRole('heading', { name: /academic year/i, level: 2 })).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: /acgme settings/i, level: 2 })).toBeInTheDocument()
      expect(
        screen.getByRole('heading', { name: /scheduling algorithm/i, level: 2 })
      ).toBeInTheDocument()
    })
  })
})
