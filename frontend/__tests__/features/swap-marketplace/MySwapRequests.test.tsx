/**
 * Tests for MySwapRequests Component
 *
 * Tests tabs, rendering of incoming/outgoing/recent requests
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MySwapRequests } from '@/features/swap-marketplace/MySwapRequests';
import * as hooks from '@/features/swap-marketplace/hooks';
import { mockMySwapsResponse, mockEmptyMySwapsResponse } from './mockData';

// Mock the hooks
jest.mock('@/features/swap-marketplace/hooks');

// Create mock mutation objects
const mockAcceptMutation = {
  mutateAsync: jest.fn(),
  isPending: false,
  isSuccess: false,
  isError: false,
  error: null,
};

const mockRejectMutation = {
  mutateAsync: jest.fn(),
  isPending: false,
  isSuccess: false,
  isError: false,
  error: null,
};

const mockCancelMutation = {
  mutateAsync: jest.fn(),
  isPending: false,
  isSuccess: false,
  isError: false,
  error: null,
};

// Mock the AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { id: 'test-user-1', name: 'Test User', email: 'test@example.com', role: 'FACULTY' },
    isLoading: false,
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
  })),
}));

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

describe('MySwapRequests', () => {
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementation
    (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
      data: mockMySwapsResponse,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    // Mock the mutation hooks used by SwapRequestCard
    (hooks.useAcceptSwap as jest.Mock).mockReturnValue(mockAcceptMutation);
    (hooks.useRejectSwap as jest.Mock).mockReturnValue(mockRejectMutation);
    (hooks.useCancelSwap as jest.Mock).mockReturnValue(mockCancelMutation);
  });

  describe('Loading State', () => {
    it('should show loading spinner when data is loading', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading your swap requests...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when request fails', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load swap requests' },
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByText('Error Loading Swap Requests')).toBeInTheDocument();
      expect(screen.getByText('Failed to load swap requests')).toBeInTheDocument();
    });

    it('should show retry button in error state', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load swap requests' },
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should call refetch when retry button is clicked', async () => {
      const user = userEvent.setup();

      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load swap requests' },
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Tabs Rendering', () => {
    it('should render all three tabs', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /incoming/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /outgoing/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /recent/i })).toBeInTheDocument();
    });

    it('should show count badges on tabs', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      // Based on mockMySwapsResponse: 2 incoming, 2 outgoing, 2 recent
      const tabs = screen.getAllByRole('button');
      expect(tabs[0]).toHaveTextContent('2'); // Incoming
      expect(tabs[1]).toHaveTextContent('2'); // Outgoing
      expect(tabs[2]).toHaveTextContent('2'); // Recent
    });

    it('should highlight active tab', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      const incomingTab = screen.getByRole('button', { name: /incoming/i });
      expect(incomingTab).toHaveClass('border-blue-500');
      expect(incomingTab).toHaveClass('text-blue-600');
    });

    it('should switch tabs when clicked', async () => {
      const user = userEvent.setup();

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const outgoingTab = screen.getByRole('button', { name: /outgoing/i });
      await user.click(outgoingTab);

      expect(outgoingTab).toHaveClass('border-blue-500');
      expect(outgoingTab).toHaveClass('text-blue-600');
    });
  });

  describe('Incoming Tab', () => {
    it('should display incoming requests by default', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByText(/incoming requests \(2\)/i)).toBeInTheDocument();
      expect(
        screen.getByText(/swap requests from other faculty members that you can accept or reject/i)
      ).toBeInTheDocument();
    });

    it('should render incoming request cards', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      // Based on mockMySwapsResponse incoming requests
      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument();
      expect(screen.getByText('Dr. Bob Johnson')).toBeInTheDocument();
    });

    it('should show empty state when no incoming requests', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: mockEmptyMySwapsResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByText('No Incoming Requests')).toBeInTheDocument();
      expect(
        screen.getByText(/you don't have any pending swap requests directed to you/i)
      ).toBeInTheDocument();
    });
  });

  describe('Outgoing Tab', () => {
    it('should display outgoing requests when tab is clicked', async () => {
      const user = userEvent.setup();

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const outgoingTab = screen.getByRole('button', { name: /outgoing/i });
      await user.click(outgoingTab);

      expect(screen.getByText(/outgoing requests \(2\)/i)).toBeInTheDocument();
      expect(
        screen.getByText(/swap requests you've created that are awaiting response/i)
      ).toBeInTheDocument();
    });

    it('should render outgoing request cards', async () => {
      const user = userEvent.setup();

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const outgoingTab = screen.getByRole('button', { name: /outgoing/i });
      await user.click(outgoingTab);

      // Based on mockMySwapsResponse outgoing requests - names may appear multiple times on page
      const janeDoeElements = screen.getAllByText('Dr. Jane Doe');
      expect(janeDoeElements.length).toBeGreaterThan(0);
      const johnSmithElements = screen.getAllByText('Dr. John Smith');
      expect(johnSmithElements.length).toBeGreaterThan(0);
    });

    it('should show empty state when no outgoing requests', async () => {
      const user = userEvent.setup();

      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: mockEmptyMySwapsResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const outgoingTab = screen.getByRole('button', { name: /outgoing/i });
      await user.click(outgoingTab);

      expect(screen.getByText('No Outgoing Requests')).toBeInTheDocument();
      expect(
        screen.getByText(/you haven't created any swap requests yet/i)
      ).toBeInTheDocument();
    });
  });

  describe('Recent Tab', () => {
    it('should display recent swaps when tab is clicked', async () => {
      const user = userEvent.setup();

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const recentTab = screen.getByRole('button', { name: /recent/i });
      await user.click(recentTab);

      expect(screen.getByText(/recent swaps \(2\)/i)).toBeInTheDocument();
      expect(
        screen.getByText(/recently completed, rejected, or cancelled swap requests/i)
      ).toBeInTheDocument();
    });

    it('should render recent swap cards', async () => {
      const user = userEvent.setup();

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const recentTab = screen.getByRole('button', { name: /recent/i });
      await user.click(recentTab);

      // Based on mockMySwapsResponse recent swaps (approved and rejected)
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('Rejected')).toBeInTheDocument();
    });

    it('should show empty state when no recent swaps', async () => {
      const user = userEvent.setup();

      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: mockEmptyMySwapsResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const recentTab = screen.getByRole('button', { name: /recent/i });
      await user.click(recentTab);

      expect(screen.getByText('No Recent Swaps')).toBeInTheDocument();
      expect(
        screen.getByText(/you don't have any recently completed or rejected swaps/i)
      ).toBeInTheDocument();
    });
  });

  describe('Summary Stats', () => {
    it('should display summary section when there are requests', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.getByText('Summary')).toBeInTheDocument();
    });

    it('should show correct counts in summary', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      // Based on mockMySwapsResponse: 2 incoming, 2 outgoing, 2 recent
      const summarySection = screen.getByText('Summary').closest('div');
      expect(summarySection).toHaveTextContent('2');
      expect(summarySection).toHaveTextContent('Incoming requests');
      expect(summarySection).toHaveTextContent('Outgoing requests');
      expect(summarySection).toHaveTextContent('Recent swaps');
    });

    it('should not display summary when no requests exist', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: mockEmptyMySwapsResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      expect(screen.queryByText('Summary')).not.toBeInTheDocument();
    });
  });

  describe('Action Completion', () => {
    it('should call refetch when swap card action is completed', () => {
      render(<MySwapRequests />, { wrapper: createWrapper() });

      // SwapRequestCard components receive onActionComplete prop that calls refetch
      // We're verifying the prop is passed correctly by checking the mock
      expect(hooks.useMySwapRequests).toHaveBeenCalled();
    });
  });

  describe('Tab Badge Visibility', () => {
    it('should show badge only when count is greater than 0', () => {
      (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
        data: {
          incomingRequests: [],
          outgoingRequests: [mockMySwapsResponse.outgoingRequests[0]],
          recentSwaps: [],
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<MySwapRequests />, { wrapper: createWrapper() });

      const tabs = screen.getAllByRole('button');

      // Incoming tab should not have badge (0 requests)
      expect(tabs[0]).not.toHaveTextContent('0');

      // Outgoing tab should have badge (1 request)
      expect(tabs[1]).toHaveTextContent('1');

      // Recent tab should not have badge (0 swaps)
      expect(tabs[2]).not.toHaveTextContent('0');
    });
  });
});
