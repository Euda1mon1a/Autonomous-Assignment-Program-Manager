/**
 * Tests for ComplianceTimeline Component
 * Component: compliance/ComplianceTimeline - Historical ACGME compliance event timeline
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { ComplianceTimeline, ComplianceEvent } from '../ComplianceTimeline';

// Mock the Badge component to simplify assertions
jest.mock('../../ui/Badge', () => ({
  Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <span data-testid="badge" data-variant={variant}>
      {children}
    </span>
  ),
}));

describe('ComplianceTimeline', () => {
  const sampleEvents: ComplianceEvent[] = [
    {
      id: 'evt-1',
      date: '2024-06-15T12:00:00',
      type: 'violation',
      category: 'Work Hours',
      message: 'Exceeded 80-hour weekly limit',
      details: { actual: '85', limit: '80' },
    },
    {
      id: 'evt-2',
      date: '2024-06-18T12:00:00',
      type: 'warning',
      category: 'Days Off',
      message: 'Approaching 1-in-7 limit',
    },
    {
      id: 'evt-3',
      date: '2024-06-10T12:00:00',
      type: 'compliant',
      category: 'Supervision',
      message: 'Supervision ratios within limits',
    },
  ];

  describe('Rendering', () => {
    it('renders with required props', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(
        screen.getByRole('region', { name: 'Compliance history timeline' })
      ).toBeInTheDocument();
    });

    it('displays the "Compliance History" heading', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('Compliance History')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <ComplianceTimeline events={sampleEvents} className="extra-class" />
      );
      expect(container.firstChild).toHaveClass('extra-class');
    });
  });

  describe('Empty State', () => {
    it('shows "No compliance events recorded" when events array is empty', () => {
      render(<ComplianceTimeline events={[]} />);
      expect(
        screen.getByText('No compliance events recorded')
      ).toBeInTheDocument();
    });

    it('has role="status" on empty state container', () => {
      render(<ComplianceTimeline events={[]} />);
      const emptyStatus = screen.getByText('No compliance events recorded')
        .closest('[role="status"]');
      expect(emptyStatus).toBeInTheDocument();
    });

    it('still shows summary stats at zero when empty', () => {
      render(<ComplianceTimeline events={[]} />);
      expect(screen.getByText('0 Violations')).toBeInTheDocument();
      expect(screen.getByText('0 Warnings')).toBeInTheDocument();
      expect(screen.getByText('0 Compliant')).toBeInTheDocument();
    });
  });

  describe('Events Sorted by Date Descending', () => {
    it('renders the most recent event first', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      const buttons = screen.getAllByRole('button');
      // Most recent event is evt-2 (2024-06-18), then evt-1 (2024-06-15), then evt-3 (2024-06-10)
      expect(buttons[0]).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Days Off')
      );
      expect(buttons[1]).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Work Hours')
      );
      expect(buttons[2]).toHaveAttribute(
        'aria-label',
        expect.stringContaining('Supervision')
      );
    });

    it('renders all events', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('Exceeded 80-hour weekly limit')).toBeInTheDocument();
      expect(screen.getByText('Approaching 1-in-7 limit')).toBeInTheDocument();
      expect(screen.getByText('Supervision ratios within limits')).toBeInTheDocument();
    });
  });

  describe('Summary Stats', () => {
    it('displays correct violation count', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('1 Violations')).toBeInTheDocument();
    });

    it('displays correct warning count', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('1 Warnings')).toBeInTheDocument();
    });

    it('displays correct compliant count', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('1 Compliant')).toBeInTheDocument();
    });

    it('has role="status" with aria-label on summary', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(
        screen.getByRole('status', { name: 'Compliance event summary' })
      ).toBeInTheDocument();
    });

    it('displays correct badge variants for stats', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      const badges = screen.getAllByTestId('badge');
      const variants = badges.map((b) => b.getAttribute('data-variant'));
      expect(variants).toContain('destructive');
      expect(variants).toContain('warning');
    });

    it('counts correctly with multiple events of same type', () => {
      const eventsWithMultipleViolations: ComplianceEvent[] = [
        ...sampleEvents,
        {
          id: 'evt-4',
          date: '2024-06-20',
          type: 'violation',
          category: 'Rest Period',
          message: 'Insufficient rest between shifts',
        },
      ];
      render(
        <ComplianceTimeline events={eventsWithMultipleViolations} />
      );
      expect(screen.getByText('2 Violations')).toBeInTheDocument();
    });
  });

  describe('Event Click Handler', () => {
    it('calls onEventClick when an event card is clicked', () => {
      const onEventClick = jest.fn();
      render(
        <ComplianceTimeline
          events={sampleEvents}
          onEventClick={onEventClick}
        />
      );
      // Events are sorted by date descending. The first button is evt-2 (2024-06-18)
      const buttons = screen.getAllByRole('button');
      fireEvent.click(buttons[0]);
      expect(onEventClick).toHaveBeenCalledTimes(1);
      expect(onEventClick).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'evt-2' })
      );
    });

    it('calls onEventClick with the correct event data', () => {
      const onEventClick = jest.fn();
      render(
        <ComplianceTimeline
          events={sampleEvents}
          onEventClick={onEventClick}
        />
      );
      // Click the last button (evt-3, earliest date)
      const buttons = screen.getAllByRole('button');
      fireEvent.click(buttons[2]);
      expect(onEventClick).toHaveBeenCalledWith(
        expect.objectContaining({
          id: 'evt-3',
          category: 'Supervision',
          type: 'compliant',
        })
      );
    });

    it('renders clickable buttons even without onEventClick', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      // Buttons still render, they just call onEventClick?.(event) which does nothing
      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(3);
    });
  });

  describe('Date Range Display', () => {
    it('displays date range when startDate and endDate are provided', () => {
      render(
        <ComplianceTimeline
          events={sampleEvents}
          startDate="2024-06-01T12:00:00"
          endDate="2024-06-30T12:00:00"
        />
      );
      // Dates formatted via toLocaleDateString()
      expect(screen.getByText(/6\/1\/2024/)).toBeInTheDocument();
      expect(screen.getByText(/6\/30\/2024/)).toBeInTheDocument();
    });

    it('does not display date range when dates are not provided', () => {
      const { container } = render(
        <ComplianceTimeline events={sampleEvents} />
      );
      // The date range paragraph (p.text-sm.text-gray-600 inside .mb-6)
      // is only rendered when both startDate AND endDate exist
      const dateRangeParagraph = container.querySelector('.mb-6 > p.text-sm.text-gray-600');
      expect(dateRangeParagraph).toBeNull();
    });

    it('does not display date range when only startDate is provided', () => {
      const { container } = render(
        <ComplianceTimeline events={sampleEvents} startDate="2024-06-01T12:00:00" />
      );
      // Requires both startDate AND endDate
      const paragraphs = container.querySelectorAll('.mb-6 > p');
      expect(paragraphs).toHaveLength(0);
    });
  });

  describe('Event Details Rendering', () => {
    it('renders event category as heading', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(screen.getByText('Work Hours')).toBeInTheDocument();
      expect(screen.getByText('Days Off')).toBeInTheDocument();
      expect(screen.getByText('Supervision')).toBeInTheDocument();
    });

    it('renders event message', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      expect(
        screen.getByText('Exceeded 80-hour weekly limit')
      ).toBeInTheDocument();
    });

    it('renders event type as badge', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      const badges = screen.getAllByTestId('badge');
      const badgeTexts = badges.map((b) => b.textContent);
      expect(badgeTexts).toContain('violation');
      expect(badgeTexts).toContain('warning');
      expect(badgeTexts).toContain('compliant');
    });

    it('renders detail key-value pairs when details are present', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      // evt-1 has details { actual: '85', limit: '80' }
      expect(screen.getByText('actual:')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('limit:')).toBeInTheDocument();
      expect(screen.getByText('80')).toBeInTheDocument();
    });

    it('does not render details section when no details', () => {
      const eventsWithoutDetails: ComplianceEvent[] = [
        {
          id: 'evt-no-details',
          date: '2024-06-15',
          type: 'compliant',
          category: 'Test',
          message: 'All good',
        },
      ];
      render(<ComplianceTimeline events={eventsWithoutDetails} />);
      // No key-value detail pairs should exist
      expect(screen.queryByText('actual:')).not.toBeInTheDocument();
    });

    it('renders formatted event dates', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      // Dates formatted with toLocaleDateString('en-US', { weekday: 'short', ... })
      expect(screen.getByText(/Jun 15, 2024/)).toBeInTheDocument();
    });

    it('sets aria-label on event buttons including type and category', () => {
      render(<ComplianceTimeline events={sampleEvents} />);
      const buttons = screen.getAllByRole('button');
      expect(buttons[0]).toHaveAttribute(
        'aria-label',
        expect.stringContaining('warning event: Days Off')
      );
    });
  });
});
