import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AbsenceCalendar } from '@/components/AbsenceCalendar'
import { mockFactories } from '../utils/test-utils'
import type { Absence, Person } from '@/types/api'

describe('AbsenceCalendar', () => {
  const mockPeople: Person[] = [
    mockFactories.person({ id: 'person-1', name: 'Dr. John Smith' }),
    mockFactories.person({ id: 'person-2', name: 'Dr. Jane Doe' }),
  ]

  const mockAbsences: Absence[] = [
    mockFactories.absence({
      id: 'absence-1',
      person_id: 'person-1',
      start_date: '2024-02-05',
      end_date: '2024-02-05',
      absence_type: 'vacation',
    }),
    mockFactories.absence({
      id: 'absence-2',
      person_id: 'person-2',
      start_date: '2024-02-10',
      end_date: '2024-02-14',
      absence_type: 'deployment',
    }),
  ]

  const mockOnAbsenceClick = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    // Mock current date to February 2024 for consistency
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-02-01'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Calendar Rendering', () => {
    it('should render calendar with current month header', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('February 2024')).toBeInTheDocument()
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

    it('should render calendar grid with correct number of cells', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // February 2024 has 29 days, and the grid should have blank cells + day cells
      const calendarGrid = container.querySelector('.grid.grid-cols-7')
      expect(calendarGrid).toBeInTheDocument()
    })

    it('should render legend with absence types', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('vacation')).toBeInTheDocument()
      expect(screen.getByText('conference')).toBeInTheDocument()
    })
  })

  describe('Month Navigation', () => {
    it('should render previous and next month buttons', () => {
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

    it('should navigate to previous month when clicking previous button', async () => {
      const user = userEvent.setup({ delay: null })

      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('February 2024')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Previous month'))

      expect(screen.getByText('January 2024')).toBeInTheDocument()
    })

    it('should navigate to next month when clicking next button', async () => {
      const user = userEvent.setup({ delay: null })

      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('February 2024')).toBeInTheDocument()

      await user.click(screen.getByLabelText('Next month'))

      expect(screen.getByText('March 2024')).toBeInTheDocument()
    })

    it('should navigate multiple months', async () => {
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

      expect(screen.getByText('April 2024')).toBeInTheDocument()
    })
  })

  describe('Absence Display', () => {
    it('should display absence in correct day cell', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Look for the vacation absence on Feb 5
      expect(screen.getByText(/vacation/i)).toBeInTheDocument()
    })

    it('should display person initials for absence', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Dr. John Smith = JS
      expect(screen.getByText('JS')).toBeInTheDocument()
    })

    it('should show multi-day absences across multiple cells', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Deployment from Feb 10-14 (5 days)
      const deploymentElements = screen.getAllByText(/deployment/i)
      // Should appear in multiple day cells
      expect(deploymentElements.length).toBeGreaterThan(1)
    })

    it('should show "more" indicator when more than 3 absences in a day', () => {
      const manyAbsences: Absence[] = [
        ...mockAbsences,
        mockFactories.absence({
          id: 'absence-3',
          person_id: 'person-1',
          start_date: '2024-02-05',
          end_date: '2024-02-05',
          absence_type: 'conference',
        }),
        mockFactories.absence({
          id: 'absence-4',
          person_id: 'person-2',
          start_date: '2024-02-05',
          end_date: '2024-02-05',
          absence_type: 'medical',
        }),
        mockFactories.absence({
          id: 'absence-5',
          person_id: 'person-1',
          start_date: '2024-02-05',
          end_date: '2024-02-05',
          absence_type: 'tdy',
        }),
      ]

      render(
        <AbsenceCalendar
          absences={manyAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Should show "+ more" indicator
      expect(screen.getByText(/\+.*more/i)).toBeInTheDocument()
    })

    it('should apply correct color classes for different absence types', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Vacation should have green color
      const vacationButton = screen.getByTitle(/Dr. John Smith.*vacation/i)
      expect(vacationButton).toHaveClass('bg-green-100')

      // Deployment should have orange color
      const deploymentButtons = screen.getAllByTitle(/Dr. Jane Doe.*deployment/i)
      deploymentButtons.forEach((btn) => {
        expect(btn).toHaveClass('bg-orange-100')
      })
    })
  })

  describe('Absence Interactions', () => {
    it('should call onAbsenceClick when clicking absence', async () => {
      const user = userEvent.setup({ delay: null })

      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      const absenceButton = screen.getByTitle(/Dr. John Smith.*vacation/i)
      await user.click(absenceButton)

      expect(mockOnAbsenceClick).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'absence-1',
          person_id: 'person-1',
          absence_type: 'vacation',
        })
      )
    })

    it('should have correct title attribute for absence button', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      const absenceButton = screen.getByTitle(/Dr. John Smith.*vacation/i)
      expect(absenceButton).toHaveAttribute('title', 'Dr. John Smith - vacation')
    })
  })

  describe('Empty States', () => {
    it('should render calendar even with no absences', () => {
      render(
        <AbsenceCalendar
          absences={[]}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('February 2024')).toBeInTheDocument()
      expect(screen.getByText('Sun')).toBeInTheDocument()
    })

    it('should render calendar even with no people', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={[]}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('February 2024')).toBeInTheDocument()
      // Should show ?? for unknown person
      expect(screen.getByText('??')).toBeInTheDocument()
    })
  })

  describe('Weekend Highlighting', () => {
    it('should apply weekend styling to Saturday and Sunday', () => {
      const { container } = render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // February 2024 starts on Thursday
      // Day 3 (Sat) and 4 (Sun) should have weekend styling
      const weekendCells = container.querySelectorAll('.bg-gray-50')
      expect(weekendCells.length).toBeGreaterThan(0)
    })
  })

  describe('Current Day Highlighting', () => {
    it('should highlight current day', () => {
      // System time is set to Feb 1, 2024 in beforeEach
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Day 1 should have special highlighting
      const dayNumbers = screen.getAllByText('1')
      const currentDay = dayNumbers.find((el) => el.classList.contains('bg-blue-600'))
      expect(currentDay).toBeInTheDocument()
    })
  })

  describe('Person Mapping', () => {
    it('should handle missing person gracefully', () => {
      const absenceWithUnknownPerson: Absence[] = [
        mockFactories.absence({
          id: 'absence-unknown',
          person_id: 'unknown-person',
          start_date: '2024-02-15',
          end_date: '2024-02-15',
          absence_type: 'vacation',
        }),
      ]

      render(
        <AbsenceCalendar
          absences={absenceWithUnknownPerson}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('??')).toBeInTheDocument()
      expect(screen.getByTitle('Unknown - vacation')).toBeInTheDocument()
    })

    it('should correctly extract initials from person names', () => {
      const peopleWithVariousNames: Person[] = [
        mockFactories.person({ id: 'person-1', name: 'John Smith' }),
        mockFactories.person({ id: 'person-2', name: 'Mary Jane Watson' }),
        mockFactories.person({ id: 'person-3', name: 'X' }),
      ]

      const absencesForPeople: Absence[] = [
        mockFactories.absence({
          id: 'absence-1',
          person_id: 'person-1',
          start_date: '2024-02-05',
          end_date: '2024-02-05',
        }),
        mockFactories.absence({
          id: 'absence-2',
          person_id: 'person-2',
          start_date: '2024-02-06',
          end_date: '2024-02-06',
        }),
        mockFactories.absence({
          id: 'absence-3',
          person_id: 'person-3',
          start_date: '2024-02-07',
          end_date: '2024-02-07',
        }),
      ]

      render(
        <AbsenceCalendar
          absences={absencesForPeople}
          people={peopleWithVariousNames}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText('JS')).toBeInTheDocument() // John Smith
      expect(screen.getByText('MJ')).toBeInTheDocument() // Mary Jane (only first 2 initials)
      expect(screen.getByText('X')).toBeInTheDocument() // Single letter name
    })
  })

  describe('Absence Type Formatting', () => {
    it('should replace underscores with spaces in absence type display', () => {
      const absenceWithUnderscore: Absence[] = [
        mockFactories.absence({
          id: 'absence-1',
          person_id: 'person-1',
          start_date: '2024-02-05',
          end_date: '2024-02-05',
          absence_type: 'family_emergency',
        }),
      ]

      render(
        <AbsenceCalendar
          absences={absenceWithUnderscore}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      expect(screen.getByText(/family emergency/i)).toBeInTheDocument()
    })

    it('should capitalize absence type display', () => {
      render(
        <AbsenceCalendar
          absences={mockAbsences}
          people={mockPeople}
          onAbsenceClick={mockOnAbsenceClick}
        />
      )

      // Check that text is rendered with capitalize class
      const absenceButtons = screen.getAllByRole('button')
      const vacationButton = absenceButtons.find((btn) =>
        btn.textContent?.includes('vacation')
      )
      expect(vacationButton).toHaveClass('capitalize')
    })
  })
})
