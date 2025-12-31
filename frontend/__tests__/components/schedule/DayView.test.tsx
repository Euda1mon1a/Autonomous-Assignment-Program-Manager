import { render, screen, fireEvent } from '@/test-utils'
import { DayView } from '@/components/schedule/DayView'
import { format } from 'date-fns'

describe('DayView', () => {
  const mockCurrentDate = new Date('2024-01-15T12:00:00')
  const mockOnDateChange = jest.fn()
  const mockOnCellClick = jest.fn()

  const mockPerson1 = {
    id: 'p1',
    name: 'Dr. Smith',
    type: 'resident',
    pgy_level: 1,
  }

  const mockPerson2 = {
    id: 'p2',
    name: 'Dr. Johnson',
    type: 'resident',
    pgy_level: 3,
  }

  const mockPerson3 = {
    id: 'p3',
    name: 'Dr. Williams',
    type: 'faculty',
    pgy_level: null,
  }

  const mockSchedule = {
    '2024-01-15': {
      AM: [
        {
          id: 'a1',
          person: mockPerson1,
          role: 'primary',
          activity: 'clinic',
          abbreviation: 'CL',
        },
        {
          id: 'a2',
          person: mockPerson2,
          role: 'primary',
          activity: 'inpatient',
          abbreviation: 'IM',
        },
      ],
      PM: [
        {
          id: 'a3',
          person: mockPerson1,
          role: 'primary',
          activity: 'procedure',
          abbreviation: 'PR',
        },
      ],
    },
  }

  const mockHolidays = {
    '2024-01-15': 'Martin Luther King Jr. Day',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Header and Navigation', () => {
    it('should render the current date', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getByText(/Monday, January 15, 2024/)).toBeInTheDocument()
    })

    it('should show "Today" badge when current date is today', () => {
      const today = new Date()
      render(
        <DayView currentDate={today} schedule={{}} onDateChange={mockOnDateChange} />
      )

      // "Today" appears twice: as a button and as a badge when isToday is true
      const todayElements = screen.getAllByText('Today')
      expect(todayElements.length).toBeGreaterThanOrEqual(2) // button + badge
    })

    it('should show "Weekend" badge for Saturday', () => {
      const saturday = new Date('2024-01-13T12:00:00') // Saturday
      render(
        <DayView currentDate={saturday} schedule={{}} onDateChange={mockOnDateChange} />
      )

      expect(screen.getByText('Weekend')).toBeInTheDocument()
    })

    it('should show "Weekend" badge for Sunday', () => {
      const sunday = new Date('2024-01-14T12:00:00') // Sunday
      render(
        <DayView currentDate={sunday} schedule={{}} onDateChange={mockOnDateChange} />
      )

      expect(screen.getByText('Weekend')).toBeInTheDocument()
    })

    it('should show holiday badge when holiday is provided', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          holidays={mockHolidays}
        />
      )

      expect(screen.getByText('Martin Luther King Jr. Day')).toBeInTheDocument()
    })

    it('should call onDateChange with previous day when prev button clicked', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      const prevButton = screen.getByTitle('Previous day')
      fireEvent.click(prevButton)

      expect(mockOnDateChange).toHaveBeenCalledWith(new Date('2024-01-14T12:00:00'))
    })

    it('should call onDateChange with next day when next button clicked', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      const nextButton = screen.getByTitle('Next day')
      fireEvent.click(nextButton)

      expect(mockOnDateChange).toHaveBeenCalledWith(new Date('2024-01-16T12:00:00'))
    })

    it('should call onDateChange with today when Today button clicked', () => {
      const pastDate = new Date('2024-01-01T12:00:00')
      render(
        <DayView currentDate={pastDate} schedule={{}} onDateChange={mockOnDateChange} />
      )

      const todayButton = screen.getByText('Today')
      fireEvent.click(todayButton)

      expect(mockOnDateChange).toHaveBeenCalled()
      const calledDate = mockOnDateChange.mock.calls[0][0]
      expect(format(calledDate, 'yyyy-MM-dd')).toBe(format(new Date(), 'yyyy-MM-dd'))
    })
  })

  describe('Date Picker', () => {
    it('should toggle date picker when calendar button clicked', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      const calendarButton = screen.getByTitle('Jump to date')
      fireEvent.click(calendarButton)

      expect(screen.getByDisplayValue('2024-01-15')).toBeInTheDocument()
    })

    it('should call onDateChange when date input changes', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      const calendarButton = screen.getByTitle('Jump to date')
      fireEvent.click(calendarButton)

      const dateInput = screen.getByDisplayValue('2024-01-15') as HTMLInputElement
      fireEvent.change(dateInput, { target: { value: '2024-02-20' } })

      expect(mockOnDateChange).toHaveBeenCalled()
    })
  })

  describe('AM/PM Sections', () => {
    it('should render AM section header', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getByText('Morning (AM)')).toBeInTheDocument()
    })

    it('should render PM section header', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getByText('Afternoon (PM)')).toBeInTheDocument()
    })
  })

  describe('Person Rendering', () => {
    it('should render all people with assignments', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getAllByText('Dr. Smith')).toHaveLength(2) // AM and PM sections
      expect(screen.getAllByText('Dr. Johnson')).toHaveLength(2)
    })

    it('should show PGY level for residents', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getAllByText('PGY-1')).toHaveLength(2)
      expect(screen.getAllByText('PGY-3')).toHaveLength(2)
    })

    it('should show "Faculty" for faculty members', () => {
      const scheduleWithFaculty = {
        '2024-01-15': {
          AM: [
            {
              id: 'a4',
              person: mockPerson3,
              role: 'primary',
              activity: 'clinic',
              abbreviation: 'CL',
            },
          ],
          PM: [],
        },
      }

      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={scheduleWithFaculty}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getAllByText('Faculty')).toHaveLength(2)
    })

    it('should sort people by PGY level then name', () => {
      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      const amSection = container.querySelector('div')
      const names = screen.getAllByText(/Dr\. (Smith|Johnson)/)

      // PGY-1 (Smith) should come before PGY-3 (Johnson)
      const smithIndex = names.findIndex(el => el.textContent === 'Dr. Smith')
      const johnsonIndex = names.findIndex(el => el.textContent === 'Dr. Johnson')
      expect(smithIndex).toBeLessThan(johnsonIndex)
    })
  })

  describe('Assignment Display', () => {
    it('should render assignment activities', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getByText('clinic')).toBeInTheDocument()
      expect(screen.getByText('inpatient')).toBeInTheDocument()
      expect(screen.getByText('procedure')).toBeInTheDocument()
    })

    it('should render assignment abbreviations and roles', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getAllByText(/CL.*primary/)).toHaveLength(1)
      expect(screen.getAllByText(/IM.*primary/)).toHaveLength(1)
    })

    it('should apply color coding based on activity type', () => {
      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      // Get the assignment cells (need to go 2 levels up from activity text)
      // Activity text is in inner div, color class is on parent wrapper
      const clinicCell = screen.getByText('clinic').closest('div')?.parentElement
      expect(clinicCell?.className).toMatch(/bg-blue/)

      const inpatientCell = screen.getByText('inpatient').closest('div')?.parentElement
      expect(inpatientCell?.className).toMatch(/bg-purple/)

      const procedureCell = screen.getByText('procedure').closest('div')?.parentElement
      expect(procedureCell?.className).toMatch(/bg-red/)
    })

    it('should show "No assignment" for empty slots', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
        />
      )

      // Dr. Johnson has no PM assignment in mock data
      const noAssignmentCells = screen.getAllByText('No assignment')
      expect(noAssignmentCells.length).toBeGreaterThan(0)
    })
  })

  describe('Cell Click Interactions', () => {
    it('should call onCellClick when assignment cell is clicked', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          onCellClick={mockOnCellClick}
        />
      )

      const clinicCell = screen.getByText('clinic').closest('div')
      if (clinicCell) {
        fireEvent.click(clinicCell)
      }

      expect(mockOnCellClick).toHaveBeenCalledWith(
        'p1',
        mockCurrentDate,
        'AM',
        expect.objectContaining({
          activity: 'clinic',
        })
      )
    })

    it('should call onCellClick for empty cells', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          onCellClick={mockOnCellClick}
        />
      )

      const noAssignmentCell = screen.getAllByText('No assignment')[0].closest('div')
      if (noAssignmentCell) {
        fireEvent.click(noAssignmentCell)
      }

      expect(mockOnCellClick).toHaveBeenCalled()
    })
  })

  describe('Person Filter', () => {
    it('should filter to show only selected people', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          personFilter={['p1']}
        />
      )

      expect(screen.getAllByText('Dr. Smith')).toHaveLength(2)
      expect(screen.queryByText('Dr. Johnson')).not.toBeInTheDocument()
    })

    it('should show all people when filter is empty', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          personFilter={[]}
        />
      )

      expect(screen.getAllByText('Dr. Smith')).toHaveLength(2)
      expect(screen.getAllByText('Dr. Johnson')).toHaveLength(2)
    })

    it('should show multiple filtered people', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          personFilter={['p1', 'p2']}
        />
      )

      expect(screen.getAllByText('Dr. Smith')).toHaveLength(2)
      expect(screen.getAllByText('Dr. Johnson')).toHaveLength(2)
    })
  })

  describe('Empty Schedule', () => {
    it('should show "No assignments" message when schedule is empty', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={{}}
          onDateChange={mockOnDateChange}
        />
      )

      expect(screen.getAllByText('No assignments for this day')).toHaveLength(2)
    })

    it('should show empty message in both AM and PM sections', () => {
      render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={{}}
          onDateChange={mockOnDateChange}
        />
      )

      const emptyMessages = screen.getAllByText('No assignments for this day')
      expect(emptyMessages).toHaveLength(2)
    })
  })

  describe('Hover Effects', () => {
    it('should apply hover effects to assignment cells', () => {
      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          onCellClick={mockOnCellClick}
        />
      )

      const assignmentCells = container.querySelectorAll('[class*="cursor-pointer"]')
      expect(assignmentCells.length).toBeGreaterThan(0)
    })

    it('should apply hover effects to empty cells', () => {
      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={mockSchedule}
          onDateChange={mockOnDateChange}
          onCellClick={mockOnCellClick}
        />
      )

      const emptyCell = screen.getAllByText('No assignment')[0].closest('div')
      expect(emptyCell).toHaveClass('cursor-pointer')
      expect(emptyCell).toHaveClass('hover:bg-gray-100')
    })
  })

  describe('Activity Color Mapping', () => {
    it('should handle case-insensitive activity types', () => {
      const scheduleWithUppercase = {
        '2024-01-15': {
          AM: [
            {
              id: 'a1',
              person: mockPerson1,
              role: 'primary',
              activity: 'CLINIC',
              abbreviation: 'CL',
            },
          ],
          PM: [],
        },
      }

      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={scheduleWithUppercase}
          onDateChange={mockOnDateChange}
        />
      )

      // Need to go to parent element to find color class
      const clinicCell = screen.getByText('CLINIC').closest('div')?.parentElement
      expect(clinicCell?.className).toMatch(/bg-blue/)
    })

    it('should apply default color for unknown activity types', () => {
      const scheduleWithUnknown = {
        '2024-01-15': {
          AM: [
            {
              id: 'a1',
              person: mockPerson1,
              role: 'primary',
              activity: 'unknown-activity',
              abbreviation: 'XX',
            },
          ],
          PM: [],
        },
      }

      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={scheduleWithUnknown}
          onDateChange={mockOnDateChange}
        />
      )

      // Need to go to parent element to find color class
      const unknownCell = screen.getByText('unknown-activity').closest('div')?.parentElement
      expect(unknownCell?.className).toMatch(/bg-slate/)
    })

    it('should handle partial activity type matches', () => {
      const scheduleWithPartial = {
        '2024-01-15': {
          AM: [
            {
              id: 'a1',
              person: mockPerson1,
              role: 'primary',
              activity: 'on-call duty',
              abbreviation: 'CA',
            },
          ],
          PM: [],
        },
      }

      const { container } = render(
        <DayView
          currentDate={mockCurrentDate}
          schedule={scheduleWithPartial}
          onDateChange={mockOnDateChange}
        />
      )

      // Need to go to parent element to find color class
      const callCell = screen.getByText('on-call duty').closest('div')?.parentElement
      expect(callCell?.className).toMatch(/bg-orange/)
    })
  })
})
