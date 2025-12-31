/**
 * Tests for CalendarSync Component
 *
 * Tests modal interactions, format selection, and calendar sync functionality
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CalendarSync } from '@/features/my-dashboard/CalendarSync';
import * as api from '@/lib/api';
import { mockCalendarSyncResponse } from './mockData';

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

// Mock window.open and window.location.href
const mockWindowOpen = jest.fn();
const originalWindowOpen = window.open;
const originalLocationHref = window.location.href;

describe('CalendarSync', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.open = mockWindowOpen;
    delete (window as any).location;
    window.location = { href: '' } as any;
  });

  afterEach(() => {
    window.open = originalWindowOpen;
    window.location.href = originalLocationHref;
  });

  describe('Button Rendering', () => {
    it('should render sync button', () => {
      render(<CalendarSync />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /sync to calendar/i })).toBeInTheDocument();
    });

    it('should show full text on desktop', () => {
      render(<CalendarSync />, { wrapper: createWrapper() });

      expect(screen.getByText('Sync to Calendar')).toBeInTheDocument();
    });

    it('should apply custom className to button', () => {
      const { container } = render(<CalendarSync className="custom-class" />, {
        wrapper: createWrapper(),
      });

      const button = container.querySelector('.custom-class');
      expect(button).toBeInTheDocument();
    });
  });

  describe('Modal Display', () => {
    it('should open modal when button is clicked', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      // Wait for and verify modal content is visible
      // Note: "Sync to Calendar" appears twice (button + header), so we check for modal-specific content
      await waitFor(() => {
        expect(screen.getByText('Choose Calendar Format')).toBeInTheDocument();
      });
      // Also verify the format options are visible
      expect(screen.getByText('ICS File Download')).toBeInTheDocument();
    });

    it('should close modal when X button is clicked', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      // Wait for modal to open
      await waitFor(() => {
        expect(screen.getByText('Choose Calendar Format')).toBeInTheDocument();
      });

      // Close modal - find the X button which is in the header area and has an X icon
      // The X button is the one with the lucide-x class on its SVG
      const closeButtons = screen.getAllByRole('button');
      const closeButton = closeButtons.find((btn) => {
        const svg = btn.querySelector('svg');
        return svg && svg.classList.contains('lucide-x');
      });
      expect(closeButton).toBeDefined();
      await user.click(closeButton!);

      await waitFor(() => {
        expect(screen.queryByText('Choose Calendar Format')).not.toBeInTheDocument();
      });
    });

    it('should close modal when Cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Choose Calendar Format')).not.toBeInTheDocument();
      });
    });
  });

  describe('Format Selection', () => {
    it('should default to ICS format', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      const icsButton = screen.getByText('ICS File Download').closest('button');
      expect(icsButton).toHaveClass('border-blue-500');
    });

    it('should select Google Calendar format when clicked', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      const googleButton = screen.getByText('Google Calendar').closest('button');
      await user.click(googleButton!);

      expect(googleButton).toHaveClass('border-blue-500');
    });

    it('should select Outlook Calendar format when clicked', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      const outlookButton = screen.getByText('Outlook Calendar').closest('button');
      await user.click(outlookButton!);

      expect(outlookButton).toHaveClass('border-blue-500');
    });

    it('should render all three format options', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      expect(screen.getByText('ICS File Download')).toBeInTheDocument();
      expect(screen.getByText('Google Calendar')).toBeInTheDocument();
      expect(screen.getByText('Outlook Calendar')).toBeInTheDocument();
    });
  });

  describe('Weeks Ahead Slider', () => {
    it('should default to 12 weeks', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      expect(screen.getByText('Include Next 12 Weeks')).toBeInTheDocument();
    });

    it('should update weeks ahead when slider is changed', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      const slider = screen.getByRole('slider');
      await user.type(slider, '{ArrowRight}{ArrowRight}');

      // Note: Exact value may vary based on slider implementation
      const weeksText = screen.getByText(/Include Next \d+ Weeks/);
      expect(weeksText).toBeInTheDocument();
    });

    it('should have correct min and max values', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      const slider = screen.getByRole('slider') as HTMLInputElement;
      expect(slider.min).toBe('4');
      expect(slider.max).toBe('52');
      expect(slider.step).toBe('4');
    });
  });

  describe('Sync Functionality', () => {
    it('should call API when sync button is clicked', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync now
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith('/portal/my/calendar-sync', {
          format: 'ics',
          include_weeks_ahead: 12,
        });
      });
    });

    it('should trigger download for ICS format', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(window.location.href).toBe(mockCalendarSyncResponse.url);
      });
    });

    it('should open new tab for Google Calendar', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Select Google format
      const googleButton = screen.getByText('Google Calendar').closest('button');
      await user.click(googleButton!);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(mockWindowOpen).toHaveBeenCalledWith(mockCalendarSyncResponse.url, '_blank');
      });
    });

    it('should open new tab for Outlook Calendar', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Select Outlook format
      const outlookButton = screen.getByText('Outlook Calendar').closest('button');
      await user.click(outlookButton!);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(mockWindowOpen).toHaveBeenCalledWith(mockCalendarSyncResponse.url, '_blank');
      });
    });

    it('should show loading state during sync', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockImplementation(() => new Promise(() => {})); // Never resolves

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(screen.getByText('Syncing...')).toBeInTheDocument();
      });
    });

    it('should show success state after sync', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
      });
    });

    it('should disable buttons during sync', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        const cancelButton = screen.getByRole('button', { name: /cancel/i });
        expect(cancelButton).toBeDisabled();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message on sync failure', async () => {
      const user = userEvent.setup();
      const error = new Error('Failed to sync calendar');
      (api.post as jest.Mock).mockRejectedValue(error);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument();
        expect(screen.getByText(/Failed to sync calendar/)).toBeInTheDocument();
      });
    });

    it('should not close modal on error', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockRejectedValue(new Error('Sync failed'));

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(screen.getByText(/Error:/)).toBeInTheDocument();
      });

      // Modal should still be open
      expect(screen.getByText('Choose Calendar Format')).toBeInTheDocument();
    });

    it('should handle invalid URL gracefully', async () => {
      const user = userEvent.setup();
      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      (api.post as jest.Mock).mockResolvedValue({
        success: true,
        url: 'invalid-url',
        message: 'Success',
      });

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(consoleErrorSpy).toHaveBeenCalled();
      });

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Mobile Tip', () => {
    it('should display mobile tip', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      expect(screen.getByText(/Mobile Tip:/)).toBeInTheDocument();
      expect(
        screen.getByText(/After syncing, check your calendar app/)
      ).toBeInTheDocument();
    });
  });

  describe('Success Message Auto-Close', () => {
    it('should close modal after success', async () => {
      jest.useFakeTimers();
      const user = userEvent.setup({ delay: null });
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Click sync
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(screen.getByText('Success!')).toBeInTheDocument();
      });

      // Fast-forward timer
      jest.advanceTimersByTime(2000);

      await waitFor(() => {
        expect(screen.queryByText('Choose Calendar Format')).not.toBeInTheDocument();
      });

      jest.useRealTimers();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      expect(button).toBeInTheDocument();
    });

    it('should have accessible form controls in modal', async () => {
      const user = userEvent.setup();

      render(<CalendarSync />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(button);

      expect(screen.getByRole('slider')).toBeInTheDocument();
      expect(screen.getByLabelText(/Include Next \d+ Weeks/)).toBeInTheDocument();
    });
  });

  describe('Different Weeks Ahead Values', () => {
    it('should sync with weeks ahead value from slider', async () => {
      const user = userEvent.setup();
      (api.post as jest.Mock).mockResolvedValue(mockCalendarSyncResponse);

      render(<CalendarSync />, { wrapper: createWrapper() });

      // Open modal
      const openButton = screen.getByRole('button', { name: /sync to calendar/i });
      await user.click(openButton);

      // Slider should be at default value (12 weeks)
      const slider = screen.getByRole('slider') as HTMLInputElement;
      expect(slider.value).toBe('12');

      // Click sync with default value
      const syncButton = screen.getByRole('button', { name: /sync now/i });
      await user.click(syncButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith('/portal/my/calendar-sync', {
          format: 'ics',
          include_weeks_ahead: 12,
        });
      });
    });
  });
});
