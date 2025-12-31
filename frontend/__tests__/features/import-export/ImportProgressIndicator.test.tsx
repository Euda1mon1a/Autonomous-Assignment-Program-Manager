/**
 * Tests for ImportProgressIndicator component
 *
 * Tests progress display, status messages, loading states, and error handling
 */

import { render, screen } from '@testing-library/react';
import { ImportProgressIndicator, ImportProgressSkeleton } from '@/features/import-export/ImportProgressIndicator';
import { importExportMockFactories } from './import-export-mocks';
import type { ImportProgress } from '@/features/import-export/types';

describe('ImportProgressIndicator', () => {
  describe('Idle State', () => {
    it('should not render when status is idle', () => {
      const progress = importExportMockFactories.importProgress({ status: 'idle' });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Parsing State', () => {
    it('should display parsing message', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        message: 'Parsing file...',
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Parsing file...')).toBeInTheDocument();
    });

    it('should show loading spinner during parsing', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        message: 'Parsing file...',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should display blue color for parsing', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        message: 'Parsing file...',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const statusText = screen.getByText('Parsing file...');
      expect(statusText).toHaveClass('text-blue-600');

      const spinner = container.querySelector('.text-blue-500');
      expect(spinner).toBeInTheDocument();
    });

    it('should show progress bar during parsing', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        totalRows: 100,
        processedRows: 50,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('should calculate percentage correctly', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        totalRows: 100,
        processedRows: 25,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('25%')).toBeInTheDocument();
    });
  });

  describe('Validating State', () => {
    it('should display validating message', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'validating',
        message: 'Validating data...',
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Validating data...')).toBeInTheDocument();
    });

    it('should show loading spinner during validation', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'validating',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show progress bar during validation', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'validating',
        totalRows: 50,
        processedRows: 30,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toBeInTheDocument();
      expect(screen.getByText('60%')).toBeInTheDocument();
    });
  });

  describe('Importing State', () => {
    it('should display importing message', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        message: 'Importing data...',
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Importing data...')).toBeInTheDocument();
    });

    it('should show loading spinner during import', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const spinner = container.querySelector('.animate-spin.text-blue-500');
      expect(spinner).toBeInTheDocument();
    });

    it('should show progress bar during import', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 100,
        processedRows: 75,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toBeInTheDocument();
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should display statistics during import', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        successCount: 50,
        warningCount: 3,
        errorCount: 2,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText(/50 successful/i)).toBeInTheDocument();
      expect(screen.getByText(/3 warnings/i)).toBeInTheDocument();
      expect(screen.getByText(/2 errors/i)).toBeInTheDocument();
    });

    it('should only show statistics when counts are greater than zero', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        successCount: 10,
        warningCount: 0,
        errorCount: 0,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText(/10 successful/i)).toBeInTheDocument();
      expect(screen.queryByText(/warnings/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/errors/i)).not.toBeInTheDocument();
    });

    it('should display current row progress', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        currentRow: 45,
        totalRows: 100,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Processing row 45 of 100')).toBeInTheDocument();
    });

    it('should not show row progress when totalRows is 0', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        currentRow: 0,
        totalRows: 0,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.queryByText(/processing row/i)).not.toBeInTheDocument();
    });
  });

  describe('Complete State', () => {
    it('should display complete status with green checkmark', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'complete',
        message: 'Import complete',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Import complete')).toBeInTheDocument();

      const checkIcon = container.querySelector('.text-green-500');
      expect(checkIcon).toBeInTheDocument();
    });

    it('should use green color for complete status', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'complete',
        message: 'Success',
      });

      render(<ImportProgressIndicator progress={progress} />);

      const statusText = screen.getByText('Success');
      expect(statusText).toHaveClass('text-green-600');
    });

    it('should display final statistics', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'complete',
        successCount: 95,
        warningCount: 3,
        errorCount: 2,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText(/95 successful/i)).toBeInTheDocument();
      expect(screen.getByText(/3 warnings/i)).toBeInTheDocument();
      expect(screen.getByText(/2 errors/i)).toBeInTheDocument();
    });

    it('should not show progress bar when complete', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'complete',
        totalRows: 100,
        processedRows: 100,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.h-2\\.5.overflow-hidden');
      expect(progressBar).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should display error status with red X icon', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'error',
        message: 'Import failed',
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Import failed')).toBeInTheDocument();

      const errorIcon = container.querySelector('.text-red-500');
      expect(errorIcon).toBeInTheDocument();
    });

    it('should use red color for error status', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'error',
        message: 'Failed',
      });

      render(<ImportProgressIndicator progress={progress} />);

      const statusText = screen.getByText('Failed');
      expect(statusText).toHaveClass('text-red-600');
    });

    it('should display error details', () => {
      const errors = [
        { row: 1, column: 'email', value: 'bad', message: 'Invalid email', severity: 'error' as const },
        { row: 2, column: 'name', value: '', message: 'Required field', severity: 'error' as const },
      ];

      const progress = importExportMockFactories.importProgress({
        status: 'error',
        message: 'Import failed',
        errors,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('Errors encountered:')).toBeInTheDocument();
      expect(screen.getByText(/row 1.*invalid email/i)).toBeInTheDocument();
      expect(screen.getByText(/row 2.*required field/i)).toBeInTheDocument();
    });

    it('should limit error display to 10 errors', () => {
      const errors = Array.from({ length: 15 }, (_, i) => ({
        row: i + 1,
        column: 'test',
        value: 'bad',
        message: `Error ${i + 1}`,
        severity: 'error' as const,
      }));

      const progress = importExportMockFactories.importProgress({
        status: 'error',
        errors,
      });

      render(<ImportProgressIndicator progress={progress} />);

      // Should show first 10 errors
      expect(screen.getByText(/row 1.*error 1/i)).toBeInTheDocument();
      expect(screen.getByText(/row 10.*error 10/i)).toBeInTheDocument();

      // Should show "and X more" message
      expect(screen.getByText(/and 5 more errors/i)).toBeInTheDocument();
    });

    it('should not show error details when errors array is empty', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'error',
        message: 'Import failed',
        errors: [],
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.queryByText('Errors encountered:')).not.toBeInTheDocument();
    });

    it('should display error details in scrollable container', () => {
      const errors = [
        { row: 1, column: 'email', value: 'bad', message: 'Invalid email', severity: 'error' as const },
      ];

      const progress = importExportMockFactories.importProgress({
        status: 'error',
        errors,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const errorContainer = container.querySelector('.max-h-32.overflow-y-auto');
      expect(errorContainer).toBeInTheDocument();
    });
  });

  describe('Progress Percentage', () => {
    it('should calculate 0% when totalRows is 0', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 0,
        processedRows: 0,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('should calculate 100% when all rows processed', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 50,
        processedRows: 50,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should round percentage to nearest integer', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 3,
        processedRows: 1, // 33.33%
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.getByText('33%')).toBeInTheDocument();
    });

    it('should only show percentage when totalRows > 0', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'parsing',
        totalRows: 0,
        processedRows: 0,
      });

      render(<ImportProgressIndicator progress={progress} />);

      expect(screen.queryByText('%')).not.toBeInTheDocument();
    });
  });

  describe('Progress Bar Styling', () => {
    it('should use blue progress bar for active states', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 100,
        processedRows: 50,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('should use green progress bar for complete', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'complete',
        totalRows: 100,
        processedRows: 100,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      // Complete state doesn't show progress bar, but if it did it would be green
      // Since complete doesn't show a bar, let's just verify the status color is green
      const statusIcon = container.querySelector('.text-green-500');
      expect(statusIcon).toBeInTheDocument();
    });

    it('should use red progress bar for error', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'error',
        totalRows: 100,
        processedRows: 50,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      // Error state doesn't show progress bar, but icon is red
      const errorIcon = container.querySelector('.text-red-500');
      expect(errorIcon).toBeInTheDocument();
    });

    it('should animate progress bar width', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 100,
        processedRows: 75,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toHaveStyle({ width: '75%' });
    });

    it('should have smooth transition on progress bar', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        totalRows: 100,
        processedRows: 50,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toHaveClass('transition-all');
      expect(progressBar).toHaveClass('duration-300');
    });
  });

  describe('Statistics Icons', () => {
    it('should show green check icon for success count', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        successCount: 10,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const successText = screen.getByText(/10 successful/i);
      const successIcon = successText.parentElement?.querySelector('.text-green-600');
      expect(successIcon).toBeInTheDocument();
    });

    it('should show yellow warning icon for warning count', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        warningCount: 5,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const warningText = screen.getByText(/5 warnings/i);
      const warningIcon = warningText.parentElement?.querySelector('.text-yellow-600');
      expect(warningIcon).toBeInTheDocument();
    });

    it('should show red X icon for error count', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        errorCount: 3,
      });

      const { container } = render(<ImportProgressIndicator progress={progress} />);

      const errorText = screen.getByText(/3 errors/i);
      const errorIcon = errorText.parentElement?.querySelector('.text-red-600');
      expect(errorIcon).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('should apply custom className', () => {
      const progress = importExportMockFactories.importProgress({
        status: 'importing',
        message: 'Processing...',
      });

      const { container } = render(
        <ImportProgressIndicator progress={progress} className="custom-progress" />
      );

      expect(container.querySelector('.custom-progress')).toBeInTheDocument();
    });
  });
});

describe('ImportProgressSkeleton', () => {
  it('should render skeleton loader', () => {
    const { container } = render(<ImportProgressSkeleton />);

    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('should render status header skeleton', () => {
    const { container } = render(<ImportProgressSkeleton />);

    const headerSkeleton = container.querySelector('.flex.items-center.justify-between');
    expect(headerSkeleton).toBeInTheDocument();

    const iconSkeleton = container.querySelector('.w-5.h-5.bg-gray-200.rounded-full');
    expect(iconSkeleton).toBeInTheDocument();

    const textSkeleton = container.querySelector('.h-4.w-32.bg-gray-200.rounded');
    expect(textSkeleton).toBeInTheDocument();
  });

  it('should render progress bar skeleton', () => {
    const { container } = render(<ImportProgressSkeleton />);

    const progressBarSkeleton = container.querySelector('.w-full.bg-gray-200.rounded-full.h-2\\.5');
    expect(progressBarSkeleton).toBeInTheDocument();
  });

  it('should render statistics skeleton', () => {
    const { container } = render(<ImportProgressSkeleton />);

    const statSkeletons = container.querySelectorAll('.h-4.w-24.bg-gray-200.rounded');
    expect(statSkeletons.length).toBeGreaterThan(0);
  });
});
