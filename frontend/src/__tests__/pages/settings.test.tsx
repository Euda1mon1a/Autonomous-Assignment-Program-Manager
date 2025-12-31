/**
 * Settings Page Tests
 *
 * Comprehensive tests for the settings page including form rendering,
 * loading states, error states, form validation, save functionality.
 * Updated to match the actual SettingsPage component structure.
 *
 * Note: The component uses labels without proper for/id associations,
 * so tests use alternative selectors (getByRole, getByDisplayValue, etc.)
 */
import { render, screen, waitFor, act, within, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import SettingsPage from '@/app/settings/page'
import * as api from '@/lib/api'

// Mock dependencies
jest.mock('@/lib/api')

// Note: api.ApiError is not available in mocked module, so we use plain Error objects
jest.mock('@/components/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const mockedApi = api as jest.Mocked<typeof api>

// Mock settings data matching actual backend schema
const mockSettings = {
  scheduling_algorithm: 'greedy' as const,
  work_hours_per_week: 80,
  max_consecutive_days: 6,
  min_days_off_per_week: 1,
  pgy1_supervision_ratio: '1:2',
  pgy2_supervision_ratio: '1:4',
  pgy3_supervision_ratio: '1:4',
  enable_weekend_scheduling: true,
  enable_holiday_scheduling: false,
  default_block_duration_hours: 4,
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

// Helper to find input by label text (for labels not properly associated with inputs)
function findInputByLabelText(container: HTMLElement, labelText: RegExp): HTMLInputElement | null {
  const labels = container.querySelectorAll('label')
  for (const label of labels) {
    if (labelText.test(label.textContent || '')) {
      // Find the next sibling that is an input or select
      const parent = label.parentElement
      if (parent) {
        const input = parent.querySelector('input, select')
        return input as HTMLInputElement | null
      }
    }
  }
  return null
}

// Helper to find select by label text
function findSelectByLabelText(container: HTMLElement, labelText: RegExp): HTMLSelectElement | null {
  const labels = container.querySelectorAll('label')
  for (const label of labels) {
    if (labelText.test(label.textContent || '')) {
      const parent = label.parentElement
      if (parent) {
        const select = parent.querySelector('select')
        return select as HTMLSelectElement | null
      }
    }
  }
  return null
}

// Helper to change a number input value (userEvent.clear doesn't work well with number inputs)
function changeNumberInput(input: HTMLInputElement, value: string) {
  fireEvent.change(input, { target: { value } })
}

describe('SettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading spinner while fetching settings', () => {
      // Mock a pending query
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      renderWithProviders(<SettingsPage />)

      expect(screen.getByText(/loading settings\.\.\./i)).toBeInTheDocument()
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

    it('should render settings sections', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText('Work Hours')).toBeInTheDocument()
      })
      expect(screen.getByText('Supervision Ratios')).toBeInTheDocument()
      expect(screen.getByText('Scheduling')).toBeInTheDocument()
    })

    it('should render work hours fields', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })
      expect(screen.getByText(/max consecutive days/i)).toBeInTheDocument()
      expect(screen.getByText(/min days off per week/i)).toBeInTheDocument()

      // Verify inputs exist
      const workHoursInput = findInputByLabelText(container, /max work hours per week/i)
      expect(workHoursInput).toBeInTheDocument()
    })

    it('should render supervision ratio fields', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })
      expect(screen.getByText(/pgy-2 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByText(/pgy-3 supervision ratio/i)).toBeInTheDocument()
    })

    it('should render scheduling fields', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/default algorithm/i)).toBeInTheDocument()
      })
      expect(screen.getByText(/default block duration/i)).toBeInTheDocument()
      expect(screen.getByText(/enable weekend scheduling/i)).toBeInTheDocument()
      expect(screen.getByText(/enable holiday scheduling/i)).toBeInTheDocument()
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

    it('should display fetched work hours values', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)
      expect(maxHoursInput?.value).toBe('80')

      const maxConsecutiveInput = findInputByLabelText(container, /max consecutive days/i)
      const minDaysOffInput = findInputByLabelText(container, /min days off per week/i)

      expect(maxConsecutiveInput?.value).toBe('6')
      expect(minDaysOffInput?.value).toBe('1')
    })

    it('should display fetched supervision values', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })

      const pgy1Select = findSelectByLabelText(container, /pgy-1 supervision ratio/i)
      expect(pgy1Select?.value).toBe('1:2')

      const pgy2Select = findSelectByLabelText(container, /pgy-2 supervision ratio/i)
      const pgy3Select = findSelectByLabelText(container, /pgy-3 supervision ratio/i)

      expect(pgy2Select?.value).toBe('1:4')
      expect(pgy3Select?.value).toBe('1:4')
    })

    it('should display fetched algorithm value', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/default algorithm/i)).toBeInTheDocument()
      })

      const algorithmSelect = findSelectByLabelText(container, /default algorithm/i)
      expect(algorithmSelect?.value).toBe('greedy')
    })

    it('should display fetched checkbox values', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/enable weekend scheduling/i)).toBeInTheDocument()
      })

      // Checkboxes are wrapped inside labels, so find them differently
      const checkboxes = screen.getAllByRole('checkbox')
      const weekendCheckbox = checkboxes.find(cb =>
        cb.closest('label')?.textContent?.includes('Weekend Scheduling')
      ) as HTMLInputElement
      const holidayCheckbox = checkboxes.find(cb =>
        cb.closest('label')?.textContent?.includes('Holiday Scheduling')
      ) as HTMLInputElement

      expect(weekendCheckbox.checked).toBe(true)
      expect(holidayCheckbox.checked).toBe(false)
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
      // Use a plain Error object instead of ApiError since we're mocking the api module
      const saveError = new Error('Save failed')
      mockedApi.post.mockRejectedValue(saveError)

      const { container } = renderWithProviders(<SettingsPage />)

      // Wait for form to load
      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      // Make a change
      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Check for error message
      await waitFor(() => {
        expect(screen.getByText(/failed to save settings/i)).toBeInTheDocument()
      })
    })

    it('should show error with proper styling', async () => {
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
      jest.useFakeTimers()
      mockedApi.get.mockResolvedValue(mockSettings)
      mockedApi.post.mockResolvedValue(mockSettings)
    })

    afterEach(() => {
      jest.runOnlyPendingTimers()
      jest.useRealTimers()
    })

    it('should display success message after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      // Make a change
      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Check for success message
      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument()
      })
    })

    it('should auto-hide success message after 3 seconds', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      // Make a change and save
      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      // Success message should appear
      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument()
      })

      // Fast-forward time by 3 seconds
      await act(async () => {
        jest.advanceTimersByTime(3000)
      })

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

    it('should update max work hours when changed', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!

      // Use fireEvent to change the value directly - this simulates the actual DOM behavior
      fireEvent.change(maxHoursInput, { target: { value: '75' } })

      expect(maxHoursInput.value).toBe('75')
    })

    it('should update PGY-1 supervision ratio when changed', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = findSelectByLabelText(container, /pgy-1 supervision ratio/i)!
      await user.selectOptions(supervisionSelect, '1:1')

      expect(supervisionSelect.value).toBe('1:1')
    })

    it('should update algorithm when changed', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/default algorithm/i)).toBeInTheDocument()
      })

      const algorithmSelect = findSelectByLabelText(container, /default algorithm/i)!
      await user.selectOptions(algorithmSelect, 'cp_sat')

      expect(algorithmSelect.value).toBe('cp_sat')
    })

    it('should toggle weekend scheduling checkbox', async () => {
      const user = userEvent.setup({ delay: null })

      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/enable weekend scheduling/i)).toBeInTheDocument()
      })

      const checkboxes = screen.getAllByRole('checkbox')
      const checkbox = checkboxes.find(cb =>
        cb.closest('label')?.textContent?.includes('Weekend Scheduling')
      ) as HTMLInputElement

      expect(checkbox.checked).toBe(true)
      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })
  })

  describe('Change Tracking', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should show "unsaved changes" indicator when fields are modified', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()
    })

    it('should enable save button when changes are made', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const saveButton = screen.getByRole('button', { name: /save settings/i })
      expect(saveButton).toBeDisabled()

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      expect(saveButton).not.toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
      mockedApi.post.mockResolvedValue(mockSettings)
    })

    it('should call API with updated settings when save button is clicked', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      // Make a change
      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(mockedApi.post).toHaveBeenCalledWith(
          '/settings',
          expect.objectContaining({
            work_hours_per_week: 75,
          })
        )
      })
    })

    it('should show saving state while submitting', async () => {
      const user = userEvent.setup({ delay: null })
      mockedApi.post.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)))

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
    })

    it('should clear unsaved changes indicator after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()
      })
    })

    it('should disable save button after successful save', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      const maxHoursInput = findInputByLabelText(container, /max work hours per week/i)!
      changeNumberInput(maxHoursInput, '75')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /save settings/i })).toBeDisabled()
      })
    })
  })

  describe('Algorithm Options', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should have all algorithm options available', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/default algorithm/i)).toBeInTheDocument()
      })

      const algorithmSelect = findSelectByLabelText(container, /default algorithm/i)!
      const options = algorithmSelect.querySelectorAll('option')

      expect(options).toHaveLength(4)
      expect(options[0].textContent).toContain('Greedy')
      expect(options[1].textContent).toContain('CP-SAT')
      expect(options[2].textContent).toContain('PuLP')
      expect(options[3].textContent).toContain('Hybrid')
    })
  })

  describe('Supervision Ratio Options', () => {
    beforeEach(() => {
      mockedApi.get.mockResolvedValue(mockSettings)
    })

    it('should have PGY-1 supervision ratio options', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = findSelectByLabelText(container, /pgy-1 supervision ratio/i)!
      const options = supervisionSelect.querySelectorAll('option')

      expect(options).toHaveLength(2)
      expect(options[0].value).toBe('1:1')
      expect(options[1].value).toBe('1:2')
    })

    it('should have PGY-2 supervision ratio options', async () => {
      const { container } = renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/pgy-2 supervision ratio/i)).toBeInTheDocument()
      })

      const supervisionSelect = findSelectByLabelText(container, /pgy-2 supervision ratio/i)!
      const options = supervisionSelect.querySelectorAll('option')

      expect(options).toHaveLength(3)
      expect(options[0].value).toBe('1:2')
      expect(options[1].value).toBe('1:3')
      expect(options[2].value).toBe('1:4')
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

    it('should have labels for inputs', async () => {
      renderWithProviders(<SettingsPage />)

      await waitFor(() => {
        expect(screen.getByText(/max work hours per week/i)).toBeInTheDocument()
      })

      // Verify labels exist (even if not properly associated with inputs)
      expect(screen.getByText(/max consecutive days/i)).toBeInTheDocument()
      expect(screen.getByText(/min days off per week/i)).toBeInTheDocument()
      expect(screen.getByText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByText(/pgy-2 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByText(/pgy-3 supervision ratio/i)).toBeInTheDocument()
      expect(screen.getByText(/default algorithm/i)).toBeInTheDocument()
    })
  })
})
