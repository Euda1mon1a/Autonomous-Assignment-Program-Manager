import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { SwapApprovalPanel } from '@/components/swap/SwapApprovalPanel';
import { SwapRequest } from '@/components/swap/SwapCard';

jest.mock('@/components/swap/SwapCard', () => ({
  SwapCard: ({ swap, compact, onViewDetails }: any) => (
    <div data-testid={`swap-card-${swap.id}`} onClick={onViewDetails}>
      {compact ? 'Compact' : 'Full'} - {swap.requestor.name}
    </div>
  ),
}));

describe('SwapApprovalPanel', () => {
  const mockPendingSwaps: SwapRequest[] = [
    {
      id: 'swap-1',
      swapType: 'one-to-one',
      status: 'pending',
      requestor: { id: 'user-1', name: 'Dr. Alice' },
      givingUpBlock: { date: '2025-01-15', shift: 'AM', rotationType: 'Inpatient' },
      targetPerson: { id: 'user-2', name: 'Dr. Bob' },
      targetBlock: { date: '2025-01-20', shift: 'PM', rotationType: 'Clinic' },
      reason: 'Personal',
      createdAt: '2025-01-01',
    },
    {
      id: 'swap-2',
      swapType: 'absorb',
      status: 'pending',
      requestor: { id: 'user-3', name: 'Dr. Carol' },
      givingUpBlock: { date: '2025-01-25', shift: 'Night', rotationType: 'Call' },
      reason: 'Medical',
      createdAt: '2025-01-02',
    },
  ];

  const mockOnApprove = jest.fn().mockResolvedValue(undefined);
  const mockOnReject = jest.fn().mockResolvedValue(undefined);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      expect(screen.getByText('Swap Approvals')).toBeInTheDocument();
    });

    it('displays pending count', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      expect(screen.getByText(/2 pending requests require review/i)).toBeInTheDocument();
    });

    it('displays all swap cards', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      expect(screen.getByTestId('swap-card-swap-1')).toBeInTheDocument();
      expect(screen.getByTestId('swap-card-swap-2')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no pending swaps', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={[]}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      expect(screen.getByText('All Caught Up!')).toBeInTheDocument();
      expect(screen.getByText(/No pending swap requests to review/i)).toBeInTheDocument();
    });
  });

  describe('Swap Selection', () => {
    it('shows swaps in compact mode by default', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      expect(screen.getByText(/Compact - Dr. Alice/)).toBeInTheDocument();
    });

    it('expands swap when clicked', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      expect(screen.getByText(/Full - Dr. Alice/)).toBeInTheDocument();
    });

    it('shows action selection when swap expanded', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      expect(screen.getByText('Review This Request')).toBeInTheDocument();
      expect(screen.getByText('Approve Swap')).toBeInTheDocument();
      expect(screen.getByText('Reject Swap')).toBeInTheDocument();
    });

    it('collapses swap when clicked again', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      const swapCard = screen.getByTestId('swap-card-swap-1');
      fireEvent.click(swapCard);
      fireEvent.click(swapCard);
      expect(screen.getByText(/Compact - Dr. Alice/)).toBeInTheDocument();
    });
  });

  describe('Approve Flow', () => {
    it('shows approval form when approve clicked', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      const approveButtons = screen.getAllByText('Approve Swap');
      fireEvent.click(approveButtons[0]); // First approve button (selection)

      expect(screen.getByText('Approve Swap Request')).toBeInTheDocument();
      expect(screen.getByLabelText(/Notes \(Optional\)/i)).toBeInTheDocument();
    });

    it('calls onApprove when submitted without notes', async () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Approve Swap')[0]);

      // Re-query after DOM update
      const submitButton = screen.getAllByText('Approve Swap')[1];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockOnApprove).toHaveBeenCalledWith('swap-1', undefined);
      });
    });

    it('calls onApprove with notes when provided', async () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Approve Swap')[0]);

      const notesTextarea = screen.getByLabelText(/Notes \(Optional\)/i);
      fireEvent.change(notesTextarea, { target: { value: 'Approved for coverage' } });

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Approve Swap')[1]);

      await waitFor(() => {
        expect(mockOnApprove).toHaveBeenCalledWith('swap-1', 'Approved for coverage');
      });
    });
  });

  describe('Reject Flow', () => {
    it('shows rejection form when reject clicked', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      const rejectButtons = screen.getAllByText('Reject Swap');
      fireEvent.click(rejectButtons[0]); // Selection button

      expect(screen.getByText('Reject Swap Request')).toBeInTheDocument();
      expect(screen.getByLabelText(/Rejection Reason \*/i)).toBeInTheDocument();
    });

    it('requires reason for rejection', async () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Reject Swap')[0]);

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Reject Swap')[1]);

      await waitFor(() => {
        expect(screen.getByText(/Please provide a reason for rejection/i)).toBeInTheDocument();
      });

      expect(mockOnReject).not.toHaveBeenCalled();
    });

    it('calls onReject with reason when provided', async () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Reject Swap')[0]);

      const reasonTextarea = screen.getByLabelText(/Rejection Reason \*/i);
      fireEvent.change(reasonTextarea, { target: { value: 'Coverage conflict' } });

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Reject Swap')[1]);

      await waitFor(() => {
        expect(mockOnReject).toHaveBeenCalledWith('swap-1', 'Coverage conflict');
      });
    });

    it('resets form after successful rejection', async () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Reject Swap')[0]);

      const reasonTextarea = screen.getByLabelText(/Rejection Reason \*/i);
      fireEvent.change(reasonTextarea, { target: { value: 'Coverage conflict' } });

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Reject Swap')[1]);

      await waitFor(() => {
        expect(screen.queryByText('Reject Swap Request')).not.toBeInTheDocument();
      });
    });
  });

  describe('Cancel Action', () => {
    it('shows cancel button in action form', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      const approveButtons = screen.getAllByText('Approve Swap');
      fireEvent.click(approveButtons[0]);

      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('returns to action selection when cancel clicked', () => {
      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      const approveButtons = screen.getAllByText('Approve Swap');
      fireEvent.click(approveButtons[0]);
      fireEvent.click(screen.getByText('Cancel'));

      expect(screen.getByText('Review This Request')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('shows error message on approval failure', async () => {
      mockOnApprove.mockRejectedValueOnce(new Error('Server error'));

      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Approve Swap')[0]);

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Approve Swap')[1]);

      await waitFor(() => {
        expect(screen.getByText('Server error')).toBeInTheDocument();
      });
    });

    it('shows error message on rejection failure', async () => {
      mockOnReject.mockRejectedValueOnce(new Error('Network error'));

      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByText('Reject Swap')[0]);

      const reasonTextarea = screen.getByLabelText(/Rejection Reason \*/i);
      fireEvent.change(reasonTextarea, { target: { value: 'Test' } });

      // Re-query after DOM update
      fireEvent.click(screen.getAllByText('Reject Swap')[1]);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('shows processing state during submission', async () => {
      mockOnApprove.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByRole('button', { name: /Approve Swap/i })[0]);

      // Re-query after DOM update
      fireEvent.click(screen.getAllByRole('button', { name: /Approve Swap/i })[1]);

      expect(await screen.findByText('Processing...')).toBeInTheDocument();
    });

    it('disables buttons during submission', async () => {
      mockOnApprove.mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
        />
      );
      fireEvent.click(screen.getByTestId('swap-card-swap-1'));
      fireEvent.click(screen.getAllByRole('button', { name: /Approve Swap/i })[0]);

      // Re-query after DOM update
      fireEvent.click(screen.getAllByRole('button', { name: /Approve Swap/i })[1]);

      const cancelButton = await screen.findByRole('button', { name: /Cancel/i });
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <SwapApprovalPanel
          pendingSwaps={mockPendingSwaps}
          onApprove={mockOnApprove}
          onReject={mockOnReject}
          className="custom-panel"
        />
      );
      expect(container.querySelector('.custom-panel')).toBeInTheDocument();
    });
  });
});
