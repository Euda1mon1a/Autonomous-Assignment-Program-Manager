import { render, screen } from '@testing-library/react'
import { ComplianceAlert } from '@/components/dashboard/ComplianceAlert'
import { useValidateSchedule } from '@/lib/hooks'
import { createWrapper } from '../utils/test-utils'

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  useValidateSchedule: jest.fn(),
}))

describe('ComplianceAlert', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading skeleton when data is loading', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check for loading indicators (animated pulse divs)
      const loadingElements = document.querySelectorAll('.animate-pulse')
      expect(loadingElements.length).toBeGreaterThan(0)
    })

    it('should render title even when loading', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: true,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('Compliance Status')).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message when API call fails', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        isError: true,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText(/unable to load compliance data/i)).toBeInTheDocument()
    })

    it('should show warning icon in error state', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        isError: true,
      })

      const { container } = render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check for AlertTriangle icon (lucide-react icon)
      const iconElement = container.querySelector('.text-gray-400')
      expect(iconElement).toBeInTheDocument()
    })
  })

  describe('No Data State', () => {
    it('should show empty state when no validation data exists', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText(/no compliance data/i)).toBeInTheDocument()
      expect(screen.getByText(/generate a schedule to view compliance status/i)).toBeInTheDocument()
    })

    it('should show empty state when validation data is incomplete', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: { valid: undefined },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText(/no compliance data/i)).toBeInTheDocument()
    })
  })

  describe('Clean/Compliant State', () => {
    it('should display "All Clear" when no violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: true,
          total_violations: 0,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('All Clear')).toBeInTheDocument()
      expect(screen.getByText(/no acgme violations/i)).toBeInTheDocument()
    })

    it('should show green shield check icon when compliant', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: true,
          total_violations: 0,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      const { container } = render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check for ShieldCheck icon with green color
      const greenIcons = container.querySelectorAll('.text-green-600')
      expect(greenIcons.length).toBeGreaterThan(0)
    })

    it('should display current month in compliant message', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: true,
          total_violations: 0,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check that it shows the month (format is like "December 2024")
      const monthText = screen.getByText(/no acgme violations for/i)
      expect(monthText).toBeInTheDocument()
    })
  })

  describe('Violations State', () => {
    it('should display violation count when violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 5,
          violations: [
            { message: 'Violation 1', severity: 'critical' },
            { message: 'Violation 2', severity: 'warning' },
            { message: 'Violation 3', severity: 'warning' },
          ],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText(/violations found/i)).toBeInTheDocument()
    })

    it('should display singular "Violation" when count is 1', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 1,
          violations: [{ message: 'Single violation', severity: 'critical' }],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('1')).toBeInTheDocument()
      expect(screen.getByText('Violation Found')).toBeInTheDocument()
    })

    it('should show red shield alert icon when violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 3,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      const { container } = render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check for ShieldAlert icon with red color
      const redIcons = container.querySelectorAll('.text-red-600')
      expect(redIcons.length).toBeGreaterThan(0)
    })

    it('should display top 2 violations', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 5,
          violations: [
            { message: 'First violation message', severity: 'critical' },
            { message: 'Second violation message', severity: 'warning' },
            { message: 'Third violation message', severity: 'warning' },
            { message: 'Fourth violation message', severity: 'info' },
            { message: 'Fifth violation message', severity: 'info' },
          ],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('First violation message')).toBeInTheDocument()
      expect(screen.getByText('Second violation message')).toBeInTheDocument()
      expect(screen.queryByText('Third violation message')).not.toBeInTheDocument()
    })

    it('should show "+N more" text when more than 2 violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 5,
          violations: [
            { message: 'Violation 1', severity: 'critical' },
            { message: 'Violation 2', severity: 'warning' },
            { message: 'Violation 3', severity: 'warning' },
            { message: 'Violation 4', severity: 'info' },
            { message: 'Violation 5', severity: 'info' },
          ],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('+3 more')).toBeInTheDocument()
    })

    it('should not show "+N more" text when exactly 2 violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 2,
          violations: [
            { message: 'Violation 1', severity: 'critical' },
            { message: 'Violation 2', severity: 'warning' },
          ],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.queryByText(/\+\d+ more/)).not.toBeInTheDocument()
    })

    it('should show warning icons for violations', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 2,
          violations: [
            { message: 'Violation 1', severity: 'critical' },
            { message: 'Violation 2', severity: 'warning' },
          ],
        },
        isLoading: false,
        isError: false,
      })

      const { container } = render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check for AlertTriangle icons (amber colored)
      const warningIcons = container.querySelectorAll('.text-amber-500')
      expect(warningIcons.length).toBeGreaterThan(0)
    })
  })

  describe('Link to Compliance Details', () => {
    it('should always render link to compliance page', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: true,
          total_violations: 0,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      const link = screen.getByRole('link', { name: /view compliance details/i })
      expect(link).toBeInTheDocument()
      expect(link).toHaveAttribute('href', '/compliance')
    })

    it('should render link even when violations exist', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: false,
          total_violations: 3,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      const link = screen.getByRole('link', { name: /view compliance details/i })
      expect(link).toBeInTheDocument()
    })
  })

  describe('Component Structure', () => {
    it('should render with proper container styling', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: {
          valid: true,
          total_violations: 0,
          violations: [],
        },
        isLoading: false,
        isError: false,
      })

      const { container } = render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Check that the main container has styling classes
      const mainDiv = container.firstChild as HTMLElement
      expect(mainDiv).toHaveClass('glass-panel')
      expect(mainDiv).toHaveClass('p-6')
    })

    it('should always show title', () => {
      ;(useValidateSchedule as jest.Mock).mockReturnValue({
        data: null,
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      expect(screen.getByText('Compliance Status')).toBeInTheDocument()
    })
  })

  describe('Date Handling', () => {
    it('should call useValidateSchedule with current month date range', () => {
      const mockUseValidateSchedule = useValidateSchedule as jest.Mock
      mockUseValidateSchedule.mockReturnValue({
        data: { valid: true, total_violations: 0, violations: [] },
        isLoading: false,
        isError: false,
      })

      render(<ComplianceAlert />, { wrapper: createWrapper() })

      // Verify the hook was called
      expect(mockUseValidateSchedule).toHaveBeenCalled()

      // Get the arguments passed to the hook
      const args = mockUseValidateSchedule.mock.calls[0]

      // Should be called with start and end date strings
      expect(args).toHaveLength(2)
      expect(typeof args[0]).toBe('string')
      expect(typeof args[1]).toBe('string')

      // Dates should be in YYYY-MM-DD format
      expect(args[0]).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(args[1]).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    })
  })
})
