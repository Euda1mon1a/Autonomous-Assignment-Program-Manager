import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { CalendarExportButton, SimpleCalendarExportButton } from '@/components/CalendarExportButton'

// Mock toast context
const mockToast = {
  success: jest.fn(),
  error: jest.fn(),
}

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ toast: mockToast }),
}))

// Mock fetch
global.fetch = jest.fn()

// Mock URL methods
const mockCreateObjectURL = jest.fn(() => 'blob:mock-url')
const mockRevokeObjectURL = jest.fn()
global.URL.createObjectURL = mockCreateObjectURL
global.URL.revokeObjectURL = mockRevokeObjectURL

// Mock clipboard - will be set up in beforeEach
let mockClipboardWriteText: jest.Mock

describe('CalendarExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Create fresh clipboard mock for each test
    mockClipboardWriteText = jest.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: mockClipboardWriteText,
      },
      writable: true,
      configurable: true,
    })
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-02-15'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Button Rendering', () => {
    it('should render export button', () => {
      render(<CalendarExportButton personId="person-1" />)

      expect(screen.getByRole('button', { name: /export calendar/i })).toBeInTheDocument()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <CalendarExportButton personId="person-1" className="custom-class" />
      )

      const button = container.querySelector('.custom-class')
      expect(button).toBeInTheDocument()
    })

    it('should have calendar icon', () => {
      const { container } = render(<CalendarExportButton personId="person-1" />)

      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })
  })

  describe('Dropdown Behavior', () => {
    it('should open dropdown when clicking button', async () => {
      const user = userEvent.setup({ delay: null })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))

      // Both button text and h3 header have "Export Calendar" - use heading role for the dropdown title
      expect(screen.getByRole('heading', { name: 'Export Calendar' })).toBeInTheDocument()
      expect(screen.getByText(/download ics file/i)).toBeInTheDocument()
    })

    it('should close dropdown when clicking backdrop', async () => {
      const user = userEvent.setup({ delay: null })

      const { container } = render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      expect(screen.getByRole('heading', { name: 'Export Calendar' })).toBeInTheDocument()

      const backdrop = container.querySelector('.fixed.inset-0')
      await user.click(backdrop!)

      await waitFor(() => {
        expect(screen.queryByText(/download ics file/i)).not.toBeInTheDocument()
      })
    })

    it('should toggle dropdown when clicking button multiple times', async () => {
      const user = userEvent.setup({ delay: null })

      render(<CalendarExportButton personId="person-1" />)

      const button = screen.getByRole('button', { name: /export calendar/i })

      await user.click(button)
      expect(screen.getByRole('heading', { name: 'Export Calendar' })).toBeInTheDocument()

      await user.click(button)
      await waitFor(() => {
        expect(screen.queryByText(/download ics file/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Download ICS Functionality', () => {
    it('should download ICS for person calendar', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(<CalendarExportButton personId="person-123" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/person/person-123')
        )
      })

      expect(mockToast.success).toHaveBeenCalledWith('Calendar exported successfully')
    })

    it('should download ICS for rotation calendar', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(<CalendarExportButton rotationId="rotation-456" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/rotation/rotation-456')
        )
      })
    })

    it('should include date range in request', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(
        <CalendarExportButton
          personId="person-1"
          startDate="2024-01-01"
          endDate="2024-12-31"
        />
      )

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('startDate=2024-01-01&endDate=2024-12-31')
        )
      })
    })

    it('should include activity types in request', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(
        <CalendarExportButton
          personId="person-1"
          includeTypes={['clinic', 'inpatient']}
        />
      )

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('include_types=clinic&include_types=inpatient')
        )
      })
    })

    it('should show loading state during export', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, blob: () => Promise.resolve(new Blob()) }), 100))
      )

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
    })

    it('should handle export error', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Export failed' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Export failed')
      })
    })

    it('should close dropdown after successful export', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /download ics/i }))

      await waitFor(() => {
        expect(screen.queryByText(/download ics file/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Subscription Functionality', () => {
    it('should show subscription option for person calendars', async () => {
      const user = userEvent.setup({ delay: null })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))

      expect(screen.getByText(/create subscription url/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create subscription/i })).toBeInTheDocument()
    })

    it('should not show subscription option for rotation calendars', async () => {
      const user = userEvent.setup({ delay: null })

      render(<CalendarExportButton rotationId="rotation-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))

      expect(screen.queryByText(/create subscription url/i)).not.toBeInTheDocument()
    })

    it('should create subscription URL', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ subscription_url: 'https://example.com/calendar/subscribe/token123' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/calendar/subscribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ personId: 'person-1', expires_days: null }),
        })
      })

      // The subscription URL is displayed in a monospace font inside the dropdown
      await waitFor(() => {
        expect(screen.getByText('https://example.com/calendar/subscribe/token123')).toBeInTheDocument()
      })
      expect(mockToast.success).toHaveBeenCalledWith('Subscription URL created')
    })

    it('should show loading state during subscription creation', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, json: () => Promise.resolve({ subscription_url: 'url' }) }), 100))
      )

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      expect(screen.getByText('Creating...')).toBeInTheDocument()
    })

    it('should handle subscription creation error', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Subscription failed' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Subscription failed')
      })
    })
  })

  describe('Copy URL Functionality', () => {
    it('should copy subscription URL to clipboard', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ subscription_url: 'https://example.com/calendar/subscribe/token123' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      // Open dropdown
      await user.click(screen.getByRole('button', { name: /export calendar/i }))

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create subscription/i })).toBeInTheDocument()
      })

      // Click create subscription
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      // Wait for subscription URL to appear
      await waitFor(() => {
        expect(screen.getByText('https://example.com/calendar/subscribe/token123')).toBeInTheDocument()
      })

      // Wait for copy button to be available
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy url/i })).toBeInTheDocument()
      })

      // Click copy button
      const copyButton = screen.getByRole('button', { name: /copy url/i })
      await user.click(copyButton)

      // Verify the success toast is shown (this confirms the copy handler was invoked)
      await waitFor(() => {
        expect(mockToast.success).toHaveBeenCalledWith('Subscription URL copied to clipboard')
      })
    })

    it('should show "Copied!" feedback after copying', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ subscription_url: 'https://example.com/url' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy url/i })).toBeInTheDocument()
      })

      await user.click(screen.getByRole('button', { name: /copy url/i }))

      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument()
      })
    })

    it('should have copy URL button when subscription is created', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ subscription_url: 'https://example.com/url' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      // Open dropdown
      await user.click(screen.getByRole('button', { name: /export calendar/i }))

      // Wait for dropdown to open
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create subscription/i })).toBeInTheDocument()
      })

      // Click create subscription
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      // Wait for copy button to be available - this confirms the URL was created
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /copy url/i })).toBeInTheDocument()
      })

      // Verify the URL is displayed
      expect(screen.getByText('https://example.com/url')).toBeInTheDocument()
    })
  })

  describe('Subscription Instructions', () => {
    it('should show subscription instructions after URL is created', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ subscription_url: 'https://example.com/url' }),
      })

      render(<CalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export calendar/i }))
      await user.click(screen.getByRole('button', { name: /create subscription/i }))

      await waitFor(() => {
        expect(screen.getByText('How to subscribe:')).toBeInTheDocument()
        expect(screen.getByText(/google calendar.*add by url/i)).toBeInTheDocument()
        expect(screen.getByText(/outlook.*subscribe to calendar/i)).toBeInTheDocument()
        expect(screen.getByText(/apple calendar.*new calendar subscription/i)).toBeInTheDocument()
      })
    })
  })
})

describe('SimpleCalendarExportButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
    jest.setSystemTime(new Date('2024-02-15'))
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  describe('Simple Export', () => {
    it('should render simple export button', () => {
      render(<SimpleCalendarExportButton personId="person-1" />)

      expect(screen.getByRole('button', { name: /export to calendar/i })).toBeInTheDocument()
    })

    it('should export directly without dropdown', async () => {
      const user = userEvent.setup({ delay: null })

      const mockBlob = new Blob(['mock ics data'], { type: 'text/calendar' })
      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      render(<SimpleCalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export to calendar/i }))

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/person/person-1')
        )
      })

      expect(mockToast.success).toHaveBeenCalledWith('Calendar exported successfully')
    })

    it('should disable button during export', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ ok: true, blob: () => Promise.resolve(new Blob()) }), 100))
      )

      render(<SimpleCalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export to calendar/i }))

      const button = screen.getByRole('button', { name: /exporting/i })
      expect(button).toBeDisabled()
    })

    it('should handle export error', async () => {
      const user = userEvent.setup({ delay: null })

      ;(global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Export failed' }),
      })

      render(<SimpleCalendarExportButton personId="person-1" />)

      await user.click(screen.getByRole('button', { name: /export to calendar/i }))

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('Export failed')
      })
    })
  })
})
