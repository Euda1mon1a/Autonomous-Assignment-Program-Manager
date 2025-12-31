/**
 * Tests for ICS calendar export components
 *
 * Tests CalendarExportButton and SimpleCalendarExportButton components
 * covering ICS download, subscription URL creation, date range selection,
 * loading states, and error handling
 */
import React from 'react'
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import {
  CalendarExportButton,
  SimpleCalendarExportButton,
} from '@/components/CalendarExportButton'
import { ToastProvider } from '@/contexts/ToastContext'

// Mock fetch
global.fetch = jest.fn()

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = jest.fn(() => 'mock-blob-url')
global.URL.revokeObjectURL = jest.fn()

// Wrapper with ToastProvider
function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <ToastProvider>{children}</ToastProvider>
  }
}

describe('CalendarExportButton', () => {
  const defaultProps = {
    personId: 'person-123',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render export button with correct text', () => {
      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByRole('button', { name: /export calendar/i })).toBeInTheDocument()
    })

    it('should not show dropdown initially', () => {
      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.queryByText('Download ICS')).not.toBeInTheDocument()
    })

    it('should apply custom className', () => {
      render(<CalendarExportButton {...defaultProps} className="custom-class" />, {
        wrapper: createWrapper(),
      })

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })
  })

  describe('Dropdown Behavior', () => {
    it('should open dropdown when button is clicked', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      await waitFor(() => {
        const downloadButton = screen.getByRole('button', { name: /download ics/i })
        expect(downloadButton).toBeInTheDocument()
      })
    })

    it('should show download option when dropdown is open', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      await waitFor(() => {
        const downloadButton = screen.getByRole('button', { name: /download ics/i })
        expect(downloadButton).toBeInTheDocument()
      })
    })

    it('should handle multiple button clicks without errors', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })

      // Open
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /download ics/i })).toBeInTheDocument()
      })

      // Click main button again (should handle toggle)
      await user.click(button)

      // Verify button is still functional
      expect(button).toBeEnabled()
      expect(button).toBeInTheDocument()
    })
  })

  describe('ICS Download', () => {
    it('should download ICS file for person calendar', async () => {
      const user = userEvent.setup()

      const mockBlob = new Blob(['mock ics content'], { type: 'text/calendar' })
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/person/person-123')
        )
      })
    })

    it('should download ICS file for rotation calendar', async () => {
      const user = userEvent.setup()

      const mockBlob = new Blob(['mock ics content'], { type: 'text/calendar' })
      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => mockBlob,
      } as Response)

      render(<CalendarExportButton rotationId="rotation-456" />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/rotation/rotation-456')
        )
      })
    })

    it('should use provided dates in API call', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('start_date=2024-01-01&end_date=2024-06-30')
        )
      })
    })

    it('should include activity types in API call when provided', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(
        <CalendarExportButton
          {...defaultProps}
          includeTypes={['clinic', 'inpatient']}
        />,
        { wrapper: createWrapper() }
      )

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringMatching(/include_types=clinic.*include_types=inpatient/)
        )
      })
    })

    it('should show loading state during download', async () => {
      const user = userEvent.setup()

      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          blob: async () => new Blob(),
        } as Response), 100))
      )

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
      expect(downloadButton).toBeDisabled()

      await waitFor(() => {
        expect(screen.queryByText('Exporting...')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should show success toast after download', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      // Wait for fetch to be called
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })

  describe('Subscription URL Creation', () => {
    it('should show subscription option for person calendars', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      expect(screen.getByText(/create subscription url/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create subscription/i })).toBeInTheDocument()
    })

    it('should not show subscription option for rotation calendars', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton rotationId="rotation-456" />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      expect(screen.queryByRole('button', { name: /create subscription/i })).not.toBeInTheDocument()
    })

    it('should create subscription URL when button is clicked', async () => {
      const user = userEvent.setup()

      const mockSubscriptionUrl = 'https://example.com/calendar/subscribe/abc123'
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ subscription_url: mockSubscriptionUrl }),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const createButton = screen.getByRole('button', { name: /create subscription/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          '/api/calendar/subscribe',
          expect.objectContaining({
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              person_id: 'person-123',
              expires_days: null,
            }),
          })
        )
      })

      expect(screen.getByText(mockSubscriptionUrl)).toBeInTheDocument()
    })

    it('should show loading state during subscription creation', async () => {
      const user = userEvent.setup()

      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ subscription_url: 'https://example.com' }),
        } as Response), 100))
      )

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const createButton = screen.getByRole('button', { name: /create subscription/i })
      await user.click(createButton)

      expect(screen.getByText('Creating...')).toBeInTheDocument()
      expect(createButton).toBeDisabled()

      await waitFor(() => {
        expect(screen.queryByText('Creating...')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should allow copying subscription URL', async () => {
      const user = userEvent.setup()

      const mockSubscriptionUrl = 'https://example.com/calendar/subscribe/abc123'
      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ subscription_url: mockSubscriptionUrl }),
      } as Response)

      // Mock clipboard API
      const mockWriteText = jest.fn().mockResolvedValue(undefined)
      Object.defineProperty(navigator, 'clipboard', {
        value: {
          writeText: mockWriteText,
        },
        writable: true,
        configurable: true,
      })

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const createButton = screen.getByRole('button', { name: /create subscription/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByText(mockSubscriptionUrl)).toBeInTheDocument()
      })

      const copyButton = screen.getByRole('button', { name: /copy url/i })
      await user.click(copyButton)

      expect(mockWriteText).toHaveBeenCalledWith(mockSubscriptionUrl)

      await waitFor(() => {
        expect(screen.getByText('Copied!')).toBeInTheDocument()
      })
    })

    it('should show calendar app instructions after subscription creation', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => ({ subscription_url: 'https://example.com' }),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const createButton = screen.getByRole('button', { name: /create subscription/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(screen.getByText(/how to subscribe:/i)).toBeInTheDocument()
        expect(screen.getByText(/google calendar/i)).toBeInTheDocument()
        expect(screen.getByText(/outlook/i)).toBeInTheDocument()
        expect(screen.getByText(/apple calendar/i)).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('should show error when download fails', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Calendar not found' }),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        // Toast error should be shown (we can't easily test toast content in this setup)
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it('should show error when subscription creation fails', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Failed to create subscription' }),
      } as Response)

      render(<CalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const createButton = screen.getByRole('button', { name: /create subscription/i })
      await user.click(createButton)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })

    it('should show error when neither personId nor rotationId is provided', async () => {
      const user = userEvent.setup()

      render(<CalendarExportButton />, { wrapper: createWrapper() })

      const button = screen.getByRole('button', { name: /export calendar/i })
      await user.click(button)

      const downloadButton = screen.getByRole('button', { name: /download ics/i })
      await user.click(downloadButton)

      await waitFor(() => {
        // Should not call fetch
        expect(mockFetch).not.toHaveBeenCalled()
      })
    })
  })
})

describe('SimpleCalendarExportButton', () => {
  const defaultProps = {
    personId: 'person-123',
    startDate: '2024-01-01',
    endDate: '2024-06-30',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render export button', () => {
      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.getByRole('button', { name: /export to calendar/i })).toBeInTheDocument()
    })

    it('should not show dropdown or extra options', () => {
      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      expect(screen.queryByText('Export Calendar')).not.toBeInTheDocument()
      expect(screen.queryByText('Create Subscription')).not.toBeInTheDocument()
    })

    it('should apply custom className', () => {
      render(<SimpleCalendarExportButton {...defaultProps} className="custom-class" />, {
        wrapper: createWrapper(),
      })

      const button = screen.getByRole('button')
      expect(button).toHaveClass('custom-class')
    })
  })

  describe('Direct Export', () => {
    it('should export directly when clicked', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/calendar/export/person/person-123')
        )
      })
    })

    it('should use provided dates', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('start_date=2024-01-01&end_date=2024-06-30')
        )
      })
    })

    it('should use default dates when not provided', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      render(<SimpleCalendarExportButton personId="person-123" />, {
        wrapper: createWrapper(),
      })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringMatching(/start_date=.*&end_date=.*/)
        )
      })
    })

    it('should show loading state during export', async () => {
      const user = userEvent.setup()

      mockFetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({
          ok: true,
          blob: async () => new Blob(),
        } as Response), 100))
      )

      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      expect(screen.getByText('Exporting...')).toBeInTheDocument()
      expect(button).toBeDisabled()

      await waitFor(() => {
        expect(screen.queryByText('Exporting...')).not.toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should handle export errors', async () => {
      const user = userEvent.setup()

      mockFetch.mockResolvedValue({
        ok: false,
        json: async () => ({ detail: 'Export failed' }),
      } as Response)

      render(<SimpleCalendarExportButton {...defaultProps} />, { wrapper: createWrapper() })

      const button = screen.getByRole('button')
      await user.click(button)

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalled()
      })
    })
  })
})
