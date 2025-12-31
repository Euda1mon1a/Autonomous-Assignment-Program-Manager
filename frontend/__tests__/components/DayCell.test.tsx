import { render, screen } from '@/test-utils'
import { DayCell } from '@/components/DayCell'

// Helper to create a local date (avoiding timezone issues)
function localDate(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day) // month is 0-indexed
}

describe('DayCell', () => {
  const mockDate = localDate(2024, 2, 15) // Thursday

  const mockAmAssignment = {
    id: 'assignment-1',
    activity: 'Clinic - Orthopedics',
    abbreviation: 'ORTHO',
    role: 'primary',
  }

  const mockPmAssignment = {
    id: 'assignment-2',
    activity: 'Inpatient Ward',
    abbreviation: 'IP',
    role: 'primary',
  }

  describe('Empty Cell Rendering', () => {
    it('should render empty cell when no assignments', () => {
      const { container } = render(<DayCell date={mockDate} />)

      expect(container.querySelector('.schedule-cell')).toBeInTheDocument()
      expect(screen.getByText('-')).toBeInTheDocument()
    })

    it('should apply white background for weekday with no assignments', () => {
      const { container } = render(<DayCell date={mockDate} />)

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveClass('bg-white')
    })

    it('should apply gray background for weekend with no assignments', () => {
      const saturdayDate = localDate(2024, 2, 17) // Saturday
      const { container } = render(<DayCell date={saturdayDate} />)

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveClass('bg-gray-50')
    })

    it('should apply gray background for Sunday', () => {
      const sundayDate = localDate(2024, 2, 18) // Sunday
      const { container } = render(<DayCell date={sundayDate} />)

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveClass('bg-gray-50')
    })

    it('should center empty state text', () => {
      const { container } = render(<DayCell date={mockDate} />)

      const emptyText = container.querySelector('.text-center')
      expect(emptyText).toBeInTheDocument()
      expect(emptyText).toHaveTextContent('-')
    })

    it('should apply gray color to empty state text', () => {
      const { container } = render(<DayCell date={mockDate} />)

      const emptyText = container.querySelector('.text-gray-300')
      expect(emptyText).toBeInTheDocument()
    })
  })

  describe('AM/PM Split Display', () => {
    it('should display AM assignment', () => {
      render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      expect(screen.getByText('ORTHO')).toBeInTheDocument()
      expect(screen.getByText('AM')).toBeInTheDocument()
    })

    it('should display PM assignment', () => {
      render(<DayCell date={mockDate} pmAssignment={mockPmAssignment} />)

      expect(screen.getByText('IP')).toBeInTheDocument()
      expect(screen.getByText('PM')).toBeInTheDocument()
    })

    it('should display both AM and PM assignments when different', () => {
      render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={mockPmAssignment}
        />
      )

      expect(screen.getByText('ORTHO')).toBeInTheDocument()
      expect(screen.getByText('IP')).toBeInTheDocument()
      expect(screen.getByText('AM')).toBeInTheDocument()
      expect(screen.getByText('PM')).toBeInTheDocument()
    })

    it('should display dash for AM when only PM assignment', () => {
      render(<DayCell date={mockDate} pmAssignment={mockPmAssignment} />)

      const dashes = screen.getAllByText('-')
      expect(dashes.length).toBe(1) // One dash for missing AM
    })

    it('should display dash for PM when only AM assignment', () => {
      render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const dashes = screen.getAllByText('-')
      expect(dashes.length).toBe(1) // One dash for missing PM
    })
  })

  describe('All-Day Display', () => {
    it('should display as all-day when AM and PM are same activity', () => {
      const sameAssignment = { ...mockAmAssignment }

      render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={sameAssignment}
        />
      )

      expect(screen.getByText('All day')).toBeInTheDocument()
      expect(screen.queryByText('AM')).not.toBeInTheDocument()
      expect(screen.queryByText('PM')).not.toBeInTheDocument()
    })

    it('should show abbreviation once for all-day assignment', () => {
      const sameAssignment = { ...mockAmAssignment }

      render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={sameAssignment}
        />
      )

      const abbreviations = screen.getAllByText('ORTHO')
      expect(abbreviations).toHaveLength(1)
    })

    it('should center all-day content', () => {
      const sameAssignment = { ...mockAmAssignment }

      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={sameAssignment}
        />
      )

      const centerContainer = container.querySelector('.text-center')
      expect(centerContainer).toBeInTheDocument()
    })

    it('should apply activity color to all-day cell', () => {
      const sameAssignment = { ...mockAmAssignment }

      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={sameAssignment}
        />
      )

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveClass('bg-clinic-light')
    })

    it('should have title attribute for all-day assignment', () => {
      const sameAssignment = { ...mockAmAssignment }

      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={sameAssignment}
        />
      )

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveAttribute('title', 'Clinic - Orthopedics')
    })
  })

  describe('Activity Colors', () => {
    it('should apply clinic colors for clinic activity', () => {
      const clinicAssignment = {
        ...mockAmAssignment,
        activity: 'Clinic - Primary Care',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={clinicAssignment} />)

      const amBlock = container.querySelector('.bg-clinic-light')
      expect(amBlock).toBeInTheDocument()
      expect(amBlock).toHaveClass('text-clinic-dark')
    })

    it('should apply inpatient colors for inpatient activity', () => {
      const inpatientAssignment = {
        ...mockAmAssignment,
        activity: 'Inpatient Medicine',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={inpatientAssignment} />)

      const amBlock = container.querySelector('.bg-inpatient-light')
      expect(amBlock).toBeInTheDocument()
      expect(amBlock).toHaveClass('text-inpatient-dark')
    })

    it('should apply call colors for call activity', () => {
      const callAssignment = {
        ...mockAmAssignment,
        activity: 'Call - Night Shift',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={callAssignment} />)

      const amBlock = container.querySelector('.bg-call-light')
      expect(amBlock).toBeInTheDocument()
      expect(amBlock).toHaveClass('text-call-dark')
    })

    it('should apply leave colors for leave activity', () => {
      const leaveAssignment = {
        ...mockAmAssignment,
        activity: 'Leave - Vacation',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={leaveAssignment} />)

      const amBlock = container.querySelector('.bg-leave-light')
      expect(amBlock).toBeInTheDocument()
      expect(amBlock).toHaveClass('text-leave-dark')
    })

    it('should apply conference colors for conference activity', () => {
      const conferenceAssignment = {
        ...mockAmAssignment,
        activity: 'Conference - Grand Rounds',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={conferenceAssignment} />)

      const conferenceBlock = container.querySelector('.bg-gray-100')
      expect(conferenceBlock).toBeInTheDocument()
      expect(conferenceBlock).toHaveClass('text-gray-700')
    })

    it('should apply default colors for unknown activity', () => {
      const unknownAssignment = {
        ...mockAmAssignment,
        activity: 'Unknown Activity',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={unknownAssignment} />)

      const amBlock = container.querySelector('.bg-blue-50')
      expect(amBlock).toBeInTheDocument()
      expect(amBlock).toHaveClass('text-blue-700')
    })

    it('should handle case-insensitive activity matching', () => {
      const uppercaseAssignment = {
        ...mockAmAssignment,
        activity: 'CLINIC - ORTHOPEDICS',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={uppercaseAssignment} />)

      const amBlock = container.querySelector('.bg-clinic-light')
      expect(amBlock).toBeInTheDocument()
    })
  })

  describe('Title Attributes', () => {
    it('should have title attribute for AM assignment', () => {
      const { container } = render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const amBlock = container.querySelectorAll('[title]')[0]
      expect(amBlock).toHaveAttribute('title', 'Clinic - Orthopedics')
    })

    it('should have title attribute for PM assignment', () => {
      const { container } = render(<DayCell date={mockDate} pmAssignment={mockPmAssignment} />)

      const pmBlock = container.querySelectorAll('[title]')[0]
      expect(pmBlock).toHaveAttribute('title', 'Inpatient Ward')
    })

    it('should have separate title attributes for different AM/PM assignments', () => {
      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={mockPmAssignment}
        />
      )

      const blocks = container.querySelectorAll('[title]')
      expect(blocks[0]).toHaveAttribute('title', 'Clinic - Orthopedics')
      expect(blocks[1]).toHaveAttribute('title', 'Inpatient Ward')
    })
  })

  describe('Assignment Formatting', () => {
    it('should display abbreviation in bold', () => {
      render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const abbreviation = screen.getByText('ORTHO')
      expect(abbreviation).toHaveClass('font-medium')
    })

    it('should display time indicator with reduced opacity', () => {
      const { container } = render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const timeIndicator = screen.getByText('AM')
      // The opacity class is on the span itself containing 'AM'
      expect(timeIndicator).toHaveClass('opacity-75')
    })

    it('should apply spacing between AM and PM blocks', () => {
      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={mockPmAssignment}
        />
      )

      const amBlock = container.querySelectorAll('.rounded')[0]
      expect(amBlock).toHaveClass('mb-1')
    })

    it('should apply padding to assignment blocks', () => {
      const { container } = render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const amBlock = container.querySelector('.rounded')
      expect(amBlock).toHaveClass('px-1')
      expect(amBlock).toHaveClass('py-0.5')
    })
  })

  describe('Weekend Behavior', () => {
    it('should maintain assignment display on weekends', () => {
      const saturdayDate = localDate(2024, 2, 17) // Saturday

      render(<DayCell date={saturdayDate} amAssignment={mockAmAssignment} />)

      expect(screen.getByText('ORTHO')).toBeInTheDocument()
      expect(screen.getByText('AM')).toBeInTheDocument()
    })

    it('should apply gray background for weekend with split assignments', () => {
      const saturdayDate = localDate(2024, 2, 17) // Saturday

      const { container } = render(
        <DayCell
          date={saturdayDate}
          amAssignment={mockAmAssignment}
          pmAssignment={mockPmAssignment}
        />
      )

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toHaveClass('bg-gray-50')
    })
  })

  describe('Edge Cases', () => {
    it('should handle assignment with empty abbreviation', () => {
      const noAbbreviation = {
        ...mockAmAssignment,
        abbreviation: '',
      }

      render(<DayCell date={mockDate} amAssignment={noAbbreviation} />)

      expect(screen.getByText('AM')).toBeInTheDocument()
    })

    it('should handle assignment with long activity name', () => {
      const longActivity = {
        ...mockAmAssignment,
        activity: 'Very Long Activity Name That Should Be Displayed In Title',
      }

      const { container } = render(<DayCell date={mockDate} amAssignment={longActivity} />)

      const block = container.querySelector('[title]')
      expect(block).toHaveAttribute(
        'title',
        'Very Long Activity Name That Should Be Displayed In Title'
      )
    })

    it('should handle same ID but different activities as different', () => {
      const differentPmAssignment = {
        id: 'assignment-1', // Same ID as AM
        activity: 'Different Activity',
        abbreviation: 'DIFF',
        role: 'primary',
      }

      render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={differentPmAssignment}
        />
      )

      // Should display as split, not all-day
      expect(screen.getByText('AM')).toBeInTheDocument()
      expect(screen.getByText('PM')).toBeInTheDocument()
      expect(screen.queryByText('All day')).not.toBeInTheDocument()
    })
  })

  describe('Layout Structure', () => {
    it('should have schedule-cell class on main container', () => {
      const { container } = render(<DayCell date={mockDate} amAssignment={mockAmAssignment} />)

      const cell = container.querySelector('.schedule-cell')
      expect(cell).toBeInTheDocument()
    })

    it('should render AM block before PM block', () => {
      const { container } = render(
        <DayCell
          date={mockDate}
          amAssignment={mockAmAssignment}
          pmAssignment={mockPmAssignment}
        />
      )

      const blocks = container.querySelectorAll('.rounded')
      expect(blocks[0]).toHaveTextContent('ORTHO')
      expect(blocks[1]).toHaveTextContent('IP')
    })
  })
})
