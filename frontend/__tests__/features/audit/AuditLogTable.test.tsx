/**
 * Tests for AuditLogTable Component
 *
 * Tests table rendering, sorting, pagination, expandable rows, and interactions
 */

import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditLogTable } from '@/features/audit/AuditLogTable';
import type { AuditLogSort } from '@/features/audit/types';
import { mockAuditLogs, getMockLogs } from './mockData';

describe('AuditLogTable', () => {
  const mockOnPageChange = jest.fn();
  const mockOnPageSizeChange = jest.fn();
  const mockOnSortChange = jest.fn();
  const mockOnEntrySelect = jest.fn();

  const defaultProps = {
    logs: getMockLogs(5),
    total: 50,
    page: 1,
    pageSize: 10,
    sort: { field: 'timestamp' as const, direction: 'desc' as const },
    onPageChange: mockOnPageChange,
    onPageSizeChange: mockOnPageSizeChange,
    onSortChange: mockOnSortChange,
    onEntrySelect: mockOnEntrySelect,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================================
  // Rendering Tests
  // ============================================================================

  describe('Rendering', () => {
    it('should render table with audit log entries', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText(/Dr. John Doe - ICU/i)).toBeInTheDocument();
      expect(screen.getByText(/Dr. Jane Smith/i)).toBeInTheDocument();
    });

    it('should render all table headers', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByText('Timestamp')).toBeInTheDocument();
      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('Action')).toBeInTheDocument();
      expect(screen.getByText('Entity')).toBeInTheDocument();
      expect(screen.getByText('Severity')).toBeInTheDocument();
      expect(screen.getByText('Reason')).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(<AuditLogTable {...defaultProps} isLoading={true} />);

      // Loading state may not show table, check for skeletons in document
      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should render empty state when no logs', () => {
      render(<AuditLogTable {...defaultProps} logs={[]} total={0} />);

      expect(screen.getByText('No audit logs found')).toBeInTheDocument();
      expect(screen.getByText(/Try adjusting your filters/i)).toBeInTheDocument();
    });

    it('should render action badges with correct colors', () => {
      render(<AuditLogTable {...defaultProps} />);

      // Created action should be present
      const createdBadge = screen.getByText('Created');
      expect(createdBadge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('should render severity badges', () => {
      render(<AuditLogTable {...defaultProps} />);

      const severityBadges = screen.getAllByText(/info|warning|critical/i);
      expect(severityBadges.length).toBeGreaterThan(0);
    });

    it('should highlight ACGME override entries', () => {
      const overrideLogs = mockAuditLogs.filter((log) => log.acgmeOverride);
      if (overrideLogs.length === 0) {
        // Skip test if no override logs in mock data
        return;
      }
      render(<AuditLogTable {...defaultProps} logs={overrideLogs} />);

      // Should find ACGME Override indicator (badge or text)
      const overrideElements = screen.queryAllByText(/ACGME|Override/i);
      expect(overrideElements.length).toBeGreaterThan(0);
    });
  });

  // ============================================================================
  // Sorting Tests
  // ============================================================================

  describe('Sorting', () => {
    it('should call onSortChange when clicking timestamp header', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const timestampHeader = screen.getByText('Timestamp').closest('th');
      await user.click(timestampHeader!);

      expect(mockOnSortChange).toHaveBeenCalledWith({
        field: 'timestamp',
        direction: 'asc',
      });
    });

    it('should call onSortChange when clicking user header', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const userHeader = screen.getByText('User').closest('th');
      await user.click(userHeader!);

      expect(mockOnSortChange).toHaveBeenCalledWith({
        field: 'user',
        direction: 'desc',
      });
    });

    it('should call onSortChange when clicking action header', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const actionHeader = screen.getByText('Action').closest('th');
      await user.click(actionHeader!);

      expect(mockOnSortChange).toHaveBeenCalledWith({
        field: 'action',
        direction: 'desc',
      });
    });

    it('should toggle sort direction on repeated clicks', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<AuditLogTable {...defaultProps} />);

      const timestampHeader = screen.getByText('Timestamp').closest('th');

      // First click - should change to asc
      await user.click(timestampHeader!);
      expect(mockOnSortChange).toHaveBeenCalledWith({
        field: 'timestamp',
        direction: 'asc',
      });

      // Simulate sort direction change with rerender
      mockOnSortChange.mockClear();
      const newSort: AuditLogSort = { field: 'timestamp', direction: 'asc' };
      rerender(<AuditLogTable {...defaultProps} sort={newSort} />);

      // Second click - should change back to desc
      const timestampHeaderAgain = screen.getByText('Timestamp').closest('th');
      await user.click(timestampHeaderAgain!);
      expect(mockOnSortChange).toHaveBeenCalledWith({
        field: 'timestamp',
        direction: 'desc',
      });
    });

    it('should display sort indicators', () => {
      render(<AuditLogTable {...defaultProps} />);

      // Should show down arrow for descending timestamp sort
      const timestampHeader = screen.getByText('Timestamp').closest('th');
      const chevronDown = timestampHeader?.querySelector('svg');
      expect(chevronDown).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Pagination Tests
  // ============================================================================

  describe('Pagination', () => {
    it('should render pagination controls', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Last')).toBeInTheDocument();
    });

    it('should display current page information', () => {
      render(<AuditLogTable {...defaultProps} />);

      // Page info shows entries count - verify text exists in the document
      const bodyText = document.body.textContent || '';
      expect(bodyText).toMatch(/Showing.*entries/i);
    });

    it('should call onPageChange when clicking Next button', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });

    it('should call onPageChange when clicking Previous button', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} page={2} />);

      const prevButton = screen.getByText('Previous');
      await user.click(prevButton);

      expect(mockOnPageChange).toHaveBeenCalledWith(1);
    });

    it('should call onPageChange when clicking page number', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      // Find page 2 button
      const page2Button = screen.getByRole('button', { name: '2' });
      await user.click(page2Button);

      expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });

    it('should disable Previous and First buttons on first page', () => {
      render(<AuditLogTable {...defaultProps} page={1} />);

      const firstButton = screen.getByText('First');
      const prevButton = screen.getByText('Previous');

      expect(firstButton).toBeDisabled();
      expect(prevButton).toBeDisabled();
    });

    it('should disable Next and Last buttons on last page', () => {
      render(<AuditLogTable {...defaultProps} page={5} total={50} pageSize={10} />);

      const nextButton = screen.getByText('Next');
      const lastButton = screen.getByText('Last');

      expect(nextButton).toBeDisabled();
      expect(lastButton).toBeDisabled();
    });

    it('should call onPageSizeChange when changing page size', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const pageSizeSelect = screen.getByDisplayValue('10');
      await user.selectOptions(pageSizeSelect, '25');

      expect(mockOnPageSizeChange).toHaveBeenCalledWith(25);
    });

    it('should render all page size options', () => {
      render(<AuditLogTable {...defaultProps} />);

      const pageSizeSelect = screen.getByDisplayValue('10');
      const options = within(pageSizeSelect as HTMLSelectElement).getAllByRole('option');

      expect(options).toHaveLength(4); // 10, 25, 50, 100
      expect(options.map((o) => o.textContent)).toEqual(['10', '25', '50', '100']);
    });
  });

  // ============================================================================
  // Expandable Rows Tests
  // ============================================================================

  describe('Expandable Rows', () => {
    it('should expand row when clicking expand button', async () => {
      const user = userEvent.setup();
      const logsWithChanges = mockAuditLogs.slice(0, 3);
      render(<AuditLogTable {...defaultProps} logs={logsWithChanges} />);

      // Find the expand button (chevron right icon)
      const expandButtons = screen.getAllByLabelText('Expand details');
      await user.click(expandButtons[0]);

      // Check if changes are displayed
      expect(screen.getByText('Changes')).toBeInTheDocument();
    });

    it('should collapse row when clicking collapse button', async () => {
      const user = userEvent.setup();
      const logsWithChanges = mockAuditLogs.slice(0, 3);
      render(<AuditLogTable {...defaultProps} logs={logsWithChanges} />);

      // Expand first
      const expandButton = screen.getAllByLabelText('Expand details')[0];
      await user.click(expandButton);

      // Now collapse
      const collapseButton = screen.getByLabelText('Collapse details');
      await user.click(collapseButton);

      // Changes should no longer be visible
      expect(screen.queryByText('Changes')).not.toBeInTheDocument();
    });

    it('should display field changes when expanded', async () => {
      const user = userEvent.setup();
      const logsWithChanges = mockAuditLogs.slice(0, 1);
      render(<AuditLogTable {...defaultProps} logs={logsWithChanges} />);

      const expandButton = screen.getByLabelText('Expand details');
      await user.click(expandButton);

      // Check for change details
      expect(screen.getByText('Assignment Date')).toBeInTheDocument();
      expect(screen.getByText('Rotation')).toBeInTheDocument();
    });

    it('should display ACGME override details when expanded', async () => {
      const user = userEvent.setup();
      const overrideLogs = mockAuditLogs.filter((log) => log.acgmeOverride);
      render(<AuditLogTable {...defaultProps} logs={overrideLogs.slice(0, 1)} />);

      const expandButton = screen.getByLabelText('Expand details');
      await user.click(expandButton);

      expect(screen.getByText(/ACGME Override/i)).toBeInTheDocument();
      expect(screen.getByText(/Emergency coverage needed/i)).toBeInTheDocument();
    });

    it('should display metadata when expanded', async () => {
      const user = userEvent.setup();
      const logsWithMetadata = mockAuditLogs.filter((log) => log.metadata);
      render(<AuditLogTable {...defaultProps} logs={logsWithMetadata.slice(0, 1)} />);

      const expandButton = screen.getByLabelText('Expand details');
      await user.click(expandButton);

      expect(screen.getByText('Additional Details')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Selection Tests
  // ============================================================================

  describe('Selection', () => {
    it('should call onEntrySelect when clicking a row', async () => {
      const user = userEvent.setup();
      render(<AuditLogTable {...defaultProps} />);

      const rows = screen.getAllByRole('row');
      // Skip header row, click first data row
      await user.click(rows[1]);

      expect(mockOnEntrySelect).toHaveBeenCalledWith(
        expect.objectContaining({ id: getMockLogs(5)[0].id })
      );
    });

    it('should highlight selected row', () => {
      const selectedId = getMockLogs(5)[0].id;
      render(<AuditLogTable {...defaultProps} selectedEntryId={selectedId} />);

      // Find the row with the selected entry
      const selectedRow = screen.getByText(/Dr. John Doe - ICU/i).closest('tr');
      expect(selectedRow).toHaveClass('bg-blue-50');
    });

    it('should not propagate click when clicking expand button', async () => {
      const user = userEvent.setup();
      const logsWithChanges = mockAuditLogs.slice(0, 3);
      render(<AuditLogTable {...defaultProps} logs={logsWithChanges} />);

      const expandButton = screen.getAllByLabelText('Expand details')[0];
      await user.click(expandButton);

      // onEntrySelect should not have been called
      expect(mockOnEntrySelect).not.toHaveBeenCalled();
    });
  });

  // ============================================================================
  // Data Display Tests
  // ============================================================================

  describe('Data Display', () => {
    it('should format timestamps correctly', () => {
      render(<AuditLogTable {...defaultProps} />);

      // Should display formatted date like "Dec 17, 2025 10:30:00"
      expect(screen.getByText(/Dec 17, 2025/i)).toBeInTheDocument();
    });

    it('should display user names', () => {
      render(<AuditLogTable {...defaultProps} />);

      // User names may appear multiple times
      expect(screen.getAllByText('Dr. Sarah Chen').length).toBeGreaterThan(0);
    });

    it('should display entity type labels', () => {
      render(<AuditLogTable {...defaultProps} />);

      // Entity labels may appear multiple times
      expect(screen.getAllByText('Assignment').length).toBeGreaterThan(0);
    });

    it('should display entity names when available', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByText(/Dr. John Doe - ICU/i)).toBeInTheDocument();
      expect(screen.getByText(/Dr. Jane Smith/i)).toBeInTheDocument();
    });

    it('should display reasons when available', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByText(/New resident assignment/i)).toBeInTheDocument();
      expect(screen.getByText(/Annual progression update/i)).toBeInTheDocument();
    });

    it('should display dash when no reason', () => {
      const logsWithoutReason = [
        {
          ...getMockLogs(1)[0],
          reason: undefined,
        },
      ];
      render(<AuditLogTable {...defaultProps} logs={logsWithoutReason} />);

      expect(screen.getByText('-')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have proper ARIA labels on expand buttons', () => {
      const logsWithChanges = mockAuditLogs.slice(0, 3);
      render(<AuditLogTable {...defaultProps} logs={logsWithChanges} />);

      const expandButtons = screen.getAllByLabelText('Expand details');
      expect(expandButtons.length).toBeGreaterThan(0);
    });

    it('should have accessible table structure', () => {
      render(<AuditLogTable {...defaultProps} />);

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();

      const headers = within(table).getAllByRole('columnheader');
      expect(headers.length).toBeGreaterThan(0);
    });

    it('should have accessible pagination buttons', () => {
      render(<AuditLogTable {...defaultProps} />);

      expect(screen.getByRole('button', { name: 'First' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Last' })).toBeInTheDocument();
    });
  });
});
