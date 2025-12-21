import { render, screen, fireEvent } from '@testing-library/react'
import { BlockNavigation } from '@/components/schedule/BlockNavigation'
import { addDays, subDays, format } from 'date-fns'

describe('BlockNavigation', () => {
  const mockStartDate = new Date('2024-01-01T00:00:00')
  const mockEndDate = new Date('2024-01-28T00:00:00') // 28 days later (4 weeks)
  const mockOnDateRangeChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render Previous Block button', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText('Previous Block')).toBeInTheDocument()
    })

    it('should render Next Block button', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText('Next Block')).toBeInTheDocument()
    })

    it('should render Today button', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText('Today')).toBeInTheDocument()
    })

    it('should render This Block button', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText('This Block')).toBeInTheDocument()
    })

    it('should render start date input', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date') as HTMLInputElement
      expect(startInput).toBeInTheDocument()
      expect(startInput.value).toBe('2024-01-01')
    })

    it('should render end date input', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const endInput = screen.getByLabelText('End date') as HTMLInputElement
      expect(endInput).toBeInTheDocument()
      expect(endInput.value).toBe('2024-01-28')
    })

    it('should display current date range', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText(/Jan 1, 2024.*Jan 28, 2024/)).toBeInTheDocument()
    })
  })

  describe('Previous Block Navigation', () => {
    it('should call onDateRangeChange with dates 28 days earlier', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const prevButton = screen.getByLabelText('Previous block')
      fireEvent.click(prevButton)

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        subDays(mockStartDate, 28),
        subDays(mockEndDate, 28)
      )
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const prevButton = screen.getByLabelText('Previous block')
      expect(prevButton).toHaveAttribute('aria-label', 'Previous block')
    })
  })

  describe('Next Block Navigation', () => {
    it('should call onDateRangeChange with dates 28 days later', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const nextButton = screen.getByLabelText('Next block')
      fireEvent.click(nextButton)

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        addDays(mockStartDate, 28),
        addDays(mockEndDate, 28)
      )
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const nextButton = screen.getByLabelText('Next block')
      expect(nextButton).toHaveAttribute('aria-label', 'Next block')
    })
  })

  describe('Today Navigation', () => {
    it('should call onDateRangeChange with today as start', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const todayButton = screen.getByLabelText('Jump to today')
      fireEvent.click(todayButton)

      expect(mockOnDateRangeChange).toHaveBeenCalled()
      const [startDate, endDate] = mockOnDateRangeChange.mock.calls[0]

      // Should be a 28-day block starting from Monday of current week
      const daysDiff = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24))
      expect(daysDiff).toBe(27) // 28 days total (0-indexed)
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const todayButton = screen.getByLabelText('Jump to today')
      expect(todayButton).toHaveAttribute('aria-label', 'Jump to today')
    })
  })

  describe('This Block Navigation', () => {
    it('should call onDateRangeChange with current block start', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const thisBlockButton = screen.getByLabelText('Jump to this block')
      fireEvent.click(thisBlockButton)

      expect(mockOnDateRangeChange).toHaveBeenCalled()
      const [startDate, endDate] = mockOnDateRangeChange.mock.calls[0]

      // Should be a 28-day block
      const daysDiff = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24))
      expect(daysDiff).toBe(27)
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const thisBlockButton = screen.getByLabelText('Jump to this block')
      expect(thisBlockButton).toHaveAttribute('aria-label', 'Jump to this block')
    })
  })

  describe('Start Date Input', () => {
    it('should call onDateRangeChange when start date changes', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date') as HTMLInputElement
      fireEvent.change(startInput, { target: { value: '2024-02-01' } })

      expect(mockOnDateRangeChange).toHaveBeenCalled()
      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0]

      expect(format(newStart, 'yyyy-MM-dd')).toBe('2024-02-01')
      // End date should be 27 days after start (28-day block)
      expect(format(newEnd, 'yyyy-MM-dd')).toBe('2024-02-28')
    })

    it('should maintain 28-day duration when start date changes', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date') as HTMLInputElement
      fireEvent.change(startInput, { target: { value: '2024-03-10' } })

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0]
      const daysDiff = Math.floor((newEnd - newStart) / (1000 * 60 * 60 * 24))

      expect(daysDiff).toBe(27) // 28 days (0-indexed)
    })

    it('should not call onDateRangeChange with invalid date', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date') as HTMLInputElement
      fireEvent.change(startInput, { target: { value: 'invalid-date' } })

      expect(mockOnDateRangeChange).not.toHaveBeenCalled()
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date')
      expect(startInput).toHaveAttribute('aria-label', 'Start date')
    })
  })

  describe('End Date Input', () => {
    it('should call onDateRangeChange when end date changes', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const endInput = screen.getByLabelText('End date') as HTMLInputElement
      fireEvent.change(endInput, { target: { value: '2024-02-15' } })

      expect(mockOnDateRangeChange).toHaveBeenCalled()
      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0]

      expect(format(newStart, 'yyyy-MM-dd')).toBe('2024-01-01')
      expect(format(newEnd, 'yyyy-MM-dd')).toBe('2024-02-15')
    })

    it('should not call onDateRangeChange if end date is before start date', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const endInput = screen.getByLabelText('End date') as HTMLInputElement
      fireEvent.change(endInput, { target: { value: '2023-12-31' } })

      expect(mockOnDateRangeChange).not.toHaveBeenCalled()
    })

    it('should not call onDateRangeChange with invalid date', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const endInput = screen.getByLabelText('End date') as HTMLInputElement
      fireEvent.change(endInput, { target: { value: 'invalid-date' } })

      expect(mockOnDateRangeChange).not.toHaveBeenCalled()
    })

    it('should have proper aria-label', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const endInput = screen.getByLabelText('End date')
      expect(endInput).toHaveAttribute('aria-label', 'End date')
    })
  })

  describe('Button Styling', () => {
    it('should apply btn-secondary class to navigation buttons', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const prevButton = screen.getByLabelText('Previous block')
      const nextButton = screen.getByLabelText('Next block')

      expect(prevButton).toHaveClass('btn-secondary')
      expect(nextButton).toHaveClass('btn-secondary')
    })

    it('should apply btn-secondary class to quick nav buttons', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const todayButton = screen.getByLabelText('Jump to today')
      const thisBlockButton = screen.getByLabelText('Jump to this block')

      expect(todayButton).toHaveClass('btn-secondary')
      expect(thisBlockButton).toHaveClass('btn-secondary')
    })
  })

  describe('Date Format Display', () => {
    it('should format dates correctly in display text', () => {
      const start = new Date('2024-03-15T00:00:00')
      const end = new Date('2024-04-11T00:00:00')

      render(
        <BlockNavigation
          startDate={start}
          endDate={end}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      expect(screen.getByText(/Mar 15, 2024.*Apr 11, 2024/)).toBeInTheDocument()
    })
  })

  describe('Responsive Behavior', () => {
    it('should hide date range display on small screens', () => {
      const { container } = render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const dateRangeDisplay = screen.getByText(/Jan 1, 2024.*Jan 28, 2024/)
      expect(dateRangeDisplay.parentElement).toHaveClass('hidden')
      expect(dateRangeDisplay.parentElement).toHaveClass('lg:block')
    })
  })

  describe('Input Types', () => {
    it('should use date input type for date pickers', () => {
      render(
        <BlockNavigation
          startDate={mockStartDate}
          endDate={mockEndDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      )

      const startInput = screen.getByLabelText('Start date') as HTMLInputElement
      const endInput = screen.getByLabelText('End date') as HTMLInputElement

      expect(startInput.type).toBe('date')
      expect(endInput.type).toBe('date')
    })
  })
})
