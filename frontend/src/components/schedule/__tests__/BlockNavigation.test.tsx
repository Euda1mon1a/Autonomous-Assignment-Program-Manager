import React from 'react';
import { renderWithProviders, screen, fireEvent } from '@/test-utils';
import { BlockNavigation } from '../BlockNavigation';
import { addDays, subDays } from 'date-fns';

// Mock the hooks that make API calls
jest.mock('@/hooks', () => ({
  useBlocks: jest.fn().mockReturnValue({
    data: null,
    isLoading: false,
    error: { status: 401 }, // Simulate fallback mode
  }),
  useBlockRanges: jest.fn().mockReturnValue({
    data: null,
    isLoading: false,
    error: { status: 401 },
  }),
}));

describe('BlockNavigation', () => {
  const defaultStartDate = new Date(2024, 0, 1); // Monday - local time
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
    it('renders navigation buttons', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      expect(screen.getByLabelText('Previous block')).toBeInTheDocument();
      expect(screen.getByLabelText('Next block')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to today')).toBeInTheDocument();
    });

    it('displays current date range', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      // Date range is rendered across text nodes; use regex on the status element
      const rangeDisplay = screen.getByRole('status');
      expect(rangeDisplay).toHaveTextContent(/Jan 1.*Jan 28, 2024/);
    });

    it('displays full range in desktop view', () => {
      const { container } = renderWithProviders(<BlockNavigation {...defaultProps} />);

      const fullRange = container.querySelector('.lg\\:block');
      expect(fullRange).toHaveTextContent('Jan 1, 2024 - Jan 28, 2024');
    });
  });

  describe('previous block navigation', () => {
    it('navigates to previous 4-week block', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      fireEvent.click(previousButton);

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        subDays(defaultStartDate, 28),
        subDays(defaultEndDate, 28)
      );
    });

    it('maintains 4-week block size', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      fireEvent.click(previousButton);

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27); // 28 days = 0-27 days apart
    });
  });

  describe('next block navigation', () => {
    it('navigates to next 4-week block', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const nextButton = screen.getByLabelText('Next block');
      fireEvent.click(nextButton);

      expect(mockOnDateRangeChange).toHaveBeenCalledWith(
        addDays(defaultStartDate, 28),
        addDays(defaultEndDate, 28)
      );
    });

    it('maintains 4-week block size', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const nextButton = screen.getByLabelText('Next block');
      fireEvent.click(nextButton);

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27);
    });
  });

  describe('today navigation', () => {
    it('jumps to block containing today', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const todayButton = screen.getByLabelText('Jump to today');
      fireEvent.click(todayButton);

      expect(mockOnDateRangeChange).toHaveBeenCalled();

      const [newStart, newEnd] = mockOnDateRangeChange.mock.calls[0];
      // Fallback mode uses today as start + 27 days
      const daysDiff = Math.round((newEnd - newStart) / (1000 * 60 * 60 * 24));
      expect(daysDiff).toBe(27);
    });
  });

  describe('button styling', () => {
    it('applies secondary button classes', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      const previousButton = screen.getByLabelText('Previous block');
      expect(previousButton).toHaveClass('btn-secondary');

      const nextButton = screen.getByLabelText('Next block');
      expect(nextButton).toHaveClass('btn-secondary');
    });

    it('displays navigation icons', () => {
      const { container } = renderWithProviders(<BlockNavigation {...defaultProps} />);

      const svgElements = container.querySelectorAll('svg');
      expect(svgElements.length).toBeGreaterThan(0);
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA labels for all buttons', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      expect(screen.getByLabelText('Previous block')).toBeInTheDocument();
      expect(screen.getByLabelText('Next block')).toBeInTheDocument();
      expect(screen.getByLabelText('Jump to today')).toBeInTheDocument();
    });

    it('has visible button text', () => {
      renderWithProviders(<BlockNavigation {...defaultProps} />);

      // In fallback mode, button text is 'Previous'/'Next' (not 'Previous Block'/'Next Block')
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Today')).toBeInTheDocument();
    });
  });

  describe('responsive layout', () => {
    it('renders flex layout for mobile and desktop', () => {
      const { container } = renderWithProviders(<BlockNavigation {...defaultProps} />);

      const mainContainer = container.firstChild;
      expect(mainContainer).toHaveClass('flex', 'flex-col', 'sm:flex-row');
    });

    it('hides full range on small screens', () => {
      const { container } = renderWithProviders(<BlockNavigation {...defaultProps} />);

      const fullRange = container.querySelector('.lg\\:block');
      expect(fullRange).toHaveClass('hidden');
    });
  });

  describe('date formatting', () => {
    it('formats dates consistently', () => {
      const startDate = new Date(2024, 1, 1);
      const endDate = new Date(2024, 1, 28);

      renderWithProviders(
        <BlockNavigation
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      );

      const rangeDisplay = screen.getByRole('status');
      expect(rangeDisplay).toHaveTextContent(/Feb 1.*Feb 28, 2024/);
    });

    it('handles year transitions', () => {
      const startDate = new Date(2023, 11, 18);
      const endDate = new Date(2024, 0, 14);

      renderWithProviders(
        <BlockNavigation
          startDate={startDate}
          endDate={endDate}
          onDateRangeChange={mockOnDateRangeChange}
        />
      );

      const rangeDisplay = screen.getByRole('status');
      expect(rangeDisplay).toHaveTextContent(/Dec 18.*Jan 14, 2024/);
    });
  });
});
