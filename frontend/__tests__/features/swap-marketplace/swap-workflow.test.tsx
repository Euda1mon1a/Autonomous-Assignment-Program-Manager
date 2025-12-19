/**
 * Integration Workflow Tests for Swap Marketplace
 *
 * Tests complete user workflows from creation to resolution,
 * including Create → Review → Approve, Create → Review → Reject,
 * and Cancel flows.
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapRequestForm } from '@/features/swap-marketplace/SwapRequestForm';
import { SwapRequestCard } from '@/features/swap-marketplace/SwapRequestCard';
import { MySwapRequests } from '@/features/swap-marketplace/MySwapRequests';
import * as hooks from '@/features/swap-marketplace/hooks';
import {
  mockAvailableWeeks,
  mockFacultyMembers,
  mockCreateSwapResponse,
  mockSwapRequestIncoming,
  mockSwapRequestOutgoing,
  mockSwapRespondResponse,
  mockMySwapsResponse,
} from './mockData';
import { SwapStatus } from '@/features/swap-marketplace/types';

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

describe('Swap Workflow Integration Tests', () => {
  const mockOnSuccess = jest.fn();
  const mockOnActionComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    (hooks.useAvailableWeeks as jest.Mock).mockReturnValue({
      data: mockAvailableWeeks,
      isLoading: false,
      error: null,
    });

    (hooks.useFacultyMembers as jest.Mock).mockReturnValue({
      data: mockFacultyMembers,
      isLoading: false,
      error: null,
    });

    (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      isSuccess: false,
      data: null,
      error: null,
    });

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

    (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
      data: mockMySwapsResponse,
      isLoading: false,
      error: null,
    });
  });

  // ============================================================================
  // Create → Review → Approve Flow
  // ============================================================================

  describe('Create → Review → Approve Flow', () => {
    it('should complete full approval workflow', async () => {
      const user = userEvent.setup();
      const mockCreateMutate = jest.fn().mockResolvedValue(mockCreateSwapResponse);
      const mockAcceptMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateMutate,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockAcceptMutate,
        isPending: false,
        isError: false,
        error: null,
      });

      // Step 1: Create swap request
      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getByLabelText(/week to offload/i);
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const reasonTextarea = screen.getByLabelText(/reason \/ notes/i);
      await user.type(reasonTextarea, 'Conference attendance');

      const createButton = screen.getByRole('button', { name: /create request/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(mockCreateMutate).toHaveBeenCalledWith({
          weekToOffload: mockAvailableWeeks[0].date,
          reason: 'Conference attendance',
          autoFindCandidates: true,
          preferredTargetFacultyId: undefined,
        });
      });

      // Step 2: Review incoming swap request
      const { unmount } = render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('One-to-One Swap')).toBeInTheDocument();
      expect(screen.getByText('Incoming Request')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();

      // Step 3: Accept the swap request
      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      const notesTextarea = screen.getByPlaceholderText(/add optional notes for accepting/i);
      await user.type(notesTextarea, 'Happy to help');

      const confirmButton = screen.getByRole('button', { name: /confirm accept/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockAcceptMutate).toHaveBeenCalledWith({ notes: 'Happy to help' });
        expect(mockOnActionComplete).toHaveBeenCalled();
      });

      unmount();
    });

    it('should show approved status after acceptance', async () => {
      const approvedSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.APPROVED,
        approvedAt: '2025-01-11T12:00:00Z',
      };

      render(
        <SwapRequestCard swap={approvedSwap} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Approved')).toBeInTheDocument();
      // Should not show action buttons
      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });

    it('should transition from pending to approved in MySwapRequests', async () => {
      const { rerender } = render(<MySwapRequests />, { wrapper: createWrapper() });

      // Initially pending
      expect(screen.getByText(/pending/i)).toBeInTheDocument();

      // After approval
      const updatedResponse = {
        incomingRequests: [],
        outgoingRequests: [
          {
            ...mockSwapRequestOutgoing,
            status: SwapStatus.APPROVED,
            approvedAt: '2025-01-26T10:00:00Z',
          },
        ],
        recentSwaps: [
          {
            ...mockSwapRequestOutgoing,
            status: SwapStatus.APPROVED,
            approvedAt: '2025-01-26T10:00:00Z',
          },
        ],
      };

      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: updatedResponse,
        isLoading: false,
        error: null,
      });

      rerender(<MySwapRequests />);

      expect(screen.getByText(/approved/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Create → Review → Reject Flow
  // ============================================================================

  describe('Create → Review → Reject Flow', () => {
    it('should complete full rejection workflow', async () => {
      const user = userEvent.setup();
      const mockCreateMutate = jest.fn().mockResolvedValue(mockCreateSwapResponse);
      const mockRejectMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateMutate,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockRejectMutate,
        isPending: false,
        isError: false,
        error: null,
      });

      // Step 1: Create swap request
      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getByLabelText(/week to offload/i);
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const createButton = screen.getByRole('button', { name: /create request/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(mockCreateMutate).toHaveBeenCalled();
      });

      // Step 2: Review and reject incoming swap request
      const { unmount } = render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      const notesTextarea = screen.getByPlaceholderText(/add optional notes for rejecting/i);
      await user.type(notesTextarea, 'Already committed that week');

      const confirmButton = screen.getByRole('button', { name: /confirm reject/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockRejectMutate).toHaveBeenCalledWith({ notes: 'Already committed that week' });
        expect(mockOnActionComplete).toHaveBeenCalled();
      });

      unmount();
    });

    it('should show rejected status with notes', async () => {
      const rejectedSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.REJECTED,
        notes: 'Schedule conflict',
      };

      render(
        <SwapRequestCard swap={rejectedSwap} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Rejected')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });

    it('should allow rejection without notes', async () => {
      const user = userEvent.setup();
      const mockRejectMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockRejectMutate,
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

      // Don't type notes, just confirm
      const confirmButton = screen.getByRole('button', { name: /confirm reject/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockRejectMutate).toHaveBeenCalledWith({ notes: undefined });
      });
    });
  });

  // ============================================================================
  // Cancel Flow
  // ============================================================================

  describe('Cancel Flow', () => {
    it('should complete cancellation workflow with confirmation', async () => {
      const user = userEvent.setup();
      const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(true);
      const mockCancelMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockCancelMutate,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Outgoing Request')).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockConfirm).toHaveBeenCalledWith(
        'Are you sure you want to cancel this swap request?'
      );

      await waitFor(() => {
        expect(mockCancelMutate).toHaveBeenCalled();
        expect(mockOnActionComplete).toHaveBeenCalled();
      });

      mockConfirm.mockRestore();
    });

    it('should abort cancellation if user declines confirmation', async () => {
      const user = userEvent.setup();
      const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false);
      const mockCancelMutate = jest.fn();

      (hooks.useCancelSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockCancelMutate,
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
      expect(mockCancelMutate).not.toHaveBeenCalled();
      expect(mockOnActionComplete).not.toHaveBeenCalled();

      mockConfirm.mockRestore();
    });

    it('should show cancelled status after cancellation', async () => {
      const cancelledSwap = {
        ...mockSwapRequestOutgoing,
        status: SwapStatus.CANCELLED,
      };

      render(
        <SwapRequestCard swap={cancelledSwap} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Cancelled')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Multi-Step Workflows
  // ============================================================================

  describe('Multi-Step Workflows', () => {
    it('should handle create with specific faculty then accept workflow', async () => {
      const user = userEvent.setup();
      const mockCreateMutate = jest.fn().mockResolvedValue({
        ...mockCreateSwapResponse,
        candidatesNotified: 1,
      });
      const mockAcceptMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateMutate,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      // Step 1: Create with specific faculty
      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getByLabelText(/week to offload/i);
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const specificRadio = screen.getByLabelText(/request specific faculty/i);
      await user.click(specificRadio);

      const facultySelect = screen.getByLabelText(/target faculty/i);
      await user.selectOptions(facultySelect, mockFacultyMembers[0].id);

      const createButton = screen.getByRole('button', { name: /create request/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(mockCreateMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            preferredTargetFacultyId: mockFacultyMembers[0].id,
            autoFindCandidates: false,
          })
        );
      });
    });

    it('should handle create with auto-find, review, then reject workflow', async () => {
      const user = userEvent.setup();
      const mockCreateMutate = jest.fn().mockResolvedValue({
        ...mockCreateSwapResponse,
        candidatesNotified: 5,
      });
      const mockRejectMutate = jest.fn().mockResolvedValue(mockSwapRespondResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateMutate,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      (hooks.useRejectSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockRejectMutate,
        isPending: false,
        isError: false,
        error: null,
      });

      // Step 1: Create with auto-find
      const { unmount: unmountForm } = render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getByLabelText(/week to offload/i);
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const createButton = screen.getByRole('button', { name: /create request/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(mockCreateMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            autoFindCandidates: true,
          })
        );
      });

      unmountForm();

      // Step 2: Reject incoming request
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      const confirmButton = screen.getByRole('button', { name: /confirm reject/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockRejectMutate).toHaveBeenCalled();
      });
    });
  });

  // ============================================================================
  // Error Recovery Workflows
  // ============================================================================

  describe('Error Recovery Workflows', () => {
    it('should handle creation failure and retry', async () => {
      const user = userEvent.setup();
      const mockCreateMutate = jest
        .fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockCreateSwapResponse);

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockCreateMutate,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      render(<SwapRequestForm onSuccess={mockOnSuccess} />, {
        wrapper: createWrapper(),
      });

      const weekSelect = screen.getByLabelText(/week to offload/i);
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      const createButton = screen.getByRole('button', { name: /create request/i });

      // First attempt fails
      await user.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Retry succeeds
      await user.click(createButton);

      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalled();
      });
    });

    it('should handle accept failure and show error', async () => {
      const user = userEvent.setup();
      const mockAcceptMutate = jest
        .fn()
        .mockRejectedValue(new Error('ACGME compliance violation'));

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockAcceptMutate,
        isPending: false,
        isError: true,
        error: { message: 'ACGME compliance violation' },
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
        expect(screen.getByText(/ACGME compliance violation/i)).toBeInTheDocument();
      });

      // Should not call onActionComplete due to error
      expect(mockOnActionComplete).not.toHaveBeenCalled();
    });

    it('should allow user to change mind during action confirmation', async () => {
      const user = userEvent.setup();
      const mockAcceptMutate = jest.fn();

      (hooks.useAcceptSwap as jest.Mock).mockReturnValue({
        mutateAsync: mockAcceptMutate,
        isPending: false,
        isError: false,
        error: null,
      });

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Enter accept mode
      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      // Cancel instead of confirming
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Should return to initial state
      expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
      expect(mockAcceptMutate).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // State Transitions
  // ============================================================================

  describe('State Transitions', () => {
    it('should show correct state transitions: pending → approved → executed', async () => {
      // Start with pending
      const { rerender } = render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();

      // Transition to approved
      const approvedSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.APPROVED,
        approvedAt: '2025-01-11T12:00:00Z',
      };

      rerender(
        <SwapRequestCard swap={approvedSwap} onActionComplete={mockOnActionComplete} />
      );

      expect(screen.getByText('Approved')).toBeInTheDocument();

      // Transition to executed
      const executedSwap = {
        ...approvedSwap,
        status: SwapStatus.EXECUTED,
        executedAt: '2025-01-15T08:00:00Z',
      };

      rerender(
        <SwapRequestCard swap={executedSwap} onActionComplete={mockOnActionComplete} />
      );

      expect(screen.getByText('Executed')).toBeInTheDocument();
    });

    it('should show correct state transitions: pending → rejected', async () => {
      const { rerender } = render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();

      const rejectedSwap = {
        ...mockSwapRequestIncoming,
        status: SwapStatus.REJECTED,
        notes: 'Cannot accommodate',
      };

      rerender(
        <SwapRequestCard swap={rejectedSwap} onActionComplete={mockOnActionComplete} />
      );

      expect(screen.getByText('Rejected')).toBeInTheDocument();
    });

    it('should show correct state transitions: pending → cancelled', async () => {
      const { rerender } = render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();

      const cancelledSwap = {
        ...mockSwapRequestOutgoing,
        status: SwapStatus.CANCELLED,
      };

      rerender(
        <SwapRequestCard swap={cancelledSwap} onActionComplete={mockOnActionComplete} />
      );

      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });
  });
});
