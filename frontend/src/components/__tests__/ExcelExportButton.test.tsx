/**
 * Tests for ExcelExportButton Component
 * Component: ExcelExportButton - Excel export functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { ExcelExportButton, ExcelExportDropdown } from '../ExcelExportButton';

// Mock export utility
jest.mock('@/lib/export', () => ({
  exportToLegacyXlsx: jest.fn(),
}));

// Mock toast context
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

import { exportToLegacyXlsx } from '@/lib/export';

describe('ExcelExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders export button', () => {
      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);
      expect(screen.getByText('Export Excel')).toBeInTheDocument();
    });

    it('shows file spreadsheet icon', () => {
      const { container } = render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);
      expect(container.querySelector('.lucide-file-spreadsheet')).toBeInTheDocument();
    });

    it('is enabled by default', () => {
      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);
      expect(screen.getByText('Export Excel')).not.toBeDisabled();
    });
  });

  describe('Export functionality', () => {
    it('calls export function on click', async () => {
      (exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined);

      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" blockNumber={1} />);

      fireEvent.click(screen.getByText('Export Excel'));

      await waitFor(() => {
        expect(exportToLegacyXlsx).toHaveBeenCalledWith('2024-01-01', '2024-01-28', 1, undefined);
      });
    });

    it('passes federal holidays', async () => {
      (exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined);

      const holidays = ['2024-01-01', '2024-07-04'];
      render(
        <ExcelExportButton
          startDate="2024-01-01"
          endDate="2024-12-31"
          federalHolidays={holidays}
        />
      );

      fireEvent.click(screen.getByText('Export Excel'));

      await waitFor(() => {
        expect(exportToLegacyXlsx).toHaveBeenCalledWith('2024-01-01', '2024-12-31', undefined, holidays);
      });
    });

    it('shows loading state while exporting', async () => {
      (exportToLegacyXlsx as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);

      fireEvent.click(screen.getByText('Export Excel'));

      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeInTheDocument();
      });
    });

    it('disables button while exporting', async () => {
      (exportToLegacyXlsx as jest.Mock).mockImplementation(() => new Promise(() => {}));

      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);

      fireEvent.click(screen.getByText('Export Excel'));

      await waitFor(() => {
        expect(screen.getByText('Exporting...')).toBeDisabled();
      });
    });

    it('displays error message on export failure', async () => {
      const errorMessage = 'Export failed: network error';
      (exportToLegacyXlsx as jest.Mock).mockRejectedValue(new Error(errorMessage));

      render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);

      fireEvent.click(screen.getByText('Export Excel'));

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('Styling', () => {
    it('has green color scheme', () => {
      const { container } = render(<ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />);
      expect(container.querySelector('.bg-green-600')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <ExcelExportButton
          startDate="2024-01-01"
          endDate="2024-01-28"
          className="custom-class"
        />
      );
      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });
  });
});

describe('ExcelExportDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders dropdown button', () => {
      render(<ExcelExportDropdown />);
      expect(screen.getByText('Export Excel')).toBeInTheDocument();
    });

    it('opens dropdown when clicked', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      expect(screen.getByText('Export Schedule')).toBeInTheDocument();
      expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
      expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    });

    it('shows block number input', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      expect(screen.getByLabelText('Block Number (optional)')).toBeInTheDocument();
    });

    it('closes dropdown when backdrop clicked', () => {
      const { container } = render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));
      expect(screen.getByText('Export Schedule')).toBeInTheDocument();

      const backdrop = container.querySelector('.fixed.inset-0');
      fireEvent.click(backdrop!);

      expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument();
    });
  });

  describe('Date selection', () => {
    it('sets default dates on open', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;

      expect(startDateInput.value).toBeTruthy();
      expect(endDateInput.value).toBeTruthy();
    });

    it('allows changing start date', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      const startDateInput = screen.getByLabelText('Start Date') as HTMLInputElement;
      fireEvent.change(startDateInput, { target: { value: '2024-02-01' } });

      expect(startDateInput.value).toBe('2024-02-01');
    });

    it('allows changing end date', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      const endDateInput = screen.getByLabelText('End Date') as HTMLInputElement;
      fireEvent.change(endDateInput, { target: { value: '2024-02-28' } });

      expect(endDateInput.value).toBe('2024-02-28');
    });

    it('allows setting block number', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      const blockNumberInput = screen.getByLabelText('Block Number (optional)') as HTMLInputElement;
      fireEvent.change(blockNumberInput, { target: { value: '5' } });

      expect(blockNumberInput.value).toBe('5');
    });
  });

  describe('Export functionality', () => {
    it('exports with selected dates', async () => {
      (exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined);

      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      const startDateInput = screen.getByLabelText('Start Date');
      fireEvent.change(startDateInput, { target: { value: '2024-03-01' } });

      const endDateInput = screen.getByLabelText('End Date');
      fireEvent.change(endDateInput, { target: { value: '2024-03-28' } });

      fireEvent.click(screen.getByText('Download Excel'));

      await waitFor(() => {
        expect(exportToLegacyXlsx).toHaveBeenCalledWith('2024-03-01', '2024-03-28', undefined);
      });
    });

    it('requires dates to be selected', () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      // Clear dates
      const startDateInput = screen.getByLabelText('Start Date');
      fireEvent.change(startDateInput, { target: { value: '' } });

      const downloadButton = screen.getByText('Download Excel');
      expect(downloadButton).toBeDisabled();
    });

    it('shows validation error when dates missing', async () => {
      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));

      // Clear dates
      const startDateInput = screen.getByLabelText('Start Date');
      fireEvent.change(startDateInput, { target: { value: '' } });

      const endDateInput = screen.getByLabelText('End Date');
      fireEvent.change(endDateInput, { target: { value: '' } });

      const downloadButton = screen.getByText('Download Excel');
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(screen.getByText('Please select start and end dates')).toBeInTheDocument();
      });
    });

    it('closes dropdown after successful export', async () => {
      (exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined);

      render(<ExcelExportDropdown />);

      fireEvent.click(screen.getByText('Export Excel'));
      fireEvent.click(screen.getByText('Download Excel'));

      await waitFor(() => {
        expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument();
      });
    });
  });
});
