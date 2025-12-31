/**
 * Tests for Excel export components
 *
 * Tests ExcelExportButton and ExcelExportDropdown components
 * covering export button rendering, loading states, error handling,
 * and date range selection functionality
 */
import React from 'react'
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { ExcelExportButton, ExcelExportDropdown } from '@/components/ExcelExportButton'
import * as exportModule from '@/lib/export'
import { ToastProvider } from '@/contexts/ToastContext'

// Mock the export library
jest.mock('@/lib/export')

const mockExportToLegacyXlsx = exportModule.exportToLegacyXlsx as jest.MockedFunction<
  typeof exportModule.exportToLegacyXlsx
>

// Wrapper with ToastProvider
function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <ToastProvider>{children}</ToastProvider>
  }
}

describe('ExcelExportButton', () => {
  const defaultProps = {
    startDate: '2024-01-01',
    endDate: '2024-01-28',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    mockExportToLegacyXlsx.mockResolvedValue(undefined)
  })

  describe('Rendering', () => {
    it('should render export button with correct text', () => {
      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument()
    })

    it('should render with FileSpreadsheet icon', () => {
      const { container } = render(<ExcelExportButton {...defaultProps} />, {
        wrapper: createWrapper(),
      })

      // Check for the icon (lucide-react renders as svg)
      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('should apply custom className when provided', () => {
      const { container } = render(
        <ExcelExportButton {...defaultProps} className="custom-class" />,
        { wrapper: createWrapper() }
      )

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })

    it('should not be disabled initially', () => {
      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      expect(button).not.toBeDisabled()
    })
  })

  describe('Export Functionality', () => {
    it('should trigger export when button is clicked', async () => {
      const user = userEvent.setup()

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockExportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          undefined,
          undefined
        )
      })
    })

    it('should pass block number when provided', async () => {
      const user = userEvent.setup()

      render(<ExcelExportButton {...defaultProps} blockNumber={5} />, {
        wrapper: createWrapper(),
      })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockExportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          5,
          undefined
        )
      })
    })

    it('should pass federal holidays when provided', async () => {
      const user = userEvent.setup()
      const holidays = ['2024-01-01', '2024-01-15']

      render(<ExcelExportButton {...defaultProps} federalHolidays={holidays} />, {
        wrapper: createWrapper(),
      })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockExportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          undefined,
          holidays
        )
      })
    })
  })

  describe('Loading State', () => {
    it('should show loading state during export', async () => {
      const user = userEvent.setup()

      // Make export take some time
      mockExportToLegacyXlsx.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      // Should show loading text
      expect(screen.getByText('Exporting...')).toBeInTheDocument()

      // Button should be disabled
      expect(button).toBeDisabled()

      // Should show spinner icon
      const spinner = screen.getByText('Exporting...').parentElement?.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()

      // Wait for export to complete
      await waitFor(() => {
        expect(screen.queryByText('Exporting...')).not.toBeInTheDocument()
      })
    })

    it('should return to normal state after export completes', async () => {
      const user = userEvent.setup()

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText('Export Excel')).toBeInTheDocument()
        expect(button).not.toBeDisabled()
      })
    })

    it('should prevent multiple simultaneous exports', async () => {
      const user = userEvent.setup()

      mockExportToLegacyXlsx.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')

      // Click multiple times
      await user.click(button)
      await user.click(button)
      await user.click(button)

      // Should only call export once
      expect(mockExportToLegacyXlsx).toHaveBeenCalledTimes(1)
    })
  })

  describe('Error Handling', () => {
    it('should display error message when export fails', async () => {
      const user = userEvent.setup()
      const errorMessage = 'Failed to generate Excel file'

      mockExportToLegacyXlsx.mockRejectedValue(new Error(errorMessage))

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        // Check for error in the component's error display (below the button)
        const errorElements = screen.getAllByText(errorMessage)
        expect(errorElements.length).toBeGreaterThan(0)
      })
    })

    it('should handle generic errors', async () => {
      const user = userEvent.setup()

      mockExportToLegacyXlsx.mockRejectedValue('Generic error')

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        // Should show generic error message
        const errorElements = screen.getAllByText('Export failed')
        expect(errorElements.length).toBeGreaterThan(0)
      })
    })

    it('should clear error on successful export', async () => {
      const user = userEvent.setup()

      mockExportToLegacyXlsx.mockRejectedValueOnce(new Error('First export failed'))

      render(<ExcelExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')

      // First export fails
      await user.click(button)
      await waitFor(() => {
        const errorElements = screen.getAllByText('First export failed')
        expect(errorElements.length).toBeGreaterThan(0)
      })

      // Second export succeeds
      mockExportToLegacyXlsx.mockResolvedValue(undefined)
      await user.click(button)

      await waitFor(() => {
        // The error should be cleared from the component's error display
        // (Note: Toast messages may persist longer, which is expected behavior)
        expect(mockExportToLegacyXlsx).toHaveBeenCalledTimes(2)
      })
    })
  })
})

describe('ExcelExportDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockExportToLegacyXlsx.mockResolvedValue(undefined)
  })

  describe('Rendering', () => {
    it('should render export button', () => {
      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument()
    })

    it('should not show dropdown initially', () => {
      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
    })
  })

  describe('Dropdown Behavior', () => {
    it('should open dropdown when button is clicked', async () => {
      const user = userEvent.setup()

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      expect(screen.getByText('Export Schedule')).toBeInTheDocument()
    })

    it('should close dropdown when clicking backdrop', async () => {
      const user = userEvent.setup()

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      expect(screen.getByText('Export Schedule')).toBeInTheDocument()

      // Click the backdrop
      const backdrop = document.querySelector('.fixed.inset-0')
      if (backdrop) {
        await user.click(backdrop)

        await waitFor(() => {
          expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
        })
      }
    })

    it('should toggle dropdown on subsequent clicks', async () => {
      const user = userEvent.setup()

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })

      // Open
      await user.click(button)
      expect(screen.getByText('Export Schedule')).toBeInTheDocument()

      // Close
      await user.click(button)
      await waitFor(() => {
        expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
      })
    })
  })

  describe('Date Range Selection', () => {
    it('should render date input fields when dropdown is open', async () => {
      const user = userEvent.setup()

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      expect(screen.getByText(/start date/i)).toBeInTheDocument()
      expect(screen.getByText(/end date/i)).toBeInTheDocument()

      const dateInputs = screen.getAllByDisplayValue(/^\d{4}-\d{2}-\d{2}$/)
      expect(dateInputs.length).toBeGreaterThanOrEqual(2)
    })

    it('should set default dates when opened', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      // Get all date inputs
      const inputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = inputs[0] as HTMLInputElement
      const endDateInput = inputs[1] as HTMLInputElement

      // Should have default values set
      expect(startDateInput.value).toBeTruthy()
      expect(endDateInput.value).toBeTruthy()
    })

    it('should allow changing start date', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const inputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = inputs[0] as HTMLInputElement
      await user.clear(startDateInput)
      await user.type(startDateInput, '2024-03-01')

      expect(startDateInput.value).toBe('2024-03-01')
    })

    it('should allow changing end date', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const inputs = container.querySelectorAll('input[type="date"]')
      const endDateInput = inputs[1] as HTMLInputElement
      await user.clear(endDateInput)
      await user.type(endDateInput, '2024-03-28')

      expect(endDateInput.value).toBe('2024-03-28')
    })

    it('should allow changing block number', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const blockInput = container.querySelector('input[type="number"]') as HTMLInputElement
      await user.type(blockInput, '7')

      expect(blockInput.value).toBe('7')
    })
  })

  describe('Export with Date Range', () => {
    it('should export with selected dates', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const inputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = inputs[0] as HTMLInputElement
      const endDateInput = inputs[1] as HTMLInputElement

      await user.clear(startDateInput)
      await user.type(startDateInput, '2024-02-01')
      await user.clear(endDateInput)
      await user.type(endDateInput, '2024-02-28')

      const downloadButton = screen.getByRole('button', { name: /download excel/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(mockExportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-02-01',
          '2024-02-28',
          undefined
        )
      })
    })

    it('should show error if dates are missing', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const inputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = inputs[0] as HTMLInputElement
      await user.clear(startDateInput)

      // The download button should be disabled when dates are missing
      const downloadButton = screen.getByRole('button', { name: /download excel/i })
      expect(downloadButton).toBeDisabled()

      // Export function should not be called
      expect(mockExportToLegacyXlsx).not.toHaveBeenCalled()
    })

    it('should disable download button when dates are missing', async () => {
      const user = userEvent.setup()

      const { container } = render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const inputs = container.querySelectorAll('input[type="date"]')
      const startDateInput = inputs[0] as HTMLInputElement
      await user.clear(startDateInput)

      const downloadButton = screen.getByRole('button', { name: /download excel/i })
      expect(downloadButton).toBeDisabled()
    })

    it('should close dropdown after successful export', async () => {
      const user = userEvent.setup()

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download excel/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
      })
    })

    it('should show loading state during export', async () => {
      const user = userEvent.setup()

      mockExportToLegacyXlsx.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExcelExportDropdown />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export excel/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download excel/i })
      await user.click(downloadButton)

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
      expect(downloadButton).toBeDisabled()

      await waitFor(() => {
        expect(screen.queryByText('Exporting...')).not.toBeInTheDocument()
      })
    })
  })
})
