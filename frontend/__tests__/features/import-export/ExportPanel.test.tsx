import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExportPanel, QuickExportButton, ExportModal } from '@/features/import-export/ExportPanel';
import {
  importExportMockFactories,
  importExportMockResponses,
} from './import-export-mocks';
import { createWrapper } from '../../utils/test-utils';
import * as useExportModule from '@/features/import-export/useExport';

// Mock the useExport hook
jest.mock('@/features/import-export/useExport');

const mockedUseExport = useExportModule.useExport as jest.MockedFunction<
  typeof useExportModule.useExport
>;

describe('ExportPanel', () => {
  const mockExportData = jest.fn();
  const mockReset = jest.fn();
  const mockOnExportComplete = jest.fn();
  const mockOnExportError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseExport.mockReturnValue({
      progress: importExportMockFactories.exportProgress(),
      isExporting: false,
      isComplete: false,
      exportData: mockExportData,
      reset: mockReset,
    });
  });

  describe('Button Variant', () => {
    it('should render export button', () => {
      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="button"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    it('should be disabled when no data', () => {
      render(
        <ExportPanel
          data={[]}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="button"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should call exportData when clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="button"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockExportData).toHaveBeenCalledWith(
        importExportMockResponses.exportData,
        expect.objectContaining({
          format: 'csv',
          filename: 'test-export',
        })
      );
    });

    it('should show loading state when exporting', () => {
      mockedUseExport.mockReturnValue({
        progress: importExportMockFactories.exportProgress({ status: 'generating' }),
        isExporting: true,
        isComplete: false,
        exportData: mockExportData,
        reset: mockReset,
      });

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="button"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should show complete state after export', () => {
      mockedUseExport.mockReturnValue({
        progress: importExportMockFactories.exportProgress({ status: 'complete' }),
        isExporting: false,
        isComplete: true,
        exportData: mockExportData,
        reset: mockReset,
      });

      const { container } = render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="button"
        />,
        { wrapper: createWrapper() }
      );

      // Check for checkmark icon (success indicator)
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Dropdown Variant', () => {
    it('should render dropdown button', () => {
      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="dropdown"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    it('should open dropdown menu when clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="dropdown"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByText('Export');
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Export as CSV')).toBeInTheDocument();
        expect(screen.getByText('Export as Excel')).toBeInTheDocument();
        expect(screen.getByText('Export as JSON')).toBeInTheDocument();
        expect(screen.getByText('Export as PDF')).toBeInTheDocument();
      });
    });

    it('should export in selected format when menu item clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="dropdown"
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByText('Export');
      await user.click(button);

      const xlsxOption = await screen.findByText('Export as Excel');
      await user.click(xlsxOption);

      expect(mockExportData).toHaveBeenCalledWith(
        importExportMockResponses.exportData,
        expect.objectContaining({
          format: 'xlsx',
          filename: 'test-export',
        })
      );
    });

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup();

      render(
        <div>
          <div data-testid="outside">Outside</div>
          <ExportPanel
            data={importExportMockResponses.exportData}
            columns={importExportMockResponses.exportColumns}
            filename="test-export"
            variant="dropdown"
          />
        </div>,
        { wrapper: createWrapper() }
      );

      const button = screen.getByText('Export');
      await user.click(button);

      expect(screen.getByText('Export as CSV')).toBeInTheDocument();

      const outside = screen.getByTestId('outside');
      await user.click(outside);

      await waitFor(() => {
        expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument();
      });
    });

    it('should only show available formats', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="dropdown"
          availableFormats={['csv', 'xlsx']}
        />,
        { wrapper: createWrapper() }
      );

      const button = screen.getByText('Export');
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText('Export as CSV')).toBeInTheDocument();
        expect(screen.getByText('Export as Excel')).toBeInTheDocument();
        expect(screen.queryByText('Export as JSON')).not.toBeInTheDocument();
        expect(screen.queryByText('Export as PDF')).not.toBeInTheDocument();
      });
    });
  });

  describe('Panel Variant', () => {
    it('should render panel with title', () => {
      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Export Data')).toBeInTheDocument();
    });

    it('should display record count', () => {
      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('3 records available for export')).toBeInTheDocument();
    });

    it('should render all format options', () => {
      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('CSV')).toBeInTheDocument();
      expect(screen.getByText('Excel')).toBeInTheDocument();
      expect(screen.getByText('JSON')).toBeInTheDocument();
      expect(screen.getByText('PDF')).toBeInTheDocument();
    });

    it('should select format when clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      const xlsxButton = screen.getByText('Excel').closest('button');
      await user.click(xlsxButton!);

      expect(xlsxButton).toHaveClass('border-blue-500');
    });

    it('should toggle export options', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      const optionsButton = screen.getByText('Export Options');
      await user.click(optionsButton);

      await waitFor(() => {
        expect(screen.getByText('Include column headers')).toBeInTheDocument();
        expect(screen.getByText('Columns to export:')).toBeInTheDocument();
      });
    });

    it('should toggle include headers checkbox', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      const optionsButton = screen.getByText('Export Options');
      await user.click(optionsButton);

      const checkbox = await screen.findByRole('checkbox');
      expect(checkbox).toBeChecked();

      await user.click(checkbox);
      expect(checkbox).not.toBeChecked();
    });

    it('should display all columns in options panel', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      const optionsButton = screen.getByText('Export Options');
      await user.click(optionsButton);

      await waitFor(() => {
        expect(screen.getByText('Name')).toBeInTheDocument();
        expect(screen.getByText('Email')).toBeInTheDocument();
        expect(screen.getByText('Type')).toBeInTheDocument();
      });
    });

    it('should show progress when exporting', () => {
      mockedUseExport.mockReturnValue({
        progress: importExportMockFactories.exportProgress({
          status: 'generating',
          message: 'Generating export file...',
        }),
        isExporting: true,
        isComplete: false,
        exportData: mockExportData,
        reset: mockReset,
      });

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Generating export file...')).toBeInTheDocument();
    });

    it('should show success message when complete', () => {
      mockedUseExport.mockReturnValue({
        progress: importExportMockFactories.exportProgress({ status: 'complete' }),
        isExporting: false,
        isComplete: true,
        exportData: mockExportData,
        reset: mockReset,
      });

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Export complete!')).toBeInTheDocument();
    });

    it('should export with selected format when button clicked', async () => {
      const user = userEvent.setup();

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          variant="panel"
        />,
        { wrapper: createWrapper() }
      );

      const xlsxButton = screen.getByText('Excel').closest('button');
      await user.click(xlsxButton!);

      const exportButton = screen.getByText('Export as Excel');
      await user.click(exportButton);

      expect(mockExportData).toHaveBeenCalledWith(
        importExportMockResponses.exportData,
        expect.objectContaining({
          format: 'xlsx',
          filename: 'test-export',
        })
      );
    });
  });

  describe('Callbacks', () => {
    it('should call onExportComplete when provided', () => {
      mockedUseExport.mockImplementation((options) => {
        if (options?.onComplete) {
          options.onComplete();
        }
        return {
          progress: importExportMockFactories.exportProgress(),
          isExporting: false,
          isComplete: false,
          exportData: mockExportData,
          reset: mockReset,
        };
      });

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          onExportComplete={mockOnExportComplete}
        />,
        { wrapper: createWrapper() }
      );

      expect(mockOnExportComplete).toHaveBeenCalled();
    });

    it('should call onExportError when provided', () => {
      const error = new Error('Export failed');

      mockedUseExport.mockImplementation((options) => {
        if (options?.onError) {
          options.onError(error);
        }
        return {
          progress: importExportMockFactories.exportProgress({ status: 'error' }),
          isExporting: false,
          isComplete: false,
          exportData: mockExportData,
          reset: mockReset,
        };
      });

      render(
        <ExportPanel
          data={importExportMockResponses.exportData}
          columns={importExportMockResponses.exportColumns}
          filename="test-export"
          onExportError={mockOnExportError}
        />,
        { wrapper: createWrapper() }
      );

      expect(mockOnExportError).toHaveBeenCalledWith(error);
    });
  });
});

describe('QuickExportButton', () => {
  const mockExportData = jest.fn();
  const mockReset = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseExport.mockReturnValue({
      progress: importExportMockFactories.exportProgress(),
      isExporting: false,
      isComplete: false,
      exportData: mockExportData,
      reset: mockReset,
    });
  });

  it('should render with default CSV format', () => {
    render(
      <QuickExportButton
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Export CSV')).toBeInTheDocument();
  });

  it('should render with custom format', () => {
    render(
      <QuickExportButton
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
        format="xlsx"
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Export Excel')).toBeInTheDocument();
  });

  it('should render with custom children', () => {
    render(
      <QuickExportButton
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      >
        Custom Export
      </QuickExportButton>,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Custom Export')).toBeInTheDocument();
  });

  it('should export when clicked', async () => {
    const user = userEvent.setup();

    render(
      <QuickExportButton
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
        format="xlsx"
      />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button');
    await user.click(button);

    expect(mockExportData).toHaveBeenCalledWith(
      importExportMockResponses.exportData,
      expect.objectContaining({
        format: 'xlsx',
        filename: 'test-export',
      })
    );
  });
});

describe('ExportModal', () => {
  const mockExportData = jest.fn();
  const mockReset = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseExport.mockReturnValue({
      progress: importExportMockFactories.exportProgress(),
      isExporting: false,
      isComplete: false,
      exportData: mockExportData,
      reset: mockReset,
    });
  });

  it('should not render when closed', () => {
    render(
      <ExportModal
        isOpen={false}
        onClose={mockOnClose}
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.queryByText('Export Data')).not.toBeInTheDocument();
  });

  it('should render when open', () => {
    render(
      <ExportModal
        isOpen={true}
        onClose={mockOnClose}
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByText('Export Data')).toBeInTheDocument();
  });

  it('should close when close button clicked', async () => {
    const user = userEvent.setup();

    render(
      <ExportModal
        isOpen={true}
        onClose={mockOnClose}
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      />,
      { wrapper: createWrapper() }
    );

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should close when backdrop clicked', async () => {
    const user = userEvent.setup();

    const { container } = render(
      <ExportModal
        isOpen={true}
        onClose={mockOnClose}
        data={importExportMockResponses.exportData}
        columns={importExportMockResponses.exportColumns}
        filename="test-export"
      />,
      { wrapper: createWrapper() }
    );

    const backdrop = container.querySelector('.bg-black\\/50');
    if (backdrop) {
      await user.click(backdrop);
      expect(mockOnClose).toHaveBeenCalled();
    }
  });
});
