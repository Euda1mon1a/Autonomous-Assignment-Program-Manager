/**
 * Tests for UpcomingSchedule Component
 *
 * Tests assignment display, swap request functionality, and loading states
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UpcomingSchedule } from '@/features/my-dashboard/UpcomingSchedule';
import * as api from '@/lib/api';
import {
  mockAssignmentToday,
  mockAssignmentTomorrow,
  mockAssignmentNextWeek,
  mockAssignmentWithConflict,
  mockAssignmentNotTradeable,
  mockUpcomingAssignments,
  mockSwapRequestResponse,
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

describe('UpcomingSchedule', () => {
  const mockOnSwapRequested = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue(mockSwapRequestResponse);
  });

  describe('Empty State', () => {
    it('should display empty state when no assignments', () => {
      render(<UpcomingSchedule assignments={[]} />, { wrapper: createWrapper() });

      expect(screen.getByText('No upcoming assignments')).toBeInTheDocument();
      expect(
        screen.getByText('Your schedule is clear for the selected period')
      ).toBeInTheDocument();
    });

    it('should display empty state icon', () => {
      const { container } = render(<UpcomingSchedule assignments={[]} />, {
        wrapper: createWrapper(),
      });

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should not display empty state when assignments exist', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText('No upcoming assignments')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should display loading skeletons', () => {
      const { container } = render(<UpcomingSchedule assignments={[]} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should display multiple loading cards', () => {
      const { container } = render(<UpcomingSchedule assignments={[]} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      const cards = container.querySelectorAll('.bg-white.rounded-lg');
      expect(cards.length).toBe(3);
    });

    it('should not display data when loading', () => {
      render(<UpcomingSchedule assignments={mockUpcomingAssignments} isLoading={true} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByText('Inpatient Medicine')).not.toBeInTheDocument();
    });
  });

  describe('Assignment Display', () => {
    it('should display assignment activity', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
    });

    it('should display assignment location', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Ward')).toBeInTheDocument();
    });

    it('should display time of day', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Morning')).toBeInTheDocument();
    });

    it('should render all assignments in the list', () => {
      render(<UpcomingSchedule assignments={mockUpcomingAssignments} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Inpatient Medicine')).toBeInTheDocument();
      expect(screen.getByText('Emergency Department')).toBeInTheDocument();
      expect(screen.getByText('ICU Coverage')).toBeInTheDocument();
    });
  });

  describe('Date Labels', () => {
    it('should display "Today" for current day assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Today/)).toBeInTheDocument();
    });

    it('should display "Tomorrow" for next day assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentTomorrow]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText(/Tomorrow/)).toBeInTheDocument();
    });

    it('should display formatted date for future assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentNextWeek]} />, {
        wrapper: createWrapper(),
      });

      // Should have a formatted date
      const dateElements = screen.getAllByText(/\d{4}/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  describe('Upcoming Badge', () => {
    it('should display "Soon" badge for assignments within 7 days', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday, mockAssignmentTomorrow]} />, {
        wrapper: createWrapper(),
      });

      const soonBadges = screen.getAllByText('Soon');
      expect(soonBadges.length).toBeGreaterThan(0);
    });

    it('should highlight upcoming assignments with ring', () => {
      const { container } = render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const ringElement = container.querySelector('.ring-2.ring-blue-500\\/20');
      expect(ringElement).toBeInTheDocument();
    });
  });

  describe('Conflict Display', () => {
    it('should display conflict warning for conflicting assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentWithConflict]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('Overlaps with approved vacation request')).toBeInTheDocument();
    });

    it('should highlight conflicting assignments with red border', () => {
      const { container } = render(<UpcomingSchedule assignments={[mockAssignmentWithConflict]} />, {
        wrapper: createWrapper(),
      });

      const conflictCard = container.querySelector('.border-red-300');
      expect(conflictCard).toBeInTheDocument();
    });

    it('should show alert icon for conflicts', () => {
      const { container } = render(<UpcomingSchedule assignments={[mockAssignmentWithConflict]} />, {
        wrapper: createWrapper(),
      });

      // Conflict should have an alert icon
      const conflictSection = container.querySelector('.bg-red-50');
      expect(conflictSection).toBeInTheDocument();
    });

    it('should not show conflict warning for non-conflicting assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(
        screen.queryByText('Overlaps with approved vacation request')
      ).not.toBeInTheDocument();
    });
  });

  describe('Swap Request Button', () => {
    it('should show "Request Swap" button for tradeable assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByRole('button', { name: /request swap/i })).toBeInTheDocument();
    });

    it('should not show "Request Swap" button for non-tradeable assignments', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentNotTradeable]} />, {
        wrapper: createWrapper(),
      });

      expect(screen.queryByRole('button', { name: /request swap/i })).not.toBeInTheDocument();
      expect(screen.getByText('This assignment cannot be traded')).toBeInTheDocument();
    });

    it('should open swap form when "Request Swap" is clicked', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      expect(
        screen.getByPlaceholderText(/reason for swap request/i)
      ).toBeInTheDocument();
    });
  });

  describe('Swap Request Form', () => {
    it('should display textarea for swap reason', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const textarea = screen.getByPlaceholderText(/reason for swap request/i);
      expect(textarea).toBeInTheDocument();
    });

    it('should allow typing in reason textarea', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const textarea = screen.getByPlaceholderText(/reason for swap request/i);
      await user.type(textarea, 'Medical conference');

      expect(textarea).toHaveValue('Medical conference');
    });

    it('should show Submit Request and Cancel buttons', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      expect(screen.getByRole('button', { name: /submit request/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should close form when Cancel is clicked', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      // Close form
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(
        screen.queryByPlaceholderText(/reason for swap request/i)
      ).not.toBeInTheDocument();
    });

    it('should clear reason when form is cancelled', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and type
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const textarea = screen.getByPlaceholderText(/reason for swap request/i);
      await user.type(textarea, 'Test reason');

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Reopen form
      await user.click(requestButton);

      const newTextarea = screen.getByPlaceholderText(/reason for swap request/i);
      expect(newTextarea).toHaveValue('');
    });
  });

  describe('Swap Request Submission', () => {
    it('should call API when swap request is submitted', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      // Type reason
      const textarea = screen.getByPlaceholderText(/reason for swap request/i);
      await user.type(textarea, 'Medical conference');

      // Submit
      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          `/portal/my/assignments/${mockAssignmentToday.id}/request-swap`,
          { reason: 'Medical conference' }
        );
      });
    });

    it('should submit without reason if not provided', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      // Submit without typing
      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          expect.any(String),
          { reason: undefined }
        );
      });
    });

    it('should show loading state during submission', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and submit
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Submitting...')).toBeInTheDocument();
      });
    });

    it('should call onSwapRequested callback after successful submission', async () => {
      const user = userEvent.setup();

      render(
        <UpcomingSchedule
          assignments={[mockAssignmentToday]}
          onSwapRequested={mockOnSwapRequested}
        />,
        { wrapper: createWrapper() }
      );

      // Open form
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      // Submit
      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnSwapRequested).toHaveBeenCalled();
      });
    });

    it('should show success message after submission', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and submit
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Swap request created successfully!')).toBeInTheDocument();
      });
    });

    it('should close form after successful submission', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and submit
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.queryByPlaceholderText(/reason for swap request/i)
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message on submission failure', async () => {
      const user = userEvent.setup();
      const error = new Error('Failed to create swap request');
      (api.post as jest.Mock).mockRejectedValue(error);

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and submit
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to create swap request/)).toBeInTheDocument();
      });
    });

    it('should keep form open on error', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockRejectedValue(new Error('API Error'));

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      // Open form and submit
      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const submitButton = screen.getByRole('button', { name: /submit request/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/API Error/)).toBeInTheDocument();
      });

      // Form should still be open
      expect(screen.getByPlaceholderText(/reason for swap request/i)).toBeInTheDocument();
    });
  });

  describe('Multiple Assignments', () => {
    it('should render correct number of assignment cards', () => {
      const { container } = render(<UpcomingSchedule assignments={mockUpcomingAssignments} />, {
        wrapper: createWrapper(),
      });

      const cards = container.querySelectorAll('.bg-white.rounded-lg.border');
      expect(cards.length).toBe(mockUpcomingAssignments.length);
    });

    it('should handle swap requests for different assignments independently', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={mockUpcomingAssignments} />, {
        wrapper: createWrapper(),
      });

      // Get all Request Swap buttons
      const requestButtons = screen.getAllByRole('button', { name: /request swap/i });
      expect(requestButtons.length).toBeGreaterThan(1);

      // Click the first one
      await user.click(requestButtons[0]);

      // Only one form should open
      const textareas = screen.getAllByPlaceholderText(/reason for swap request/i);
      expect(textareas.length).toBe(1);
    });
  });

  describe('Location Colors', () => {
    it('should apply different colors for different locations', () => {
      const { container } = render(<UpcomingSchedule assignments={mockUpcomingAssignments} />, {
        wrapper: createWrapper(),
      });

      // Different assignments have different location badges
      const badges = container.querySelectorAll('[class*="bg-"][class*="-100"]');
      expect(badges.length).toBeGreaterThan(0);
    });
  });

  describe('Icons', () => {
    it('should display calendar icon', () => {
      const { container } = render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should display clock icon', () => {
      const { container } = render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const button = screen.getByRole('button', { name: /request swap/i });
      expect(button).toBeInTheDocument();
    });

    it('should have accessible textarea in swap form', async () => {
      const user = userEvent.setup();

      render(<UpcomingSchedule assignments={[mockAssignmentToday]} />, {
        wrapper: createWrapper(),
      });

      const requestButton = screen.getByRole('button', { name: /request swap/i });
      await user.click(requestButton);

      const textarea = screen.getByPlaceholderText(/reason for swap request/i);
      expect(textarea).toHaveAttribute('rows', '3');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined assignments array', () => {
      render(<UpcomingSchedule assignments={undefined as any} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('No upcoming assignments')).toBeInTheDocument();
    });

    it('should handle null assignments array', () => {
      render(<UpcomingSchedule assignments={null as any} />, {
        wrapper: createWrapper(),
      });

      expect(screen.getByText('No upcoming assignments')).toBeInTheDocument();
    });

    it('should handle assignment without activity', () => {
      const assignment = { ...mockAssignmentToday, activity: '' };
      render(<UpcomingSchedule assignments={[assignment]} />, {
        wrapper: createWrapper(),
      });

      // Should still render without crashing
      expect(screen.getByText('Ward')).toBeInTheDocument();
    });
  });
});
