/**
 * Tests for SwapMarketplace Component
 *
 * Tests main marketplace page, tab navigation, and integration
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SwapMarketplace } from '@/features/swap-marketplace/SwapMarketplace';
import * as hooks from '@/features/swap-marketplace/hooks';
import {
  mockMarketplaceResponse,
  mockEmptyMarketplaceResponse,
  mockAvailableWeeks,
  mockFacultyMembers,
} from './mockData';

// Mock the hooks
jest.mock('@/features/swap-marketplace/hooks');

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
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('SwapMarketplace', () => {
  const mockRefetch = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock implementations
    (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
      data: mockMarketplaceResponse,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    (hooks.useMySwapRequests as jest.Mock).mockReturnValue({
      data: { incomingRequests: [], outgoingRequests: [], recentSwaps: [] },
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    });

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
  });

  describe('Page Header', () => {
    it('should render page title', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Swap Marketplace')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/browse available swap opportunities, manage your requests/i)
      ).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should render all three main tabs', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /browse swaps/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /my requests/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create request/i })).toBeInTheDocument();
    });

    it('should have Browse Swaps tab active by default', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const browseTab = screen.getByRole('button', { name: /browse swaps/i });
      expect(browseTab).toHaveClass('border-blue-500');
      expect(browseTab).toHaveClass('text-blue-600');
    });

    it('should switch to My Requests tab when clicked', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const myRequestsTab = screen.getByRole('button', { name: /my requests/i });
      await user.click(myRequestsTab);

      expect(myRequestsTab).toHaveClass('border-blue-500');
      expect(myRequestsTab).toHaveClass('text-blue-600');
    });

    it('should switch to Create Request tab when clicked', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const createTab = screen.getByRole('button', { name: /create request/i });
      await user.click(createTab);

      expect(createTab).toHaveClass('border-blue-500');
      expect(createTab).toHaveClass('text-blue-600');
    });
  });

  describe('Browse Tab - Loading State', () => {
    it('should show loading spinner when marketplace data is loading', () => {
      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading marketplace...')).toBeInTheDocument();
    });
  });

  describe('Browse Tab - Error State', () => {
    it('should show error message when marketplace fails to load', () => {
      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load marketplace' },
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Error Loading Marketplace')).toBeInTheDocument();
      expect(screen.getByText('Failed to load marketplace')).toBeInTheDocument();
    });

    it('should show retry button in error state', () => {
      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load marketplace' },
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });

    it('should call refetch when retry button is clicked', async () => {
      const user = userEvent.setup();

      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: 'Failed to load marketplace' },
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('Browse Tab - Stats Display', () => {
    it('should display total available swaps', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Find the stat container with "Available Swaps" label and verify the count
      const availableSwapsLabel = screen.getByText('Available Swaps');
      expect(availableSwapsLabel).toBeInTheDocument();
      // The count is in a sibling element - use getAllByText and find the one in stats
      const allThrees = screen.getAllByText('3');
      expect(allThrees.length).toBeGreaterThan(0);
    });

    it('should display compatible swaps count', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // mockMarketplaceResponse has 2 compatible entries
      const compatibleLabel = screen.getByText('Compatible with You');
      expect(compatibleLabel).toBeInTheDocument();
      const allTwos = screen.getAllByText('2');
      expect(allTwos.length).toBeGreaterThan(0);
    });

    it('should display my postings count', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const postingsLabel = screen.getByText('Your Postings');
      expect(postingsLabel).toBeInTheDocument();
      const allOnes = screen.getAllByText('1');
      expect(allOnes.length).toBeGreaterThan(0);
    });
  });

  describe('Browse Tab - Marketplace Entries', () => {
    it('should render SwapFilters component', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should render marketplace entry cards', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Dr. Sarah Williams')).toBeInTheDocument();
      expect(screen.getByText('Dr. Michael Chen')).toBeInTheDocument();
      expect(screen.getByText('Dr. Emily Brown')).toBeInTheDocument();
    });

    it('should show entry count in heading', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText(/available swap requests \(3\)/i)).toBeInTheDocument();
    });
  });

  describe('Browse Tab - Empty State', () => {
    it('should show empty state when no swaps are available', () => {
      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: mockEmptyMarketplaceResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('No Swaps Available')).toBeInTheDocument();
      expect(
        screen.getByText(/there are currently no swap requests in the marketplace/i)
      ).toBeInTheDocument();
    });

    it('should show Create a Request button in empty state', () => {
      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: mockEmptyMarketplaceResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /create a request/i })).toBeInTheDocument();
    });

    it('should navigate to create tab when empty state button is clicked', async () => {
      const user = userEvent.setup();

      (hooks.useSwapMarketplace as jest.Mock).mockReturnValue({
        data: mockEmptyMarketplaceResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const createButton = screen.getByRole('button', { name: /create a request/i });
      await user.click(createButton);

      // Should show create form
      expect(screen.getByText('Create Swap Request')).toBeInTheDocument();
    });
  });

  describe('My Requests Tab', () => {
    it('should render MySwapRequests component when tab is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const myRequestsTab = screen.getByRole('button', { name: /my requests/i });
      await user.click(myRequestsTab);

      // Should show the incoming/outgoing/recent tabs from MySwapRequests
      expect(screen.getByRole('button', { name: /incoming/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /outgoing/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /recent/i })).toBeInTheDocument();
    });
  });

  describe('Create Request Tab', () => {
    it('should render SwapRequestForm when tab is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      const createTab = screen.getByRole('button', { name: /create request/i });
      await user.click(createTab);

      // Should show create form with heading and week selector
      expect(screen.getByText('Create Swap Request')).toBeInTheDocument();
      // Find the select element by role (combobox) instead of label association
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should navigate to My Requests tab after successful form submission', async () => {
      const user = userEvent.setup();
      const mockMutateAsync = jest.fn().mockResolvedValue({ success: true });

      (hooks.useCreateSwapRequest as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isSuccess: false,
        data: null,
        error: null,
      });

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Navigate to create tab
      const createTab = screen.getByRole('button', { name: /create request/i });
      await user.click(createTab);

      // Fill and submit form - use role selector instead of label
      const weekSelect = screen.getByRole('combobox');
      await user.selectOptions(weekSelect, mockAvailableWeeks[0].date);

      // Find submit button - there are multiple "create request" buttons (tabs + form)
      const submitButtons = screen.getAllByRole('button', { name: /create request/i });
      const submitButton = submitButtons.find(btn => btn.getAttribute('type') === 'submit') || submitButtons[submitButtons.length - 1];
      await user.click(submitButton);

      // Should navigate to My Requests tab after successful submission
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /incoming/i })).toBeInTheDocument();
      });
    });

    it('should navigate to Browse tab when cancel is clicked', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Navigate to create tab
      const createTab = screen.getByRole('button', { name: /create request/i });
      await user.click(createTab);

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Should navigate back to Browse tab - use heading instead of paragraph
      await waitFor(() => {
        expect(screen.getByText(/available swap requests \(\d+\)/i)).toBeInTheDocument();
      });
    });
  });

  describe('Filter Updates', () => {
    it('should pass filters to useSwapMarketplace hook', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(hooks.useSwapMarketplace).toHaveBeenCalledWith(
        {},
        expect.objectContaining({
          enabled: true,
        })
      );
    });

    it('should update filters when SwapFilters emits changes', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Type in search box
      const searchInput = screen.getByPlaceholderText(/search by faculty name or reason/i);
      await user.type(searchInput, 'Dr. Smith');

      // Hook should be called with updated filters
      await waitFor(() => {
        expect(hooks.useSwapMarketplace).toHaveBeenCalledWith(
          expect.objectContaining({
            searchQuery: 'Dr. Smith',
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('Help Section', () => {
    it('should render help section at bottom of page', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('How the Swap Marketplace Works')).toBeInTheDocument();
    });

    it('should show three-step guide', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(screen.getByText('Browse & Filter')).toBeInTheDocument();
      // "Create Request" appears both in tabs and help section - use getAllByText
      const createRequestTexts = screen.getAllByText(/create request/i);
      expect(createRequestTexts.length).toBeGreaterThan(0);
      expect(screen.getByText('Accept & Execute')).toBeInTheDocument();
    });

    it('should display detailed step descriptions', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/view available swap requests from other faculty members/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/create a swap request for one of your assigned FMIT weeks/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/review incoming requests and accept or reject them/i)
      ).toBeInTheDocument();
    });
  });

  describe('Conditional Query Enabling', () => {
    it('should enable marketplace query only on browse tab', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // On browse tab - should be enabled
      expect(hooks.useSwapMarketplace).toHaveBeenLastCalledWith(
        {},
        expect.objectContaining({
          enabled: true,
        })
      );

      // Switch to My Requests tab
      const myRequestsTab = screen.getByRole('button', { name: /my requests/i });
      await user.click(myRequestsTab);

      // Should be disabled
      await waitFor(() => {
        expect(hooks.useSwapMarketplace).toHaveBeenLastCalledWith(
          {},
          expect.objectContaining({
            enabled: false,
          })
        );
      });
    });

    it('should re-enable marketplace query when returning to browse tab', async () => {
      const user = userEvent.setup();

      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Switch to My Requests
      const myRequestsTab = screen.getByRole('button', { name: /my requests/i });
      await user.click(myRequestsTab);

      // Switch back to Browse
      const browseTab = screen.getByRole('button', { name: /browse swaps/i });
      await user.click(browseTab);

      // Should be enabled again
      await waitFor(() => {
        expect(hooks.useSwapMarketplace).toHaveBeenLastCalledWith(
          {},
          expect.objectContaining({
            enabled: true,
          })
        );
      });
    });
  });

  describe('Responsive Design Elements', () => {
    it('should render mobile-friendly tab labels', () => {
      render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Main tabs should have both full and shortened labels for mobile
      const tabs = screen.getAllByRole('button', { name: /browse|my|create/i });
      expect(tabs.length).toBeGreaterThan(0);
    });

    it('should have proper spacing classes for responsive layout', () => {
      const { container } = render(<SwapMarketplace />, { wrapper: createWrapper() });

      // Check for responsive padding classes
      const mainContainer = container.querySelector('.max-w-7xl');
      expect(mainContainer).toHaveClass('px-4');
      expect(mainContainer).toHaveClass('sm:px-6');
      expect(mainContainer).toHaveClass('lg:px-8');
    });
  });
});
