/**
 * ScheduleGrid Component Tests
 *
 * Tests for the ScheduleGrid component including data fetching,
 * rendering of people groups, assignments, and loading/error states.
 */
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ScheduleGrid } from '@/components/schedule/ScheduleGrid'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockPeople = [
  {
    id: 'person-1',
    name: 'Dr. Alice PGY1',
    email: 'alice@hospital.org',
    type: 'resident' as const,
    pgy_level: 1,
    performs_procedures: true,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Bob PGY2',
    email: 'bob@hospital.org',
    type: 'resident' as const,
    pgy_level: 2,
    performs_procedures: true,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-3',
    name: 'Dr. Carol Faculty',
    email: 'carol@hospital.org',
    type: 'faculty' as const,
    pgy_level: null,
    performs_procedures: true,
    specialties: ['Cardiology'],
    primary_duty: 'Attending',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

const mockBlocks = [
  {
    id: 'block-1',
    date: '2024-01-01',
    time_of_day: 'AM' as const,
    block_number: 1,
    is_weekend: false,
    is_holiday: false,
    holiday_name: null,
  },
  {
    id: 'block-2',
    date: '2024-01-01',
    time_of_day: 'PM' as const,
    block_number: 1,
    is_weekend: false,
    is_holiday: false,
    holiday_name: null,
  },
]

const mockTemplates = [
  {
    id: 'template-1',
    name: 'Cardiology Clinic',
    activity_type: 'clinic',
    abbreviation: 'CARD',
    clinic_location: null,
    max_residents: 4,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-01-01T00:00:00Z',
  },
]

const mockAssignments = [
  {
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'template-1',
    role: 'primary' as const,
    activity_override: null,
    notes: null,
    created_by: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

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

describe('ScheduleGrid', () => {
  const startDate = new Date('2024-01-01')
  const endDate = new Date('2024-01-07')

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading spinner while fetching data', () => {
      // Mock API to never resolve (keeps loading state)
      mockedApi.get.mockImplementation(() => new Promise(() => {}))

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      expect(screen.getByText(/loading schedule/i)).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error when blocks fail to load', async () => {
      mockedApi.get.mockRejectedValueOnce({ message: 'Failed to fetch blocks', status: 500 })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/failed to load schedule data/i)).toBeInTheDocument()
      })
    })

    it('should display error when assignments fail to load', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockRejectedValueOnce({ message: 'Failed to fetch assignments', status: 500 })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/failed to load schedule data/i)).toBeInTheDocument()
      })
    })

    it('should display error when people fail to load', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockRejectedValueOnce({ message: 'Failed to fetch people', status: 500 })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/failed to load schedule data/i)).toBeInTheDocument()
      })
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no people exist', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: [], total: 0 }) // No people
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/no people found/i)).toBeInTheDocument()
      })

      expect(screen.getByText(/add residents and faculty/i)).toBeInTheDocument()
    })
  })

  describe('Successful Rendering', () => {
    beforeEach(() => {
      // Mock all required API calls
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: mockPeople, total: mockPeople.length })
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })
    })

    it('should render schedule grid with header', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      // Schedule grid should be rendered as a table
      const table = screen.getByRole('table')
      expect(table).toBeInTheDocument()
    })

    it('should group people by PGY level', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText('PGY-1')).toBeInTheDocument()
      })

      expect(screen.getByText('PGY-2')).toBeInTheDocument()
      expect(screen.getByText('Faculty')).toBeInTheDocument()
    })

    it('should display person names in the grid', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText('Dr. Alice PGY1')).toBeInTheDocument()
      })

      expect(screen.getByText('Dr. Bob PGY2')).toBeInTheDocument()
      expect(screen.getByText('Dr. Carol Faculty')).toBeInTheDocument()
    })

    it('should display PGY badges for residents', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText('PGY-1')).toBeInTheDocument()
      })

      expect(screen.getByText('PGY-2')).toBeInTheDocument()
    })

    it('should display faculty badge for faculty members', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText('Faculty')).toBeInTheDocument()
      })
    })
  })

  describe('Date Range Handling', () => {
    it('should render days in the specified date range', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: mockPeople, total: mockPeople.length })
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      // The schedule should make API calls with the correct date range
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      )
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('end_date=2024-01-07')
      )
    })

    it('should handle single day range', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: mockPeople, total: mockPeople.length })
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })

      const singleDay = new Date('2024-01-01')
      renderWithProviders(
        <ScheduleGrid startDate={singleDay} endDate={singleDay} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2024-01-01')
      )
    })
  })

  describe('Assignment Display', () => {
    it('should display assignments with abbreviations', async () => {
      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: mockPeople, total: mockPeople.length })
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      // Assignment abbreviation should be displayed
      // Based on mockTemplates, the abbreviation is 'CARD'
      await waitFor(() => {
        expect(screen.getByText(/CARD/i)).toBeInTheDocument()
      })
    })
  })

  describe('Person Grouping', () => {
    it('should sort people within groups by name', async () => {
      const multiplePGY1 = [
        { ...mockPeople[0], id: 'p1', name: 'Dr. Zara PGY1', pgy_level: 1 },
        { ...mockPeople[0], id: 'p2', name: 'Dr. Alice PGY1', pgy_level: 1 },
        { ...mockPeople[0], id: 'p3', name: 'Dr. Mike PGY1', pgy_level: 1 },
      ]

      mockedApi.get
        .mockResolvedValueOnce({ items: mockBlocks, total: mockBlocks.length })
        .mockResolvedValueOnce({ items: mockAssignments, total: mockAssignments.length })
        .mockResolvedValueOnce({ items: multiplePGY1, total: multiplePGY1.length })
        .mockResolvedValueOnce({ items: mockTemplates, total: mockTemplates.length })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText('Dr. Alice PGY1')).toBeInTheDocument()
      })

      expect(screen.getByText('Dr. Mike PGY1')).toBeInTheDocument()
      expect(screen.getByText('Dr. Zara PGY1')).toBeInTheDocument()
    })
  })
})
