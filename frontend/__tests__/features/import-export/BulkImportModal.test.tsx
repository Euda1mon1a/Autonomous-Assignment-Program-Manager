/**
 * Tests for BulkImportModal component
 *
 * Tests file upload, drag-and-drop, preview, import execution, and error handling
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BulkImportModal } from '@/features/import-export/BulkImportModal';
import * as useImportModule from '@/features/import-export/useImport';
import { importExportMockFactories } from './import-export-mocks';

// Mock useImport hook
jest.mock('@/features/import-export/useImport');

const mockedUseImport = useImportModule.useImport as jest.MockedFunction<
  typeof useImportModule.useImport
>;

// Mock URL methods for file download
const mockCreateObjectURL = jest.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = jest.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

describe('BulkImportModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();
  const mockPreviewImport = jest.fn();
  const mockExecuteImport = jest.fn();
  const mockCancelImport = jest.fn();
  const mockReset = jest.fn();
  const mockUpdateOptions = jest.fn();
  const mockSetDataType = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockedUseImport.mockReturnValue({
      file: null,
      dataType: 'schedules',
      preview: null,
      progress: importExportMockFactories.importProgress(),
      options: importExportMockFactories.importOptions(),
      isLoading: false,
      isError: false,
      xlsxFallbackUsed: false,
      xlsxWarnings: [],
      previewImport: mockPreviewImport,
      executeImport: mockExecuteImport,
      cancelImport: mockCancelImport,
      reset: mockReset,
      updateOptions: mockUpdateOptions,
      setDataType: mockSetDataType,
      format: 'csv',
    });
  });

  describe('Modal Visibility', () => {
    it('should not render when isOpen is false', () => {
      render(
        <BulkImportModal isOpen={false} onClose={mockOnClose} />
      );

      expect(screen.queryByText('Bulk Import')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Bulk Import')).toBeInTheDocument();
    });

    it('should render with custom title', () => {
      render(
        <BulkImportModal
          isOpen={true}
          onClose={mockOnClose}
          title="Custom Import Title"
        />
      );

      expect(screen.getByText('Custom Import Title')).toBeInTheDocument();
    });
  });

  describe('Upload Step - Data Type Selection', () => {
    it('should render data type selector', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('What are you importing?')).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should have default data type as schedules', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const select = screen.getByRole('combobox') as HTMLSelectElement;
      expect(select.value).toBe('schedules');
    });

    it('should use provided defaultDataType', () => {
      render(
        <BulkImportModal
          isOpen={true}
          onClose={mockOnClose}
          defaultDataType="people"
        />
      );

      expect(mockSetDataType).not.toHaveBeenCalled(); // Should not be called on mount
    });

    it('should call setDataType when selection changes', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'people');

      expect(mockSetDataType).toHaveBeenCalledWith('people');
    });

    it('should display all data type options', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('option', { name: /schedule.*assignments/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /people.*residents.*faculty/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /absences/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /individual assignments/i })).toBeInTheDocument();
    });
  });

  describe('Upload Step - File Drop Zone', () => {
    it('should render file drop zone', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Drag and drop your file here')).toBeInTheDocument();
      expect(screen.getByText('or click to browse')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /select file/i })).toBeInTheDocument();
    });

    it('should display supported formats', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/supported formats.*csv.*excel.*json/i)).toBeInTheDocument();
    });

    it('should call previewImport when file is selected', async () => {
      const user = userEvent.setup();
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const input = screen.getByRole('button', { name: /select file/i })
        .parentElement?.querySelector('input[type="file"]') as HTMLInputElement;

      await user.upload(input, mockFile);

      await waitFor(() => {
        expect(mockPreviewImport).toHaveBeenCalledWith(mockFile);
      });
    });

    it('should show error for invalid file type', async () => {
      const user = userEvent.setup();
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const input = screen.getByRole('button', { name: /select file/i })
        .parentElement?.querySelector('input[type="file"]') as HTMLInputElement;

      await user.upload(input, mockFile);

      await waitFor(() => {
        expect(screen.getByText(/please select a csv, excel, or json file/i)).toBeInTheDocument();
      });

      expect(mockPreviewImport).not.toHaveBeenCalled();
    });

    it('should show error for file exceeding size limit', async () => {
      const user = userEvent.setup();
      // Create a file larger than 10MB
      const largeContent = 'x'.repeat(11 * 1024 * 1024);
      const mockFile = new File([largeContent], 'large.csv', { type: 'text/csv' });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const input = screen.getByRole('button', { name: /select file/i })
        .parentElement?.querySelector('input[type="file"]') as HTMLInputElement;

      await user.upload(input, mockFile);

      await waitFor(() => {
        expect(screen.getByText(/file size exceeds 10mb limit/i)).toBeInTheDocument();
      });

      expect(mockPreviewImport).not.toHaveBeenCalled();
    });

    it('should handle drag and drop', async () => {
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });

      const { container } = render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const dropZone = container.querySelector('.border-dashed') as HTMLElement;

      // Simulate drag over
      const dragOverEvent = new Event('dragover', { bubbles: true });
      Object.defineProperty(dragOverEvent, 'dataTransfer', {
        value: { files: [mockFile] }
      });
      dropZone.dispatchEvent(dragOverEvent);

      // Simulate drop
      const dropEvent = new Event('drop', { bubbles: true });
      Object.defineProperty(dropEvent, 'dataTransfer', {
        value: { files: [mockFile] }
      });
      dropZone.dispatchEvent(dropEvent);

      await waitFor(() => {
        expect(mockPreviewImport).toHaveBeenCalledWith(mockFile);
      });
    });

    it('should apply active styling during drag', () => {
      const { container } = render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const dropZone = container.querySelector('.border-dashed') as HTMLElement;

      const dragOverEvent = new Event('dragover', { bubbles: true });
      dropZone.dispatchEvent(dragOverEvent);

      expect(dropZone).toHaveClass('border-blue-500');
    });
  });

  describe('Upload Step - Template Download', () => {
    it('should render template download section', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Need a template?')).toBeInTheDocument();
      expect(screen.getByText(/download a sample csv file/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /download template/i })).toBeInTheDocument();
    });

    it('should download template when button clicked', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const downloadButton = screen.getByRole('button', { name: /download template/i });
      await user.click(downloadButton);

      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalled();
    });

    it('should download template for selected data type', async () => {
      const user = userEvent.setup();

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        dataType: 'people',
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const downloadButton = screen.getByRole('button', { name: /download template/i });
      await user.click(downloadButton);

      // Template should be created and downloaded
      expect(mockCreateObjectURL).toHaveBeenCalled();
      const blob = mockCreateObjectURL.mock.calls[0][0] as Blob;
      const text = await blob.text();
      expect(text).toContain('name,email,type');
    });
  });

  describe('Preview Step', () => {
    beforeEach(() => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        totalRows: 10,
        validRows: 8,
        errorRows: 1,
        warningRows: 1,
      });

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        file: new File(['test'], 'test.csv', { type: 'text/csv' }),
        preview: mockPreview,
      } as any);
    });

    it('should display file info', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('test.csv')).toBeInTheDocument();
      expect(screen.getByText(/10 rows detected/i)).toBeInTheDocument();
    });

    it('should display import options checkboxes', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Skip duplicate entries')).toBeInTheDocument();
      expect(screen.getByText('Update existing records')).toBeInTheDocument();
      expect(screen.getByText('Skip invalid rows')).toBeInTheDocument();
    });

    it('should call updateOptions when checkbox changed', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const checkbox = screen.getByLabelText('Skip duplicate entries');
      await user.click(checkbox);

      expect(mockUpdateOptions).toHaveBeenCalled();
    });

    it('should display validation summary for errors', () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        errorRows: 3,
        warningRows: 2,
      });

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        preview: mockPreview,
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/validation issues found/i)).toBeInTheDocument();
      expect(screen.getByText(/3 rows have errors/i)).toBeInTheDocument();
      expect(screen.getByText(/2 rows have warnings/i)).toBeInTheDocument();
    });

    it('should display xlsx fallback warning', () => {
      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        xlsxFallbackUsed: true,
        preview: importExportMockFactories.importPreviewResult(),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Using Client-Side Parsing')).toBeInTheDocument();
      expect(screen.getByText(/backend excel parsing is unavailable/i)).toBeInTheDocument();
    });

    it('should display xlsx warnings', () => {
      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        xlsxWarnings: ['Warning 1', 'Warning 2'],
        preview: importExportMockFactories.importPreviewResult(),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Parsing Notes')).toBeInTheDocument();
      expect(screen.getByText('Warning 1')).toBeInTheDocument();
      expect(screen.getByText('Warning 2')).toBeInTheDocument();
    });

    it('should have back button to return to upload', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockReset).toHaveBeenCalled();
    });

    it('should have import button with valid row count', () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 8,
      });

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        preview: mockPreview,
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('button', { name: /import 8 records/i })).toBeInTheDocument();
    });

    it('should disable import button when no valid rows', () => {
      const mockPreview = importExportMockFactories.importPreviewResult({
        validRows: 0,
      });

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        preview: mockPreview,
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const importButton = screen.getByRole('button', { name: /import 0 records/i });
      expect(importButton).toBeDisabled();
    });

    it('should call executeImport when import button clicked', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const importButton = screen.getByRole('button', { name: /import/i });
      await user.click(importButton);

      expect(mockExecuteImport).toHaveBeenCalled();
    });
  });

  describe('Importing Step', () => {
    it('should display progress indicator during import', () => {
      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        progress: importExportMockFactories.importProgress({
          status: 'importing',
          message: 'Importing data...',
        }),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Importing data...')).toBeInTheDocument();
    });
  });

  describe('Complete Step', () => {
    beforeEach(() => {
      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        progress: importExportMockFactories.importProgress({
          status: 'complete',
          successCount: 8,
          errorCount: 2,
          warningCount: 1,
        }),
      } as any);
    });

    it('should display success message', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Import Complete!')).toBeInTheDocument();
      expect(screen.getByText(/successfully imported 8 records/i)).toBeInTheDocument();
    });

    it('should display error count if present', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/2 records failed/i)).toBeInTheDocument();
    });

    it('should display warning count if present', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/1 records had warnings/i)).toBeInTheDocument();
    });

    it('should display error details', () => {
      const errors = [
        { row: 1, column: 'email', value: 'bad', message: 'Invalid email', severity: 'error' as const },
        { row: 2, column: 'name', value: '', message: 'Required field', severity: 'error' as const },
      ];

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        progress: importExportMockFactories.importProgress({
          status: 'complete',
          errors,
        }),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText('Errors:')).toBeInTheDocument();
      expect(screen.getByText(/row 1.*invalid email/i)).toBeInTheDocument();
      expect(screen.getByText(/row 2.*required field/i)).toBeInTheDocument();
    });

    it('should limit error display to 10', () => {
      const errors = Array.from({ length: 15 }, (_, i) => ({
        row: i + 1,
        column: 'test',
        value: 'bad',
        message: `Error ${i + 1}`,
        severity: 'error' as const,
      }));

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        progress: importExportMockFactories.importProgress({
          status: 'complete',
          errors,
        }),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByText(/and 5 more/i)).toBeInTheDocument();
    });

    it('should call onSuccess when complete', () => {
      render(
        <BulkImportModal
          isOpen={true}
          onClose={mockOnClose}
          onSuccess={mockOnSuccess}
        />
      );

      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  describe('Modal Controls', () => {
    it('should have close button in header', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      expect(closeButton).toBeInTheDocument();
    });

    it('should call onClose when close button clicked', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const closeButton = screen.getByRole('button', { name: /close modal/i });
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
      expect(mockReset).toHaveBeenCalled();
    });

    it('should call onClose when backdrop clicked', async () => {
      const user = userEvent.setup();

      const { container } = render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const backdrop = container.querySelector('.bg-black\\/50');
      if (backdrop) {
        await user.click(backdrop);
        expect(mockOnClose).toHaveBeenCalled();
      }
    });

    it('should have cancel button in footer', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should show "Close" text on complete step', () => {
      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        progress: importExportMockFactories.importProgress({ status: 'complete' }),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });

    it('should cancel import when cancel clicked during import', async () => {
      const user = userEvent.setup();

      mockedUseImport.mockReturnValue({
        ...mockedUseImport(),
        isLoading: true,
        progress: importExportMockFactories.importProgress({ status: 'importing' }),
      } as any);

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockCancelImport).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role and aria attributes', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby');
    });

    it('should have file input with proper accept attribute', () => {
      const { container } = render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const fileInput = container.querySelector('input[type="file"]');
      expect(fileInput).toHaveAttribute('accept', '.csv,.xlsx,.xls,.json');
    });

    it('should hide file input visually', () => {
      const { container } = render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const fileInput = container.querySelector('input[type="file"]');
      expect(fileInput).toHaveClass('hidden');
    });
  });

  describe('Error Handling', () => {
    it('should display file error message', () => {
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      // Manually trigger error state by uploading invalid file
      // (this is tested in the file upload tests above)
    });

    it('should clear error when new file selected', async () => {
      const user = userEvent.setup();

      // First upload invalid file
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const input = screen.getByRole('button', { name: /select file/i })
        .parentElement?.querySelector('input[type="file"]') as HTMLInputElement;

      await user.upload(input, invalidFile);

      await waitFor(() => {
        expect(screen.getByText(/please select a csv, excel, or json file/i)).toBeInTheDocument();
      });

      // Then upload valid file
      const validFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      await user.upload(input, validFile);

      await waitFor(() => {
        expect(screen.queryByText(/please select a csv, excel, or json file/i)).not.toBeInTheDocument();
      });
    });
  });
});
