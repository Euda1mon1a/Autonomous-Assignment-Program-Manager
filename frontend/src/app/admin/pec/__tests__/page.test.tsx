/**
 * Tests for PEC Dashboard Page
 *
 * Tests cover:
 * - Page renders with mock data
 * - Tab navigation works
 * - Metric cards display correctly
 * - Filters work as expected
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ReactNode } from 'react';

import PecDashboardPage from '../page';

// Mock the hooks with controlled return values
jest.mock('@/hooks/usePec', () => ({
  usePecDashboard: jest.fn(() => ({
    data: {
      academicYear: 'AY25-26',
      totalResidents: 18,
      residentsByPgy: { '1': 6, '2': 6, '3': 6 },
      upcomingMeetings: [],
      recentDecisions: [],
      openActionItems: [],
      metrics: {
        meetingsThisYear: 3,
        decisionsThisYear: 12,
        openActions: 8,
        overdueActions: 2,
        commandPendingCount: 1,
        avgActionCompletionDays: 14,
      },
    },
    isLoading: false,
  })),
  usePecMeetings: jest.fn(() => ({
    data: [
      {
        id: 'mtg-001',
        meetingDate: '2026-04-15',
        academicYear: 'AY25-26',
        meetingType: 'quarterly',
        focusAreas: ['PGY-1 Progress'],
        status: 'scheduled',
        attendanceCount: 0,
        agendaItemCount: 5,
        decisionCount: 0,
        openActionCount: 0,
      },
    ],
    isLoading: false,
  })),
  usePecActionItems: jest.fn(() => ({
    data: [
      {
        id: 'act-001',
        description: 'Review curriculum requirements',
        ownerName: 'Dr. Smith',
        dueDate: '2026-02-15',
        priority: 'high',
        status: 'open',
        isOverdue: false,
      },
    ],
    isLoading: false,
  })),
  pecQueryKeys: {
    all: ['pec'],
    dashboard: (year: string) => ['pec', 'dashboard', year],
    meetings: (filters?: unknown) => ['pec', 'meetings', filters],
    actions: (filters?: unknown) => ['pec', 'actions', filters],
  },
  getMeetingStatusColor: jest.fn(() => 'text-blue-400 bg-blue-500/10 border-blue-500/30'),
  getMeetingTypeLabel: jest.fn((type: string) => type.charAt(0).toUpperCase() + type.slice(1)),
  getActionPriorityColor: jest.fn(() => 'text-orange-400 bg-orange-500/10 border-orange-500/30'),
  getActionStatusColor: jest.fn(() => 'text-blue-400 bg-blue-500/10'),
}));

// Wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('PecDashboardPage', () => {
  it('renders page header with title', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Program Evaluation Committee')).toBeInTheDocument();
    expect(screen.getByText('ACGME-compliant program oversight')).toBeInTheDocument();
  });

  it('renders all tab buttons', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /meetings/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /action items/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /analytics/i })).toBeInTheDocument();
  });

  it('shows Overview tab content by default', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    // Overview tab should show metrics
    expect(screen.getByText('Total Residents')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
    expect(screen.getByText('Meetings This Year')).toBeInTheDocument();
  });

  it('switches to Meetings tab when clicked', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const meetingsTab = screen.getByRole('tab', { name: /meetings/i });
    fireEvent.click(meetingsTab);

    await waitFor(() => {
      expect(screen.getByText('All Statuses')).toBeInTheDocument();
    });
  });

  it('switches to Actions tab when clicked', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const actionsTab = screen.getByRole('tab', { name: /action items/i });
    fireEvent.click(actionsTab);

    await waitFor(() => {
      expect(screen.getByText('All Priorities')).toBeInTheDocument();
    });
  });

  it('switches to Analytics tab when clicked', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const analyticsTab = screen.getByRole('tab', { name: /analytics/i });
    fireEvent.click(analyticsTab);

    await waitFor(() => {
      expect(screen.getByText('Analytics Coming Soon')).toBeInTheDocument();
    });
  });

  it('renders academic year selector', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const yearSelect = screen.getByLabelText('Select academic year');
    expect(yearSelect).toBeInTheDocument();
    expect(yearSelect).toHaveValue('AY25-26');
  });

  it('renders refresh button', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByLabelText('Refresh data')).toBeInTheDocument();
  });

  it('renders mock data banner', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Demo Mode - Using Mock Data')).toBeInTheDocument();
  });

  it('shows command approval alert when decisions pending', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText(/Decision\(s\) Pending Command Approval/)).toBeInTheDocument();
  });
});

describe('PecDashboardPage - Overview Tab', () => {
  it('renders metric cards with correct values', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Total Residents')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
    expect(screen.getByText('Meetings This Year')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('Open Action Items')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('Overdue Actions')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('renders Next Meeting section', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Next Meeting')).toBeInTheDocument();
  });

  it('renders Overdue Actions section', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    // Use getAllBy since "Overdue Actions" appears in both metric card and section header
    const overdueElements = screen.getAllByText(/Overdue Actions/);
    expect(overdueElements.length).toBeGreaterThan(0);
  });

  it('renders Recent Decisions section', () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Recent Decisions')).toBeInTheDocument();
  });
});

describe('PecDashboardPage - Meetings Tab', () => {
  it('renders meeting table headers', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const meetingsTab = screen.getByRole('tab', { name: /meetings/i });
    fireEvent.click(meetingsTab);

    await waitFor(() => {
      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Focus Areas')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });
  });

  it('renders status filter dropdown', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const meetingsTab = screen.getByRole('tab', { name: /meetings/i });
    fireEvent.click(meetingsTab);

    await waitFor(() => {
      expect(screen.getByText('All Statuses')).toBeInTheDocument();
    });
  });
});

describe('PecDashboardPage - Actions Tab', () => {
  it('renders action table headers', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const actionsTab = screen.getByRole('tab', { name: /action items/i });
    fireEvent.click(actionsTab);

    await waitFor(() => {
      expect(screen.getByText('Description')).toBeInTheDocument();
      expect(screen.getByText('Owner')).toBeInTheDocument();
      expect(screen.getByText('Due Date')).toBeInTheDocument();
      expect(screen.getByText('Priority')).toBeInTheDocument();
    });
  });

  it('renders priority filter dropdown', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const actionsTab = screen.getByRole('tab', { name: /action items/i });
    fireEvent.click(actionsTab);

    await waitFor(() => {
      expect(screen.getByText('All Priorities')).toBeInTheDocument();
    });
  });

  it('renders overdue only checkbox', async () => {
    render(<PecDashboardPage />, { wrapper: createWrapper() });

    const actionsTab = screen.getByRole('tab', { name: /action items/i });
    fireEvent.click(actionsTab);

    await waitFor(() => {
      expect(screen.getByText('Overdue only')).toBeInTheDocument();
    });
  });
});
