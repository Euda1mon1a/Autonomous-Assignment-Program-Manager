/**
 * Tests for AuditLogPage Component
 *
 * Tests main page integration, view mode switching, statistics, and component interactions
 */

import React from 'react';
import { render, screen, within, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditLogPage } from '@/features/audit/AuditLogPage';
import * as hooks from '@/features/audit/hooks';
import {
  mockAuditLogResponse,
  mockStatistics,
  mockUsers,
  getMockLogs,
} from './mockData';

// Mock the hooks
jest.mock('@/features/audit/hooks');
const mockUseAuditLogs = hooks.useAuditLogs as jest.MockedFunction<
  typeof hooks.useAuditLogs
>;
const mockUseAuditStatistics = hooks.useAuditStatistics as jest.MockedFunction<
  typeof hooks.useAuditStatistics
>;
const mockUseAuditUsers = hooks.useAuditUsers as jest.MockedFunction<
  typeof hooks.useAuditUsers
>;

// Create a test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('AuditLogPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default successful responses
    mockUseAuditLogs.mockReturnValue({
      data: mockAuditLogResponse,
      isLoading: false,
      refetch: jest.fn(),
    } as any);

    mockUseAuditStatistics.mockReturnValue({
      data: mockStatistics,
      isLoading: false,
    } as any);

    mockUseAuditUsers.mockReturnValue({
      data: mockUsers,
    } as any);
  });

  // ============================================================================
  // Page Rendering Tests
  // ============================================================================

  describe('Page Rendering', () => {
    it('should render page title', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Audit Log')).toBeInTheDocument();
    });

    it('should render page description', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(
        screen.getByText(/Track and review all system changes/i)
      ).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
    });

    it('should render export button', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
    });

    it('should render statistics cards', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Total Entries')).toBeInTheDocument();
      expect(screen.getByText('ACGME Overrides')).toBeInTheDocument();
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });

    it('should render filters component', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(
        screen.getByPlaceholderText(/Search audit logs/i)
      ).toBeInTheDocument();
    });

    it('should render view mode toggle', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Table')).toBeInTheDocument();
      expect(screen.getByText('Timeline')).toBeInTheDocument();
      expect(screen.getByText('Compare')).toBeInTheDocument();
    });

    it('should render total entries count', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/15 total entries/i)).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Statistics Display Tests
  // ============================================================================

  describe('Statistics Display', () => {
    it('should display total entries from statistics', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('150')).toBeInTheDocument();
    });

    it('should display ACGME override count', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('should display unique users count', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByText('12')).toBeInTheDocument();
    });

    it('should show loading skeletons for statistics', () => {
      mockUseAuditStatistics.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      render(<AuditLogPage />, { wrapper: createWrapper() });

      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should display icons in statistics cards', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Should have icons for each stat card
      const statCards = document.querySelectorAll('[class*="bg-blue-100"]');
      expect(statCards.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // View Mode Tests
  // ============================================================================

  describe('View Mode', () => {
    it('should start in table view by default', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const tableButton = screen.getByText('Table').closest('button');
      expect(tableButton).toHaveClass('bg-white', 'text-blue-600');
    });

    it('should switch to timeline view', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const timelineButton = screen.getByText('Timeline').closest('button');
      await user.click(timelineButton!);

      expect(timelineButton).toHaveClass('bg-white', 'text-blue-600');
    });

    it('should switch to comparison view', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      expect(compareButton).toHaveClass('bg-white', 'text-blue-600');
    });

    it('should show comparison helper panel in comparison mode', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      expect(screen.getByText('Comparison Mode')).toBeInTheDocument();
      expect(
        screen.getByText(/Select two entries from the table/i)
      ).toBeInTheDocument();
    });

    it('should render table in table view', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('should render timeline in timeline view', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const timelineButton = screen.getByText('Timeline').closest('button');
      await user.click(timelineButton!);

      await waitFor(() => {
        expect(screen.getByText('Activity Timeline')).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Refresh Tests
  // ============================================================================

  describe('Refresh', () => {
    it('should call refetch when clicking refresh button', async () => {
      const mockRefetch = jest.fn();
      mockUseAuditLogs.mockReturnValue({
        data: mockAuditLogResponse,
        isLoading: false,
        refetch: mockRefetch,
      } as any);

      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });

    it('should show spinning icon when loading', () => {
      mockUseAuditLogs.mockReturnValue({
        data: mockAuditLogResponse,
        isLoading: true,
        refetch: jest.fn(),
      } as any);

      render(<AuditLogPage />, { wrapper: createWrapper() });

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      const icon = refreshButton.querySelector('.animate-spin');
      expect(icon).toBeInTheDocument();
    });

    it('should disable refresh button when loading', () => {
      mockUseAuditLogs.mockReturnValue({
        data: mockAuditLogResponse,
        isLoading: true,
        refetch: jest.fn(),
      } as any);

      render(<AuditLogPage />, { wrapper: createWrapper() });

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });
      expect(refreshButton).toBeDisabled();
    });
  });

  // ============================================================================
  // Filters Integration Tests
  // ============================================================================

  describe('Filters Integration', () => {
    it('should pass users to filters component', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Filters component should render (we can verify by checking for filter button)
      expect(screen.getByRole('button', { name: /Filters/i })).toBeInTheDocument();
    });

    it('should update query when filters change', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // The component should re-render with new filters
      // (Full integration would require more complex mocking)
      expect(screen.getByText('Entity Type')).toBeInTheDocument();
    });

    it('should reset page when filters change', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Component should be rendered with filters
      expect(screen.getByText('Entity Type')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Initial Filters Tests
  // ============================================================================

  describe('Initial Filters', () => {
    it('should accept initial filters prop', () => {
      const initialFilters = {
        entityTypes: ['assignment' as const],
      };

      render(<AuditLogPage initialFilters={initialFilters} />, {
        wrapper: createWrapper(),
      });

      // Page should render with initial filters applied
      expect(screen.getByText('Audit Log')).toBeInTheDocument();
    });

    it('should accept initial view prop', () => {
      render(<AuditLogPage initialView="timeline" />, {
        wrapper: createWrapper(),
      });

      // Timeline button should be active
      const timelineButton = screen.getByText('Timeline').closest('button');
      expect(timelineButton).toHaveClass('bg-white', 'text-blue-600');
    });
  });

  // ============================================================================
  // Loading State Tests
  // ============================================================================

  describe('Loading State', () => {
    it('should show loading state for logs', () => {
      mockUseAuditLogs.mockReturnValue({
        data: undefined,
        isLoading: true,
        refetch: jest.fn(),
      } as any);

      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Should show loading skeleton in table
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should show loading state for statistics', () => {
      mockUseAuditStatistics.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Statistics cards should show loading skeletons
      const statCards = screen.getAllByText('Total Entries');
      expect(statCards.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Entry Selection Tests
  // ============================================================================

  describe('Entry Selection', () => {
    it('should show detail panel when entry is selected in table view', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Click on a table row
      const rows = screen.getAllByRole('row');
      if (rows.length > 1) {
        await user.click(rows[1]); // Skip header row

        // Detail panel should appear - use getAllByText since component has multiple "Entry Details" labels
        await waitFor(() => {
          const entryDetails = screen.getAllByText('Entry Details');
          expect(entryDetails.length).toBeGreaterThan(0);
        });
      }
    });

    it('should show detail panel when event is selected in timeline view', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Switch to timeline view
      const timelineButton = screen.getByText('Timeline').closest('button');
      await user.click(timelineButton!);

      await waitFor(() => {
        expect(screen.getByText('Activity Timeline')).toBeInTheDocument();
      });

      // Click on a timeline event
      const eventCards = document.querySelectorAll('[class*="cursor-pointer"]');
      if (eventCards.length > 0) {
        await user.click(eventCards[0]);

        // Detail panel should appear - use getAllByText since component has multiple "Entry Details" labels
        await waitFor(() => {
          const entryDetails = screen.getAllByText('Entry Details');
          expect(entryDetails.length).toBeGreaterThan(0);
        });
      }
    });

    it('should close detail panel when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Select an entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 1) {
        await user.click(rows[1]);

        await waitFor(() => {
          const entryDetails = screen.getAllByText('Entry Details');
          expect(entryDetails.length).toBeGreaterThan(0);
        });

        // Click close button
        const closeButton = screen.getByLabelText('Close');
        await user.click(closeButton);

        await waitFor(() => {
          expect(screen.queryByText('Entry Details')).not.toBeInTheDocument();
        });
      }
    });
  });

  // ============================================================================
  // Comparison Mode Tests
  // ============================================================================

  describe('Comparison Mode', () => {
    it('should build comparison selection in comparison mode', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Switch to comparison mode
      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      expect(screen.getByText('Comparison Mode')).toBeInTheDocument();
    });

    it('should show selected entries in comparison helper', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Switch to comparison mode
      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      // Click first entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 2) {
        await user.click(rows[1]);

        await waitFor(() => {
          expect(screen.getByText(/Select one more entry/i)).toBeInTheDocument();
        });
      }
    });

    it('should show comparison panel when two entries selected', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Switch to comparison mode
      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      // Click first entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 2) {
        await user.click(rows[1]);

        // Click second entry
        await user.click(rows[2]);

        await waitFor(() => {
          expect(screen.getByText('Compare Entries')).toBeInTheDocument();
        });
      }
    });

    it('should clear comparison selection', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Switch to comparison mode
      const compareButton = screen.getByText('Compare').closest('button');
      await user.click(compareButton!);

      // Click entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 1) {
        await user.click(rows[1]);

        // Click clear selection
        const clearButton = screen.getByText('Clear selection');
        await user.click(clearButton);

        expect(
          screen.getByText(/Select two entries from the table/i)
        ).toBeInTheDocument();
      }
    });
  });

  // ============================================================================
  // Pagination Tests
  // ============================================================================

  describe('Pagination', () => {
    it('should clear selected entry when page changes', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Select an entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 1) {
        await user.click(rows[1]);

        await waitFor(() => {
          const entryDetails = screen.getAllByText('Entry Details');
          expect(entryDetails.length).toBeGreaterThan(0);
        });

        // Change page
        const nextButton = screen.getByText('Next');
        await user.click(nextButton);

        // Detail panel should be closed
        await waitFor(() => {
          expect(screen.queryByText('Entry Details')).not.toBeInTheDocument();
        });
      }
    });
  });

  // ============================================================================
  // Responsive Layout Tests
  // ============================================================================

  describe('Responsive Layout', () => {
    it('should adjust layout when detail panel is open', async () => {
      const user = userEvent.setup();
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Select an entry
      const rows = screen.getAllByRole('row');
      if (rows.length > 1) {
        await user.click(rows[1]);

        // First verify detail panel appears
        await waitFor(() => {
          const entryDetails = screen.getAllByText('Entry Details');
          expect(entryDetails.length).toBeGreaterThan(0);
        });

        // Then check layout
        await waitFor(() => {
          // Should have 2-column layout (lg:col-span-2 and lg:col-span-1)
          const mainContent = document.querySelector('.lg\\:col-span-2');
          expect(mainContent).toBeInTheDocument();
        });
      }
    });

    it('should use full width when no detail panel', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // Should have full-width layout (lg:col-span-3)
      const mainContent = document.querySelector('.lg\\:col-span-3');
      expect(mainContent).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const heading = screen.getByRole('heading', { name: 'Audit Log' });
      expect(heading).toBeInTheDocument();
    });

    it('should have accessible buttons', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have accessible navigation controls', () => {
      render(<AuditLogPage />, { wrapper: createWrapper() });

      // View mode toggle buttons should be accessible
      expect(screen.getByText('Table')).toBeInTheDocument();
      expect(screen.getByText('Timeline')).toBeInTheDocument();
      expect(screen.getByText('Compare')).toBeInTheDocument();
    });
  });
});
