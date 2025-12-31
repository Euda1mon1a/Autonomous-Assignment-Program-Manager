import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BlockNavigation } from '../BlockNavigation';
import { addDays, subDays } from 'date-fns';

describe('BlockNavigation', () => {
  const defaultStartDate = new Date('2024-01-01'); // Monday
  const defaultEndDate = addDays(defaultStartDate, 27); // 4-week block
  const mockOnDateRangeChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-15')); // Mid-block date
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const defaultProps = {
    startDate: defaultStartDate,
    endDate: defaultEndDate,
    onDateRangeChange: mockOnDateRangeChange,
  };

  describe('rendering', () => {
    it('renders all navigation buttons', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByLabelText('Previous block')).toBeInTheDocument();
      expect(screen.getByLabelText('Next block')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to today')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to this block')).toBeInTheDocument();
    });

    it('displays current date range', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByText(/Jan 1 - Jan 28, 2024/)).toBeInTheDocument();
    });

    it('displays block label', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByText('Block:')).toBeInTheDocument();
    });

    it('displays full range in desktop view', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByText('Jan 1, 2024 - Jan 28, 2024')).toBeInTheDocument();
    });
  });

  describe('previous block navigation', () => {
    it('navigates to previous 4-week block', () => {
      render(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      fireEvent.click(previousButton);

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        subDays(defaultStartDate, 28),
        subDays(defaultEndDate, 28)
      );
    });

    it('maintains 4-week block size', () => {
      render(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      fireEvent.click(previousButton);

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27); // 28 days = 0-27 days apart
    });
  });

  describe('next block navigation', () => {
    it('navigates to next 4-week block', () => {
      render(<BlockNavigation {...defaultProps} />);

      const nextButton = screen.getByLabelText('Next block');
      fireEvent.click(nextButton);

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        addDays(defaultStartDate, 28),
        addDays(defaultEndDate, 28)
      );
    });

    it('maintains 4-week block size', () => {
      render(<BlockNavigation {...defaultProps} />);

      const nextButton = screen.getByLabelText('Next block');
      fireEvent.click(nextButton);

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27);
    });
  });

  describe('today navigation', () => {
    it('jumps to block containing today', () => {
      render(<BlockNavigation {...defaultProps} />);

      const todayButton = screen.getByLabelText('Jump to today');
      fireEvent.click(todayButton);

      expect(mockOnDateRangeChange).toHaveBeenCalled();

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];

      // Should be a 4-week block starting on Monday
      expect(newStart.getDay()).toBe(1); // Monday

      // Should be 28 days
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27);
    });

    it('centers on the Monday of current week', () => {
      jest.setSystemTime(new Date('2024-01-17')); // Wednesday

      render(<BlockNavigation {...defaultProps} />);

      const todayButton = screen.getByLabelText('Jump to today');
      fireEvent.click(todayButton);

      const [newStart] = mockOnDateRangeChange.mock.calls[0];

      // Should start on Monday Jan 15, 2024
      expect(newStart.getDate()).toBe(15);
      expect(newStart.getDay()).toBe(1); // Monday
    });
  });

  describe('this block navigation', () => {
    it('jumps to current 4-week block', () => {
      render(<BlockNavigation {...defaultProps} />);

      const thisBlockButton = screen.getByLabelText('Jump to this block');
      fireEvent.click(thisBlockButton);

      expect(mockOnDateRangeChange).toHaveBeenCalled();

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];

      // Should be a 4-week block
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27);

      // Should start on Monday
      expect(newStart.getDay()).toBe(1);
    });
  });

  describe('button styling', () => {
    it('applies secondary button classes', () => {
      render(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      expect(previousButton).toHaveClass('btn-secondary');

      const nextButton = screen.getByLabelText('Next block');
      expect(nextButton).toHaveClass('btn-secondary');
    });

    it('displays navigation icons', () => {
      const { container } = render(<BlockNavigation {...defaultProps} />);

      const svgElements = container.querySelectorAll('svg');
      expect(svgElements.length).toBeGreaterThan(0);
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA labels for all buttons', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByLabelText('Previous block')).toBeInTheDocument();
      expect(screen.getByLabelText('Next block')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to today')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to this block')).toBeInTheDocument();
    });

    it('has visible button text', () => {
      render(<BlockNavigation {...defaultProps} />);

      expect(screen.getByText('Previous Block')).toBeInTheDocument();
      expect(screen.getByText('Next Block')).toBeInTheDocument();
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('This Block')).toBeInTheDocument();
    });
  });

  describe('responsive layout', () => {
    it('renders flex layout for mobile and desktop', () => {
      const { container } = render(<BlockNavigation {...defaultProps} />);

      const mainContainer = container.firstChild;
      expect(mainContainer).toHaveClass('flex', 'flex-col', 'sm:flex-row');
    });

    it('hides full range on small screens', () => {
      const { container } = render(<BlockNavigation {...defaultProps} />);

      const fullRange = container.querySelector('.lg\\:block');
      expect(fullRange).toHaveClass('hidden');
    });
  });

  describe('date formatting', () => {
    it('formats dates consistently', () => {
      const startDate = new Date('2024-02-01');
      const endDate = new Date('2024-02-28');

      render(
        <BlockNavigation
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      );

      expect(screen.getByText('Feb 1 - Feb 28, 2024')).toBeInTheDocument();
    });

    it('handles year transitions', () => {
      const startDate = new Date('2023-12-18');
      const endDate = new Date('2024-01-14');

      render(
        <BlockNavigation
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      );

      expect(screen.getByText('Dec 18 - Jan 14, 2024')).toBeInTheDocument();
    });
  });
});
