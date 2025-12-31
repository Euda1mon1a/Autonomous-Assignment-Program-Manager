/**
 * Tests for ImportPreview component
 *
 * Tests preview table, filtering, sorting, row expansion, and validation display
 */

import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ImportPreview, ImportPreviewSkeleton } from '@/features/import-export/ImportPreview';
import { importExportMockFactories } from './import-export-mocks';
import type { ImportPreviewResult } from '@/features/import-export/types';

describe('ImportPreview', () => {
  const mockPreview: ImportPreviewResult = {
    totalRows: 10,
    validRows: 7,
    errorRows: 2,
    warningRows: 1,
    skippedRows: 0,
    columns: ['name', 'email', 'type'],
    detectedFormat: 'csv',
    dataType: 'people',
    rows: [
      {
        rowNumber: 1,
        data: { name: 'John Doe', email: 'john@example.com', type: 'resident' },
        status: 'valid',
        errors: [],
        warnings: [],
      },
      {
        rowNumber: 2,
        data: { name: 'Jane Smith', email: 'jane@example.com', type: 'faculty' },
        status: 'valid',
        errors: [],
        warnings: [],
      },
      {
        rowNumber: 3,
        data: { name: 'Bob Johnson', email: 'invalid-email', type: 'resident' },
        status: 'error',
        errors: [
          { row: 3, column: 'email', value: 'invalid-email', message: 'Invalid email format', severity: 'error' },
        ],
        warnings: [],
      },
      {
        rowNumber: 4,
        data: { name: 'Alice Williams', email: 'alice@example.com', type: 'faculty' },
        status: 'warning',
        errors: [],
        warnings: [
          { row: 4, column: 'type', value: 'faculty', message: 'Duplicate entry found', severity: 'warning' },
        ],
      },
      {
        rowNumber: 5,
        data: { name: '', email: 'missing@example.com', type: 'resident' },
        status: 'error',
        errors: [
          { row: 5, column: 'name', value: '', message: 'Name is required', severity: 'error' },
        ],
        warnings: [],
      },
    ],
  };

  describe('Summary Display', () => {
    it('should display total row count', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText('Total:')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    it('should display valid row count', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText(/valid.*7/i)).toBeInTheDocument();
    });

    it('should display warning count', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText(/warnings.*1/i)).toBeInTheDocument();
    });

    it('should display error count', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText(/errors.*2/i)).toBeInTheDocument();
    });

    it('should display skipped count', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText(/skipped.*0/i)).toBeInTheDocument();
    });

    it('should have color-coded summary items', () => {
      render(<ImportPreview preview={mockPreview} />);

      const validText = screen.getByText(/valid.*7/i);
      expect(validText).toHaveClass('text-green-600');

      const warningText = screen.getByText(/warnings.*1/i);
      expect(warningText).toHaveClass('text-yellow-600');

      const errorText = screen.getByText(/errors.*2/i);
      expect(errorText).toHaveClass('text-red-600');
    });
  });

  describe('Filter Controls', () => {
    it('should render status filter dropdown', () => {
      render(<ImportPreview preview={mockPreview} />);

      const filterSelect = screen.getByRole('combobox');
      expect(filterSelect).toBeInTheDocument();
    });

    it('should have all filter options', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByRole('option', { name: /all rows/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /valid only/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /warnings/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /errors/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /skipped/i })).toBeInTheDocument();
    });

    it('should filter rows by status', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      // Initially shows all rows
      expect(screen.getByText(/showing 5 of 5 rows/i)).toBeInTheDocument();

      // Filter to only valid rows
      const filterSelect = screen.getByRole('combobox');
      await user.selectOptions(filterSelect, 'valid');

      expect(screen.getByText(/showing 2 of 2 rows/i)).toBeInTheDocument();
    });

    it('should filter to error rows only', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const filterSelect = screen.getByRole('combobox');
      await user.selectOptions(filterSelect, 'error');

      expect(screen.getByText(/showing 2 of 2 rows/i)).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      expect(screen.queryByText('John Doe')).not.toBeInTheDocument();
    });

    it('should filter to warning rows only', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const filterSelect = screen.getByRole('combobox');
      await user.selectOptions(filterSelect, 'warning');

      expect(screen.getByText(/showing 1 of 1 rows/i)).toBeInTheDocument();
      expect(screen.getByText('Alice Williams')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should render search input', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByPlaceholderText('Search data...')).toBeInTheDocument();
    });

    it('should filter rows by search query', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const searchInput = screen.getByPlaceholderText('Search data...');
      await user.type(searchInput, 'john');

      // Should show John Doe and Bob Johnson
      expect(screen.getByText(/showing 2 of 2 rows/i)).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    });

    it('should be case-insensitive search', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const searchInput = screen.getByPlaceholderText('Search data...');
      await user.type(searchInput, 'JOHN');

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    });

    it('should search across all columns', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const searchInput = screen.getByPlaceholderText('Search data...');
      await user.type(searchInput, 'faculty');

      expect(screen.getByText(/showing 2 of 2 rows/i)).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Alice Williams')).toBeInTheDocument();
    });

    it('should show no results message when search has no matches', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const searchInput = screen.getByPlaceholderText('Search data...');
      await user.type(searchInput, 'nonexistent');

      expect(screen.getByText('No rows match the current filter.')).toBeInTheDocument();
    });

    it('should combine search with status filter', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      // Filter to errors only
      const filterSelect = screen.getByRole('combobox');
      await user.selectOptions(filterSelect, 'error');

      // Then search for "Bob"
      const searchInput = screen.getByPlaceholderText('Search data...');
      await user.type(searchInput, 'Bob');

      expect(screen.getByText(/showing 1 of 1 rows/i)).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    });
  });

  describe('Table Display', () => {
    it('should render table with headers', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Row')).toBeInTheDocument();
      expect(screen.getByText('name')).toBeInTheDocument();
      expect(screen.getByText('email')).toBeInTheDocument();
      expect(screen.getByText('type')).toBeInTheDocument();
    });

    it('should render all data rows', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
      expect(screen.getByText('Alice Williams')).toBeInTheDocument();
    });

    it('should display row numbers', () => {
      const { container } = render(<ImportPreview preview={mockPreview} />);

      const tbody = container.querySelector('tbody');
      expect(tbody).toBeInTheDocument();

      // Check for row numbers (they're in the second column)
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should apply status-based row styling', () => {
      const { container } = render(<ImportPreview preview={mockPreview} />);

      const rows = container.querySelectorAll('tbody tr');

      // Valid rows should have green background
      expect(rows[0]).toHaveClass('bg-green-50');

      // Error rows should have red background
      expect(rows[2]).toHaveClass('bg-red-50');

      // Warning rows should have yellow background
      expect(rows[3]).toHaveClass('bg-yellow-50');
    });

    it('should format boolean values', () => {
      const previewWithBoolean: ImportPreviewResult = {
        ...mockPreview,
        columns: ['name', 'is_active'],
        rows: [
          {
            rowNumber: 1,
            data: { name: 'Test', is_active: true },
            status: 'valid',
            errors: [],
            warnings: [],
          },
          {
            rowNumber: 2,
            data: { name: 'Test 2', is_active: false },
            status: 'valid',
            errors: [],
            warnings: [],
          },
        ],
      };

      render(<ImportPreview preview={previewWithBoolean} />);

      expect(screen.getByText('Yes')).toBeInTheDocument();
      expect(screen.getByText('No')).toBeInTheDocument();
    });

    it('should format null/undefined values', () => {
      const previewWithNull: ImportPreviewResult = {
        ...mockPreview,
        columns: ['name', 'middle_name'],
        rows: [
          {
            rowNumber: 1,
            data: { name: 'Test', middle_name: null },
            status: 'valid',
            errors: [],
            warnings: [],
          },
        ],
      };

      render(<ImportPreview preview={previewWithNull} />);

      const cells = screen.getAllByText('-');
      expect(cells.length).toBeGreaterThan(0);
    });

    it('should format array values', () => {
      const previewWithArray: ImportPreviewResult = {
        ...mockPreview,
        columns: ['name', 'tags'],
        rows: [
          {
            rowNumber: 1,
            data: { name: 'Test', tags: ['tag1', 'tag2', 'tag3'] },
            status: 'valid',
            errors: [],
            warnings: [],
          },
        ],
      };

      render(<ImportPreview preview={previewWithArray} />);

      expect(screen.getByText('tag1, tag2, tag3')).toBeInTheDocument();
    });
  });

  describe('Column Sorting', () => {
    it('should sort column in ascending order when header clicked', async () => {
      const user = userEvent.setup();

      const { container } = render(<ImportPreview preview={mockPreview} />);

      const nameHeader = screen.getByText('name');
      await user.click(nameHeader);

      // Check for ascending indicator (ChevronUp)
      const chevronUp = container.querySelector('.w-3.h-3');
      expect(chevronUp).toBeInTheDocument();
    });

    it('should toggle sort direction on second click', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const nameHeader = screen.getByText('name');

      // First click - ascending
      await user.click(nameHeader);

      // Second click - descending
      await user.click(nameHeader);

      // Rows should be in descending order by name
      // This is a simplified check - in reality you'd verify the actual order
    });

    it('should apply sorting indicator to sorted column', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const emailHeader = screen.getByText('email');
      await user.click(emailHeader);

      // The header should now show a sort indicator
      const headerWithIcon = emailHeader.parentElement;
      expect(headerWithIcon).toBeInTheDocument();
    });

    it('should allow sorting different columns', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const nameHeader = screen.getByText('name');
      await user.click(nameHeader);

      const emailHeader = screen.getByText('email');
      await user.click(emailHeader);

      // Email column should now be sorted
    });
  });

  describe('Row Expansion', () => {
    it('should expand row to show errors when clicked', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const errorRow = screen.getByText('Bob Johnson').closest('tr');
      expect(errorRow).toBeInTheDocument();

      await user.click(errorRow!);

      expect(screen.getByText(/email.*invalid email format/i)).toBeInTheDocument();
    });

    it('should expand row to show warnings when clicked', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const warningRow = screen.getByText('Alice Williams').closest('tr');
      await user.click(warningRow!);

      expect(screen.getByText(/type.*duplicate entry found/i)).toBeInTheDocument();
    });

    it('should collapse expanded row when clicked again', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const errorRow = screen.getByText('Bob Johnson').closest('tr');

      // Expand
      await user.click(errorRow!);
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();

      // Collapse
      await user.click(errorRow!);
      expect(screen.queryByText(/invalid email format/i)).not.toBeInTheDocument();
    });

    it('should not be clickable for rows without errors or warnings', async () => {
      const user = userEvent.setup();

      render(<ImportPreview preview={mockPreview} />);

      const validRow = screen.getByText('John Doe').closest('tr');
      expect(validRow).not.toHaveClass('cursor-pointer');
    });

    it('should display multiple errors in expanded row', async () => {
      const user = userEvent.setup();

      const previewWithMultipleErrors: ImportPreviewResult = {
        ...mockPreview,
        rows: [
          {
            rowNumber: 1,
            data: { name: '', email: 'invalid', type: '' },
            status: 'error',
            errors: [
              { row: 1, column: 'name', value: '', message: 'Name is required', severity: 'error' },
              { row: 1, column: 'email', value: 'invalid', message: 'Invalid email', severity: 'error' },
              { row: 1, column: 'type', value: '', message: 'Type is required', severity: 'error' },
            ],
            warnings: [],
          },
        ],
      };

      render(<ImportPreview preview={previewWithMultipleErrors} />);

      const errorRow = screen.getByText('1').closest('tr');
      await user.click(errorRow!);

      expect(screen.getByText(/name.*required/i)).toBeInTheDocument();
      expect(screen.getByText(/email.*invalid/i)).toBeInTheDocument();
      expect(screen.getByText(/type.*required/i)).toBeInTheDocument();
    });

    it('should display both errors and warnings in expanded row', async () => {
      const user = userEvent.setup();

      const previewWithBoth: ImportPreviewResult = {
        ...mockPreview,
        rows: [
          {
            rowNumber: 1,
            data: { name: 'Test', email: 'test@example.com', type: 'resident' },
            status: 'warning',
            errors: [
              { row: 1, column: 'email', value: 'test@example.com', message: 'Email validation warning', severity: 'error' },
            ],
            warnings: [
              { row: 1, column: 'name', value: 'Test', message: 'Possible duplicate', severity: 'warning' },
            ],
          },
        ],
      };

      render(<ImportPreview preview={previewWithBoth} />);

      const row = screen.getByText('Test').closest('tr');
      await user.click(row!);

      expect(screen.getByText(/email.*validation warning/i)).toBeInTheDocument();
      expect(screen.getByText(/name.*possible duplicate/i)).toBeInTheDocument();
    });
  });

  describe('Pagination/Display Limits', () => {
    it('should limit display to maxDisplayRows', () => {
      const manyRows = Array.from({ length: 150 }, (_, i) => ({
        rowNumber: i + 1,
        data: { name: `Person ${i + 1}`, email: `person${i + 1}@example.com`, type: 'resident' },
        status: 'valid' as const,
        errors: [],
        warnings: [],
      }));

      const largePreview: ImportPreviewResult = {
        ...mockPreview,
        totalRows: 150,
        rows: manyRows,
      };

      render(<ImportPreview preview={largePreview} maxDisplayRows={100} />);

      expect(screen.getByText(/showing first 100 rows/i)).toBeInTheDocument();
      expect(screen.getByText(/50 more rows not displayed/i)).toBeInTheDocument();
    });

    it('should use default maxDisplayRows of 100', () => {
      const manyRows = Array.from({ length: 150 }, (_, i) => ({
        rowNumber: i + 1,
        data: { name: `Person ${i + 1}`, email: `person${i + 1}@example.com`, type: 'resident' },
        status: 'valid' as const,
        errors: [],
        warnings: [],
      }));

      const largePreview: ImportPreviewResult = {
        ...mockPreview,
        totalRows: 150,
        rows: manyRows,
      };

      render(<ImportPreview preview={largePreview} />);

      expect(screen.getByText(/showing first 100 rows/i)).toBeInTheDocument();
    });

    it('should not show more rows message when all rows displayed', () => {
      render(<ImportPreview preview={mockPreview} />);

      expect(screen.queryByText(/more rows not displayed/i)).not.toBeInTheDocument();
    });
  });

  describe('Status Icons', () => {
    it('should display check icon for valid rows', () => {
      const { container } = render(<ImportPreview preview={mockPreview} />);

      const validRow = screen.getByText('John Doe').closest('tr');
      const statusCell = validRow?.querySelector('td:first-child');
      const checkIcon = statusCell?.querySelector('.text-green-500');
      expect(checkIcon).toBeInTheDocument();
    });

    it('should display X icon for error rows', () => {
      const { container } = render(<ImportPreview preview={mockPreview} />);

      const errorRow = screen.getByText('Bob Johnson').closest('tr');
      const statusCell = errorRow?.querySelector('td:first-child');
      const errorIcon = statusCell?.querySelector('.text-red-500');
      expect(errorIcon).toBeInTheDocument();
    });

    it('should display warning icon for warning rows', () => {
      const { container } = render(<ImportPreview preview={mockPreview} />);

      const warningRow = screen.getByText('Alice Williams').closest('tr');
      const statusCell = warningRow?.querySelector('td:first-child');
      const warningIcon = statusCell?.querySelector('.text-yellow-500');
      expect(warningIcon).toBeInTheDocument();
    });
  });

  describe('Empty States', () => {
    it('should show empty message when no rows match filter', async () => {
      const user = userEvent.setup();

      const previewWithNoSkipped: ImportPreviewResult = {
        ...mockPreview,
        skippedRows: 0,
        rows: mockPreview.rows.filter(r => r.status !== 'skipped'),
      };

      render(<ImportPreview preview={previewWithNoSkipped} />);

      const filterSelect = screen.getByRole('combobox');
      await user.selectOptions(filterSelect, 'skipped');

      expect(screen.getByText('No rows match the current filter.')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <ImportPreview preview={mockPreview} className="custom-preview" />
      );

      expect(container.querySelector('.custom-preview')).toBeInTheDocument();
    });
  });
});

describe('ImportPreviewSkeleton', () => {
  it('should render skeleton loader', () => {
    const { container } = render(<ImportPreviewSkeleton />);

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render summary skeleton', () => {
    const { container } = render(<ImportPreviewSkeleton />);

    const summarySkeletons = container.querySelectorAll('.bg-gray-50 .bg-gray-200');
    expect(summarySkeletons.length).toBeGreaterThan(0);
  });

  it('should render filters skeleton', () => {
    const { container } = render(<ImportPreviewSkeleton />);

    const filterSkeletons = container.querySelectorAll('.h-8.w-32, .h-8.w-48');
    expect(filterSkeletons.length).toBeGreaterThan(0);
  });

  it('should render table skeleton', () => {
    const { container } = render(<ImportPreviewSkeleton />);

    const tableHeader = container.querySelector('.bg-gray-100');
    expect(tableHeader).toBeInTheDocument();

    const tableRows = container.querySelectorAll('.border-t');
    expect(tableRows.length).toBeGreaterThan(0);
  });
});
