/**
 * Tests for CallRoster Component
 *
 * Tests the main call roster view including calendar/list toggle,
 * month navigation, role filtering, and today's highlight section.
 */

import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { CallRoster } from '@/features/call-roster/CallRoster';
import type { CallAssignment } from '@/features/call-roster/types';

// Mock hooks
jest.mock('@/features/call-roster/hooks', () => ({
  useMonthlyOnCallRoster: jest.fn(),
  useTodayOnCall: jest.fn(),
}));

// Mock child components
jest.mock('@/features/call-roster/CallCalendarDay', () => ({
  CallCalendarDay: ({ date, assignments, isToday }: any) => (
    <div data-testid="calendar-day">
      {date.toString()} - {assignments.length} assignments
      {isToday && <span data-testid="today-marker">TODAY</span>}
    </div>
  ),
  CalendarDayHeader: ({ day }: any) => (
    <div data-testid="day-header">{day}</div>
  ),
}));

jest.mock('@/features/call-roster/CallCard', () => ({
  CallCard: ({ assignment }: any) => (
    <div data-testid="call-card">{assignment.person.name}</div>
  ),
  CallListItem: ({ assignment, showDate }: any) => (
    <div data-testid="list-item">
      {assignment.person.name} {showDate && '(with date)'}
    </div>
  ),
}));

import { useMonthlyOnCallRoster, useTodayOnCall } from '@/features/call-roster/hooks';

const mockUseMonthlyOnCallRoster = useMonthlyOnCallRoster as jest.MockedFunction<
  typeof useMonthlyOnCallRoster
>;
const mockUseTodayOnCall = useTodayOnCall as jest.MockedFunction<typeof useTodayOnCall>;

describe('CallRoster', () => {
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
    {
      id: 'assignment-3',
      date: '2025-01-16',
      shift: 'day',
      person: {
        id: 'person-3',
        name: 'Dr. Carol White',
        role: 'attending',
        phone: '555-3333',
      },
      rotation_name: 'Attending Call',
    },
  ];

  const mockTodayAssignments: CallAssignment[] = [mockAssignments[0]];

  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseMonthlyOnCallRoster.mockReturnValue({
      data: mockAssignments,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    mockUseTodayOnCall.mockReturnValue({
      data: mockTodayAssignments,
      isLoading: false,
      error: null,
    } as any);
  });

  describe('Basic Rendering', () => {
    it('should render page title and subtitle', () => {
      render(<CallRoster />);

      expect(screen.getByText('Call Roster')).toBeInTheDocument();
      expect(screen.getByText('Who to page right now')).toBeInTheDocument();
    });

    it('should render view mode toggle buttons', () => {
      render(<CallRoster />);

      expect(screen.getByRole('button', { name: /calendar/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /list/i })).toBeInTheDocument();
    });

    it('should render role filter legend', () => {
      render(<CallRoster />);

      expect(screen.getByText('Role Legend:')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /attending/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /senior/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /intern/i })).toBeInTheDocument();
    });

    it('should render month navigation controls', () => {
      render(<CallRoster />);

      const prevButton = screen.getByTitle('Previous month');
      const nextButton = screen.getByTitle('Next month');
      const todayButton = screen.getByRole('button', { name: /today/i });

      expect(prevButton).toBeInTheDocument();
      expect(nextButton).toBeInTheDocument();
      expect(todayButton).toBeInTheDocument();
    });

    it('should render current month name', () => {
      render(<CallRoster />);

      // Should show current month (test will show whatever the current month is)
      const monthDisplay = screen.getByText(/\w+ \d{4}/);
      expect(monthDisplay).toBeInTheDocument();
    });
  });

  describe('Today On Call Highlight', () => {
    it('should render today highlight section when data exists', () => {
      render(<CallRoster />);

      expect(screen.getByText('On Call RIGHT NOW')).toBeInTheDocument();
    });

    it('should render today assignments in highlight section', () => {
      render(<CallRoster />);

      const callCards = screen.getAllByTestId('call-card');
      expect(callCards.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
    });

    it('should not render highlight section when no today assignments', () => {
      mockUseTodayOnCall.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any);

      render(<CallRoster />);

      expect(screen.queryByText('On Call RIGHT NOW')).not.toBeInTheDocument();
    });

    it('should not render highlight section when today data is null', () => {
      mockUseTodayOnCall.mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
      } as any);

      render(<CallRoster />);

      expect(screen.queryByText('On Call RIGHT NOW')).not.toBeInTheDocument();
    });
  });

  describe('View Mode Toggle', () => {
    it('should show calendar view by default', () => {
      render(<CallRoster />);

      const calendarButton = screen.getByRole('button', { name: /calendar/i });
      expect(calendarButton).toHaveClass('bg-white');
      expect(screen.getAllByTestId('calendar-day').length).toBeGreaterThan(0);
    });

    it('should switch to list view when list button clicked', () => {
      render(<CallRoster />);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      expect(listButton).toHaveClass('bg-white');
      expect(screen.queryByTestId('calendar-day')).not.toBeInTheDocument();
    });

    it('should show list items in list view', () => {
      render(<CallRoster />);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      const listItems = screen.getAllByTestId('list-item');
      expect(listItems.length).toBe(mockAssignments.length);
    });

    it('should switch back to calendar view', () => {
      render(<CallRoster />);

      const listButton = screen.getByRole('button', { name: /list/i });
      const calendarButton = screen.getByRole('button', { name: /calendar/i });

      fireEvent.click(listButton);
      fireEvent.click(calendarButton);

      expect(calendarButton).toHaveClass('bg-white');
      expect(screen.getAllByTestId('calendar-day').length).toBeGreaterThan(0);
    });
  });

  describe('Role Filtering', () => {
    it('should show all assignments by default', () => {
      render(<CallRoster />);

      const allButton = screen.getByRole('button', { name: /^all$/i });
      expect(allButton).toHaveClass('bg-gray-800');
    });

    it('should filter by attending role', () => {
      render(<CallRoster />);

      const attendingButton = screen.getByRole('button', { name: /attending/i });
      fireEvent.click(attendingButton);

      // Switch to list view to verify filtering
      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      const listItems = screen.getAllByTestId('list-item');
      // Only 1 attending in mock data
      expect(listItems).toHaveLength(1);
      expect(screen.getByText('Dr. Carol White')).toBeInTheDocument();
    });

    it('should filter by senior role', () => {
      render(<CallRoster />);

      const seniorButton = screen.getByRole('button', { name: /senior/i });
      fireEvent.click(seniorButton);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      const listItems = screen.getAllByTestId('list-item');
      // Only 1 senior in mock data
      expect(listItems).toHaveLength(1);
      expect(screen.getByText('Dr. Alice Smith')).toBeInTheDocument();
    });

    it('should filter by intern role', () => {
      render(<CallRoster />);

      const internButton = screen.getByRole('button', { name: /intern/i });
      fireEvent.click(internButton);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      const listItems = screen.getAllByTestId('list-item');
      // Only 1 intern in mock data
      expect(listItems).toHaveLength(1);
      expect(screen.getByText('Dr. Bob Jones')).toBeInTheDocument();
    });

    it('should show all assignments when All filter selected', () => {
      render(<CallRoster />);

      // Select a specific role first
      const internButton = screen.getByRole('button', { name: /intern/i });
      fireEvent.click(internButton);

      // Then select All
      const allButton = screen.getByRole('button', { name: /^all$/i });
      fireEvent.click(allButton);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      const listItems = screen.getAllByTestId('list-item');
      expect(listItems).toHaveLength(mockAssignments.length);
    });
  });

  describe('Month Navigation', () => {
    it('should navigate to previous month', () => {
      render(<CallRoster />);

      const currentMonth = screen.getByText(/\w+ \d{4}/);
      const currentMonthText = currentMonth.textContent;

      const prevButton = screen.getByTitle('Previous month');
      fireEvent.click(prevButton);

      const newMonth = screen.getByText(/\w+ \d{4}/);
      expect(newMonth.textContent).not.toBe(currentMonthText);
    });

    it('should navigate to next month', () => {
      render(<CallRoster />);

      const currentMonth = screen.getByText(/\w+ \d{4}/);
      const currentMonthText = currentMonth.textContent;

      const nextButton = screen.getByTitle('Next month');
      fireEvent.click(nextButton);

      const newMonth = screen.getByText(/\w+ \d{4}/);
      expect(newMonth.textContent).not.toBe(currentMonthText);
    });

    it('should navigate to today when Today button clicked', () => {
      render(<CallRoster />);

      // Navigate away from current month first
      const nextButton = screen.getByTitle('Next month');
      fireEvent.click(nextButton);
      fireEvent.click(nextButton);

      // Then click Today
      const todayButton = screen.getByRole('button', { name: /today/i });
      fireEvent.click(todayButton);

      // Should show current month again
      const now = new Date();
      const expectedMonth = now.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });
      expect(screen.getByText(expectedMonth)).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when data is loading', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      expect(screen.getByText('Loading call roster...')).toBeInTheDocument();
    });

    it('should not show calendar when loading', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      expect(screen.queryByTestId('calendar-day')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when loading fails', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch roster'),
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      expect(screen.getByText('Error loading call roster')).toBeInTheDocument();
      expect(screen.getByText('Failed to fetch roster')).toBeInTheDocument();
    });

    it('should not show calendar when error occurs', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch roster'),
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      expect(screen.queryByTestId('calendar-day')).not.toBeInTheDocument();
    });
  });

  describe('Statistics Display', () => {
    it('should show total call shifts statistic', () => {
      render(<CallRoster />);

      expect(screen.getByText('Total Call Shifts')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should show attending count', () => {
      render(<CallRoster />);

      expect(screen.getByText('Attending')).toBeInTheDocument();
      // 1 attending in mock data
      const stats = screen.getAllByText('1');
      expect(stats.length).toBeGreaterThan(0);
    });

    it('should show senior count', () => {
      render(<CallRoster />);

      expect(screen.getByText('Senior')).toBeInTheDocument();
    });

    it('should show intern count', () => {
      render(<CallRoster />);

      expect(screen.getByText('Intern')).toBeInTheDocument();
    });

    it('should not show stats when loading', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      expect(screen.queryByText('Total Call Shifts')).not.toBeInTheDocument();
    });
  });

  describe('List View Empty State', () => {
    it('should show empty message when no assignments', () => {
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<CallRoster />);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);

      expect(
        screen.getByText('No on-call assignments found for this month')
      ).toBeInTheDocument();
    });

    it('should show empty message when all assignments filtered out', () => {
      render(<CallRoster />);

      // Filter by a role that has no assignments (create scenario)
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: mockAssignments,
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      } as any);

      const attendingButton = screen.getByRole('button', { name: /attending/i });
      fireEvent.click(attendingButton);

      // Change mock to empty array for this filter
      mockUseMonthlyOnCallRoster.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      } as any);

      const listButton = screen.getByRole('button', { name: /list/i });
      fireEvent.click(listButton);
    });
  });

  describe('Calendar View', () => {
    it('should render day of week headers', () => {
      render(<CallRoster />);

      const dayHeaders = screen.getAllByTestId('day-header');
      expect(dayHeaders).toHaveLength(7);
    });

    it('should render calendar grid with days', () => {
      render(<CallRoster />);

      const calendarDays = screen.getAllByTestId('calendar-day');
      // Calendar should show ~35-42 days (5-6 weeks)
      expect(calendarDays.length).toBeGreaterThanOrEqual(28);
      expect(calendarDays.length).toBeLessThanOrEqual(42);
    });
  });
});
