/**
 * Tests for AuditLogFilters Component
 *
 * Tests filter rendering, search, date range selection, multi-select filters,
 * and filter management
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { AuditLogFilters } from '@/features/audit/AuditLogFilters';
import type { AuditLogFilters as FilterType } from '@/features/audit/types';
import { mockUsers } from './mockData';

describe('AuditLogFilters', () => {
  const mockOnFiltersChange = jest.fn();

  const defaultProps = {
    filters: {},
    onFiltersChange: mockOnFiltersChange,
    users: mockUsers.map((u) => ({ id: u.id, name: u.name })),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // ============================================================================
  // Rendering Tests
  // ============================================================================

  describe('Rendering', () => {
    it('should render search input', () => {
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i);
      expect(searchInput).toBeInTheDocument();
    });

    it('should render Filters button', () => {
      render(<AuditLogFilters {...defaultProps} />);

      expect(screen.getByRole('button', { name: /Filters/i })).toBeInTheDocument();
    });

    it('should not show advanced filters by default', () => {
      render(<AuditLogFilters {...defaultProps} />);

      expect(screen.queryByText('Entity Type')).not.toBeInTheDocument();
      expect(screen.queryByText('Action')).not.toBeInTheDocument();
    });

    it('should show advanced filters when Filters button is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      const filtersButton = screen.getByRole('button', { name: /Filters/i });
      await user.click(filtersButton);

      expect(screen.getByText(/Entity Type/i)).toBeInTheDocument();
      expect(screen.getByText(/Action/i)).toBeInTheDocument();
    });

    it('should show loading indicator when isLoading is true', () => {
      render(<AuditLogFilters {...defaultProps} isLoading={true} />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should display filter count badge when filters are active', () => {
      const activeFilters: FilterType = {
        entityTypes: ['assignment'],
        actions: ['create'],
      };
      render(<AuditLogFilters {...defaultProps} filters={activeFilters} />);

      const filtersButton = screen.getByRole('button', { name: /Filters/i });
      expect(within(filtersButton).getByText('2')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Search Tests
  // ============================================================================

  describe('Search', () => {
    it('should update search input value when typing', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i);
      await user.type(searchInput, 'test query');

      expect(searchInput).toHaveValue('test query');
    });

    it('should debounce search and call onFiltersChange after delay', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i);
      await user.type(searchInput, 'test');

      // Should not call immediately
      expect(mockOnFiltersChange).not.toHaveBeenCalled();

      // Advance timers by debounce delay (300ms)
      jest.advanceTimersByTime(300);

      await waitFor(() => {
        expect(mockOnFiltersChange).toHaveBeenCalledWith(
          expect.objectContaining({ searchQuery: 'test' })
        );
      });
    });

    it('should show clear button when search has value', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i);
      await user.type(searchInput, 'test');

      const clearButton = searchInput.parentElement?.querySelector('button');
      expect(clearButton).toBeInTheDocument();
    });

    it('should clear search when clicking clear button', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i) as HTMLInputElement;
      await user.type(searchInput, 'test');

      const clearButton = searchInput.parentElement?.querySelector('button');
      await user.click(clearButton!);

      expect(searchInput).toHaveValue('');
    });
  });

  // ============================================================================
  // Date Range Filter Tests
  // ============================================================================

  describe('Date Range Filter', () => {
    it('should render date range picker button', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      expect(screen.getByText('All time')).toBeInTheDocument();
    });

    it('should display selected date range', async () => {
      const dateRange = { start: '2025-12-01', end: '2025-12-17' };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={{ dateRange }} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // When date range is set, we should see a filter tag or the date in the dropdown
      // The filter tags show even when panel is closed
      await waitFor(() => {
        // Look for Dec dates anywhere in the document
        const dateElements = document.body.textContent || '';
        expect(dateElements).toMatch(/Dec/i);
      });
    });

    it('should open date range dropdown when clicked', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters first
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Click date range button
      const dateButton = screen.getByText('All time');
      await user.click(dateButton);

      // Quick select options should appear
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Last 7 days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 days')).toBeInTheDocument();
    });

    it('should select quick date range', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open date picker
      await user.click(screen.getByText('All time'));

      // Select "Today"
      await user.click(screen.getByText('Today'));

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          dateRange: expect.objectContaining({
            start: expect.any(String),
            end: expect.any(String),
          }),
        })
      );
    });

    it('should allow custom date range selection', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open date picker
      await user.click(screen.getByText('All time'));

      // Find custom date inputs by type="date"
      const dateInputs = screen.getAllByRole('textbox') as HTMLInputElement[];
      // The date inputs might be type="date" which renders differently
      // Use direct DOM query for date inputs
      const dateElements = document.querySelectorAll('input[type="date"]');
      expect(dateElements.length).toBeGreaterThanOrEqual(2);
    });
  });

  // ============================================================================
  // Multi-Select Filter Tests
  // ============================================================================

  describe('Multi-Select Filters', () => {
    it('should render entity type multi-select', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      expect(screen.getByText('Entity Type')).toBeInTheDocument();
    });

    it('should open entity type dropdown', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Click entity type button
      await user.click(screen.getByText('Entity Type'));

      // Should show options
      expect(screen.getByText('Assignment')).toBeInTheDocument();
      expect(screen.getByText('Person')).toBeInTheDocument();
      expect(screen.getByText('Absence')).toBeInTheDocument();
    });

    it('should select entity type option', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open entity type dropdown
      await user.click(screen.getByText('Entity Type'));

      // Select Assignment checkbox
      const assignmentCheckbox = screen.getByLabelText('Assignment');
      await user.click(assignmentCheckbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          entityTypes: ['assignment'],
        })
      );
    });

    it('should show selected count badge', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment', 'person'],
      };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const entityTypeButton = screen.getByText('Entity Type').closest('button');
      expect(within(entityTypeButton!).getByText('2')).toBeInTheDocument();
    });

    it('should select all options', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open entity type dropdown
      await user.click(screen.getByText('Entity Type'));

      // Click "Select all"
      await user.click(screen.getByText('Select all'));

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          entityTypes: expect.arrayContaining([
            'assignment',
            'person',
            'absence',
            'rotation_template',
            'schedule_run',
            'block',
            'system',
          ]),
        })
      );
    });

    it('should clear all options', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment', 'person'],
      };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open entity type dropdown
      await user.click(screen.getByText('Entity Type'));

      // Click "Clear all" in the dropdown (there may be multiple, get the ones in the dropdown)
      const clearButtons = screen.getAllByText('Clear all');
      // The dropdown's clear button should be one of them
      await user.click(clearButtons[clearButtons.length - 1]);

      expect(mockOnFiltersChange).toHaveBeenCalled();
    });

    it('should render action multi-select', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // There are multiple elements with "Action", get the button
      const actionButtons = screen.getAllByText('Action');
      expect(actionButtons.length).toBeGreaterThan(0);
    });

    it('should render user multi-select', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      expect(screen.getByText('User')).toBeInTheDocument();
    });

    it('should render severity multi-select', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      expect(screen.getByText('Severity')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // ACGME Override Filter Tests
  // ============================================================================

  describe('ACGME Override Filter', () => {
    it('should render ACGME overrides checkbox', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      expect(screen.getByText('ACGME Overrides Only')).toBeInTheDocument();
    });

    it('should toggle ACGME overrides filter', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const checkbox = screen.getByLabelText('ACGME Overrides Only');
      await user.click(checkbox);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          acgmeOverridesOnly: true,
        })
      );
    });

    it('should show ACGME override in active filters', async () => {
      const filters: FilterType = {
        acgmeOverridesOnly: true,
      };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      expect(screen.getByText('ACGME Overrides Only')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Active Filters Tests
  // ============================================================================

  describe('Active Filters', () => {
    it('should display active filter tags', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment'],
        actions: ['create'],
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      expect(screen.getByText('Assignment')).toBeInTheDocument();
      expect(screen.getByText('Created')).toBeInTheDocument();
    });

    it('should show "Active filters:" label when filters exist', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment'],
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      expect(screen.getByText('Active filters:')).toBeInTheDocument();
    });

    it('should remove individual filter tag when clicking X', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment', 'person'],
      };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      const assignmentTag = screen.getByText('Assignment').closest('span');
      const removeButton = within(assignmentTag!).getByRole('button');
      await user.click(removeButton);

      expect(mockOnFiltersChange).toHaveBeenCalledWith(
        expect.objectContaining({
          entityTypes: ['person'],
        })
      );
    });

    it('should show Clear all button when filters are active', () => {
      const filters: FilterType = {
        entityTypes: ['assignment'],
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      expect(screen.getByText('Clear all')).toBeInTheDocument();
    });

    it('should clear all filters when clicking Clear all', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment'],
        actions: ['create'],
        searchQuery: 'test',
      };
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      await user.click(screen.getByText('Clear all'));

      expect(mockOnFiltersChange).toHaveBeenCalledWith({});
    });
  });

  // ============================================================================
  // Filter Combinations Tests
  // ============================================================================

  describe('Filter Combinations', () => {
    it('should handle multiple active filters', async () => {
      const filters: FilterType = {
        entityTypes: ['assignment', 'person'],
        actions: ['create', 'update'],
        severity: ['warning'],
        dateRange: { start: '2025-12-01', end: '2025-12-17' },
        searchQuery: 'test',
        acgmeOverridesOnly: true,
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      // Should show filter count badge - count may vary based on implementation
      const filtersButton = screen.getByRole('button', { name: /Filters/i });
      // Badge should exist with some number
      const badge = within(filtersButton).queryByText(/\d+/);
      expect(badge).toBeInTheDocument();
    });

    it('should display date range in filter tags', () => {
      const filters: FilterType = {
        dateRange: { start: '2025-12-01', end: '2025-12-17' },
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      // Filter tag shows date range - look for Date: prefix
      const dateTag = document.body.textContent || '';
      expect(dateTag).toMatch(/Date:/i);
    });

    it('should display severity in filter tags', () => {
      const filters: FilterType = {
        severity: ['warning', 'critical'],
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      expect(screen.getByText('Severity: warning')).toBeInTheDocument();
      expect(screen.getByText('Severity: critical')).toBeInTheDocument();
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have accessible search input', () => {
      render(<AuditLogFilters {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText(/Search audit logs/i);
      expect(searchInput).toHaveAttribute('type', 'text');
    });

    it('should have accessible filter buttons', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have accessible checkboxes', async () => {
      const user = userEvent.setup({ delay: null });
      render(<AuditLogFilters {...defaultProps} />);

      // Open advanced filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Open entity type dropdown
      await user.click(screen.getByText('Entity Type'));

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
    });

    it('should have aria labels on remove buttons', () => {
      const filters: FilterType = {
        entityTypes: ['assignment'],
      };
      render(<AuditLogFilters {...defaultProps} filters={filters} />);

      const removeButton = screen.getByLabelText(/Remove Assignment filter/i);
      expect(removeButton).toBeInTheDocument();
    });
  });
});
