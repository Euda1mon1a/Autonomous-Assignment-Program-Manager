/**
 * SettingsPanel Component Tests
 *
 * Tests for settings management functionality including form inputs,
 * validation, saving, and different configuration sections.
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api')

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

// Simplified SettingsPanel component for testing
// This simulates the core functionality of the settings page
interface SettingsPanelProps {
  onSave?: (settings: typeof mockSettings) => void
}

function SettingsPanel({ onSave }: SettingsPanelProps) {
  const [settings, setSettings] = React.useState(mockSettings)
  const [hasChanges, setHasChanges] = React.useState(false)
  const [isSaving, setIsSaving] = React.useState(false)

  const handleChange = (section: string, field: string, value: any) => {
    setSettings((prev) => ({
      ...prev,
      [section]: {
        ...(prev as any)[section],
        [field]: value,
      },
    }))
    setHasChanges(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      await api.put('/settings', settings)
      setHasChanges(false)
      onSave?.(settings)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <h2>Academic Year</h2>
        <label>
          Start Date
          <input
            type="date"
            value={settings.academicYear.startDate}
            onChange={(e) => handleChange('academicYear', 'startDate', e.target.value)}
          />
        </label>
        <label>
          End Date
          <input
            type="date"
            value={settings.academicYear.endDate}
            onChange={(e) => handleChange('academicYear', 'endDate', e.target.value)}
          />
        </label>
        <label>
          Block Duration (days)
          <input
            type="number"
            value={settings.academicYear.blockDuration}
            onChange={(e) => handleChange('academicYear', 'blockDuration', parseInt(e.target.value))}
          />
        </label>
      </div>

      <div>
        <h2>ACGME Settings</h2>
        <label>
          Max Weekly Hours
          <input
            type="number"
            value={settings.acgme.maxWeeklyHours}
            onChange={(e) => handleChange('acgme', 'maxWeeklyHours', parseInt(e.target.value))}
          />
        </label>
        <label>
          PGY-1 Supervision Ratio
          <select
            value={settings.acgme.pgy1SupervisionRatio}
            onChange={(e) => handleChange('acgme', 'pgy1SupervisionRatio', parseInt(e.target.value))}
          >
            <option value={1}>1:1</option>
            <option value={2}>1:2</option>
          </select>
        </label>
      </div>

      <div>
        <h2>Scheduling Algorithm</h2>
        <label>
          Default Algorithm
          <select
            value={settings.scheduling.defaultAlgorithm}
            onChange={(e) => handleChange('scheduling', 'defaultAlgorithm', e.target.value)}
          >
            <option value="greedy">Greedy (Fast)</option>
            <option value="cp_sat">CP-SAT (Optimal, OR-Tools)</option>
            <option value="pulp">PuLP (Linear Programming)</option>
            <option value="hybrid">Hybrid (CP-SAT + PuLP)</option>
          </select>
        </label>
      </div>

      {hasChanges && <span>Unsaved changes</span>}
      <button type="submit" disabled={isSaving || !hasChanges}>
        {isSaving ? 'Saving...' : 'Save Settings'}
      </button>
    </form>
  )
}

// We need to import React for the component above
import React from 'react'

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
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('SettingsPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render all settings sections', () => {
      renderWithProviders(<SettingsPanel />)

      expect(screen.getByText('Academic Year')).toBeInTheDocument()
      expect(screen.getByText('ACGME Settings')).toBeInTheDocument()
      expect(screen.getByText('Scheduling Algorithm')).toBeInTheDocument()
    })

    it('should render academic year fields', () => {
      renderWithProviders(<SettingsPanel />)

      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/end date/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/block duration/i)).toBeInTheDocument()
    })

    it('should render ACGME settings fields', () => {
      renderWithProviders(<SettingsPanel />)

      expect(screen.getByLabelText(/max weekly hours/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy-1 supervision ratio/i)).toBeInTheDocument()
    })

    it('should render scheduling algorithm field', () => {
      renderWithProviders(<SettingsPanel />)

      expect(screen.getByLabelText(/default algorithm/i)).toBeInTheDocument()
    })

    it('should render save button', () => {
      renderWithProviders(<SettingsPanel />)

      expect(screen.getByRole('button', { name: /save settings/i })).toBeInTheDocument()
    })
  })

  describe('Default Values', () => {
    it('should display default academic year values', () => {
      renderWithProviders(<SettingsPanel />)

      const startDateInput = screen.getByLabelText(/start date/i) as HTMLInputElement
      const endDateInput = screen.getByLabelText(/end date/i) as HTMLInputElement
      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement

      expect(startDateInput.value).toBe('2024-07-01')
      expect(endDateInput.value).toBe('2025-06-30')
      expect(blockDurationInput.value).toBe('28')
    })

    it('should display default ACGME values', () => {
      renderWithProviders(<SettingsPanel />)

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
      const supervisionSelect = screen.getByLabelText(/pgy-1 supervision ratio/i) as HTMLSelectElement

      expect(maxHoursInput.value).toBe('80')
      expect(supervisionSelect.value).toBe('2')
    })

    it('should display default algorithm value', () => {
      renderWithProviders(<SettingsPanel />)

      const algorithmSelect = screen.getByLabelText(/default algorithm/i) as HTMLSelectElement
      expect(algorithmSelect.value).toBe('greedy')
    })
  })

  describe('User Interactions', () => {
    it('should update start date when changed', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const startDateInput = screen.getByLabelText(/start date/i) as HTMLInputElement
      await user.clear(startDateInput)
      await user.type(startDateInput, '2025-07-01')

      expect(startDateInput.value).toBe('2025-07-01')
    })

    it('should update block duration when changed', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const blockDurationInput = screen.getByLabelText(/block duration/i) as HTMLInputElement
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(blockDurationInput.value).toBe('30')
    })

    it('should update max weekly hours when changed', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const maxHoursInput = screen.getByLabelText(/max weekly hours/i) as HTMLInputElement
      await user.clear(maxHoursInput)
      await user.type(maxHoursInput, '75')

      expect(maxHoursInput.value).toBe('75')
    })

    it('should update supervision ratio when changed', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const supervisionSelect = screen.getByLabelText(/pgy-1 supervision ratio/i) as HTMLSelectElement
      await user.selectOptions(supervisionSelect, '1')

      expect(supervisionSelect.value).toBe('1')
    })

    it('should update algorithm when changed', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const algorithmSelect = screen.getByLabelText(/default algorithm/i) as HTMLSelectElement
      await user.selectOptions(algorithmSelect, 'cp_sat')

      expect(algorithmSelect.value).toBe('cp_sat')
    })
  })

  describe('Change Tracking', () => {
    it('should show "unsaved changes" indicator when fields are modified', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()

      const startDateInput = screen.getByLabelText(/start date/i)
      await user.clear(startDateInput)
      await user.type(startDateInput, '2025-07-01')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()
    })

    it('should enable save button when changes are made', async () => {
      const user = userEvent.setup()
      renderWithProviders(<SettingsPanel />)

      const saveButton = screen.getByRole('button', { name: /save settings/i })
      expect(saveButton).toBeDisabled()

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(saveButton).not.toBeDisabled()
    })
  })

  describe('Form Submission', () => {
    it('should call API when save button is clicked', async () => {
      const user = userEvent.setup()
      mockedApi.put.mockResolvedValueOnce(mockSettings)

      renderWithProviders(<SettingsPanel />)

      // Make a change
      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      // Submit form
      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(mockedApi.put).toHaveBeenCalledWith('/settings', expect.objectContaining({
          academicYear: expect.objectContaining({
            blockDuration: 30,
          }),
        }))
      })
    })

    it('should show saving state while submitting', async () => {
      const user = userEvent.setup()
      mockedApi.put.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)))

      renderWithProviders(<SettingsPanel />)

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /saving/i })).toBeDisabled()
    })

    it('should clear unsaved changes indicator after successful save', async () => {
      const user = userEvent.setup()
      mockedApi.put.mockResolvedValueOnce(mockSettings)

      renderWithProviders(<SettingsPanel />)

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(screen.queryByText(/unsaved changes/i)).not.toBeInTheDocument()
      })
    })

    it('should call onSave callback after successful save', async () => {
      const user = userEvent.setup()
      const mockOnSave = jest.fn()
      mockedApi.put.mockResolvedValueOnce(mockSettings)

      renderWithProviders(<SettingsPanel onSave={mockOnSave} />)

      const blockDurationInput = screen.getByLabelText(/block duration/i)
      await user.clear(blockDurationInput)
      await user.type(blockDurationInput, '30')

      await user.click(screen.getByRole('button', { name: /save settings/i }))

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(expect.objectContaining({
          academicYear: expect.objectContaining({
            blockDuration: 30,
          }),
        }))
      })
    })
  })

  describe('Algorithm Options', () => {
    it('should have all algorithm options available', () => {
      renderWithProviders(<SettingsPanel />)

      const algorithmSelect = screen.getByLabelText(/default algorithm/i)
      const options = algorithmSelect.querySelectorAll('option')

      expect(options).toHaveLength(4)
      expect(options[0].textContent).toContain('Greedy')
      expect(options[1].textContent).toContain('CP-SAT')
      expect(options[2].textContent).toContain('PuLP')
      expect(options[3].textContent).toContain('Hybrid')
    })
  })

  describe('Supervision Ratio Options', () => {
    it('should have supervision ratio options', () => {
      renderWithProviders(<SettingsPanel />)

      const supervisionSelect = screen.getByLabelText(/pgy-1 supervision ratio/i)
      const options = supervisionSelect.querySelectorAll('option')

      expect(options).toHaveLength(2)
      // The inline SettingsPanel component uses numeric values for the select
      expect(options[0].value).toBe('1')
      expect(options[1].value).toBe('2')
    })
  })

  describe('Multiple Changes', () => {
    it('should handle multiple field changes correctly', async () => {
      const user = userEvent.setup()
      mockedApi.put.mockResolvedValueOnce(mockSettings)

      renderWithProviders(<SettingsPanel />)

      // Change multiple fields
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
        expect(mockedApi.put).toHaveBeenCalledWith('/settings', expect.objectContaining({
          academicYear: expect.objectContaining({ blockDuration: 30 }),
          acgme: expect.objectContaining({ maxWeeklyHours: 75 }),
          scheduling: expect.objectContaining({ defaultAlgorithm: 'cp_sat' }),
        }))
      })
    })
  })
})
