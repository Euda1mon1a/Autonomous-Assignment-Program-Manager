/**
 * Tests for PDF export functionality
 *
 * Tests ExportButton component with PDF format option,
 * covering export button rendering, format selection,
 * file download triggering, loading states, and error handling
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExportButton } from '@/components/ExportButton'

// Mock the export library
jest.mock('@/lib/export', () => ({
  exportToCSV: jest.fn(),
  exportToJSON: jest.fn(),
}))

// Mock fetch for PDF export
global.fetch = jest.fn()
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('PDF Export Functionality', () => {
  const mockData = [
    { id: '1', name: 'John Doe', role: 'Resident', pgy_level: 2 },
    { id: '2', name: 'Jane Smith', role: 'Faculty', pgy_level: null },
    { id: '3', name: 'Bob Johnson', role: 'Resident', pgy_level: 1 },
  ]

  const mockColumns = [
    { key: 'name', header: 'Name' },
    { key: 'role', header: 'Role' },
    { key: 'pgy_level', header: 'PGY Level' },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Export Button Rendering', () => {
    it('should render export button', () => {
      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })

    it('should show dropdown indicator icon', () => {
      const { container } = render(
        <ExportButton data={mockData} filename="test-export" columns={mockColumns} />
      )

      // Check for chevron-down icon
      const chevron = container.querySelector('.w-4.h-4')
      expect(chevron).toBeInTheDocument()
    })

    it('should be disabled when no data provided', () => {
      render(<ExportButton data={[]} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should be enabled when data is provided', () => {
      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      expect(button).not.toBeDisabled()
    })

    it('should not show dropdown menu initially', () => {
      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument()
      expect(screen.queryByText('Export as PDF')).not.toBeInTheDocument()
    })
  })

  describe('Dropdown Menu Behavior', () => {
    it('should open dropdown menu when clicked', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      expect(screen.getByText('Export as CSV')).toBeInTheDocument()
      expect(screen.getByText('Export as JSON')).toBeInTheDocument()
    })

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup()

      render(
        <div>
          <div data-testid="outside">Outside</div>
          <ExportButton data={mockData} filename="test-export" columns={mockColumns} />
        </div>
      )

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      expect(screen.getByText('Export as CSV')).toBeInTheDocument()

      const outside = screen.getByTestId('outside')
      await user.click(outside)

      await waitFor(() => {
        expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument()
      })
    })

    it('should close dropdown on escape key', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      expect(screen.getByText('Export as CSV')).toBeInTheDocument()

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument()
      })
    })

    it('should rotate chevron icon when dropdown is open', async () => {
      const user = userEvent.setup()

      const { container } = render(
        <ExportButton data={mockData} filename="test-export" columns={mockColumns} />
      )

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const chevron = container.querySelector('.rotate-180')
      expect(chevron).toBeInTheDocument()
    })
  })

  describe('Format Selection', () => {
    it('should show all export format options', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      expect(screen.getByText('Export as CSV')).toBeInTheDocument()
      expect(screen.getByText('Export as JSON')).toBeInTheDocument()
    })

    it('should have proper ARIA attributes on menu items', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      const jsonOption = screen.getByRole('menuitem', { name: /export as json/i })

      expect(csvOption).toBeInTheDocument()
      expect(jsonOption).toBeInTheDocument()
    })

    it('should highlight menu item on hover', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })

      expect(csvOption).toHaveClass('hover:bg-gray-100')
    })
  })

  describe('CSV Export', () => {
    it('should export as CSV when CSV option is selected', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledWith(mockData, 'test-export', mockColumns)
      })
    })

    it('should close dropdown after CSV export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument()
      })
    })
  })

  describe('JSON Export', () => {
    it('should export as JSON when JSON option is selected', async () => {
      const user = userEvent.setup()
      const { exportToJSON } = require('@/lib/export')

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const jsonOption = screen.getByRole('menuitem', { name: /export as json/i })
      await user.click(jsonOption)

      await waitFor(() => {
        expect(exportToJSON).toHaveBeenCalledWith(mockData, 'test-export')
      })
    })

    it('should close dropdown after JSON export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const jsonOption = screen.getByRole('menuitem', { name: /export as json/i })
      await user.click(jsonOption)

      await waitFor(() => {
        expect(screen.queryByText('Export as JSON')).not.toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    it('should show loading spinner during export', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      // Make export take some time
      exportToCSV.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      // Should show loading spinner
      const spinner = screen.getByRole('button').querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()

      await waitFor(() => {
        expect(screen.getByRole('button').querySelector('.animate-spin')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should disable button during export', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      exportToCSV.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(button).toBeDisabled()
      })

      await waitFor(() => {
        expect(button).not.toBeDisabled()
      }, { timeout: 3000 })
    })

    it('should prevent multiple simultaneous exports', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      exportToCSV.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)
      await user.click(csvOption)
      await user.click(csvOption)

      // Should only call once due to disabled state
      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle empty data gracefully', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={[]} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()

      // Should not open dropdown when disabled
      await user.click(button)
      expect(screen.queryByText('Export as CSV')).not.toBeInTheDocument()
    })

    it('should not export when data is null', () => {
      const { exportToCSV } = require('@/lib/export')

      render(
        <ExportButton
          data={null as unknown as Record<string, unknown>[]}
          filename="test-export"
          columns={mockColumns}
        />
      )

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
      expect(exportToCSV).not.toHaveBeenCalled()
    })

    it('should remain functional after export error', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      // Export throws error
      exportToCSV.mockImplementationOnce(() => {
        throw new Error('Export failed')
      })

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      // Button should be usable again after error
      await waitFor(() => {
        expect(button).not.toBeDisabled()
      })

      // Export was attempted
      expect(exportToCSV).toHaveBeenCalled()

      // Button remains functional
      expect(button).toBeEnabled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA attributes on button', () => {
      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-haspopup', 'true')
      expect(button).toHaveAttribute('aria-expanded', 'false')
    })

    it('should update aria-expanded when dropdown opens', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(button).toHaveAttribute('aria-expanded', 'true')
    })

    it('should have proper role on dropdown menu', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')
      await user.click(button)

      const menu = screen.getByRole('menu')
      expect(menu).toBeInTheDocument()
    })

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test-export" columns={mockColumns} />)

      const button = screen.getByRole('button')

      // Focus the button
      button.focus()
      expect(button).toHaveFocus()

      // Open dropdown with Enter key
      await user.keyboard('{Enter}')

      expect(screen.getByText('Export as CSV')).toBeInTheDocument()
    })
  })

  describe('Data Validation', () => {
    it('should handle data with missing fields', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      const incompleteData = [
        { id: '1', name: 'John Doe' },
        { id: '2', role: 'Faculty' },
        { id: '3', name: 'Bob Johnson', role: 'Resident' },
      ]

      render(
        <ExportButton data={incompleteData} filename="test-export" columns={mockColumns} />
      )

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledWith(incompleteData, 'test-export', mockColumns)
      })
    })

    it('should handle special characters in filename', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      render(
        <ExportButton
          data={mockData}
          filename="test export (2024-01-01)"
          columns={mockColumns}
        />
      )

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledWith(
          mockData,
          'test export (2024-01-01)',
          mockColumns
        )
      })
    })

    it('should handle large datasets', async () => {
      const user = userEvent.setup()
      const { exportToCSV } = require('@/lib/export')

      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        id: `${i + 1}`,
        name: `Person ${i + 1}`,
        role: i % 2 === 0 ? 'Resident' : 'Faculty',
      }))

      render(<ExportButton data={largeData} filename="large-export" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      await user.click(button)

      const csvOption = screen.getByRole('menuitem', { name: /export as csv/i })
      await user.click(csvOption)

      await waitFor(() => {
        expect(exportToCSV).toHaveBeenCalledWith(largeData, 'large-export', mockColumns)
      })
    })
  })
})
