/**
 * Tests for SwapRequestCard Component
 *
 * Tests rendering, action buttons, modal interactions, and status display
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapRequestCard } from '@/features/swap-marketplace/SwapRequestCard';
import {
  mockSwapRequestIncoming,
  mockSwapRequestOutgoing,
  mockSwapRequestApproved,
  mockSwapRequestAbsorb,
  mockMarketplaceEntry1,
} from './mockData';

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

describe('SwapRequestCard', () => {
  const mockOnActionComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Marketplace Entry Rendering', () => {
    it('should render marketplace entry with faculty name', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. Sarah Williams')).toBeInTheDocument();
    });

    it('should display week available date', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Jun 1, 2025/i)).toBeInTheDocument();
    });

    it('should show compatible badge when isCompatible is true', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Compatible')).toBeInTheDocument();
    });

    it('should not show compatible badge when isCompatible is false', () => {
      const entry = { ...mockMarketplaceEntry1, isCompatible: false };
      render(
        <SwapRequestCard marketplaceEntry={entry} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByText('Compatible')).not.toBeInTheDocument();
    });

    it('should display reason when provided', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Medical conference')).toBeInTheDocument();
    });

    it('should render view details button', () => {
      render(
        <SwapRequestCard
          marketplaceEntry={mockMarketplaceEntry1}
          onActionComplete={mockOnActionComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /view details/i })).toBeInTheDocument();
    });
  });

  describe('Swap Request Rendering', () => {
    it('should render swap type label', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('One-to-One Swap')).toBeInTheDocument();
    });

    it('should show incoming request label', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Incoming Request')).toBeInTheDocument();
    });

    it('should show outgoing request label', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Outgoing Request')).toBeInTheDocument();
    });

    it('should display status badge', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('should display source faculty name', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
    });

    it('should display target faculty name for one-to-one swap', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Dr. Jane Doe')).toBeInTheDocument();
    });

    it('should not display target faculty for absorb swap', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestAbsorb} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Should only show source faculty, not target
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      expect(screen.queryByText('Dr. Jane Doe')).not.toBeInTheDocument();
    });

    it('should display reason when provided', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Family emergency - need to swap this week')).toBeInTheDocument();
    });

    it('should display requested date', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/Requested Jan 10, 2025/i)).toBeInTheDocument();
    });
  });

  describe('Action Buttons - Incoming Request', () => {
    it('should show Accept button when canAccept is true', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
    });

    it('should show Reject button when canReject is true', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
    });

    it('should not show Cancel button for incoming request', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons - Outgoing Request', () => {
    it('should show Cancel button when canCancel is true', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should not show Accept/Reject buttons for outgoing request', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
    });
  });

  describe('Action Buttons - Approved Request', () => {
    it('should not show any action buttons when status is approved', () => {
      render(
        <SwapRequestCard swap={mockSwapRequestApproved} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      expect(screen.queryByRole('button', { name: /accept/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /reject/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  describe('Accept Flow', () => {
    it('should show notes textarea when Accept button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      expect(
        screen.getByPlaceholderText(/add optional notes for accepting/i)
      ).toBeInTheDocument();
    });

    it('should show confirm and cancel buttons in accept mode', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      expect(screen.getByRole('button', { name: /confirm accept/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should allow typing notes in textarea', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      const textarea = screen.getByPlaceholderText(/add optional notes for accepting/i);
      await user.type(textarea, 'Happy to help with this swap');

      expect(textarea).toHaveValue('Happy to help with this swap');
    });

    it('should cancel accept mode when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Enter accept mode
      const acceptButton = screen.getByRole('button', { name: /accept/i });
      await user.click(acceptButton);

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Should be back to initial state
      expect(
        screen.queryByPlaceholderText(/add optional notes for accepting/i)
      ).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
    });
  });

  describe('Reject Flow', () => {
    it('should show notes textarea when Reject button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      expect(
        screen.getByPlaceholderText(/add optional notes for rejecting/i)
      ).toBeInTheDocument();
    });

    it('should show confirm and cancel buttons in reject mode', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      expect(screen.getByRole('button', { name: /confirm reject/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should allow typing notes in textarea', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      const textarea = screen.getByPlaceholderText(/add optional notes for rejecting/i);
      await user.type(textarea, 'Schedule conflict that week');

      expect(textarea).toHaveValue('Schedule conflict that week');
    });

    it('should cancel reject mode when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <SwapRequestCard swap={mockSwapRequestIncoming} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      // Enter reject mode
      const rejectButton = screen.getByRole('button', { name: /reject/i });
      await user.click(rejectButton);

      // Cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Should be back to initial state
      expect(
        screen.queryByPlaceholderText(/add optional notes for rejecting/i)
      ).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reject/i })).toBeInTheDocument();
    });
  });

  describe('Cancel Confirmation', () => {
    it('should show confirmation dialog when Cancel button is clicked', async () => {
      const user = userEvent.setup();
      const mockConfirm = jest.spyOn(window, 'confirm').mockReturnValue(false);

      render(
        <SwapRequestCard swap={mockSwapRequestOutgoing} onActionComplete={mockOnActionComplete} />,
        { wrapper: createWrapper() }
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockConfirm).toHaveBeenCalledWith(
        'Are you sure you want to cancel this swap request?'
      );

      mockConfirm.mockRestore();
    });
  });

  describe('Empty State', () => {
    it('should not render when both swap and marketplaceEntry are undefined', () => {
      const { container } = render(<SwapRequestCard onActionComplete={mockOnActionComplete} />, {
        wrapper: createWrapper(),
      });

      expect(container.firstChild).toBeNull();
    });
  });
});
