/**
 * Tests for CallCalendarDay Component
 *
 * Tests calendar day cell rendering, assignment display,
 * hover popover, and today highlighting.
 */

import { render, screen, fireEvent } from '@/test-utils';
import { CallCalendarDay, CalendarDayHeader } from '@/features/call-roster/CallCalendarDay';
import type { CallAssignment } from '@/features/call-roster/types';

// Mock ContactInfo component
jest.mock('@/features/call-roster/ContactInfo', () => ({
  ContactInfo: ({ person, showLabel, compact }: any) => (
    <div data-testid="contact-info">
      Contact: {person.name} (compact: {compact?.toString()})
    </div>
  ),
}));

describe('CallCalendarDay', () => {
  const mockDate = new Date('2025-01-15');
  const mockAssignments: CallAssignment[] = [
    {
      id: 'assignment-1',
      date: '2025-01-15',
      shift: 'day',
      person: {
        id: 'person-1',
        name: 'Dr. Alice Smith',
        pgy_level: 3,
        role: 'senior',
        phone: '555-1111',
      },
      rotation_name: 'Day Call',
    },
    {
      id: 'assignment-2',
      date: '2025-01-15',
      shift: 'night',
      person: {
        id: 'person-2',
        name: 'Dr. Bob Jones',
        pgy_level: 1,
        role: 'intern',
        phone: '555-2222',
      },
      rotation_name: 'Night Call',
    },
  ];

  describe('Basic Rendering', () => {
    it('should render day number', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.getByText('15')).toBeInTheDocument();
    });

    it('should apply current month styling', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).toHaveClass('bg-white');
      expect(dayCell).not.toHaveClass('opacity-50');
    });

    it('should apply not current month styling', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={false}
          isToday={false}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).toHaveClass('bg-gray-50');
      expect(dayCell).toHaveClass('opacity-50');
    });

    it('should show empty state for current month with no assignments', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.getByText('No call')).toBeInTheDocument();
    });

    it('should not show empty state for non-current month', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={false}
          isToday={false}
        />
      );

      expect(screen.queryByText('No call')).not.toBeInTheDocument();
    });
  });

  describe('Today Highlighting', () => {
    it('should show today badge when isToday is true', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={true}
        />
      );

      expect(screen.getByText('Today')).toBeInTheDocument();
    });

    it('should not show today badge when isToday is false', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.queryByText('Today')).not.toBeInTheDocument();
    });

    it('should apply today ring styling', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={true}
        />
      );

      const dayCell = container.firstChild;
      expect(dayCell).toHaveClass('ring-2');
      expect(dayCell).toHaveClass('ring-blue-500');
    });

    it('should style day number blue when today', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={true}
        />
      );

      const dayNumber = screen.getByText('15');
      expect(dayNumber).toHaveClass('text-blue-600');
    });
  });

  describe('Assignment Display', () => {
    it('should render assignments', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
    });

    it('should show PGY level for residents', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.getByText('PGY-3')).toBeInTheDocument();
      expect(screen.getByText('PGY-1')).toBeInTheDocument();
    });

    it('should show role when no PGY level', () => {
      const attendingAssignment: CallAssignment = {
        id: 'assignment-3',
        date: '2025-01-15',
        shift: 'day',
        person: {
          id: 'person-3',
          name: 'Dr. Carol White',
          role: 'attending',
          phone: '555-3333',
        },
        rotation_name: 'Attending Call',
      };

      render(
        <CallCalendarDay
          date={mockDate}
          assignments={[attendingAssignment]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.getByText('attending')).toBeInTheDocument();
    });

    it('should limit display to first 3 assignments', () => {
      const manyAssignments: CallAssignment[] = [
        ...mockAssignments,
        {
          id: 'assignment-3',
          date: '2025-01-15',
          shift: 'day',
          person: {
            id: 'person-3',
            name: 'Dr. Carol White',
            role: 'attending',
            phone: '555-3333',
          },
        },
        {
          id: 'assignment-4',
          date: '2025-01-15',
          shift: 'day',
          person: {
            id: 'person-4',
            name: 'Dr. David Brown',
            pgy_level: 2,
            role: 'senior',
            phone: '555-4444',
          },
        },
      ];

      render(
        <CallCalendarDay
          date={mockDate}
          assignments={manyAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      // Should show "+1 more" indicator
      expect(screen.getByText('+1 more')).toBeInTheDocument();
    });

    it('should show correct count for excess assignments', () => {
      const manyAssignments: CallAssignment[] = [
        ...mockAssignments,
        ...Array(5).fill(null).map((_, i) => ({
          id: `assignment-${i + 3}`,
          date: '2025-01-15',
          shift: 'day' as const,
          person: {
            id: `person-${i + 3}`,
            name: `Dr. Person ${i + 3}`,
            pgy_level: 1,
            role: 'intern' as const,
            phone: '555-0000',
          },
        })),
      ];

      render(
        <CallCalendarDay
          date={mockDate}
          assignments={manyAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      // 7 total - 3 shown = +4 more
      expect(screen.getByText('+4 more')).toBeInTheDocument();
    });
  });

  describe('Role Color Coding', () => {
    it('should apply senior role colors', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[mockAssignments[0]]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const assignmentBadge = container.querySelector('.text-blue-800');
      expect(assignmentBadge).toBeInTheDocument();
    });

    it('should apply intern role colors', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[mockAssignments[1]]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const assignmentBadge = container.querySelector('.text-green-800');
      expect(assignmentBadge).toBeInTheDocument();
    });

    it('should apply attending role colors', () => {
      const attendingAssignment: CallAssignment = {
        id: 'assignment-3',
        date: '2025-01-15',
        shift: 'day',
        person: {
          id: 'person-3',
          name: 'Dr. Carol White',
          role: 'attending',
          phone: '555-3333',
        },
      };

      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[attendingAssignment]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const assignmentBadge = container.querySelector('.text-red-800');
      expect(assignmentBadge).toBeInTheDocument();
    });
  });

  describe('Click Handler', () => {
    it('should call onClick when provided', () => {
      const mockOnClick = jest.fn();

      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
          onClick={mockOnClick}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.click(dayCell);

      expect(mockOnClick).toHaveBeenCalledWith(mockDate, mockAssignments);
    });

    it('should not error when onClick not provided', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;

      expect(() => {
        fireEvent.click(dayCell);
      }).not.toThrow();
    });
  });

  describe('Hover Popover', () => {
    it('should not show popover initially', () => {
      render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      expect(screen.queryByTestId('contact-info')).not.toBeInTheDocument();
    });

    it('should show popover on mouse enter when assignments exist', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);

      // Popover should show full date
      expect(screen.getByText(/Tuesday, January 15, 2025/)).toBeInTheDocument();
    });

    it('should hide popover on mouse leave', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);
      expect(screen.getByText(/Tuesday, January 15, 2025/)).toBeInTheDocument();

      fireEvent.mouseLeave(dayCell);
      expect(screen.queryByText(/Tuesday, January 15, 2025/)).not.toBeInTheDocument();
    });

    it('should not show popover when no assignments', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={[]}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);

      expect(screen.queryByTestId('contact-info')).not.toBeInTheDocument();
    });

    it('should show all assignments in popover', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);

      // Both assignments should appear
      const contacts = screen.getAllByTestId('contact-info');
      expect(contacts).toHaveLength(2);
    });

    it('should show rotation name in popover', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={false}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);

      expect(screen.getByText('Day Call')).toBeInTheDocument();
      expect(screen.getByText('Night Call')).toBeInTheDocument();
    });

    it('should show today indicator in popover when isToday', () => {
      const { container } = render(
        <CallCalendarDay
          date={mockDate}
          assignments={mockAssignments}
          isCurrentMonth={true}
          isToday={true}
        />
      );

      const dayCell = container.firstChild as HTMLElement;
      fireEvent.mouseEnter(dayCell);

      expect(screen.getByText('(Today)')).toBeInTheDocument();
    });
  });
});

describe('CalendarDayHeader', () => {
  it('should render day name', () => {
    render(<CalendarDayHeader day="Mon" />);

    expect(screen.getByText('Mon')).toBeInTheDocument();
  });

  it('should apply header styling', () => {
    const { container } = render(<CalendarDayHeader day="Mon" />);

    const header = container.firstChild;
    expect(header).toHaveClass('bg-gray-100');
    expect(header).toHaveClass('font-semibold');
  });

  it('should render all days of week', () => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const { container } = render(
      <>
        {days.map((day) => (
          <CalendarDayHeader key={day} day={day} />
        ))}
      </>
    );

    days.forEach((day) => {
      expect(screen.getByText(day)).toBeInTheDocument();
    });
  });
});
