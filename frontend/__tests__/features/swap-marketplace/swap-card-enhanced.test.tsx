/**
 * Enhanced Tests for SwapRequestCard Component
 *
 * Comprehensive tests covering all swap types, states, action flows,
 * error handling, and edge cases.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapRequestCard } from '@/features/swap-marketplace/SwapRequestCard';
import { SwapStatus, SwapType } from '@/features/swap-marketplace/types';
import * as hooks from '@/features/swap-marketplace/hooks';
import {
  mockSwapRequestIncoming,
  mockSwapRequestOutgoing,
  mockSwapRequestApproved,
  mockSwapRequestAbsorb,
  mockSwapRequestRejected,
  mockMarketplaceEntry1,
  mockMarketplaceEntry2,
} from './mockData';

// Mock the hooks
jest.mock('@/features/swap-marketplace/hooks');

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

describe('SwapRequestCard - Enhanced Tests', () => {
  const mockOnActionComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isError: false,
      error: null,
    });

    (hooks.useRejectSwap as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isError: false,
      error: null,
    });

    (hooks.useCancelSwap as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isError: false,
      error: null,
    });
  });

  // ============================================================================
  // Different Swap States
  // ============================================================================

  describe('Swap Status Display', () => {
    it('should display pending status badge correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const badge = screen.getByText('Pending');
      expect(badge).toBeInTheDocument();
    });

    it('should display approved status badge correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestApproved} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const badge = screen.getByText('Approved');
      expect(badge).toBeInTheDocument();
    });

    it('should display rejected status badge correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestRejected} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const badge = screen.getByText('Rejected');
      expect(badge).toBeInTheDocument();
    });

    it('should display executed status badge for completed swaps', () => {
      const executedSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.EXECUTED,
        executedAt: '2025-01-12T10:00:00Z',
      };

      render(
        <SwapRequestCard swap={executedSwap} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Executed')).toBeInTheDocument();
    });

    it('should display cancelled status badge for cancelled swaps', () => {
      const cancelledSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.CANCELLED,
      };

      render(
        <SwapRequestCard swap={cancelledSwap} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Different Swap Types
  // ============================================================================

  describe('Swap Type Display', () => {
    it('should display one-to-one swap type correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('One-to-One Swap')).toBeInTheDocument();
    });

    it('should display absorb swap type correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestAbsorb} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Absorb Week')).toBeInTheDocument();
    });

    it('should show both faculty for one-to-one swap', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
    });

    it('should only show source faculty for absorb swap', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestAbsorb} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      // Should not show target faculty or arrow for absorb type
      const arrows = screen.queryAllByRole('img', { hidden: true }); // SVG icons
      const arrowRight = arrows.find(el => el.parentElement?.classList.contains('lucide-arrow-right'));
      expect(arrowRight).toBeUndefined();
    });
  });

  // ============================================================================
  // Marketplace Entry Display
  // ============================================================================

  describe('Marketplace Entry Features', () => {
    it('should display marketplace entry without reason', () => {
      const entryNoReason = { ...mockMarketplaceEntry2, reason: undefined };
      render(
        <SwapRequestCard marketplaceEntry={entryNoReason} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. Michael Chen')).toBeInTheDocument();
      // Reason section should not be present - just check the entry rendered
      expect(screen.queryByText(/reason:/i)).not.toBeInTheDocument();
    });

    it('should display marketplace entry with expiration', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. Sarah Williams')).toBeInTheDocument();
      expect(screen.getByText(/Jun 1, 2025/)).toBeInTheDocument();
    });

    it('should have accessible aria-label on view details button', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByLabelText(/view details for swap from/i);
      expect(button).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Action Flows with Notes
  // ============================================================================

  describe('Accept Flow with Notes', () => {
    it('should submit accept with notes successfully', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Click accept button
      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      // Type notes
      const notesTextarea = screen.getByPlaceholderText(/add optional notes for accepting/i);
      await user.type(notesTextarea, 'Happy to help out');

      // Confirm
      const confirmButton = screen.getByRole('button', { name: /confirm accept/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({ notes: 'Happy to help out' });
        expect(mockOnActionComplete).toHaveBeenCalled();
      });
    });

    it('should submit accept without notes', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      // Don't type anything, just confirm
      const confirmButton = screen.getByRole('button', { name: /confirm accept/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({ notes: undefined });
      });
    });

    it('should clear notes when canceling accept', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Click accept to enter action mode
      const acceptButton = screen.getByRole('button', { name: /accept swap request/i });
      await user.click(acceptButton);

      const notesTextarea = screen.getByPlaceholderText(/add optional notes for accepting/i);
      await user.type(notesTextarea, 'Some notes');

      // Click cancel to exit action mode
      const cancelActionButton = screen.getByRole('button', { name: /cancel action/i });
      await user.click(cancelActionButton);

      // Re-enter accept mode - need to re-query the button since UI changed
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /accept swap request/i })).toBeInTheDocument();
      });
      const newAcceptButton = screen.getByRole('button', { name: /accept swap request/i });
      await user.click(newAcceptButton);

      const freshTextarea = screen.getByPlaceholderText(/add optional notes for accepting/i);
      expect(freshTextarea).toHaveValue('');
    });
  });

  describe('Reject Flow with Notes', () => {
    it('should submit reject with notes successfully', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      const notesTextarea = screen.getByPlaceholderText(/add optional notes for rejecting/i);
      await user.type(notesTextarea, 'Already have plans that week');

      const confirmButton = screen.getByRole('button', { name: /confirm reject/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({ notes: 'Already have plans that week' });
        expect(mockOnActionComplete).toHaveBeenCalled();
      });
    });

    it('should submit reject without notes', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      const confirmButton = screen.getByRole('button', { name: /confirm reject/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({ notes: undefined });
      });
    });
  });

  // ============================================================================
  // Cancel Flow
  // ============================================================================

  describe('Cancel Confirmation Flow', () => {
    it('should not cancel if user cancels confirmation dialog', async () => {
      const user = userEvent.setup();
      const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false);
      const mockMutateAsync = jest.fn();

      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockConfirm).toHaveBeenCalled();
      expect(mockMutateAsync).not.toHaveBeenCalled();

      mockConfirm.mockRestore();
    });

    it('should cancel if user confirms dialog', async () => {
      const user = userEvent.setup();
      const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(true);
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
        expect(mockOnActionComplete).toHaveBeenCalled();
      });

      mockConfirm.mockRestore();
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('Mutation Errors', () => {
    it('should display accept error message', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockRejectedValue(new Error('ACGME violation'));

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: { message: 'ACGME violation' },
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('ACGME violation')).toBeInTheDocument();
    });

    it('should display reject error message', async () => {
      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
        isError: true,
        error: { message: 'Network error' },
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should display cancel error message', async () => {
      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: false,
        isError: true,
        error: { message: 'Cannot cancel swap' },
      });

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Cannot cancel swap')).toBeInTheDocument();
    });

    it('should not call onActionComplete if mutation fails', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockRejectedValue(new Error('Failed'));

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      const confirmButton = screen.getByRole('button', { name: /confirm accept/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalled();
      });

      // Should not call onActionComplete due to error
      expect(mockOnActionComplete).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Loading States
  // ============================================================================

  describe('Loading States', () => {
    it('should show loading state for accept button', () => {
      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: true,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should show loading state for reject button', () => {
      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: true,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });

    it('should show loading state for cancel button', () => {
      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: true,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Cancelling...')).toBeInTheDocument();
    });

    it('should disable buttons during any mutation', () => {
      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: jest.fn(),
        isPending: true,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have accessible button labels', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /accept swap request/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reject swap request/i })).toBeInTheDocument();
    });

    it('should have accessible cancel button label', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /cancel swap request/i })).toBeInTheDocument();
    });

    it('should have accessible action confirmation labels', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      expect(screen.getByRole('button', { name: /confirm accept swap request/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel action/i })).toBeInTheDocument();
    });

    it('should have proper ARIA attributes on icons', () => {
      const { container } = render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // SVG icons from lucide-react should have aria-hidden="true"
      const icons = container.querySelectorAll('svg[aria-hidden="true"]');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Edge Cases
  // ============================================================================

  describe('Edge Cases', () => {
    it('should handle swap without target week', () => {
      const swapNoTargetWeek = {
        ...mockSwapRequestIncoming,
        targetWeek: undefined,
      };

      render(
        <SwapRequestCard swap={swapNoTargetWeek} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('should handle swap without target faculty name', () => {
      const swapNoTargetName = {
        ...mockSwapRequestIncoming,
        targetFacultyName: undefined,
      };

      render(
        <SwapRequestCard swap={swapNoTargetName} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('should handle swap without reason', () => {
      const swapNoReason = {
        ...mockSwapRequestIncoming,
        reason: undefined,
      };

      render(
        <SwapRequestCard swap={swapNoReason} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Should not display reason section
      expect(screen.queryByText(/family emergency/i)).not.toBeInTheDocument();
    });

    it('should handle swap without notes', () => {
      const swapNoNotes = {
        ...mockSwapRequestRejected,
        notes: undefined,
      };

      render(
        <SwapRequestCard swap={swapNoNotes} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. Bob Johnson')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Date Formatting
  // ============================================================================

  describe('Date Formatting', () => {
    it('should format source week correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Jan 15, 2025/i)).toBeInTheDocument();
    });

    it('should format target week correctly for one-to-one swap', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Jan 22, 2025/i)).toBeInTheDocument();
    });

    it('should format requested timestamp correctly', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Requested Jan 10, 2025/i)).toBeInTheDocument();
    });
  });
});
