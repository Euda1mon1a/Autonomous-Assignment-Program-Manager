import { render, screen, within } from '@/test-utils'
import { CallRoster } from '@/components/schedule/CallRoster'

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  useAssignments: jest.fn(),
  usePeople: jest.fn(),
  useRotationTemplates: jest.fn(),
}))

const { useAssignments, usePeople, useRotationTemplates } = require('@/lib/hooks')

// Helper to create a local date (avoiding timezone issues)
function localDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day) // month is 0-indexed
}

describe('CallRoster', () => {
  const mockStartDate = localDate(2024, 1, 1)
  const mockEndDate = localDate(2024, 1, 7)

  const mockPeople = {
    items: [
      {
        id: '1',
        name: 'Dr. Smith',
        type: 'faculty',
        email: 'smith@example.com',
        pgy_level: null,
      },
      {
        id: '2',
        name: 'Dr. Johnson',
        type: 'resident',
        email: 'johnson@example.com',
        pgy_level: 3,
      },
      {
        id: '3',
        name: 'Dr. Williams',
        type: 'resident',
        email: 'williams@example.com',
        pgy_level: 1,
      },
    ],
  }

  const mockTemplates = {
    items: [
      {
        id: 't1',
        name: 'On-Call',
        abbreviation: 'CALL',
        activity_type: 'call',
      },
      {
        id: 't2',
        name: 'Clinic',
        abbreviation: 'CL',
        activity_type: 'clinic',
      },
    ],
  }

  const mockAssignments = {
    items: [
      {
        id: 'a1',
        person_id: '1',
        rotation_template_id: 't1',
        role: 'primary',
        activity_override: null,
        notes: 'Available 24/7',
        created_at: '2024-01-02T08:00:00Z',
      },
      {
        id: 'a2',
        person_id: '2',
        rotation_template_id: 't1',
        role: 'backup',
        activity_override: null,
        notes: null,
        created_at: '2024-01-02T08:00:00Z',
      },
      {
        id: 'a3',
        person_id: '3',
        rotation_template_id: 't1',
        role: 'primary',
        activity_override: null,
        notes: null,
        created_at: '2024-01-03T08:00:00Z',
      },
    ],
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should render loading spinner when data is loading', () => {
      useAssignments.mockReturnValue({ data: null, isLoading: true, error: null })
      usePeople.mockReturnValue({ data: null, isLoading: true })
      useRotationTemplates.mockReturnValue({ data: null, isLoading: true })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Loading call roster...')).toBeInTheDocument()
    })

    it('should show loading when any hook is loading', () => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: null, isLoading: true })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Loading call roster...')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should render error message when assignments fail to load', () => {
      const error = new Error('Failed to load')
      useAssignments.mockReturnValue({ data: null, isLoading: false, error })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Error Loading Call Roster')).toBeInTheDocument()
      expect(screen.getByText('Failed to load')).toBeInTheDocument()
    })

    it('should show generic error message when error has no message', () => {
      useAssignments.mockReturnValue({ data: null, isLoading: false, error: {} })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Failed to load on-call assignments')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('should render empty state when no assignments', () => {
      useAssignments.mockReturnValue({ data: { items: [] }, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('No On-Call Assignments')).toBeInTheDocument()
      expect(screen.getByText(/No on-call assignments found between/)).toBeInTheDocument()
    })

    it('should show date range in empty state message', () => {
      useAssignments.mockReturnValue({ data: { items: [] }, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      // The empty state message contains the date range
      expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument()
      expect(screen.getByText(/Jan 7, 2024/)).toBeInTheDocument()
    })
  })

  describe('Roster Rendering', () => {
    beforeEach(() => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })
    })

    it('should render header with title and date range', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('On-Call Roster')).toBeInTheDocument()
      // Date range appears in the header subtitle
      expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument()
      expect(screen.getByText(/Jan 7, 2024/)).toBeInTheDocument()
    })

    it('should render legend with seniority colors', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      // Attending/Senior/Intern may appear in legend and as role labels
      expect(screen.getAllByText('Attending').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Senior').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Intern').length).toBeGreaterThan(0)
    })

    it('should render table headers', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Date')).toBeInTheDocument()
      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Level')).toBeInTheDocument()
      expect(screen.getByText('Contact')).toBeInTheDocument()
      expect(screen.getByText('Activity')).toBeInTheDocument()
      expect(screen.getByText('Notes')).toBeInTheDocument()
    })

    it('should render person names', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Dr. Smith')).toBeInTheDocument()
      expect(screen.getByText('Dr. Johnson')).toBeInTheDocument()
      expect(screen.getByText('Dr. Williams')).toBeInTheDocument()
    })

    it('should render contact email as mailto link', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const emailLink = screen.getByText('smith@example.com')
      expect(emailLink.closest('a')).toHaveAttribute('href', 'mailto:smith@example.com')
    })

    it('should show "No email" when person has no email', () => {
      const peopleWithoutEmail = {
        items: [{ ...mockPeople.items[0], email: null }],
      }
      usePeople.mockReturnValue({ data: peopleWithoutEmail, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('No email')).toBeInTheDocument()
    })

    it('should render activity abbreviations', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const abbreviations = screen.getAllByText('CALL')
      expect(abbreviations.length).toBeGreaterThan(0)
    })

    it('should show role labels for backup and supervising', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('(Backup)')).toBeInTheDocument()
    })

    it('should render notes when present', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('Available 24/7')).toBeInTheDocument()
    })
  })

  describe('Seniority Color Coding', () => {
    beforeEach(() => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })
    })

    it('should apply red color for attending (faculty)', () => {
      const { container } = render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const smithBadge = screen.getByText('Dr. Smith').closest('div')
      expect(smithBadge).toHaveClass('bg-red-50')
      expect(smithBadge).toHaveClass('text-red-700')
      expect(smithBadge).toHaveClass('border-red-200')
    })

    it('should apply blue color for senior residents (PGY-2+)', () => {
      const { container } = render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const johnsonBadge = screen.getByText('Dr. Johnson').closest('div')
      expect(johnsonBadge).toHaveClass('bg-blue-50')
      expect(johnsonBadge).toHaveClass('text-blue-700')
    })

    it('should apply green color for interns (PGY-1)', () => {
      const { container } = render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const williamsBadge = screen.getByText('Dr. Williams').closest('div')
      expect(williamsBadge).toHaveClass('bg-green-50')
      expect(williamsBadge).toHaveClass('text-green-700')
    })
  })

  describe('Level Labels', () => {
    beforeEach(() => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })
    })

    it('should show "Attending" for faculty', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      // Attending appears in legend and as role label
      expect(screen.getAllByText('Attending').length).toBeGreaterThan(0)
    })

    it('should show "Intern" for PGY-1', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const internLabels = screen.getAllByText('Intern')
      expect(internLabels.length).toBeGreaterThan(0)
    })

    it('should show "PGY-X" for PGY-2 and PGY-3', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText('PGY-3')).toBeInTheDocument()
    })
  })

  describe('Weekend Highlighting', () => {
    it('should apply weekend background for Saturday/Sunday', () => {
      // Jan 6, 2024 is a Saturday
      const saturdayAssignment = {
        items: [{
          ...mockAssignments.items[0],
          created_at: '2024-01-06T08:00:00Z',
        }],
      }
      useAssignments.mockReturnValue({ data: saturdayAssignment, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      const { container } = render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      const rows = container.querySelectorAll('tbody tr')
      const hasWeekendRow = Array.from(rows).some(row => row.className.includes('bg-gray-50/50'))
      expect(hasWeekendRow).toBe(true)
    })
  })

  describe('Footer Summary', () => {
    beforeEach(() => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })
    })

    it('should display assignment count', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText(/3 on-call assignments/)).toBeInTheDocument()
    })

    it('should use singular form for 1 assignment', () => {
      useAssignments.mockReturnValue({
        data: { items: [mockAssignments.items[0]] },
        isLoading: false,
        error: null,
      })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText(/1 on-call assignment$/)).toBeInTheDocument()
    })

    it('should show help text for nursing staff', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      expect(screen.getByText(/Quick reference for nursing staff/)).toBeInTheDocument()
    })
  })

  describe('Filtering by showOnlyOnCall', () => {
    it('should show all assignments when showOnlyOnCall is false', () => {
      const clinicAssignment = {
        items: [
          ...mockAssignments.items,
          {
            id: 'a4',
            person_id: '1',
            rotation_template_id: 't2',
            role: 'primary',
            activity_override: null,
            notes: null,
            created_at: '2024-01-02T08:00:00Z',
          },
        ],
      }
      useAssignments.mockReturnValue({ data: clinicAssignment, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })

      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} showOnlyOnCall={false} />)

      // Should show clinic assignment too
      expect(screen.getByText('CL')).toBeInTheDocument()
    })
  })

  describe('Date Grouping', () => {
    beforeEach(() => {
      useAssignments.mockReturnValue({ data: mockAssignments, isLoading: false, error: null })
      usePeople.mockReturnValue({ data: mockPeople, isLoading: false })
      useRotationTemplates.mockReturnValue({ data: mockTemplates, isLoading: false })
    })

    it('should group assignments by date', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      // Check that dates are displayed (Jan 2 and Jan 3)
      expect(screen.getByText('Jan 2')).toBeInTheDocument()
      expect(screen.getByText('Jan 3')).toBeInTheDocument()
    })

    it('should display day of week for each date', () => {
      render(<CallRoster startDate={mockStartDate} endDate={mockEndDate} />)

      // Jan 2, 2024 is Tuesday, Jan 3 is Wednesday
      expect(screen.getByText('Tuesday')).toBeInTheDocument()
      expect(screen.getByText('Wednesday')).toBeInTheDocument()
    })
  })
})
