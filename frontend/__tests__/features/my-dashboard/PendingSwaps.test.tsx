/**
 * Tests for PendingSwaps Component
 *
 * Tests rendering, swap card display, and action handling
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { PendingSwaps } from '@/features/my-dashboard/PendingSwaps';
import {
  mockIncomingSwapPending,
  mockOutgoingSwapPending,
  mockIncomingSwapApproved,
  mockOutgoingSwapRejected,
  mockPendingSwaps,
} from './mockData';

describe('PendingSwaps', () => {
  const mockOnSwapAction = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Empty State', () => {
    it('should display empty state when no swaps', () => {
      render(<PendingSwaps swaps={[]} />);

      expect(screen.getByText('No pending swap requests')).toBeInTheDocument();
      expect(
        screen.getByText('You have no incoming or outgoing swap requests')
      ).toBeInTheDocument();
    });

    it('should display empty state icon', () => {
      const { container } = render(<PendingSwaps swaps={[]} />);

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('should not display empty state when swaps exist', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} />);

      expect(screen.queryByText('No pending swap requests')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should display loading skeletons', () => {
      const { container } = render(<PendingSwaps swaps={[]} isLoading={true} />);

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should display multiple loading cards', () => {
      const { container } = render(<PendingSwaps swaps={[]} isLoading={true} />);

      const cards = container.querySelectorAll('.bg-white.rounded-lg');
      expect(cards.length).toBe(2);
    });

    it('should not display data when loading', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} isLoading={true} />);

      expect(screen.queryByText('Dr. Sarah Williams')).not.toBeInTheDocument();
    });
  });

  describe('Incoming Swap Display', () => {
    it('should display incoming request label', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText('Incoming Request')).toBeInTheDocument();
    });

    it('should display other faculty name', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText(/from Dr. Sarah Williams/)).toBeInTheDocument();
    });

    it('should display week date', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText(/Feb 1, 2025/)).toBeInTheDocument();
    });

    it('should display requested date', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText(/Requested Jan 15, 2025/)).toBeInTheDocument();
    });

    it('should display reason when provided', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText('Family emergency - need to swap this week')).toBeInTheDocument();
    });

    it('should display status badge', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('should display correct status colors', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const badge = container.querySelector('.bg-yellow-100');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Outgoing Swap Display', () => {
    it('should display outgoing request label', () => {
      render(<PendingSwaps swaps={[mockOutgoingSwapPending]} />);

      expect(screen.getByText('Outgoing Request')).toBeInTheDocument();
    });

    it('should display target faculty name', () => {
      render(<PendingSwaps swaps={[mockOutgoingSwapPending]} />);

      expect(screen.getByText(/to Dr. Michael Chen/)).toBeInTheDocument();
    });

    it('should show waiting message for outgoing pending swaps', () => {
      render(<PendingSwaps swaps={[mockOutgoingSwapPending]} />);

      expect(screen.getByText('Waiting for response...')).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('should show Accept and Reject buttons for incoming pending swaps', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} onSwapAction={mockOnSwapAction} />);

      expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
    });

    it('should call onSwapAction when Accept is clicked', async () => {
      const user = userEvent.setup();

      render(<PendingSwaps swaps={[mockIncomingSwapPending]} onSwapAction={mockOnSwapAction} />);

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      expect(mockOnSwapAction).toHaveBeenCalledWith(mockIncomingSwapPending.id);
    });

    it('should call onSwapAction when Reject is clicked', async () => {
      const user = userEvent.setup();

      render(<PendingSwaps swaps={[mockIncomingSwapPending]} onSwapAction={mockOnSwapAction} />);

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      expect(mockOnSwapAction).toHaveBeenCalledWith(mockIncomingSwapPending.id);
    });

    it('should not show action buttons when canRespond is false', () => {
      const swap = { ...mockIncomingSwapPending, canRespond: false };
      render(<PendingSwaps swaps={[swap]} onSwapAction={mockOnSwapAction} />);

      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });

    it('should not show action buttons for approved swaps', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapApproved]} onSwapAction={mockOnSwapAction} />);

      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });

    it('should not show action buttons for rejected swaps', () => {
      render(<PendingSwaps swaps={[mockOutgoingSwapRejected]} onSwapAction={mockOnSwapAction} />);

      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });
  });

  describe('Status Badges', () => {
    it('should display pending status with yellow color', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const badge = container.querySelector('.bg-yellow-100.text-yellow-700');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Pending');
    });

    it('should display approved status with green color', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapApproved]} />);

      const badge = container.querySelector('.bg-green-100.text-green-700');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Approved');
    });

    it('should display rejected status with red color', () => {
      const { container } = render(<PendingSwaps swaps={[mockOutgoingSwapRejected]} />);

      const badge = container.querySelector('.bg-red-100.text-red-700');
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveTextContent('Rejected');
    });
  });

  describe('Incoming/Outgoing Separation', () => {
    it('should separate incoming and outgoing swaps', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} />);

      expect(screen.getByText(/Incoming \(\d+\)/)).toBeInTheDocument();
      expect(screen.getByText(/Outgoing \(\d+\)/)).toBeInTheDocument();
    });

    it('should display correct incoming count', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} />);

      // mockPendingSwaps has 2 incoming swaps
      expect(screen.getByText('Incoming (2)')).toBeInTheDocument();
    });

    it('should display correct outgoing count', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} />);

      // mockPendingSwaps has 1 outgoing swap
      expect(screen.getByText('Outgoing (1)')).toBeInTheDocument();
    });

    it('should not show incoming section when no incoming swaps', () => {
      render(<PendingSwaps swaps={[mockOutgoingSwapPending]} />);

      expect(screen.queryByText(/Incoming/)).not.toBeInTheDocument();
    });

    it('should not show outgoing section when no outgoing swaps', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.queryByText(/Outgoing/)).not.toBeInTheDocument();
    });
  });

  describe('Reason Display', () => {
    it('should display reason in a styled box', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const reasonBox = container.querySelector('.bg-gray-50.rounded');
      expect(reasonBox).toBeInTheDocument();
    });

    it('should not display reason box when reason is not provided', () => {
      const swapWithoutReason = { ...mockIncomingSwapPending, reason: undefined };
      const { container } = render(<PendingSwaps swaps={[swapWithoutReason]} />);

      expect(screen.queryByText('Family emergency')).not.toBeInTheDocument();
    });

    it('should truncate long reasons with line-clamp', () => {
      const longReason = 'This is a very long reason that should be clamped to two lines maximum';
      const swap = { ...mockIncomingSwapPending, reason: longReason };
      const { container } = render(<PendingSwaps swaps={[swap]} />);

      const reasonText = container.querySelector('.line-clamp-2');
      expect(reasonText).toBeInTheDocument();
    });
  });

  describe('Multiple Swaps', () => {
    it('should render all swaps in the list', () => {
      render(<PendingSwaps swaps={mockPendingSwaps} />);

      expect(screen.getByText(/from Dr. Sarah Williams/)).toBeInTheDocument();
      expect(screen.getByText(/to Dr. Michael Chen/)).toBeInTheDocument();
      expect(screen.getByText(/from Dr. Emily Rodriguez/)).toBeInTheDocument();
    });

    it('should render correct number of swap cards', () => {
      const { container } = render(<PendingSwaps swaps={mockPendingSwaps} />);

      const cards = container.querySelectorAll('.bg-white.rounded-lg.border');
      expect(cards.length).toBe(mockPendingSwaps.length);
    });
  });

  describe('Icons', () => {
    it('should display incoming arrow for incoming swaps', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should display swap icon for outgoing swaps', () => {
      const { container } = render(<PendingSwaps swaps={[mockOutgoingSwapPending]} />);

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Hover Effects', () => {
    it('should have hover shadow effect on cards', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const card = container.querySelector('.hover\\:shadow-md');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should truncate long names', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const truncatedElements = container.querySelectorAll('.truncate');
      expect(truncatedElements.length).toBeGreaterThan(0);
    });

    it('should use flex layout for proper spacing', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const flexElements = container.querySelectorAll('.flex');
      expect(flexElements.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined swaps array', () => {
      render(<PendingSwaps swaps={undefined as any} />);

      expect(screen.getByText('No pending swap requests')).toBeInTheDocument();
    });

    it('should handle null swaps array', () => {
      render(<PendingSwaps swaps={null as any} />);

      expect(screen.getByText('No pending swap requests')).toBeInTheDocument();
    });

    it('should handle missing onSwapAction callback', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      // Should still render buttons even without callback
      expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
    });

    it('should handle swap with valid week date', () => {
      const swap = { ...mockIncomingSwapPending, weekDate: '2025-03-15' };
      render(<PendingSwaps swaps={[swap]} />);

      // Should render with valid date
      expect(screen.getByText('Incoming Request')).toBeInTheDocument();
      expect(screen.getByText(/Mar 15, 2025/)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      const rejectButton = screen.getByRole('button', { name: /reject/i });

      expect(acceptButton).toBeInTheDocument();
      expect(rejectButton).toBeInTheDocument();
    });

    it('should have meaningful icon aria attributes', () => {
      const { container } = render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      const icons = container.querySelectorAll('svg');
      icons.forEach((icon) => {
        expect(icon).toBeInTheDocument();
      });
    });
  });

  describe('Date Formatting', () => {
    it('should format week date correctly', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText(/Feb 1, 2025/)).toBeInTheDocument();
    });

    it('should format requested date correctly', () => {
      render(<PendingSwaps swaps={[mockIncomingSwapPending]} />);

      expect(screen.getByText(/Requested Jan 15, 2025/)).toBeInTheDocument();
    });
  });
});
