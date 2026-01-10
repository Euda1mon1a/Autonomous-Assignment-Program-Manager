/**
 * AddPersonModal Component Tests
 *
 * Tests for the AddPersonModal component including form fields,
 * validation, and conditional rendering of PGY level field.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AddPersonModal } from '@/components/AddPersonModal'
import * as api from '@/lib/api'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  )
}

describe('AddPersonModal', () => {
  const mockOnClose = jest.fn()

  beforeEach(() => {
    mockOnClose.mockClear()
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render form fields when modal is open', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Check for form fields
      expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/performs procedures/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/specialties/i)).toBeInTheDocument()
    })

    it('should not render when modal is closed', () => {
      renderWithProviders(
        <AddPersonModal isOpen={false} onClose={mockOnClose} />
      )

      expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument()
    })

    it('should render submit and cancel buttons', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      expect(screen.getByRole('button', { name: /add person/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    })

    it('should render modal title', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      expect(screen.getByRole('heading', { name: /add person/i })).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should not submit form when name is empty', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Submit without filling name
      await user.click(screen.getByRole('button', { name: /add person/i }))

      // API should not be called when validation fails
      expect(mockedApi.post).not.toHaveBeenCalled()
    })

    it('should not submit form when name is too short', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Enter a single character name
      await user.type(screen.getByLabelText(/name/i), 'A')
      await user.click(screen.getByRole('button', { name: /add person/i }))

      // API should not be called when validation fails
      expect(mockedApi.post).not.toHaveBeenCalled()
    })

    it('should not submit form with invalid email format', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Enter valid name but invalid email
      await user.type(screen.getByLabelText(/name/i), 'Dr. Test')
      await user.type(screen.getByLabelText(/email/i), 'invalid-email')
      await user.click(screen.getByRole('button', { name: /add person/i }))

      // API should not be called when validation fails
      expect(mockedApi.post).not.toHaveBeenCalled()
    })

  })

  describe('Conditional PGY Level Field', () => {
    it('should show PGY level field when type is resident', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Default type is resident, so PGY level should be visible
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
    })

    it('should hide PGY level field when type is faculty', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Change type to faculty
      await user.selectOptions(screen.getByLabelText(/type/i), 'faculty')

      // PGY level field should be hidden
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()
    })

    it('should show PGY level field again when switching back to resident', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Change to faculty
      await user.selectOptions(screen.getByLabelText(/type/i), 'faculty')
      expect(screen.queryByLabelText(/pgy level/i)).not.toBeInTheDocument()

      // Change back to resident
      await user.selectOptions(screen.getByLabelText(/type/i), 'resident')
      expect(screen.getByLabelText(/pgy level/i)).toBeInTheDocument()
    })
  })

  describe('Form Submission', () => {
    it('should call onClose after successful submission', async () => {
      const user = userEvent.setup()

      // Mock successful API response
      mockedApi.post.mockResolvedValueOnce({
        id: 'person-new',
        name: 'Dr. New Resident',
        email: null,
        type: 'resident' as const,
        pgyLevel: 1,
        performsProcedures: false,
        specialties: null,
        primaryDuty: null,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      })

      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Fill in required fields
      await user.type(screen.getByLabelText(/name/i), 'Dr. New Resident')

      // Submit form
      await user.click(screen.getByRole('button', { name: /add person/i }))

      // Wait for mutation to complete and modal to close
      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled()
      })
    })

    it('should reset form when cancel is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      // Fill in some fields
      await user.type(screen.getByLabelText(/name/i), 'Dr. Test')
      await user.type(screen.getByLabelText(/email/i), 'test@example.com')

      // Click cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }))

      // onClose should be called
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('Type Selection', () => {
    it('should have resident and faculty options', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      const typeSelect = screen.getByLabelText(/type/i)
      expect(typeSelect).toBeInTheDocument()

      // Check options exist
      const options = typeSelect.querySelectorAll('option')
      const optionValues = Array.from(options).map(opt => opt.value)
      expect(optionValues).toContain('resident')
      expect(optionValues).toContain('faculty')
    })

    it('should default to resident type', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      const typeSelect = screen.getByLabelText(/type/i) as HTMLSelectElement
      expect(typeSelect.value).toBe('resident')
    })
  })

  describe('PGY Level Options', () => {
    it('should have options for PGY 1-8', () => {
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      const pgySelect = screen.getByLabelText(/pgy level/i)
      const options = pgySelect.querySelectorAll('option')

      // Should have 8 PGY levels
      expect(options.length).toBe(8)

      const optionLabels = Array.from(options).map(opt => opt.textContent)
      expect(optionLabels).toContain('PGY-1')
      expect(optionLabels).toContain('PGY-8')
    })
  })

  describe('Checkbox Interaction', () => {
    it('should toggle performs procedures checkbox', async () => {
      const user = userEvent.setup()
      renderWithProviders(
        <AddPersonModal isOpen={true} onClose={mockOnClose} />
      )

      const checkbox = screen.getByLabelText(/performs procedures/i) as HTMLInputElement

      // Initially unchecked
      expect(checkbox.checked).toBe(false)

      // Click to check
      await user.click(checkbox)
      expect(checkbox.checked).toBe(true)

      // Click to uncheck
      await user.click(checkbox)
      expect(checkbox.checked).toBe(false)
    })
  })
})
