import { render, screen, fireEvent } from '@testing-library/react';
import { SwapCard, SwapRequest } from '@/components/swap/SwapCard';

// Mock child components
jest.mock('@/components/schedule/ShiftIndicator', () => ({
  ShiftIndicator: ({ shift }: any) => <span data-testid="shift">{shift}</span>,
}));

jest.mock('@/components/schedule/RotationBadge', () => ({
  RotationBadge: ({ rotationType }: any) => <span data-testid="rotation">{rotationType}</span>,
}));

describe('SwapCard', () => {
  const mockSwap: SwapRequest = {
    id: 'swap-123',
    swapType: 'one-to-one',
    status: 'pending',
    requestor: { id: 'user-1', name: 'Dr. Alice' },
    givingUpBlock: { date: '2025-01-15', shift: 'AM', rotationType: 'Inpatient' },
    targetPerson: { id: 'user-2', name: 'Dr. Bob' },
    targetBlock: { date: '2025-01-20', shift: 'PM', rotationType: 'Clinic' },
    reason: 'Personal/Family Matter',
    notes: 'Family emergency',
    createdAt: '2025-01-01T00:00:00Z',
    expiresAt: '2025-01-10T00:00:00Z',
  };

  describe('Basic Rendering', () => {
    it('renders without crashing', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText('Swap Request')).toBeInTheDocument();
    });

    it('displays requestor name', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText(/Dr. Alice/)).toBeInTheDocument();
    });

    it('displays status badge', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('displays reason', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText(/Personal\/Family Matter/)).toBeInTheDocument();
    });

    it('displays notes when provided', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText('Family emergency')).toBeInTheDocument();
    });
  });

  describe('Swap Types', () => {
    it('displays "Swap Request" for one-to-one', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText('Swap Request')).toBeInTheDocument();
    });

    it('displays "Absorb Request" for absorb type', () => {
      const absorbSwap = { ...mockSwap, swapType: 'absorb' as const, targetPerson: undefined, targetBlock: undefined };
      render(<SwapCard swap={absorbSwap} />);
      expect(screen.getByText('Absorb Request')).toBeInTheDocument();
    });

    it('displays "Give Away Request" for give-away type', () => {
      const giveAwaySwap = { ...mockSwap, swapType: 'give-away' as const, targetPerson: undefined, targetBlock: undefined };
      render(<SwapCard swap={giveAwaySwap} />);
      expect(screen.getByText('Give Away Request')).toBeInTheDocument();
    });
  });

  describe('Status Display', () => {
    it('shows pending status correctly', () => {
      render(<SwapCard swap={{ ...mockSwap, status: 'pending' }} />);
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('shows approved status correctly', () => {
      render(<SwapCard swap={{ ...mockSwap, status: 'approved' }} />);
      expect(screen.getByText('Approved')).toBeInTheDocument();
    });

    it('shows rejected status correctly', () => {
      render(<SwapCard swap={{ ...mockSwap, status: 'rejected' }} />);
      expect(screen.getByText('Rejected')).toBeInTheDocument();
    });

    it('shows completed status correctly', () => {
      render(<SwapCard swap={{ ...mockSwap, status: 'completed' }} />);
      expect(screen.getByText('Completed')).toBeInTheDocument();
    });

    it('shows cancelled status correctly', () => {
      render(<SwapCard swap={{ ...mockSwap, status: 'cancelled' }} />);
      expect(screen.getByText('Cancelled')).toBeInTheDocument();
    });
  });

  describe('Block Information', () => {
    it('displays giving up block details', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText(/Dr. Alice.*is giving up/i)).toBeInTheDocument();
      expect(screen.getAllByTestId('shift')[0]).toHaveTextContent('AM');
      expect(screen.getAllByTestId('rotation')[0]).toHaveTextContent('Inpatient');
    });

    it('displays target block for one-to-one swaps', () => {
      render(<SwapCard swap={mockSwap} />);
      expect(screen.getByText(/Dr. Bob.*would give up/i)).toBeInTheDocument();
      expect(screen.getAllByTestId('shift')[1]).toHaveTextContent('PM');
      expect(screen.getAllByTestId('rotation')[1]).toHaveTextContent('Clinic');
    });

    it('does not show target block for absorb swaps', () => {
      const absorbSwap = { ...mockSwap, swapType: 'absorb' as const, targetPerson: undefined, targetBlock: undefined };
      render(<SwapCard swap={absorbSwap} />);
      expect(screen.queryByText(/would give up/i)).not.toBeInTheDocument();
    });
  });

  describe('User Context', () => {
    it('shows "You Requested" badge when user is requestor', () => {
      render(<SwapCard swap={mockSwap} currentUserId="user-1" />);
      expect(screen.getByText('You Requested')).toBeInTheDocument();
    });

    it('shows "You\'re Target" badge when user is target', () => {
      render(<SwapCard swap={mockSwap} currentUserId="user-2" />);
      expect(screen.getByText("You're Target")).toBeInTheDocument();
    });

    it('does not show user badges for other users', () => {
      render(<SwapCard swap={mockSwap} currentUserId="user-3" />);
      expect(screen.queryByText('You Requested')).not.toBeInTheDocument();
      expect(screen.queryByText("You're Target")).not.toBeInTheDocument();
    });
  });

  describe('Expiry Warning', () => {
    it('shows expiry warning when expires within 3 days', () => {
      const expiringSwap = {
        ...mockSwap,
        expiresAt: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days
      };
      render(<SwapCard swap={expiringSwap} />);
      expect(screen.getByText(/Expires in 2 days/i)).toBeInTheDocument();
    });

    it('does not show expiry warning when expires later', () => {
      const laterSwap = {
        ...mockSwap,
        expiresAt: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days
      };
      render(<SwapCard swap={laterSwap} />);
      expect(screen.queryByText(/Expires in/i)).not.toBeInTheDocument();
    });

    it('does not show expiry warning for non-pending swaps', () => {
      const approvedSwap = {
        ...mockSwap,
        status: 'approved' as const,
        expiresAt: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
      };
      render(<SwapCard swap={approvedSwap} />);
      expect(screen.queryByText(/Expires in/i)).not.toBeInTheDocument();
    });
  });

  describe('Actions', () => {
    const onAccept = jest.fn();
    const onReject = jest.fn();
    const onCancel = jest.fn();
    const onViewDetails = jest.fn();

    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('shows accept button for target user on pending swap', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-2" onAccept={onAccept} />
      );
      expect(screen.getByText('Accept Swap')).toBeInTheDocument();
    });

    it('calls onAccept when accept button clicked', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-2" onAccept={onAccept} />
      );
      fireEvent.click(screen.getByText('Accept Swap'));
      expect(onAccept).toHaveBeenCalledWith('swap-123');
    });

    it('shows reject button for target user on pending swap', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-2" onReject={onReject} />
      );
      expect(screen.getByText('Reject')).toBeInTheDocument();
    });

    it('calls onReject when reject button clicked', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-2" onReject={onReject} />
      );
      fireEvent.click(screen.getByText('Reject'));
      expect(onReject).toHaveBeenCalledWith('swap-123');
    });

    it('shows cancel button for requestor on pending swap', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-1" onCancel={onCancel} />
      );
      expect(screen.getByText('Cancel Request')).toBeInTheDocument();
    });

    it('calls onCancel when cancel button clicked', () => {
      render(
        <SwapCard swap={mockSwap} currentUserId="user-1" onCancel={onCancel} />
      );
      fireEvent.click(screen.getByText('Cancel Request'));
      expect(onCancel).toHaveBeenCalledWith('swap-123');
    });

    it('shows view details button when provided', () => {
      render(<SwapCard swap={mockSwap} onViewDetails={onViewDetails} />);
      expect(screen.getByText('View Details')).toBeInTheDocument();
    });

    it('calls onViewDetails when view details clicked', () => {
      render(<SwapCard swap={mockSwap} onViewDetails={onViewDetails} />);
      fireEvent.click(screen.getByText('View Details'));
      expect(onViewDetails).toHaveBeenCalledWith('swap-123');
    });

    it('does not show action buttons for non-pending swaps', () => {
      const completedSwap = { ...mockSwap, status: 'completed' as const };
      render(
        <SwapCard
          swap={completedSwap}
          currentUserId="user-2"
          onAccept={onAccept}
          onReject={onReject}
        />
      );
      expect(screen.queryByText('Accept Swap')).not.toBeInTheDocument();
      expect(screen.queryByText('Reject')).not.toBeInTheDocument();
    });
  });

  describe('Compact Mode', () => {
    it('renders compact version when compact=true', () => {
      render(<SwapCard swap={mockSwap} compact={true} />);
      expect(screen.getByText('Dr. Alice')).toBeInTheDocument();
      expect(screen.queryByText('Swap Request')).not.toBeInTheDocument(); // Full title not shown
    });

    it('shows only basic info in compact mode', () => {
      render(<SwapCard swap={mockSwap} compact={true} />);
      expect(screen.queryByText(/Family emergency/)).not.toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<SwapCard swap={mockSwap} className="custom-swap" />);
      expect(container.querySelector('.custom-swap')).toBeInTheDocument();
    });
  });
});
