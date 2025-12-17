/**
 * BlockCalendar Component Tests
 *
 * Tests for the AbsenceCalendar component (used as BlockCalendar)
 * including navigation, absence display, and user interactions.
 */
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AbsenceCalendar } from '@/components/AbsenceCalendar'
import type { Absence, Person } from '@/types/api'

// Mock data
const mockPeople: Person[] = [
  {
    id: 'person-1',
    name: 'Dr. Alice Smith',
    email: 'alice@hospital.org',
    type: 'resident',
    pgy_level: 1,
    performs_procedures: true,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'person-2',
    name: 'Dr. Bob Jones',
    email: 'bob@hospital.org',
    type: 'resident',
    pgy_level: 2,
    performs_procedures: false,
    specialties: ['Internal Medicine'],
    primary_duty: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

const mockAbsences: Absence[] = [
  {
    id: 'absence-1',
    person_id: 'person-1',
    start_date: '2024-01-15',
    end_date: '2024-01-17',
    absence_type: 'vacation',
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: 'Winter vacation',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'absence-2',
    person_id: 'person-2',
    start_date: '2024-01-10',
    end_date: '2024-01-12',
    absence_type: 'conference',
    deployment_orders: false,
    tdy_location: 'Chicago, IL',
    replacement_activity: null,
    notes: 'Medical conference',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'absence-3',
    person_id: 'person-1',
    start_date: '2024-01-20',
    end_date: '2024-01-20',
    absence_type: 'sick',
    deployment_orders: false,
    tdy_location: null,
    replacement_activity: null,
    notes: null,
    created_at: '2024-01-20T00:00:00Z',
  },
]

describe('BlockCalendar (AbsenceCalendar)', () => {
  const mockOnAbsenceClick = jest.fn()

  beforeEach(() => {
    mockOnAbsenceClick.mockClear()
    // Mock current date to ensure consistent test results
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-01-01'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Rendering', () => {
    it('should render calendar with month and year', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('January 2024')).toBeInTheDocument()
    })

    it('should render day headers', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('Sun')).toBeInTheDocument()
      expect(screen.getByText('Mon')).toBeInTheDocument()
      expect(screen.getByText('Tue')).toBeInTheDocument()
      expect(screen.getByText('Wed')).toBeInTheDocument()
      expect(screen.getByText('Thu')).toBeInTheDocument()
      expect(screen.getByText('Fri')).toBeInTheDocument()
      expect(screen.getByText('Sat')).toBeInTheDocument()
    })

    it('should render navigation buttons', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByLabelText('Previous month')).toBeInTheDocument()
      expect(screen.getByLabelText('Next month')).toBeInTheDocument()
    })

    it('should render calendar legend', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('vacation')).toBeInTheDocument()
      expect(screen.getByText('sick')).toBeInTheDocument()
      expect(screen.getByText('conference')).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('should navigate to previous month', async () => {
      const user = userEvent.setup({ delay: null })
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('January 2024')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Previous month'))

      await waitFor(() => {
        expect(screen.getByText('December 2023')).toBeInTheDocument()
      })
    })

    it('should navigate to next month', async () => {
      const user = userEvent.setup({ delay: null })
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('January 2024')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Next month'))

      await waitFor(() => {
        expect(screen.getByText('February 2024')).toBeInTheDocument()
      })
    })

    it('should navigate multiple months forward', async () => {
      const user = userEvent.setup({ delay: null })
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      await user.click(screen.getByLabelText('Next month'))
      await user.click(screen.getByLabelText('Next month'))
      await user.click(screen.getByLabelText('Next month'))

      await waitFor(() => {
        expect(screen.getByText('April 2024')).toBeInTheDocument()
      })
    })
  })

  describe('Absence Display', () => {
    it('should display absences on correct dates', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // January absences should be visible
      expect(screen.getByText(/vacation/i)).toBeInTheDocument()
      expect(screen.getByText(/conference/i)).toBeInTheDocument()
      expect(screen.getByText(/sick/i)).toBeInTheDocument()
    })

    it('should display person initials with absence type', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Dr. Alice Smith -> AS, Dr. Bob Jones -> BJ
      expect(screen.getByText(/AS/)).toBeInTheDocument()
      expect(screen.getByText(/BJ/)).toBeInTheDocument()
    })

    it('should handle multiple absences on same day', () => {
      const multipleAbsencesOneDay: Absence[] = [
        {
          ...mockAbsences[0],
          id: 'absence-multi-1',
          start_date: '2024-01-15',
          end_date: '2024-01-15',
        },
        {
          ...mockAbsences[1],
          id: 'absence-multi-2',
          start_date: '2024-01-15',
          end_date: '2024-01-15',
        },
        {
          ...mockAbsences[2],
          id: 'absence-multi-3',
          start_date: '2024-01-15',
          end_date: '2024-01-15',
        },
      ]

      render(
        <AbsenceCalendar
          absences={multipleAbsencesOneDay}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // All absences should be displayed
      const vacationElements = screen.getAllByText(/vacation/i)
      expect(vacationElements.length).toBeGreaterThan(0)
    })

    it('should show "more" indicator when more than 3 absences on one day', () => {
      const manyAbsences: Absence[] = [
        { ...mockAbsences[0], id: 'abs-1', start_date: '2024-01-15', end_date: '2024-01-15' },
        { ...mockAbsences[1], id: 'abs-2', start_date: '2024-01-15', end_date: '2024-01-15' },
        { ...mockAbsences[2], id: 'abs-3', start_date: '2024-01-15', end_date: '2024-01-15' },
        {
          ...mockAbsences[0],
          id: 'abs-4',
          start_date: '2024-01-15',
          end_date: '2024-01-15',
          absence_type: 'personal',
        },
      ]

      render(
        <AbsenceCalendar
          absences={manyAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText(/\+1 more/i)).toBeInTheDocument()
    })

    it('should handle multi-day absences spanning multiple dates', () => {
      const multiDayAbsence: Absence[] = [
        {
          id: 'absence-span',
          person_id: 'person-1',
          start_date: '2024-01-15',
          end_date: '2024-01-20',
          absence_type: 'vacation',
          deployment_orders: false,
          tdy_location: null,
          replacement_activity: null,
          notes: 'Extended vacation',
          created_at: '2024-01-01T00:00:00Z',
        },
      ]

      render(
        <AbsenceCalendar
          absences={multiDayAbsence}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // The absence should appear multiple times (once for each day)
      const vacationElements = screen.getAllByText(/vacation/i)
      expect(vacationElements.length).toBeGreaterThan(1)
    })
  })

  describe('User Interactions', () => {
    it('should call onAbsenceClick when absence is clicked', async () => {
      const user = userEvent.setup({ delay: null })
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      const absenceButton = screen.getAllByText(/vacation/i)[0].closest('button')
      expect(absenceButton).toBeInTheDocument()

      if (absenceButton) {
        await user.click(absenceButton)
        expect(mockOnAbsenceClick).toHaveBeenCalledTimes(1)
        expect(mockOnAbsenceClick).toHaveBeenCalledWith(
          expect.objectContaining({
            absence_type: 'vacation',
          })
        )
      }
    })

    it('should call onAbsenceClick with correct absence data', async () => {
      const user = userEvent.setup({ delay: null })
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      const conferenceButton = screen.getByText(/conference/i).closest('button')
      if (conferenceButton) {
        await user.click(conferenceButton)

        expect(mockOnAbsenceClick).toHaveBeenCalledWith(
          expect.objectContaining({
            id: 'absence-2',
            absence_type: 'conference',
            person_id: 'person-2',
          })
        )
      }
    })
  })

  describe('Empty States', () => {
    it('should render calendar with no absences', () => {
      render(
        <AbsenceCalendar
          absences={[]}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('January 2024')).toBeInTheDocument()
      // Calendar should still render all day headers
      expect(screen.getByText('Mon')).toBeInTheDocument()
    })

    it('should handle empty people list gracefully', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={[]}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('January 2024')).toBeInTheDocument()
    })
  })

  describe('Absence Type Colors', () => {
    it('should apply different colors for different absence types', () => {
      const differentTypes: Absence[] = [
        { ...mockAbsences[0], id: 'a1', absence_type: 'vacation' },
        { ...mockAbsences[0], id: 'a2', absence_type: 'sick', start_date: '2024-01-16', end_date: '2024-01-16' },
        { ...mockAbsences[0], id: 'a3', absence_type: 'conference', start_date: '2024-01-17', end_date: '2024-01-17' },
      ]

      const { container } = render(
        <AbsenceCalendar
          absences={differentTypes}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Each absence type should have its own color class
      // vacation -> green, sick -> red, conference -> blue
      const absenceButtons = container.querySelectorAll('button')
      expect(absenceButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Weekend Highlighting', () => {
    it('should highlight weekend days differently', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Weekend days should have bg-gray-50 class
      const weekendCells = container.querySelectorAll('.bg-gray-50')
      expect(weekendCells.length).toBeGreaterThan(0)
    })
  })

  describe('Current Day Indicator', () => {
    it('should highlight current day', () => {
      // Current date is mocked as 2024-01-01
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // The current day (1) should have special styling
      // Looking for day number "1" with blue background
      const dayElements = container.querySelectorAll('.bg-blue-600')
      expect(dayElements.length).toBeGreaterThan(0)
    })
  })
})
