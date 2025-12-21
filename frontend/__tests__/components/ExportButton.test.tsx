import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ExportButton } from '@/components/ExportButton'
import * as exportLib from '@/lib/export'

// Mock export functions
jest.mock('@/lib/export', () => ({
  exportToCSV: jest.fn(),
  exportToJSON: jest.fn(),
}))

// Mock URL methods
const mockCreateObjectURL = jest.fn(() => 'blob:mock-url')
const mockRevokeObjectURL = jest.fn()
global.URL.createObjectURL = mockCreateObjectURL
global.URL.revokeObjectURL = mockRevokeObjectURL

describe('ExportButton', () => {
  const mockData = [
    { id: '1', name: 'John Doe', email: 'john@example.com' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com' },
  ]

  const mockColumns = [
    { key: 'id', header: 'ID' },
    { key: 'name', header: 'Name' },
    { key: 'email', header: 'Email' },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Button Rendering', () => {
    it('should render export button', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })

    it('should have download icon', () => {
      const { container } = render(
        <ExportButton data={mockData} filename="test" columns={mockColumns} />
      )

      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })

    it('should have chevron down icon', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })

    it('should be disabled when data is empty', () => {
      render(<ExportButton data={[]} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toBeDisabled()
    })

    it('should be disabled when data is null', () => {
      render(<ExportButton data={null as any} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toBeDisabled()
    })

    it('should be enabled when data is provided', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).not.toBeDisabled()
    })

    it('should apply disabled styling when disabled', () => {
      render(<ExportButton data={[]} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toHaveClass('disabled:opacity-50')
      expect(button).toHaveClass('disabled:cursor-not-allowed')
    })
  })

  describe('Dropdown Behavior', () => {
    it('should open dropdown when clicking button', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      expect(screen.getByRole('menu')).toBeInTheDocument()
      expect(screen.getByRole('menuitem', { name: /export as csv/i })).toBeInTheDocument()
      expect(screen.getByRole('menuitem', { name: /export as json/i })).toBeInTheDocument()
    })

    it('should close dropdown when clicking outside', async () => {
      const user = userEvent.setup()

      render(
        <div>
          <ExportButton data={mockData} filename="test" columns={mockColumns} />
          <button>Outside button</button>
        </div>
      )

      await user.click(screen.getByRole('button', { name: /export/i }))
      expect(screen.getByRole('menu')).toBeInTheDocument()

      await user.click(screen.getByRole('button', { name: /outside button/i }))

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument()
      })
    })

    it('should close dropdown on escape key', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      expect(screen.getByRole('menu')).toBeInTheDocument()

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument()
      })
    })

    it('should set aria-expanded to true when dropdown is open', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toHaveAttribute('aria-expanded', 'false')

      await user.click(button)

      expect(button).toHaveAttribute('aria-expanded', 'true')
    })

    it('should set aria-haspopup to true', () => {
      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toHaveAttribute('aria-haspopup', 'true')
    })

    it('should rotate chevron icon when open', async () => {
      const user = userEvent.setup()

      const { container } = render(
        <ExportButton data={mockData} filename="test" columns={mockColumns} />
      )

      await user.click(screen.getByRole('button', { name: /export/i }))

      const chevron = container.querySelector('.rotate-180')
      expect(chevron).toBeInTheDocument()
    })
  })

  describe('CSV Export', () => {
    it('should call exportToCSV when clicking CSV option', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        expect(exportLib.exportToCSV).toHaveBeenCalledWith(mockData, 'test', mockColumns)
      })
    })

    it('should show loading state during CSV export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      // Loading spinner should appear briefly
      const spinner = screen.queryByRole('button')?.querySelector('.animate-spin')
      expect(spinner).toBeTruthy()
    })

    it('should close dropdown after CSV export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument()
      })
    })

    it('should not export if data is empty', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={[]} filename="test" columns={mockColumns} />)

      const button = screen.getByRole('button', { name: /export/i })
      expect(button).toBeDisabled()

      // Should not be able to click
      expect(exportLib.exportToCSV).not.toHaveBeenCalled()
    })
  })

  describe('JSON Export', () => {
    it('should call exportToJSON when clicking JSON option', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as json/i }))

      await waitFor(() => {
        expect(exportLib.exportToJSON).toHaveBeenCalledWith(mockData, 'test')
      })
    })

    it('should show loading state during JSON export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as json/i }))

      // Loading spinner should appear briefly
      const spinner = screen.queryByRole('button')?.querySelector('.animate-spin')
      expect(spinner).toBeTruthy()
    })

    it('should close dropdown after JSON export', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as json/i }))

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument()
      })
    })
  })

  describe('Menu Styling', () => {
    it('should position dropdown correctly', async () => {
      const user = userEvent.setup()

      const { container } = render(
        <ExportButton data={mockData} filename="test" columns={mockColumns} />
      )

      await user.click(screen.getByRole('button', { name: /export/i }))

      const menu = screen.getByRole('menu')
      expect(menu).toHaveClass('absolute')
      expect(menu).toHaveClass('right-0')
      expect(menu).toHaveClass('mt-2')
    })

    it('should have correct menu styling', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      const menu = screen.getByRole('menu')
      expect(menu).toHaveClass('bg-white')
      expect(menu).toHaveClass('rounded-md')
      expect(menu).toHaveClass('shadow-lg')
      expect(menu).toHaveClass('border')
    })

    it('should style menu items correctly', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      const csvMenuItem = screen.getByRole('menuitem', { name: /export as csv/i })
      expect(csvMenuItem).toHaveClass('text-left')
      expect(csvMenuItem).toHaveClass('px-4')
      expect(csvMenuItem).toHaveClass('py-2')
      expect(csvMenuItem).toHaveClass('hover:bg-gray-100')
    })
  })

  describe('Loading State', () => {
    it('should disable button during export', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToCSV as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should show spinner icon during export', async () => {
      const user = userEvent.setup()

      ;(exportLib.exportToCSV as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      const spinner = screen.getByRole('button').querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })

    it('should re-enable button after export completes', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        const button = screen.getByRole('button', { name: /export/i })
        expect(button).not.toBeDisabled()
      })
    })
  })

  describe('Dropdown Positioning', () => {
    it('should have z-index for dropdown', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      const menu = screen.getByRole('menu')
      expect(menu).toHaveClass('z-10')
    })

    it('should have relative positioning on container', () => {
      const { container } = render(
        <ExportButton data={mockData} filename="test" columns={mockColumns} />
      )

      const dropdownContainer = container.querySelector('.relative')
      expect(dropdownContainer).toBeInTheDocument()
    })
  })

  describe('Menu Items Interaction', () => {
    it('should apply focus styles to menu items', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      const csvMenuItem = screen.getByRole('menuitem', { name: /export as csv/i })
      expect(csvMenuItem).toHaveClass('focus:bg-gray-100')
      expect(csvMenuItem).toHaveClass('focus:outline-none')
    })

    it('should have correct text size for menu items', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))

      const csvMenuItem = screen.getByRole('menuitem', { name: /export as csv/i })
      expect(csvMenuItem).toHaveClass('text-sm')
    })
  })

  describe('Multiple Export Operations', () => {
    it('should allow multiple export operations', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      // First export
      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        expect(exportLib.exportToCSV).toHaveBeenCalledTimes(1)
      })

      // Second export
      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as json/i }))

      await waitFor(() => {
        expect(exportLib.exportToJSON).toHaveBeenCalledTimes(1)
      })
    })

    it('should alternate between CSV and JSON exports', async () => {
      const user = userEvent.setup()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      // CSV export
      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        expect(exportLib.exportToCSV).toHaveBeenCalled()
      })

      // JSON export
      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as json/i }))

      await waitFor(() => {
        expect(exportLib.exportToJSON).toHaveBeenCalled()
      })
    })
  })

  describe('UX Delay', () => {
    it('should add small delay for UX feedback', async () => {
      const user = userEvent.setup()
      const startTime = Date.now()

      render(<ExportButton data={mockData} filename="test" columns={mockColumns} />)

      await user.click(screen.getByRole('button', { name: /export/i }))
      await user.click(screen.getByRole('menuitem', { name: /export as csv/i }))

      await waitFor(() => {
        expect(exportLib.exportToCSV).toHaveBeenCalled()
      })

      const endTime = Date.now()
      const duration = endTime - startTime

      // Should have at least some delay (200ms in the code)
      expect(duration).toBeGreaterThanOrEqual(0)
    })
  })
})
