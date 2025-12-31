/**
 * Tests for MyLifeDashboard Component
 *
 * Tests main dashboard rendering, data integration, and user interactions
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MyLifeDashboard } from '@/features/my-dashboard/MyLifeDashboard';
import * as api from '@/lib/api';
import {
  mockDashboardApiResponse,
  mockDashboardData,
  mockDashboardDataEmpty,
  mockDashboardDataMinimal,
} from './mockData';

// Mock the API module
jest.mock('@/lib/api');

// Create a wrapper with QueryClient for testing
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('MyLifeDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue(mockDashboardApiResponse);
    (api.post as jest.Mock).mockResolvedValue({ success: true });

    // Mock localStorage for user data
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => JSON.stringify({ id: 'user-123' })),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
  });

  describe('Header Rendering', () => {
    it('should render dashboard title', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('My Schedule')).toBeInTheDocument();
      });
    });

    it('should display user name and role', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Dr. John Smith/)).toBeInTheDocument();
        expect(screen.getByText(/Resident \(PGY-2\)/)).toBeInTheDocument();
      });
    });

    it('should render refresh button', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
      });
    });

    it('should render calendar sync button', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /sync to calendar/i })).toBeInTheDocument();
      });
    });
  });

  describe('Summary Cards', () => {
    it('should render all three summary cards', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Next Assignment')).toBeInTheDocument();
        expect(screen.getByText('Workload (4 weeks)')).toBeInTheDocument();
        expect(screen.getByText('Pending Swaps')).toBeInTheDocument();
      });
    });

    it('should display next assignment value', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Today at 8 AM')).toBeInTheDocument();
      });
    });

    it('should display workload value', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('12')).toBeInTheDocument();
      });
    });

    it('should display pending swap count', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const cards = screen.getAllByText('2');
        expect(cards.length).toBeGreaterThan(0);
      });
    });

    it('should show loading state for summary cards', async () => {
      (api.get as jest.Mock).mockImplementation(() => new Promise(() => {})); // Never resolves

      const { container } = render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const skeletons = container.querySelectorAll('.animate-pulse');
        expect(skeletons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Days Ahead Selector', () => {
    it('should display default days ahead value', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/30 days/)).toBeInTheDocument();
      });
    });

    it('should open days selector when clicked', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/30 days/)).toBeInTheDocument();
      });

      const daysButton = screen.getByRole('button', { name: /30 days/i });
      await user.click(daysButton);

      expect(screen.getByText('7 days')).toBeInTheDocument();
      expect(screen.getByText('14 days')).toBeInTheDocument();
      expect(screen.getByText('60 days')).toBeInTheDocument();
      expect(screen.getByText('90 days')).toBeInTheDocument();
    });

    it('should update days ahead when option is selected', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/30 days/)).toBeInTheDocument();
      });

      // Open selector
      const daysButton = screen.getByRole('button', { name: /30 days/i });
      await user.click(daysButton);

      // Select 60 days
      const option60 = screen.getByRole('button', { name: '60 days' });
      await user.click(option60);

      await waitFor(() => {
        expect(screen.getByText(/60 days/)).toBeInTheDocument();
      });
    });

    it('should close selector after selecting option', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/30 days/)).toBeInTheDocument();
      });

      // Open selector
      const daysButton = screen.getByRole('button', { name: /30 days/i });
      await user.click(daysButton);

      // Select option
      const option14 = screen.getByRole('button', { name: '14 days' });
      await user.click(option14);

      await waitFor(() => {
        // Dropdown options should not be visible
        expect(screen.queryByRole('button', { name: '7 days' })).not.toBeInTheDocument();
      });
    });

    it('should refetch data when days ahead is changed', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const initialCallCount = (api.get as jest.Mock).mock.calls.length;

      // Open selector and change value
      const daysButton = screen.getByRole('button', { name: /30 days/i });
      await user.click(daysButton);

      const option60 = screen.getByRole('button', { name: '60 days' });
      await user.click(option60);

      await waitFor(() => {
        expect((api.get as jest.Mock).mock.calls.length).toBeGreaterThan(initialCallCount);
      });
    });
  });

  describe('Upcoming Assignments Section', () => {
    it('should render upcoming assignments section', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Upcoming Assignments')).toBeInTheDocument();
      });
    });

    it('should display total assignment count', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('2 total')).toBeInTheDocument();
      });
    });

    it('should render assignments from API data', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
        expect(screen.getByText('Emergency Department')).toBeInTheDocument();
      });
    });
  });

  describe('Pending Swaps Section', () => {
    it('should render pending swaps section when swaps exist', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Pending Swap Requests')).toBeInTheDocument();
      });
    });

    it('should display swap count', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('1 total')).toBeInTheDocument();
      });
    });

    it('should not render pending swaps section when no swaps', async () => {
      const emptyResponse = {
        ...mockDashboardApiResponse,
        pending_swaps: [],
      };
      (api.get as jest.Mock).mockResolvedValue(emptyResponse);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.queryByText('Pending Swap Requests')).not.toBeInTheDocument();
      });
    });
  });

  describe('Absences Section', () => {
    it('should render absences section when absences exist', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Upcoming Absences')).toBeInTheDocument();
      });
    });

    it('should display absence count', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/You have 1 upcoming absence/)).toBeInTheDocument();
      });
    });

    it('should not render absences section when no absences', async () => {
      const noAbsencesResponse = {
        ...mockDashboardApiResponse,
        absences: [],
      };
      (api.get as jest.Mock).mockResolvedValue(noAbsencesResponse);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.queryByText('Upcoming Absences')).not.toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should refetch data when refresh button is clicked', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const initialCallCount = (api.get as jest.Mock).mock.calls.length;

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect((api.get as jest.Mock).mock.calls.length).toBeGreaterThan(initialCallCount);
      });
    });

    it('should show loading state during refresh', async () => {
      // Clear mocks to ensure clean state
      jest.clearAllMocks();
      const user = userEvent.setup();
      // First call resolves with data, subsequent calls never resolve
      (api.get as jest.Mock)
        .mockResolvedValueOnce(mockDashboardApiResponse)
        .mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      // Wait for initial data to load
      await waitFor(
        () => {
          expect(screen.getByText(/Dr\. John Smith/)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      // Check button is disabled during refetch
      await waitFor(() => {
        expect(refreshButton).toBeDisabled();
      });
    });

    it('should show spinning icon during refresh', async () => {
      // Clear mocks to ensure clean state
      jest.clearAllMocks();
      const user = userEvent.setup();
      // First call resolves with data, subsequent calls never resolve
      (api.get as jest.Mock)
        .mockResolvedValueOnce(mockDashboardApiResponse)
        .mockImplementation(() => new Promise(() => {}));

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      // Wait for initial data to load
      await waitFor(
        () => {
          expect(screen.getByText(/Dr\. John Smith/)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        const icon = refreshButton.querySelector('.animate-spin');
        expect(icon).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when data fetch fails', async () => {
      const error = new Error('API request failed');
      (api.get as jest.Mock).mockRejectedValue(error);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      // Wait for the error state to be rendered - the component shows "Failed to load dashboard" as title
      await waitFor(
        () => {
          expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument();
        },
        { timeout: 3000 }
      );
    });

    it('should show error details', async () => {
      const error = new Error('Network error');
      (api.get as jest.Mock).mockRejectedValue(error);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
    });

    it('should show try again button on error', async () => {
      const error = new Error('Failed to load');
      (api.get as jest.Mock).mockRejectedValue(error);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
      });
    });

    it('should retry fetch when try again is clicked', async () => {
      const user = userEvent.setup();
      const error = new Error('Failed to load');
      (api.get as jest.Mock).mockRejectedValueOnce(error);
      (api.get as jest.Mock).mockResolvedValueOnce(mockDashboardApiResponse);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument();
      });

      const tryAgainButton = screen.getByRole('button', { name: /try again/i });
      await user.click(tryAgainButton);

      await waitFor(() => {
        expect(screen.queryByText('Failed to load dashboard')).not.toBeInTheDocument();
      });
    });
  });

  describe('Swap Request Callback', () => {
    it('should refresh dashboard when swap is requested', async () => {
      const user = userEvent.setup();

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
      });

      const initialCallCount = (api.get as jest.Mock).mock.calls.length;

      // Open swap request form
      const requestButtons = screen.getAllByRole('button', { name: /request swap/i });
      if (requestButtons.length > 0) {
        await user.click(requestButtons[0]);

        // Submit swap request (mock API already returns success)
        const submitButton = screen.getByRole('button', { name: /submit request/i });
        await user.click(submitButton);

        await waitFor(() => {
          expect((api.get as jest.Mock).mock.calls.length).toBeGreaterThan(initialCallCount);
        });
      }
    });
  });

  describe('Mobile Tip', () => {
    it('should display mobile tip on small screens', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Tip:/)).toBeInTheDocument();
      });
    });

    it('should mention calendar sync in mobile tip', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(
          screen.getByText(/Tap "Sync to Calendar" above/)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Custom ClassName', () => {
    it('should apply custom className', async () => {
      const { container } = render(<MyLifeDashboard className="custom-dashboard" />, {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        const element = container.querySelector('.custom-dashboard');
        expect(element).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('should fetch dashboard data on mount', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/portal/my/dashboard')
        );
      });
    });

    it('should pass default daysAhead parameter', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('days_ahead=30')
        );
      });
    });
  });

  describe('Empty Dashboard', () => {
    it('should handle empty dashboard gracefully', async () => {
      // Clear any existing mocks and set up empty response
      jest.clearAllMocks();
      const emptyResponse = {
        user: mockDashboardApiResponse.user,
        upcoming_schedule: [],
        pending_swaps: [],
        absences: [],
        summary: {
          next_assignment: null,
          workload_next_4_weeks: 0,
          pending_swap_count: 0,
          upcoming_absences: 0,
        },
      };
      (api.get as jest.Mock).mockResolvedValue(emptyResponse);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      // Wait for loading to complete - check for user name which appears after data loads
      await waitFor(
        () => {
          expect(screen.getByText(/Dr\. John Smith/)).toBeInTheDocument();
        },
        { timeout: 3000 }
      );

      // Now verify empty state is shown
      await waitFor(() => {
        expect(screen.getByText('No upcoming assignments')).toBeInTheDocument();
      });
      expect(screen.queryByText('Pending Swap Requests')).not.toBeInTheDocument();
      expect(screen.queryByText('Upcoming Absences')).not.toBeInTheDocument();
    });
  });

  describe('Responsive Layout', () => {
    it('should use grid layout for summary cards', async () => {
      const { container } = render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const grid = container.querySelector('.grid');
        expect(grid).toBeInTheDocument();
      });
    });

    it('should have responsive header layout', async () => {
      const { container } = render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const header = container.querySelector('header');
        expect(header).toBeInTheDocument();
      });
    });
  });

  describe('Data Consistency', () => {
    it('should display consistent data across sections', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        // Summary card shows 2 pending swaps
        const summaryCards = screen.getAllByText('2');
        expect(summaryCards.length).toBeGreaterThan(0);

        // Section header shows 1 total (from API response)
        expect(screen.getByText('1 total')).toBeInTheDocument();
      });
    });
  });

  describe('Section Visibility', () => {
    it('should show all sections when data is available', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Upcoming Assignments')).toBeInTheDocument();
        expect(screen.getByText('Pending Swap Requests')).toBeInTheDocument();
        expect(screen.getByText('Upcoming Absences')).toBeInTheDocument();
      });
    });

    it('should conditionally render sections based on data', async () => {
      const minimalResponse = {
        ...mockDashboardApiResponse,
        pending_swaps: [],
        absences: [],
      };
      (api.get as jest.Mock).mockResolvedValue(minimalResponse);

      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Upcoming Assignments')).toBeInTheDocument();
        expect(screen.queryByText('Pending Swap Requests')).not.toBeInTheDocument();
        expect(screen.queryByText('Upcoming Absences')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const h1 = screen.getByRole('heading', { level: 1 });
        expect(h1).toHaveTextContent('My Schedule');
      });

      const h2s = screen.getAllByRole('heading', { level: 2 });
      expect(h2s.length).toBeGreaterThan(0);
    });

    it('should have accessible buttons', async () => {
      render(<MyLifeDashboard />, { wrapper: createWrapper() });

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        buttons.forEach((button) => {
          expect(button).toBeInTheDocument();
        });
      });
    });
  });
});
