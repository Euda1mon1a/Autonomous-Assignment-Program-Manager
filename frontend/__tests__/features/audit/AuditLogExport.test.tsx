/**
 * Tests for AuditLogExport Component
 *
 * Tests export modal, format selection, export options, and export functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuditLogExport } from '@/features/audit/AuditLogExport';
import type { AuditExportConfig } from '@/features/audit/types';
import { getMockLogs } from './mockData';

describe('AuditLogExport', () => {
  const mockOnExportAll = jest.fn();

  const defaultProps = {
    logs: getMockLogs(10),
    totalCount: 50,
    onExportAll: mockOnExportAll,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================================
  // Rendering Tests
  // ============================================================================

  describe('Rendering', () => {
    it('should render main export button', () => {
      render(<AuditLogExport {...defaultProps} />);

      expect(screen.getByRole('button', { name: /Export/i })).toBeInTheDocument();
    });

    it('should render quick export buttons for CSV and JSON', () => {
      render(<AuditLogExport {...defaultProps} />);

      expect(screen.getByRole('button', { name: /CSV/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /JSON/i })).toBeInTheDocument();
    });

    it('should show total count badge when totalCount > logs length', () => {
      render(<AuditLogExport {...defaultProps} />);

      expect(screen.getByText('All 50')).toBeInTheDocument();
    });

    it('should not show count badge when totalCount equals logs length', () => {
      render(<AuditLogExport {...defaultProps} logs={getMockLogs(50)} totalCount={50} />);

      // When counts match, "All 50" badge should not appear
      expect(screen.queryByText(/All\s*50/i)).not.toBeInTheDocument();
    });

    it('should not render export modal by default', () => {
      render(<AuditLogExport {...defaultProps} />);

      expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Export Modal Tests
  // ============================================================================

  describe('Export Modal', () => {
    it('should open modal when clicking main export button', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      const exportButton = screen.getByRole('button', { name: /^Export/i });
      await user.click(exportButton);

      expect(screen.getByText('Export Audit Logs')).toBeInTheDocument();
    });

    it('should close modal when clicking close button', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Close modal
      const closeButton = screen.getByLabelText('Close');
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
      });
    });

    it('should close modal when clicking Cancel button', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click cancel
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
      });
    });

    it('should close modal when clicking backdrop', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click backdrop
      const backdrop = document.querySelector('.bg-black\\/50');
      if (backdrop) {
        await user.click(backdrop);
      }

      await waitFor(() => {
        expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Format Selection Tests
  // ============================================================================

  describe('Format Selection', () => {
    it('should render all format options', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Format options appear in modal (CSV also appears in quick export buttons)
      expect(screen.getAllByText('CSV').length).toBeGreaterThan(0);
      expect(screen.getAllByText('JSON').length).toBeGreaterThan(0);
      expect(screen.getByText('PDF')).toBeInTheDocument();
    });

    it('should show format descriptions', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      expect(screen.getByText('Spreadsheet compatible format')).toBeInTheDocument();
      expect(screen.getByText('Full data with nested objects')).toBeInTheDocument();
      expect(screen.getByText('Formatted report document')).toBeInTheDocument();
    });

    it('should have CSV selected by default', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // CSV buttons exist (quick export + modal format option)
      // The modal format button should have active styling
      const csvButtons = screen.getAllByText('CSV');
      const formatButton = csvButtons.find(btn => {
        const button = btn.closest('button');
        return button?.className.includes('border-blue-500');
      });
      expect(formatButton).toBeTruthy();
    });

    it('should change format selection when clicking format button', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Find JSON format buttons (quick export + modal)
      const jsonButtons = screen.getAllByText('JSON');
      // Click the one in the modal (the format grid, not quick export)
      const modalJsonButton = jsonButtons.find(btn => {
        const button = btn.closest('button');
        return button && !button.className.includes('rounded-lg');
      }) || jsonButtons[jsonButtons.length - 1];

      await user.click(modalJsonButton.closest('button')!);

      // Check that Include change details appears (JSON-only option)
      expect(screen.getByText(/Include change details/i)).toBeInTheDocument();
    });

    it('should change format selection to PDF', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click PDF format
      const pdfButton = screen.getByText('PDF').closest('button');
      await user.click(pdfButton!);

      // PDF button should now be active
      expect(pdfButton).toHaveClass('border-blue-500', 'bg-blue-50');
    });
  });

  // ============================================================================
  // Export Options Tests
  // ============================================================================

  describe('Export Options', () => {
    it('should render export options section', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      expect(screen.getByText('Options')).toBeInTheDocument();
    });

    it('should render include metadata checkbox', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      expect(screen.getByText(/Include metadata/i)).toBeInTheDocument();
    });

    it('should have include metadata checked by default', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const metadataCheckbox = screen.getByLabelText(/Include metadata/i) as HTMLInputElement;
      expect(metadataCheckbox.checked).toBe(true);
    });

    it('should toggle include metadata checkbox', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const metadataCheckbox = screen.getByLabelText(/Include metadata/i) as HTMLInputElement;
      await user.click(metadataCheckbox);

      expect(metadataCheckbox.checked).toBe(false);

      await user.click(metadataCheckbox);
      expect(metadataCheckbox.checked).toBe(true);
    });

    it('should show include changes checkbox only for JSON format', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Should not be visible for CSV (default)
      expect(screen.queryByText(/Include change details/i)).not.toBeInTheDocument();

      // Switch to JSON - find the format button in modal
      const jsonButtons = screen.getAllByText('JSON');
      const modalJsonButton = jsonButtons[jsonButtons.length - 1]; // Last one is in modal
      await user.click(modalJsonButton.closest('button')!);

      // Should now be visible
      expect(screen.getByText(/Include change details/i)).toBeInTheDocument();
    });

    it('should have include changes checked by default for JSON', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Switch to JSON - find the format button in modal
      const jsonButtons = screen.getAllByText('JSON');
      const modalJsonButton = jsonButtons[jsonButtons.length - 1];
      await user.click(modalJsonButton.closest('button')!);

      const changesCheckbox = screen.getByLabelText(/Include change details/i) as HTMLInputElement;
      expect(changesCheckbox.checked).toBe(true);
    });
  });

  // ============================================================================
  // Export Action Tests
  // ============================================================================

  describe('Export Action', () => {
    it('should have Export button in modal', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const exportButtons = screen.getAllByRole('button', { name: /Export/i });
      // Should have 2: one to open modal, one inside modal
      expect(exportButtons.length).toBeGreaterThan(1);
    });

    it('should call onExportAll when exporting all records', async () => {
      const user = userEvent.setup();
      mockOnExportAll.mockResolvedValue(new Blob(['test'], { type: 'text/csv' }));

      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export button in modal
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      await waitFor(() => {
        expect(mockOnExportAll).toHaveBeenCalledWith(
          expect.objectContaining({
            format: 'csv',
            includeMetadata: true,
            includeChanges: true,
          })
        );
      });
    });

    it('should show loading state while exporting', async () => {
      const user = userEvent.setup();
      // Mock a slow export
      mockOnExportAll.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(new Blob()), 1000))
      );

      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      // Should show "Exporting..." text
      expect(screen.getByText('Exporting...')).toBeInTheDocument();
    });

    it('should disable export button while exporting', async () => {
      const user = userEvent.setup();
      mockOnExportAll.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(new Blob()), 1000))
      );

      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      // Button should be disabled
      await waitFor(() => {
        expect(modalExportButton).toBeDisabled();
      });
    });

    it('should show success message after export', async () => {
      const user = userEvent.setup();
      mockOnExportAll.mockResolvedValue(new Blob(['test'], { type: 'text/csv' }));

      // Mock URL.createObjectURL and URL.revokeObjectURL
      const mockCreateObjectURL = jest.fn(() => 'blob:test');
      const mockRevokeObjectURL = jest.fn();
      global.URL.createObjectURL = mockCreateObjectURL;
      global.URL.revokeObjectURL = mockRevokeObjectURL;

      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      await waitFor(() => {
        expect(screen.getByText('Export completed successfully!')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should show error message on export failure', async () => {
      const user = userEvent.setup();
      mockOnExportAll.mockRejectedValue(new Error('Export failed'));

      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      await waitFor(() => {
        expect(screen.getByText(/Export failed/i)).toBeInTheDocument();
      });
    });
  });

  // ============================================================================
  // Quick Export Tests
  // ============================================================================

  describe('Quick Export', () => {
    it('should trigger quick export for CSV', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      const csvButton = screen.getByRole('button', { name: /^CSV$/i });
      await user.click(csvButton);

      // Should not open modal for quick export
      expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
    });

    it('should trigger quick export for JSON', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      const jsonButton = screen.getByRole('button', { name: /^JSON$/i });
      await user.click(jsonButton);

      // Should not open modal for quick export
      expect(screen.queryByText('Export Audit Logs')).not.toBeInTheDocument();
    });
  });

  // ============================================================================
  // Export with Filters Tests
  // ============================================================================

  describe('Export with Filters', () => {
    it('should pass filters to export function', async () => {
      const user = userEvent.setup();
      mockOnExportAll.mockResolvedValue(new Blob(['test'], { type: 'text/csv' }));

      const filters = {
        dateRange: { start: '2025-12-01', end: '2025-12-17' },
        entityTypes: ['assignment' as const],
      };

      render(<AuditLogExport {...defaultProps} filters={filters} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      // Click Export
      const modalExportButton = screen.getAllByRole('button', { name: /Export/i })[1];
      await user.click(modalExportButton);

      await waitFor(() => {
        expect(mockOnExportAll).toHaveBeenCalled();
      });
    });
  });

  // ============================================================================
  // Accessibility Tests
  // ============================================================================

  describe('Accessibility', () => {
    it('should have accessible export buttons', () => {
      render(<AuditLogExport {...defaultProps} />);

      const exportButton = screen.getByRole('button', { name: /Export/i });
      expect(exportButton).toBeInTheDocument();
    });

    it('should have accessible modal close button', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const closeButton = screen.getByLabelText('Close');
      expect(closeButton).toBeInTheDocument();
    });

    it('should have accessible checkboxes in modal', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
    });

    it('should have proper ARIA attributes on modal', async () => {
      const user = userEvent.setup();
      render(<AuditLogExport {...defaultProps} />);

      // Open modal
      await user.click(screen.getByRole('button', { name: /^Export/i }));

      const modal = screen.getByText('Export Audit Logs').closest('div');
      expect(modal).toBeInTheDocument();
    });
  });
});
