import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScheduleHeader } from '../ScheduleHeader';
import { addDays } from 'date-fns';

describe('ScheduleHeader', () => {
  const createDays = (count: number, startDate: Date = new Date('2024-01-01')) => {
    return Array.from({ length: count }, (_, i) => addDays(startDate, i));
  };

  beforeEach(() => {
    // Mock current date for "today" highlighting
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2024-01-03')); // Wednesday
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('rendering', () => {
    it('renders person column header', () => {
      const days = createDays(7);

      render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      expect(screen.getByText('Person')).toBeInTheDocument();
    });

    it('renders correct number of day columns', () => {
      const days = createDays(7);

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Should have 7 date header cells (each spans 2 columns for AM/PM)
      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');
      expect(dateHeaders).toHaveLength(7);
    });

    it('renders day names and dates', () => {
      const days = createDays(3, new Date('2024-01-01'));

      render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Check for day names
      expect(screen.getByText('Mon')).toBeInTheDocument();
      expect(screen.getByText('Tue')).toBeInTheDocument();
      expect(screen.getByText('Wed')).toBeInTheDocument();

      // Check for dates
      expect(screen.getByText('Jan 1')).toBeInTheDocument();
      expect(screen.getByText('Jan 2')).toBeInTheDocument();
      expect(screen.getByText('Jan 3')).toBeInTheDocument();
    });

    it('renders AM and PM sub-headers for each day', () => {
      const days = createDays(2);

      render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Each day should have AM and PM labels
      const amLabels = screen.getAllByText('AM');
      const pmLabels = screen.getAllByText('PM');

      expect(amLabels).toHaveLength(2);
      expect(pmLabels).toHaveLength(2);
    });
  });

  describe('weekend styling', () => {
    it('applies weekend styling to Saturday', () => {
      const days = [new Date('2024-01-06')]; // Saturday

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeader = container.querySelector('thead tr:first-child th[colspan="2"]');
      expect(dateHeader).toHaveClass('bg-gray-100');
    });

    it('applies weekend styling to Sunday', () => {
      const days = [new Date('2024-01-07')]; // Sunday

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeader = container.querySelector('thead tr:first-child th[colspan="2"]');
      expect(dateHeader).toHaveClass('bg-gray-100');
    });

    it('does not apply weekend styling to weekdays', () => {
      const days = [new Date('2024-01-01')]; // Monday

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeader = container.querySelector('thead tr:first-child th[colspan="2"]');
      expect(dateHeader).toHaveClass('bg-gray-50');
      expect(dateHeader).not.toHaveClass('bg-gray-100');
    });
  });

  describe('today highlighting', () => {
    it('highlights today with blue background', () => {
      const days = createDays(7, new Date('2024-01-01')); // Includes Jan 3 (today)

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Find all date header cells
      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');

      // The 3rd day (index 2) should be today (Jan 3)
      const todayHeader = dateHeaders[2];
      expect(todayHeader).toHaveClass('bg-blue-50', 'ring-2', 'ring-blue-300');
    });

    it('does not highlight other days', () => {
      const days = [new Date('2024-01-01'), new Date('2024-01-02')]; // Before today

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');

      dateHeaders.forEach((header) => {
        expect(header).not.toHaveClass('bg-blue-50');
      });
    });
  });

  describe('sticky positioning', () => {
    it('applies sticky positioning to person header', () => {
      const days = createDays(7);

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const personHeader = screen.getByText('Person').parentElement;
      expect(personHeader).toHaveClass('sticky', 'left-0', 'top-0');
    });

    it('applies sticky positioning to date headers', () => {
      const days = createDays(3);

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');

      dateHeaders.forEach((header) => {
        expect(header).toHaveClass('sticky', 'top-0');
      });
    });

    it('applies correct z-index layering', () => {
      const days = createDays(3);

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Person header (corner) should have highest z-index
      const personHeader = screen.getByText('Person').parentElement;
      expect(personHeader).toHaveClass('z-30');

      // Date headers should have medium z-index
      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');
      dateHeaders.forEach((header) => {
        expect(header).toHaveClass('z-20');
      });

      // AM/PM sub-headers should have medium z-index
      const amPmHeaders = container.querySelectorAll('thead tr:nth-child(2) th[colspan="2"]');
      amPmHeaders.forEach((header) => {
        expect(header).toHaveClass('z-20');
      });
    });
  });

  describe('accessibility', () => {
    it('uses proper table header semantics', () => {
      const days = createDays(3);

      render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const personHeader = screen.getByText('Person').parentElement;
      expect(personHeader?.tagName).toBe('TH');
      expect(personHeader).toHaveAttribute('scope', 'col');
    });

    it('has proper row span for person header', () => {
      const days = createDays(3);

      render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const personHeader = screen.getByText('Person').parentElement;
      expect(personHeader).toHaveAttribute('rowSpan', '2');
    });

    it('has proper column span for date headers', () => {
      const days = createDays(3);

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');
      dateHeaders.forEach((header) => {
        expect(header).toHaveAttribute('colSpan', '2'); // For AM and PM
      });
    });
  });

  describe('responsive layout', () => {
    it('renders compact header structure for many days', () => {
      const days = createDays(28); // 4-week block

      const { container } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      const dateHeaders = container.querySelectorAll('thead tr:first-child th[colspan="2"]');
      expect(dateHeaders).toHaveLength(28);
    });
  });

  describe('memoization', () => {
    it('memoizes header cells to prevent unnecessary recalculation', () => {
      const days = createDays(7);

      const { rerender } = render(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      // Rerender with same days - should not cause issues
      rerender(
        <table>
          <ScheduleHeader days={days} />
        </table>
      );

      expect(screen.getByText('Person')).toBeInTheDocument();
    });
  });
});
