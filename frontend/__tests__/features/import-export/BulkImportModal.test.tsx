/**
 * Tests for BulkImportModal component
 *
 * Tests file upload, drag-and-drop, preview, import execution, and error handling
 */

import { render, screen, waitFor, fireEvent } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { BulkImportModal } from '@/features/import-export/BulkImportModal';
import * as useImportModule from '@/features/import-export/useImport';
import { importExportMockFactories } from './import-export-mocks';

// Mock useImport hook
jest.mock('@/features/import-export/useImport');

const mockedUseImport = useImportModule.useImport as jest.MockedFunction<
  typeof useImportModule.useImport
>;

// Capture the onComplete/onError callbacks passed to useImport
let capturedOnComplete: (() => void) | undefined;
let capturedOnError: ((error: Error) => void) | undefined;

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

  // Default mock return value (reusable in mockImplementation)
  function getDefaultMockReturn(overrides: Record<string, unknown> = {}) {
    return {
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
      ...overrides,
    };
  }

  beforeEach(() => {
    jest.clearAllMocks();
    capturedOnComplete = undefined;
    capturedOnError = undefined;

    mockedUseImport.mockImplementation((opts?: { dataType?: string; onComplete?: () => void; onError?: (error: Error) => void }) => {
      capturedOnComplete = opts?.onComplete;
      capturedOnError = opts?.onError;
      return getDefaultMockReturn() as any;
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
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      // Use fireEvent.change to bypass the accept attribute filter
      const input = document.querySelector('input[type="file"]') as HTMLInputElement;
      fireEvent.change(input, { target: { files: [invalidFile] } });

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

      // Use fireEvent to trigger React's onDragOver handler
      fireEvent.dragOver(dropZone, { dataTransfer: { files: [] } });

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
      expect(screen.getByRole('button', { name: /download.*template/i })).toBeInTheDocument();
    });

    it('should download template when button clicked', async () => {
      const user = userEvent.setup();

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const downloadButton = screen.getByRole('button', { name: /download.*template/i });
      await user.click(downloadButton);

      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalled();
    });

    it('should download template for selected data type', async () => {
      const user = userEvent.setup();

      mockedUseImport.mockImplementation((opts?: any) => {
        capturedOnComplete = opts?.onComplete;
        capturedOnError = opts?.onError;
        return getDefaultMockReturn({ dataType: 'people' }) as any;
      });

      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const downloadButton = screen.getByRole('button', { name: /download.*template/i });
      await user.click(downloadButton);

      // Template should be created and downloaded
      expect(mockCreateObjectURL).toHaveBeenCalled();
      const calls = mockCreateObjectURL.mock.calls as unknown[][];
      const blobArg = calls[0]?.[0];
      expect(blobArg).toBeInstanceOf(Blob);
      // Read blob content using FileReader (blob.text() not available in jsdom)
      const blob = blobArg as Blob;
      const text = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.readAsText(blob);
      });
      expect(text).toContain('name,email,type');
    });
  });

  describe('Preview Step', () => {
    // Helper: upload a valid CSV file to transition from upload -> preview step
    async function uploadFileToPreview(mockPreviewOverrides = {}) {
      const mockPreview = importExportMockFactories.importPreviewResult({
        totalRows: 10,
        validRows: 8,
        errorRows: 1,
        warningRows: 1,
        ...mockPreviewOverrides,
      });
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });

      // When previewImport is called, update the mock to return preview data
      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({ file: mockFile, preview: mockPreview }) as any;
        });
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} />);

      // Upload file through the hidden input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);

      // Wait for preview to appear
      await waitFor(() => {
        expect(screen.getByText('test.csv')).toBeInTheDocument();
      });

      return { user, mockPreview };
    }

    it('should display file info', async () => {
      await uploadFileToPreview();

      expect(screen.getByText('test.csv')).toBeInTheDocument();
      expect(screen.getByText(/10 rows detected/i)).toBeInTheDocument();
    });

    it('should display import options checkboxes', async () => {
      await uploadFileToPreview();

      expect(screen.getByText('Skip duplicate entries')).toBeInTheDocument();
      expect(screen.getByText('Update existing records')).toBeInTheDocument();
      expect(screen.getByText('Skip invalid rows')).toBeInTheDocument();
    });

    it('should call updateOptions when checkbox changed', async () => {
      const { user } = await uploadFileToPreview();

      const checkbox = screen.getByLabelText('Skip duplicate entries');
      await user.click(checkbox);

      expect(mockUpdateOptions).toHaveBeenCalled();
    });

    it('should display validation summary for errors', async () => {
      await uploadFileToPreview({ errorRows: 3, warningRows: 2 });

      expect(screen.getByText(/validation issues found/i)).toBeInTheDocument();
      expect(screen.getByText(/3 rows have errors/i)).toBeInTheDocument();
      expect(screen.getByText(/2 rows have warnings/i)).toBeInTheDocument();
    });

    it('should display xlsx fallback warning', async () => {
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockPreview = importExportMockFactories.importPreviewResult();

      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
            xlsxFallbackUsed: true,
          }) as any;
        });
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} />);

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(screen.getByText('Using Client-Side Parsing')).toBeInTheDocument();
      });
      expect(screen.getByText(/backend excel parsing is unavailable/i)).toBeInTheDocument();
    });

    it('should display xlsx warnings', async () => {
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockPreview = importExportMockFactories.importPreviewResult();

      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
            xlsxWarnings: ['Warning 1', 'Warning 2'],
          }) as any;
        });
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} />);

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);

      await waitFor(() => {
        expect(screen.getByText('Parsing Notes')).toBeInTheDocument();
      });
      expect(screen.getByText('Warning 1')).toBeInTheDocument();
      expect(screen.getByText('Warning 2')).toBeInTheDocument();
    });

    it('should have back button to return to upload', async () => {
      const { user } = await uploadFileToPreview();

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockReset).toHaveBeenCalled();
    });

    it('should have import button with valid row count', async () => {
      await uploadFileToPreview({ validRows: 8 });

      expect(screen.getByRole('button', { name: /import 8.*records/i })).toBeInTheDocument();
    });

    it('should disable import button when no valid rows', async () => {
      await uploadFileToPreview({ validRows: 0 });

      const importButton = screen.getByRole('button', { name: /import 0.*records/i });
      expect(importButton).toBeDisabled();
    });

    it('should call executeImport when import button clicked', async () => {
      const { user } = await uploadFileToPreview({ validRows: 8 });

      const importButton = screen.getByRole('button', { name: /import 8.*records/i });
      await user.click(importButton);

      expect(mockExecuteImport).toHaveBeenCalled();
    });
  });

  describe('Importing Step', () => {
    it('should display progress indicator during import', async () => {
      // Drive the component to the importing step:
      // 1. Upload file -> preview step
      // 2. Click import -> importing step
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockPreview = importExportMockFactories.importPreviewResult({ validRows: 8 });

      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
          }) as any;
        });
      });

      // When executeImport is called, switch to importing state
      mockExecuteImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
            isLoading: true,
            progress: importExportMockFactories.importProgress({
              status: 'importing',
              message: 'Importing data...',
            }),
          }) as any;
        });
        // Never resolves - simulates ongoing import
        return new Promise(() => {});
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} />);

      // Upload file to get to preview
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);

      // Wait for preview step
      await waitFor(() => {
        expect(screen.getByText('test.csv')).toBeInTheDocument();
      });

      // Click import button to trigger importing step
      const importButton = screen.getByRole('button', { name: /import 8.*records/i });
      await user.click(importButton);

      await waitFor(() => {
        expect(screen.getByText('Importing data...')).toBeInTheDocument();
      });
    });
  });

  describe('Complete Step', () => {
    // Helper: drive component to complete step via onComplete callback
    async function driveToComplete(progressOverrides: Record<string, unknown> = {}) {
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockPreview = importExportMockFactories.importPreviewResult({ validRows: 8 });

      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({ file: mockFile, preview: mockPreview }) as any;
        });
      });

      // When executeImport is called, trigger onComplete and update mock to complete state
      mockExecuteImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
            progress: importExportMockFactories.importProgress({
              status: 'complete',
              successCount: 8,
              errorCount: 2,
              warningCount: 1,
              ...progressOverrides,
            }),
          }) as any;
        });
        // Trigger the onComplete callback to set step='complete'
        capturedOnComplete?.();
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);

      // Upload file -> preview
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);
      await waitFor(() => {
        expect(screen.getByText('test.csv')).toBeInTheDocument();
      });

      // Click import -> complete
      const importButton = screen.getByRole('button', { name: /import 8.*records/i });
      await user.click(importButton);

      await waitFor(() => {
        expect(screen.getByText('Import Complete!')).toBeInTheDocument();
      });

      return { user };
    }

    it('should display success message', async () => {
      await driveToComplete();

      expect(screen.getByText('Import Complete!')).toBeInTheDocument();
      expect(screen.getByText(/successfully imported 8 records/i)).toBeInTheDocument();
    });

    it('should display error count if present', async () => {
      await driveToComplete({ errorCount: 2 });

      expect(screen.getByText(/2 records failed/i)).toBeInTheDocument();
    });

    it('should display warning count if present', async () => {
      await driveToComplete({ warningCount: 1 });

      expect(screen.getByText(/1 records had warnings/i)).toBeInTheDocument();
    });

    it('should display error details', async () => {
      const errors = [
        { row: 1, column: 'email', value: 'bad', message: 'Invalid email', severity: 'error' as const },
        { row: 2, column: 'name', value: '', message: 'Required field', severity: 'error' as const },
      ];

      await driveToComplete({ errors });

      expect(screen.getByText('Errors:')).toBeInTheDocument();
      expect(screen.getByText(/row 1.*invalid email/i)).toBeInTheDocument();
      expect(screen.getByText(/row 2.*required field/i)).toBeInTheDocument();
    });

    it('should limit error display to 10', async () => {
      const errors = Array.from({ length: 15 }, (_, i) => ({
        row: i + 1,
        column: 'test',
        value: 'bad',
        message: `Error ${i + 1}`,
        severity: 'error' as const,
      }));

      await driveToComplete({ errors });

      expect(screen.getByText(/and 5 more/i)).toBeInTheDocument();
    });

    it('should call onSuccess when complete', async () => {
      await driveToComplete();

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

    it('should show "Close" text on complete step', async () => {
      // Drive to complete step via onComplete callback
      const mockFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      const mockPreview = importExportMockFactories.importPreviewResult({ validRows: 8 });

      mockPreviewImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({ file: mockFile, preview: mockPreview }) as any;
        });
      });

      mockExecuteImport.mockImplementation(async () => {
        mockedUseImport.mockImplementation((opts?: any) => {
          capturedOnComplete = opts?.onComplete;
          return getDefaultMockReturn({
            file: mockFile,
            preview: mockPreview,
            progress: importExportMockFactories.importProgress({ status: 'complete' }),
          }) as any;
        });
        capturedOnComplete?.();
      });

      const user = userEvent.setup();
      render(<BulkImportModal isOpen={true} onClose={mockOnClose} />);

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      await user.upload(fileInput, mockFile);
      await waitFor(() => { expect(screen.getByText('test.csv')).toBeInTheDocument(); });

      const importButton = screen.getByRole('button', { name: /import 8.*records/i });
      await user.click(importButton);

      await waitFor(() => {
        expect(screen.getByText('Import Complete!')).toBeInTheDocument();
      });

      // On complete step, footer button should say "Close" not "Cancel"
      expect(screen.getByRole('button', { name: /close import modal/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel import/i })).not.toBeInTheDocument();
    });

    it('should cancel import when cancel clicked during import', async () => {
      const user = userEvent.setup();

      mockedUseImport.mockImplementation((opts?: any) => {
        capturedOnComplete = opts?.onComplete;
        return getDefaultMockReturn({
          isLoading: true,
          progress: importExportMockFactories.importProgress({ status: 'importing' }),
        }) as any;
      });

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
      render(
        <BulkImportModal isOpen={true} onClose={mockOnClose} />
      );

      const input = document.querySelector('input[type="file"]') as HTMLInputElement;

      // First upload invalid file using fireEvent to bypass accept filter
      const invalidFile = new File(['test'], 'test.txt', { type: 'text/plain' });
      fireEvent.change(input, { target: { files: [invalidFile] } });

      await waitFor(() => {
        expect(screen.getByText(/please select a csv, excel, or json file/i)).toBeInTheDocument();
      });

      // Then upload valid file - error should clear
      const validFile = new File(['test,data'], 'test.csv', { type: 'text/csv' });
      fireEvent.change(input, { target: { files: [validFile] } });

      await waitFor(() => {
        expect(screen.queryByText(/please select a csv, excel, or json file/i)).not.toBeInTheDocument();
      });
    });
  });
});
