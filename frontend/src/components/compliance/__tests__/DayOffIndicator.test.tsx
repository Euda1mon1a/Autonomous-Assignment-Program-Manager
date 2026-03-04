/**
 * Tests for DayOffIndicator Component
 * Component: compliance/DayOffIndicator - 1-in-7 day off ACGME tracker
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { DayOffIndicator } from '../DayOffIndicator';

describe('DayOffIndicator', () => {
  const defaultProps = {
    consecutiveDaysWorked: 3,
    lastDayOff: '2024-06-10',
  };

  // Fix the current date for consistent testing of "X days ago" text
  const _realDateNow = Date.now;
  const realDate = global.Date;

  beforeAll(() => {
    // Mock Date to return a fixed "now" for constructor calls with no args
    const fixedDate = new Date('2024-06-13T12:00:00Z');
    const OriginalDate = global.Date;

    // @ts-expect-error - overriding Date constructor for tests
    global.Date = class extends OriginalDate {
      constructor(...args: unknown[]) {
        if (args.length === 0) {
          super(fixedDate.getTime());
        } else {
          // @ts-expect-error - spread args to Date constructor
          super(...args);
        }
      }

      static now() {
        return fixedDate.getTime();
      }
    } as DateConstructor;

    // Preserve static methods
    Object.setPrototypeOf(global.Date, OriginalDate);
  });

  afterAll(() => {
    global.Date = realDate;
  });

  describe('Rendering', () => {
    it('renders with required props', () => {
      render(<DayOffIndicator {...defaultProps} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('displays consecutive days worked count', () => {
      render(<DayOffIndicator {...defaultProps} />);
      expect(screen.getByText('3 / 6 days')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} className="my-class" />
      );
      expect(container.firstChild).toHaveClass('my-class');
    });

    it('displays last day off date', () => {
      render(<DayOffIndicator {...defaultProps} />);
      expect(screen.getByText(/Last day off:/)).toBeInTheDocument();
    });
  });

  describe('Compliant State', () => {
    it('shows "Compliant" label when consecutiveDaysWorked < maxConsecutiveDays', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />);
      expect(screen.getByText('Compliant')).toBeInTheDocument();
    });

    it('applies green styling', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />
      );
      expect(container.firstChild).toHaveClass('bg-green-100');
      expect(container.firstChild).toHaveClass('border-green-500');
    });

    it('does not show violation or warning messages', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />);
      expect(screen.queryByText('Day off required tomorrow')).not.toBeInTheDocument();
      expect(screen.queryByText(/Worked.*consecutive days/)).not.toBeInTheDocument();
    });
  });

  describe('Warning State', () => {
    it('shows "Warning" label when consecutiveDaysWorked === maxConsecutiveDays', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />);
      expect(screen.getByText('Warning')).toBeInTheDocument();
    });

    it('shows "Day off required tomorrow" message', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />);
      expect(screen.getByText('Day off required tomorrow')).toBeInTheDocument();
    });

    it('applies yellow styling', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />
      );
      expect(container.firstChild).toHaveClass('bg-yellow-100');
      expect(container.firstChild).toHaveClass('border-yellow-500');
    });

    it('displays "6 / 6 days"', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />);
      expect(screen.getByText('6 / 6 days')).toBeInTheDocument();
    });
  });

  describe('Violation State', () => {
    it('shows "Violation" label when consecutiveDaysWorked > maxConsecutiveDays', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />);
      expect(screen.getByText('Violation')).toBeInTheDocument();
    });

    it('shows violation message with actual days', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />);
      expect(
        screen.getByText('Worked 8 consecutive days (max 6)')
      ).toBeInTheDocument();
    });

    it('applies red styling', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />
      );
      expect(container.firstChild).toHaveClass('bg-red-100');
      expect(container.firstChild).toHaveClass('border-red-500');
    });

    it('displays "8 / 6 days"', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />);
      expect(screen.getByText('8 / 6 days')).toBeInTheDocument();
    });
  });

  describe('Days Until Required Calculation', () => {
    it('shows correct days remaining for compliant state', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={2} />);
      // daysUntilRequired = max(0, 6 - 2) = 4
      expect(screen.getByText('4 days until required day off')).toBeInTheDocument();
    });

    it('shows "1 day" (singular) when 1 day remains', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={5} />);
      // daysUntilRequired = max(0, 6 - 5) = 1
      expect(screen.getByText('1 day until required day off')).toBeInTheDocument();
    });

    it('shows 0 days remaining for warning state (message is different)', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />);
      // Warning state shows "Day off required tomorrow" instead of days remaining
      expect(screen.getByText('Day off required tomorrow')).toBeInTheDocument();
    });

    it('shows 0 days remaining for violation state (message is different)', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={7} />);
      // Violation state shows the violation message
      expect(
        screen.getByText('Worked 7 consecutive days (max 6)')
      ).toBeInTheDocument();
    });

    it('uses plural "days" for 0 days when in compliant state with exact match', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={0} />);
      // daysUntilRequired = max(0, 6 - 0) = 6
      expect(screen.getByText('6 days until required day off')).toBeInTheDocument();
    });
  });

  describe('Visual Timeline Rendering', () => {
    it('renders maxConsecutiveDays + 1 timeline blocks', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />
      );
      // Default maxConsecutiveDays = 6, so 7 blocks (indices 0-6)
      const timelineBlocks = container.querySelectorAll('[title^="Day "]');
      expect(timelineBlocks).toHaveLength(7);
    });

    it('marks worked days with filled color', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />
      );
      const blocks = container.querySelectorAll('[title^="Day "]');
      // First 3 blocks should be filled (green), rest should be gray
      expect(blocks[0]).toHaveClass('bg-green-500');
      expect(blocks[1]).toHaveClass('bg-green-500');
      expect(blocks[2]).toHaveClass('bg-green-500');
      expect(blocks[3]).toHaveClass('bg-gray-200');
    });

    it('marks blocks with red in violation state', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />
      );
      const blocks = container.querySelectorAll('[title^="Day "]');
      // All 7 blocks (0-6) should be red because isViolation is true
      expect(blocks[0]).toHaveClass('bg-red-500');
      expect(blocks[6]).toHaveClass('bg-red-500');
    });

    it('has aria-hidden on individual timeline blocks', () => {
      const { container } = render(
        <DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />
      );
      const blocks = container.querySelectorAll('[title^="Day "]');
      blocks.forEach((block) => {
        expect(block).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('has meter role with proper ARIA attributes', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />);
      const meter = screen.getByRole('meter');
      expect(meter).toHaveAttribute('aria-valuenow', '3');
      expect(meter).toHaveAttribute('aria-valuemin', '0');
      expect(meter).toHaveAttribute('aria-valuemax', '6');
    });
  });

  describe('Custom maxConsecutiveDays', () => {
    it('uses custom maxConsecutiveDays for warning determination', () => {
      render(
        <DayOffIndicator
          {...defaultProps}
          consecutiveDaysWorked={4}
          maxConsecutiveDays={4}
        />
      );
      // 4 === 4 => warning state
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('Day off required tomorrow')).toBeInTheDocument();
    });

    it('uses custom maxConsecutiveDays for violation determination', () => {
      render(
        <DayOffIndicator
          {...defaultProps}
          consecutiveDaysWorked={5}
          maxConsecutiveDays={4}
        />
      );
      expect(screen.getByText('Violation')).toBeInTheDocument();
      expect(
        screen.getByText('Worked 5 consecutive days (max 4)')
      ).toBeInTheDocument();
    });

    it('shows compliant when below custom maxConsecutiveDays', () => {
      render(
        <DayOffIndicator
          {...defaultProps}
          consecutiveDaysWorked={2}
          maxConsecutiveDays={4}
        />
      );
      expect(screen.getByText('Compliant')).toBeInTheDocument();
      // daysUntilRequired = max(0, 4 - 2) = 2
      expect(screen.getByText('2 days until required day off')).toBeInTheDocument();
    });

    it('renders correct number of timeline blocks with custom max', () => {
      const { container } = render(
        <DayOffIndicator
          {...defaultProps}
          consecutiveDaysWorked={2}
          maxConsecutiveDays={4}
        />
      );
      // maxConsecutiveDays + 1 = 5 blocks
      const timelineBlocks = container.querySelectorAll('[title^="Day "]');
      expect(timelineBlocks).toHaveLength(5);
    });

    it('displays custom max in the count "X / Y days"', () => {
      render(
        <DayOffIndicator
          {...defaultProps}
          consecutiveDaysWorked={2}
          maxConsecutiveDays={5}
        />
      );
      expect(screen.getByText('2 / 5 days')).toBeInTheDocument();
    });
  });

  describe('ARIA Attributes', () => {
    it('has role="status" on the container', () => {
      render(<DayOffIndicator {...defaultProps} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live="polite" on the container', () => {
      render(<DayOffIndicator {...defaultProps} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-live',
        'polite'
      );
    });

    it('includes compliance label in aria-label', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={3} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '1-in-7 days off compliance: Compliant'
      );
    });

    it('updates aria-label for violation state', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={8} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '1-in-7 days off compliance: Violation'
      );
    });

    it('updates aria-label for warning state', () => {
      render(<DayOffIndicator {...defaultProps} consecutiveDaysWorked={6} />);
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        '1-in-7 days off compliance: Warning'
      );
    });
  });
});
