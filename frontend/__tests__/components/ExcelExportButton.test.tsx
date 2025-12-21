import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExcelExportButton, ExcelExportDropdown } from '@/components/ExcelExportButton'
import * as exportLib from '@/lib/export'

// Mock toast context
const mockToast = {
  success: jest.fn(),
  error: jest.fn(),
}

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ toast: mockToast }),
}))

// Mock export function
jest.mock('@/lib/export', () => ({
  exportToLegacyXlsx: jest.fn(),
}))

describe('ExcelExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(exportLib.exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined)
  })

  describe('Button Rendering', () => {
    it('should render export button', () => {
      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument()
    })

    it('should have spreadsheet icon', () => {
      const { container } = render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <ExcelExportButton
          startDate="2024-01-01"
          endDate="2024-01-28"
          className="custom-class"
        />
      )

      const button = container.querySelector('.custom-class')
      expect(button).toBeInTheDocument()
    })

    it('should have green background', () => {
      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      const button = screen.getByRole('button', { name: /export excel/i })
      expect(button).toHaveClass('bg-green-600')
      expect(button).toHaveClass('hover:bg-green-700')
    })
  })

  describe('Export Functionality', () => {
    it('should call exportToLegacyXlsx with correct dates', async () => {
      const user = userEvent.setup()

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(exportLib.exportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          undefined,
          undefined
        )
      })
    })

    it('should include block number when provided', async () => {
      const user = userEvent.setup()

      render(
        <ExcelExportButton
          startDate="2024-01-01"
          endDate="2024-01-28"
          blockNumber={5}
        />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(exportLib.exportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          5,
          undefined
        )
      })
    })

    it('should include federal holidays when provided', async () => {
      const user = userEvent.setup()

      const holidays = ['2024-01-01', '2024-07-04']

      render(
        <ExcelExportButton
          startDate="2024-01-01"
          endDate="2024-01-28"
          federalHolidays={holidays}
        />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(exportLib.exportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          undefined,
          holidays
        )
      })
    })

    it('should show loading state during export', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
    })

    it('should disable button during export', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const button = screen.getByRole('button', { name: /exporting/i })
      expect(button).toBeDisabled()
    })

    it('should show spinner during export', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      const { container } = render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('should re-enable button after export completes', async () => {
      const user = userEvent.setup()

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /export excel/i })
        expect(button).not.toBeDisabled()
      })
    })
  })

  describe('Error Handling', () => {
    it('should display error message when export fails', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockRejectedValue(
        new Error('Export failed')
      )

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(screen.getByText('Export failed')).toBeInTheDocument()
      })
    })

    it('should show toast error notification', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockRejectedValue(
        new Error('Export failed')
      )

      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Export failed')
      })
    })

    it('should clear error on successful export', async () => {
      const user = userEvent.setup()

      // First export fails
      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockRejectedValueOnce(
        new Error('Export failed')
      )

      const { rerender } = render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(screen.getByText('Export failed')).toBeInTheDocument()
      })

      // Second export succeeds
      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockResolvedValueOnce(undefined)

      rerender(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        expect(screen.queryByText('Export failed')).not.toBeInTheDocument()
      })
    })

    it('should style error message correctly', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockRejectedValue(
        new Error('Export failed')
      )

      const { container } = render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      await waitFor(() => {
        const errorDiv = container.querySelector('.bg-red-50')
        expect(errorDiv).toBeInTheDocument()
        expect(errorDiv).toHaveClass('border-red-200')
        expect(errorDiv).toHaveClass('text-red-600')
      })
    })
  })

  describe('Button Styling', () => {
    it('should have disabled styling when disabled', () => {
      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      const button = screen.getByRole('button', { name: /export excel/i })
      expect(button).toHaveClass('disabled:bg-green-400')
      expect(button).toHaveClass('disabled:cursor-not-allowed')
    })

    it('should have transition effect', () => {
      render(
        <ExcelExportButton startDate="2024-01-01" endDate="2024-01-28" />
      )

      const button = screen.getByRole('button', { name: /export excel/i })
      expect(button).toHaveClass('transition-colors')
    })
  })
})

describe('ExcelExportDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-02-15'))
    ;(exportLib.exportToLegacyXlsx as jest.Mock).mockResolvedValue(undefined)
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Dropdown Rendering', () => {
    it('should render dropdown button', () => {
      render(<ExcelExportDropdown />)

      expect(screen.getByRole('button', { name: /export excel/i })).toBeInTheDocument()
    })

    it('should open dropdown when clicking button', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      expect(screen.getByText('Export Schedule')).toBeInTheDocument()
      expect(screen.getByLabelText('Start Date')).toBeInTheDocument()
      expect(screen.getByLabelText('End Date')).toBeInTheDocument()
    })

    it('should close dropdown when clicking backdrop', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))
      expect(screen.getByText('Export Schedule')).toBeInTheDocument()

      const backdrop = container.querySelector('.fixed.inset-0')
      await user.click(backdrop!)

      await waitFor(() => {
        expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
      })
    })
  })

  describe('Date Inputs', () => {
    it('should render start date input', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      expect(screen.getByLabelText('Start Date')).toBeInTheDocument()
    })

    it('should render end date input', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      expect(screen.getByLabelText('End Date')).toBeInTheDocument()
    })

    it('should set default dates when opening dropdown', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const startInput = screen.getByLabelText('Start Date') as HTMLInputElement
      const endInput = screen.getByLabelText('End Date') as HTMLInputElement

      expect(startInput.value).toBe('2024-02-15')
      expect(endInput.value).toBe('2024-03-13') // 27 days later
    })

    it('should allow changing start date', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const startInput = screen.getByLabelText('Start Date') as HTMLInputElement
      await user.clear(startInput)
      await user.type(startInput, '2024-01-01')

      expect(startInput.value).toBe('2024-01-01')
    })

    it('should allow changing end date', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const endInput = screen.getByLabelText('End Date') as HTMLInputElement
      await user.clear(endInput)
      await user.type(endInput, '2024-01-28')

      expect(endInput.value).toBe('2024-01-28')
    })
  })

  describe('Block Number Input', () => {
    it('should render block number input', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      expect(screen.getByLabelText(/block number/i)).toBeInTheDocument()
    })

    it('should have placeholder text', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const blockInput = screen.getByLabelText(/block number/i) as HTMLInputElement
      expect(blockInput.placeholder).toBe('Auto-calculated')
    })

    it('should allow entering block number', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const blockInput = screen.getByLabelText(/block number/i) as HTMLInputElement
      await user.type(blockInput, '5')

      expect(blockInput.value).toBe('5')
    })

    it('should have min and max constraints', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const blockInput = screen.getByLabelText(/block number/i)
      expect(blockInput).toHaveAttribute('min', '1')
      expect(blockInput).toHaveAttribute('max', '13')
    })
  })

  describe('Export from Dropdown', () => {
    it('should export with selected dates', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const startInput = screen.getByLabelText('Start Date')
      const endInput = screen.getByLabelText('End Date')

      await user.clear(startInput)
      await user.type(startInput, '2024-01-01')
      await user.clear(endInput)
      await user.type(endInput, '2024-01-28')

      await user.click(screen.getByRole('button', { name: /download excel/i }))

      await waitFor(() => {
        expect(exportLib.exportToLegacyXlsx).toHaveBeenCalledWith(
          '2024-01-01',
          '2024-01-28',
          undefined
        )
      })
    })

    it('should export with block number', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const blockInput = screen.getByLabelText(/block number/i)
      await user.type(blockInput, '7')

      await user.click(screen.getByRole('button', { name: /download excel/i }))

      await waitFor(() => {
        expect(exportLib.exportToLegacyXlsx).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(String),
          7
        )
      })
    })

    it('should close dropdown after successful export', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))
      await user.click(screen.getByRole('button', { name: /download excel/i }))

      await waitFor(() => {
        expect(screen.queryByText('Export Schedule')).not.toBeInTheDocument()
      })
    })

    it('should disable export button when dates are missing', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const startInput = screen.getByLabelText('Start Date')
      await user.clear(startInput)

      const exportButton = screen.getByRole('button', { name: /download excel/i })
      expect(exportButton).toBeDisabled()
    })

    it('should show error when trying to export without dates', async () => {
      const user = userEvent.setup({ delay: null })

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))

      const startInput = screen.getByLabelText('Start Date')
      const endInput = screen.getByLabelText('End Date')

      await user.clear(startInput)
      await user.clear(endInput)

      await user.click(screen.getByRole('button', { name: /download excel/i }))

      await waitFor(() => {
        expect(screen.getByText(/please select start and end dates/i)).toBeInTheDocument()
      })
    })

    it('should show loading state during export', async () => {
      const user = userEvent.setup({ delay: null })

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))
      await user.click(screen.getByRole('button', { name: /download excel/i }))

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
    })

    it('should show error message on export failure', async () => {
      const user = userEvent.setup({ delay: null })

      ;(exportLib.exportToLegacyXlsx as jest.Mock).mockRejectedValue(
        new Error('Export failed')
      )

      render(<ExcelExportDropdown />)

      await user.click(screen.getByRole('button', { name: /export excel/i }))
      await user.click(screen.getByRole('button', { name: /download excel/i }))

      await waitFor(() => {
        expect(screen.getByText('Export failed')).toBeInTheDocument()
        expect(mockToast.error).toHaveBeenCalledWith('Export failed')
      })
    })
  })
})
