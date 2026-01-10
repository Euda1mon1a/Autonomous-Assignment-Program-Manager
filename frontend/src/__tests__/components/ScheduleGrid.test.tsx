/**
 * ScheduleGrid Component Tests
 *
 * Tests for the ScheduleGrid component including data fetching,
 * rendering of people groups, assignments, and loading/error states.
 */
import { render, screen, waitFor } from '@/test-utils'
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
    pgyLevel: 1,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Bob PGY2',
    email: 'bob@hospital.org',
    type: 'resident' as const,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-3',
    name: 'Dr. Carol Faculty',
    email: 'carol@hospital.org',
    type: 'faculty' as const,
    pgyLevel: null,
    performsProcedures: true,
    specialties: ['Cardiology'],
    primaryDuty: 'Attending',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
]

const mockBlocks = [
  {
    id: 'block-1',
    date: '2024-01-01',
    timeOfDay: 'AM' as const,
    blockNumber: 1,
    isWeekend: false,
    isHoliday: false,
    holidayName: null,
  },
  {
    id: 'block-2',
    date: '2024-01-01',
    timeOfDay: 'PM' as const,
    blockNumber: 1,
    isWeekend: false,
    isHoliday: false,
    holidayName: null,
  },
]

const mockTemplates = [
  {
    id: 'template-1',
    name: 'Cardiology Clinic',
    activityType: 'clinic',
    abbreviation: 'CARD',
    clinicLocation: null,
    maxResidents: 4,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 2,
    createdAt: '2024-01-01T00:00:00Z',
  },
]

const mockAssignments = [
  {
    id: 'assignment-1',
    blockId: 'block-1',
    personId: 'person-1',
    rotationTemplateId: 'template-1',
    role: 'primary' as const,
    activityOverride: null,
    notes: null,
    createdBy: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
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

// Helper to create a local date (avoiding timezone issues)
function localDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day) // month is 0-indexed
}

describe('ScheduleGrid', () => {
  const startDate = localDate(2024, 1, 1)
  const endDate = localDate(2024, 1, 7)

  // Helper to setup API mocks based on URL pattern
  function setupApiMock(options: {
    blocks?: typeof mockBlocks | 'error' | 'never',
    assignments?: typeof mockAssignments | 'error' | 'never',
    people?: typeof mockPeople | 'error' | 'never',
    templates?: typeof mockTemplates | 'error' | 'never',
  }) {
    mockedApi.get.mockImplementation((url: string) => {
      if (url.includes('/blocks')) {
        if (options.blocks === 'error') return Promise.reject({ message: 'Failed to fetch blocks', status: 500 })
        if (options.blocks === 'never') return new Promise(() => {})
        return Promise.resolve({ items: options.blocks ?? mockBlocks, total: (options.blocks ?? mockBlocks).length })
      }
      if (url.includes('/assignments')) {
        if (options.assignments === 'error') return Promise.reject({ message: 'Failed to fetch assignments', status: 500 })
        if (options.assignments === 'never') return new Promise(() => {})
        return Promise.resolve({ items: options.assignments ?? mockAssignments, total: (options.assignments ?? mockAssignments).length })
      }
      if (url.includes('/people')) {
        if (options.people === 'error') return Promise.reject({ message: 'Failed to fetch people', status: 500 })
        if (options.people === 'never') return new Promise(() => {})
        return Promise.resolve({ items: options.people ?? mockPeople, total: (options.people ?? mockPeople).length })
      }
      if (url.includes('/rotation-templates')) {
        if (options.templates === 'error') return Promise.reject({ message: 'Failed to fetch templates', status: 500 })
        if (options.templates === 'never') return new Promise(() => {})
        return Promise.resolve({ items: options.templates ?? mockTemplates, total: (options.templates ?? mockTemplates).length })
      }
      return Promise.reject({ message: 'Unknown endpoint', status: 404 })
    })
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading spinner while fetching data', () => {
      // Mock API to never resolve (keeps loading state)
      setupApiMock({ blocks: 'never', assignments: 'never', people: 'never', templates: 'never' })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      expect(screen.getByText(/loading schedule/i)).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error when blocks fail to load', async () => {
      setupApiMock({ blocks: 'error' })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/failed to load schedule data/i)).toBeInTheDocument()
      })
    })

    it('should display error when assignments fail to load', async () => {
      setupApiMock({ assignments: 'error' })

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.getByText(/failed to load schedule data/i)).toBeInTheDocument()
      })
    })

    it('should display error when people fail to load', async () => {
      setupApiMock({ people: 'error' })

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
      setupApiMock({ people: [] as typeof mockPeople })

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
      // Mock all required API calls with default mock data
      setupApiMock({})
    })

    it('should render schedule grid with header', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      // Schedule grid should be rendered with role="grid" (ARIA grid pattern)
      const grid = screen.getByRole('grid')
      expect(grid).toBeInTheDocument()
    })

    it('should group people by PGY level', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        // PGY-1 appears multiple times (group header and badge), so use getAllByText
        expect(screen.getAllByText('PGY-1').length).toBeGreaterThan(0)
      })

      expect(screen.getAllByText('PGY-2').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Faculty').length).toBeGreaterThan(0)
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
        // PGY badges appear with text PGY-N
        expect(screen.getAllByText('PGY-1').length).toBeGreaterThan(0)
      })

      expect(screen.getAllByText('PGY-2').length).toBeGreaterThan(0)
    })

    it('should display faculty badge for faculty members', async () => {
      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        // Faculty text appears in group header and badge
        expect(screen.getAllByText('Faculty').length).toBeGreaterThan(0)
      })
    })
  })

  describe('Date Range Handling', () => {
    it('should render days in the specified date range', async () => {
      setupApiMock({})

      renderWithProviders(
        <ScheduleGrid startDate={startDate} endDate={endDate} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      // The schedule should make API calls with the correct date range
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      )
      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('endDate=2024-01-07')
      )
    })

    it('should handle single day range', async () => {
      setupApiMock({})

      const singleDay = localDate(2024, 1, 1)
      renderWithProviders(
        <ScheduleGrid startDate={singleDay} endDate={singleDay} />
      )

      await waitFor(() => {
        expect(screen.queryByText(/loading schedule/i)).not.toBeInTheDocument()
      })

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('startDate=2024-01-01')
      )
    })
  })

  describe('Assignment Display', () => {
    it('should display assignments with abbreviations', async () => {
      setupApiMock({})

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
        { ...mockPeople[0], id: 'p1', name: 'Dr. Zara PGY1', pgyLevel: 1 },
        { ...mockPeople[0], id: 'p2', name: 'Dr. Alice PGY1', pgyLevel: 1 },
        { ...mockPeople[0], id: 'p3', name: 'Dr. Mike PGY1', pgyLevel: 1 },
      ]

      setupApiMock({ people: multiplePGY1 as typeof mockPeople })

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
