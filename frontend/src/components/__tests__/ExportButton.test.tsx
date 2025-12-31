/**
 * Tests for ExportButton Component
 * Component: ExportButton - Data export dropdown
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@/test-utils';
import '@testing-library/jest-dom';
import { ExportButton } from '../ExportButton';

// Mock the export utilities
jest.mock('@/lib/export', () => ({
  exportToCSV: jest.fn(),
  exportToJSON: jest.fn(),
}));

import { exportToCSV, exportToJSON } from '@/lib/export';

describe('ExportButton', () => {
  const mockData = [
    { id: '1', name: 'John Doe', email: 'john@example.com' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
  ];

  const mockColumns = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  // Test: Rendering
  describe('Rendering', () => {
    it('renders export button', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      expect(screen.getByText('Export')).toBeInTheDocument();
    });

    it('shows download icon', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      expect(container.querySelector('.lucide-download')).toBeInTheDocument();
    });

    it('shows chevron icon', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      expect(container.querySelector('.lucide-chevron-down')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      const button = screen.getByText('Export');
      expect(button).toHaveAttribute('aria-haspopup', 'true');
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('is disabled when data is empty', () => {
      render(<ExportButton data={[]} filename="test" columns={mockColumns} />);

      expect(screen.getByText('Export')).toBeDisabled();
    });

    it('is enabled when data is provided', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      expect(screen.getByText('Export')).not.toBeDisabled();
    });
  });

  // Test: Dropdown interaction
  describe('Dropdown Interaction', () => {
    it('opens dropdown when button clicked', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      expect(screen.getByText('Export as CSV')).toBeInTheDocument();
      expect(screen.getByText('Export as JSON')).toBeInTheDocument();
    });

    it('closes dropdown when clicked outside', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      expect(screen.getByText('Export as CSV')).toBeInTheDocument();

      fireEvent.mouseDown(document.body);

      expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument();
    });

    it('closes dropdown on Escape key', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      expect(screen.getByText('Export as CSV')).toBeInTheDocument();

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument();
    });

    it('toggles aria-expanded when opening/closing', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      const button = screen.getByText('Export');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');

      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('rotates chevron when dropdown opens', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      const chevron = container.querySelector('.lucide-chevron-down');
      expect(chevron).not.toHaveClass('rotate-180');

      fireEvent.click(screen.getByText('Export'));

      expect(chevron).toHaveClass('rotate-180');
    });

    it('dropdown has proper menu role', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      const menu = screen.getByRole('menu');
      expect(menu).toBeInTheDocument();
    });

    it('menu items have menuitem role', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems).toHaveLength(2);
    });
  });

  // Test: Export functionality
  describe('Export Functionality', () => {
    it('calls exportToCSV when CSV option clicked', async () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      fireEvent.click(screen.getByText('Export as CSV'));

      act(() => {
        jest.advanceTimersByTime(250);
      });

      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledWith(mockData, 'test', mockColumns);
      });
    });

    it('calls exportToJSON when JSON option clicked', async () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      fireEvent.click(screen.getByText('Export as JSON'));

      act(() => {
        jest.advanceTimersByTime(250);
      });

      await waitFor(() => {
        expect(exportToJSON).toHaveBeenCalledWith(mockData, 'test');
      });
    });

    it('closes dropdown after export', async () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      fireEvent.click(screen.getByText('Export as CSV'));

      act(() => {
        jest.advanceTimersByTime(250);
      });

      await waitFor(() => {
        expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument();
      });
    });

    it('shows loading spinner during export', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      fireEvent.click(screen.getByText('Export as CSV'));

      expect(container.querySelector('.lucide-loader-2')).toBeInTheDocument();
      expect(container.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('disables button while exporting', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));
      fireEvent.click(screen.getByText('Export as CSV'));

      expect(screen.getByText('Export')).toBeDisabled();
    });

    it('does not export when data is empty', async () => {
      render(<ExportButton data={[]} filename="test" columns={mockColumns} />);

      // Button should be disabled
      expect(screen.getByText('Export')).toBeDisabled();

      expect(exportToCSV).not.toHaveBeenCalled();
      expect(exportToJSON).not.toHaveBeenCalled();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('handles long filenames', () => {
      const longFilename = 'very_long_filename_that_should_still_work_correctly';

      render(<ExportButton data={mockData} filename={longFilename} columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      expect(screen.getByText('Export as CSV')).toBeInTheDocument();
    });

    it('handles large datasets', () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: String(i),
        name: `User ${i}`,
      }));

      render(<ExportButton data={largeData} filename="large" columns={mockColumns} />);

      expect(screen.getByText('Export')).not.toBeDisabled();
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      unmount();

      fireEvent.mouseDown(document.body);
      // Should not throw error
    });

    it('dropdown is positioned correctly', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      expect(container.querySelector('.absolute.right-0.mt-2')).toBeInTheDocument();
    });

    it('has proper z-index for dropdown', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      expect(container.querySelector('.z-10')).toBeInTheDocument();
    });

    it('dropdown has shadow and border', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      expect(container.querySelector('.shadow-lg.border')).toBeInTheDocument();
    });

    it('menu items have hover states', () => {
      const { container } = render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      fireEvent.click(screen.getByText('Export'));

      const menuItems = container.querySelectorAll('.hover\\:bg-gray-100');
      expect(menuItems.length).toBeGreaterThan(0);
    });

    it('handles null data gracefully', () => {
      // @ts-expect-error Testing edge case
      render(<ExportButton data={null} filename="test" columns={mockColumns} />);

      expect(screen.getByText('Export')).toBeDisabled();
    });

    it('button has proper styling', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />);

      const button = screen.getByText('Export');
      expect(button).toHaveClass('btn-secondary');
    });
  });
});
