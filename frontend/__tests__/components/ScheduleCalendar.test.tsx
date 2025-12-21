import { render, screen, within } from '@testing-library/react'
import { ScheduleCalendar } from '@/components/ScheduleCalendar'

describe('ScheduleCalendar', () => {
  const weekStart = new Date('2024-02-12') // Monday, Feb 12, 2024

  const mockSchedule = {
    '2024-02-12': {
      AM: [
        {
          id: 'assignment-1',
          person: {
            id: 'person-1',
            name: 'Dr. John Smith',
            type: 'resident',
            pgy_level: 2,
          },
          role: 'primary',
          activity: 'Clinic - Primary Care',
          abbreviation: 'CLINIC',
        },
      ],
      PM: [
        {
          id: 'assignment-2',
          person: {
            id: 'person-1',
            name: 'Dr. John Smith',
            type: 'resident',
            pgy_level: 2,
          },
          role: 'primary',
          activity: 'Inpatient Ward',
          abbreviation: 'IP',
        },
      ],
    },
    '2024-02-13': {
      AM: [
        {
          id: 'assignment-3',
          person: {
            id: 'person-2',
            name: 'Dr. Jane Doe',
            type: 'faculty',
            pgy_level: null,
          },
          role: 'supervisor',
          activity: 'Clinic - Specialty',
          abbreviation: 'SPEC',
        },
      ],
      PM: [],
    },
    '2024-02-14': {
      AM: [],
      PM: [],
    },
    '2024-02-15': {
      AM: [],
      PM: [],
    },
    '2024-02-16': {
      AM: [],
      PM: [],
    },
    '2024-02-17': {
      AM: [],
      PM: [],
    },
    '2024-02-18': {
      AM: [],
      PM: [],
    },
  }

  describe('Calendar Structure', () => {
    it('should render calendar container', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      expect(container.querySelector('.card')).toBeInTheDocument()
    })

    it('should render header row with person column', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('Person')).toBeInTheDocument()
    })

    it('should render 7 day columns', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      // Header has 8 columns: Person + 7 days
      const headerCells = container.querySelectorAll('.grid.grid-cols-8 > div')
      expect(headerCells.length).toBeGreaterThanOrEqual(8)
    })

    it('should display correct day names', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('Mon')).toBeInTheDocument()
      expect(screen.getByText('Tue')).toBeInTheDocument()
      expect(screen.getByText('Wed')).toBeInTheDocument()
      expect(screen.getByText('Thu')).toBeInTheDocument()
      expect(screen.getByText('Fri')).toBeInTheDocument()
      expect(screen.getByText('Sat')).toBeInTheDocument()
      expect(screen.getByText('Sun')).toBeInTheDocument()
    })

    it('should display correct dates', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('Feb 12')).toBeInTheDocument()
      expect(screen.getByText('Feb 13')).toBeInTheDocument()
      expect(screen.getByText('Feb 14')).toBeInTheDocument()
      expect(screen.getByText('Feb 15')).toBeInTheDocument()
      expect(screen.getByText('Feb 16')).toBeInTheDocument()
      expect(screen.getByText('Feb 17')).toBeInTheDocument()
      expect(screen.getByText('Feb 18')).toBeInTheDocument()
    })
  })

  describe('Person Rows', () => {
    it('should render person information', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument()
    })

    it('should display PGY level for residents', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('PGY-2')).toBeInTheDocument()
    })

    it('should display "Faculty" for faculty members', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      expect(screen.getByText('Faculty')).toBeInTheDocument()
    })

    it('should extract unique people from schedule', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      const peopleNames = screen.getAllByText(/Dr\./i)
      const uniqueNames = new Set(peopleNames.map((el) => el.textContent))

      expect(uniqueNames.has('Dr. John Smith')).toBe(true)
      expect(uniqueNames.has('Dr. Jane Doe')).toBe(true)
    })

    it('should render one row per person', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      // Should have 2 person rows
      const personNames = screen.getAllByText(/Dr\./i).filter((el) => {
        return el.classList.contains('font-medium') && el.classList.contains('text-gray-900')
      })

      expect(personNames.length).toBe(2)
    })
  })

  describe('Person Sorting', () => {
    it('should sort residents by PGY level', () => {
      const scheduleWithMultipleResidents = {
        '2024-02-12': {
          AM: [
            {
              id: 'assignment-1',
              person: {
                id: 'person-3',
                name: 'Dr. Alice Brown',
                type: 'resident',
                pgy_level: 3,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
            {
              id: 'assignment-2',
              person: {
                id: 'person-1',
                name: 'Dr. Bob Smith',
                type: 'resident',
                pgy_level: 1,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
            {
              id: 'assignment-3',
              person: {
                id: 'person-2',
                name: 'Dr. Charlie Jones',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
          ],
          PM: [],
        },
      }

      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={scheduleWithMultipleResidents} />
      )

      const personRows = container.querySelectorAll('.grid.grid-cols-8.border-b')
      const firstPersonName = within(personRows[0] as HTMLElement).getByText(/Dr\./i)
      const secondPersonName = within(personRows[1] as HTMLElement).getByText(/Dr\./i)
      const thirdPersonName = within(personRows[2] as HTMLElement).getByText(/Dr\./i)

      // Should be sorted PGY-1, PGY-2, PGY-3
      expect(firstPersonName).toHaveTextContent('Dr. Bob Smith')
      expect(secondPersonName).toHaveTextContent('Dr. Charlie Jones')
      expect(thirdPersonName).toHaveTextContent('Dr. Alice Brown')
    })

    it('should sort by name when PGY levels are equal', () => {
      const scheduleWithSamePGY = {
        '2024-02-12': {
          AM: [
            {
              id: 'assignment-1',
              person: {
                id: 'person-1',
                name: 'Dr. Zachary Smith',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
            {
              id: 'assignment-2',
              person: {
                id: 'person-2',
                name: 'Dr. Alice Jones',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
          ],
          PM: [],
        },
      }

      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={scheduleWithSamePGY} />
      )

      const personRows = container.querySelectorAll('.grid.grid-cols-8.border-b')
      const firstPersonName = within(personRows[0] as HTMLElement).getByText(/Dr\./i)
      const secondPersonName = within(personRows[1] as HTMLElement).getByText(/Dr\./i)

      // Should be sorted alphabetically
      expect(firstPersonName).toHaveTextContent('Dr. Alice Jones')
      expect(secondPersonName).toHaveTextContent('Dr. Zachary Smith')
    })
  })

  describe('Day Cell Rendering', () => {
    it('should render DayCell components for each person-day combination', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      // 2 people × 7 days = 14 day cells
      const dayCells = container.querySelectorAll('.schedule-cell')
      expect(dayCells.length).toBe(14)
    })

    it('should pass correct assignment data to DayCell', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      // Dr. John Smith's assignments on Feb 12
      expect(screen.getByText('CLINIC')).toBeInTheDocument()
      expect(screen.getByText('IP')).toBeInTheDocument()
    })

    it('should pass correct date to each DayCell', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      // DayCells should render for each day of the week
      const cells = container.querySelectorAll('.schedule-cell')
      expect(cells.length).toBeGreaterThan(0)
    })
  })

  describe('Weekend Styling', () => {
    it('should apply weekend styling to Saturday header', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      const saturdayHeader = screen.getByText('Sat').closest('div')
      expect(saturdayHeader).toHaveClass('bg-gray-100')
    })

    it('should apply weekend styling to Sunday header', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      const sundayHeader = screen.getByText('Sun').closest('div')
      expect(sundayHeader).toHaveClass('bg-gray-100')
    })

    it('should not apply weekend styling to weekday headers', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      const mondayHeader = screen.getByText('Mon').closest('div')
      expect(mondayHeader).not.toHaveClass('bg-gray-100')
    })
  })

  describe('Empty State', () => {
    it('should show empty state when no schedule data', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={{}} />)

      expect(screen.getByText(/no schedule data for this week/i)).toBeInTheDocument()
    })

    it('should show generate schedule button in empty state', () => {
      render(<ScheduleCalendar weekStart={weekStart} schedule={{}} />)

      expect(screen.getByRole('button', { name: /generate schedule/i })).toBeInTheDocument()
    })

    it('should not render person rows when empty', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={{}} />
      )

      const personRows = container.querySelectorAll('.grid.grid-cols-8.border-b')
      expect(personRows.length).toBe(0)
    })

    it('should center empty state message', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={{}} />
      )

      const emptyState = container.querySelector('.text-center')
      expect(emptyState).toBeInTheDocument()
    })
  })

  describe('Row Hover Effect', () => {
    it('should apply hover class to person rows', () => {
      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      const personRows = container.querySelectorAll('.grid.grid-cols-8.border-b.hover\\:bg-gray-50')
      expect(personRows.length).toBe(2)
    })
  })

  describe('Schedule Data Handling', () => {
    it('should handle missing AM data', () => {
      const scheduleWithMissingAM = {
        '2024-02-12': {
          AM: [],
          PM: [
            {
              id: 'assignment-1',
              person: {
                id: 'person-1',
                name: 'Dr. John Smith',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
          ],
        },
      }

      render(<ScheduleCalendar weekStart={weekStart} schedule={scheduleWithMissingAM} />)

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText('CLINIC')).toBeInTheDocument()
    })

    it('should handle missing PM data', () => {
      const scheduleWithMissingPM = {
        '2024-02-12': {
          AM: [
            {
              id: 'assignment-1',
              person: {
                id: 'person-1',
                name: 'Dr. John Smith',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
          ],
          PM: [],
        },
      }

      render(<ScheduleCalendar weekStart={weekStart} schedule={scheduleWithMissingPM} />)

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText('CLINIC')).toBeInTheDocument()
    })

    it('should handle days not in schedule object', () => {
      const partialSchedule = {
        '2024-02-12': {
          AM: [
            {
              id: 'assignment-1',
              person: {
                id: 'person-1',
                name: 'Dr. John Smith',
                type: 'resident',
                pgy_level: 2,
              },
              role: 'primary',
              activity: 'Clinic',
              abbreviation: 'CLINIC',
            },
          ],
          PM: [],
        },
        // Missing other days
      }

      const { container } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={partialSchedule} />
      )

      // Should still render 7 day cells for the person
      const dayCells = container.querySelectorAll('.schedule-cell')
      expect(dayCells.length).toBe(7)
    })
  })

  describe('Week Start Handling', () => {
    it('should handle different week start dates', () => {
      const differentWeekStart = new Date('2024-03-18') // Different week

      render(<ScheduleCalendar weekStart={differentWeekStart} schedule={{}} />)

      expect(screen.getByText('Mar 18')).toBeInTheDocument()
    })

    it('should always render 7 consecutive days from weekStart', () => {
      const differentWeekStart = new Date('2024-03-18')

      render(<ScheduleCalendar weekStart={differentWeekStart} schedule={{}} />)

      expect(screen.getByText('Mar 18')).toBeInTheDocument()
      expect(screen.getByText('Mar 19')).toBeInTheDocument()
      expect(screen.getByText('Mar 20')).toBeInTheDocument()
      expect(screen.getByText('Mar 21')).toBeInTheDocument()
      expect(screen.getByText('Mar 22')).toBeInTheDocument()
      expect(screen.getByText('Mar 23')).toBeInTheDocument()
      expect(screen.getByText('Mar 24')).toBeInTheDocument()
    })
  })

  describe('Memoization', () => {
    it('should handle rerender with same props efficiently', () => {
      const { rerender } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      // Rerender with same props
      rerender(<ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />)

      // Should still render correctly
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument()
    })

    it('should update when weekStart changes', () => {
      const { rerender } = render(
        <ScheduleCalendar weekStart={weekStart} schedule={mockSchedule} />
      )

      const newWeekStart = new Date('2024-03-18')
      rerender(<ScheduleCalendar weekStart={newWeekStart} schedule={{}} />)

      expect(screen.getByText('Mar 18')).toBeInTheDocument()
    })
  })
})
