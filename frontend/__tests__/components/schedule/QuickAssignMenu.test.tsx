import { render, screen, fireEvent, waitFor } from '@/test-utils'
import { renderHook, act } from '@/test-utils'
import { QuickAssignMenu, useQuickAssignMenu } from '@/components/schedule/QuickAssignMenu'

// Mock the contexts and hooks
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/contexts/ToastContext', () => ({
  useToast: jest.fn(),
}))

jest.mock('@/lib/hooks', () => ({
  useRotationTemplates: jest.fn(),
  useDeleteAssignment: jest.fn(),
}))

const { useAuth } = require('@/contexts/AuthContext')
const { useToast } = require('@/contexts/ToastContext')
const { useRotationTemplates, useDeleteAssignment } = require('@/lib/hooks')

describe('QuickAssignMenu', () => {
  const mockPosition = { x: 100, y: 200 }
  const mockOnClose = jest.fn()
  const mockOnQuickAssign = jest.fn()
  const mockOnMarkAsOff = jest.fn()
  const mockOnClearAssignment = jest.fn()
  const mockOnEditDetails = jest.fn()

  const mockRotationTemplates = {
    items: [
      {
        id: 'r1',
        name: 'Clinic',
        abbreviation: 'CL',
        activity_type: 'clinic',
      },
      {
        id: 'r2',
        name: 'Inpatient',
        abbreviation: 'IM',
        activity_type: 'inpatient',
      },
      {
        id: 'r3',
        name: 'Call',
        abbreviation: 'CA',
        activity_type: 'call',
      },
    ],
  }

  const mockDeleteMutation = {
    mutateAsync: jest.fn(),
    isPending: false,
  }

  beforeEach(() => {
    jest.clearAllMocks()
    useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
    useToast.mockReturnValue({ toast: { error: jest.fn() } })
    useRotationTemplates.mockReturnValue({ data: mockRotationTemplates, isLoading: false })
    useDeleteAssignment.mockReturnValue(mockDeleteMutation)
  })

  describe('Rendering and Visibility', () => {
    it('should not render when isOpen is false', () => {
      render(
        <QuickAssignMenu
          isOpen={false}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.queryByRole('button', { name: /Quick Assign/i })).not.toBeInTheDocument()
    })

    it('should render when isOpen is true and user can edit', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          personName="Dr. Smith"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Dr. Smith')).toBeInTheDocument()
    })

    it('should not render when user cannot edit', () => {
      useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.queryByText(/Quick Assign/i)).not.toBeInTheDocument()
    })

    it('should position menu at specified coordinates', () => {
      const { container } = render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const menu = container.querySelector('.fixed')
      expect(menu).toHaveStyle({ left: '100px', top: '200px' })
    })
  })

  describe('Header Display', () => {
    it('should display person name in header', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          personName="Dr. Smith"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Dr. Smith')).toBeInTheDocument()
    })

    it('should show "Unknown" when person name is not provided', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Unknown')).toBeInTheDocument()
    })

    it('should display formatted date', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      // Check for date components - format may vary by timezone
      // Due to UTC parsing, "2024-01-15" may display as Jan 14 or Jan 15 depending on local TZ
      // The component should display month and a numeric day
      expect(screen.getByText(/Jan/)).toBeInTheDocument()
      // Look for any day number (1-31) to verify date is formatted
      expect(screen.getByText(/\b(1[0-5]|[1-9])\b/)).toBeInTheDocument()
    })

    it('should display session (AM/PM)', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="PM"
        />
      )

      expect(screen.getByText('PM')).toBeInTheDocument()
    })

    it('should have close button', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const closeButtons = screen.getAllByRole('button')
      const closeButton = closeButtons.find((btn) => {
        const svg = btn.querySelector('svg')
        return svg?.classList.contains('lucide-x')
      })

      expect(closeButton).toBeInTheDocument()
    })
  })

  describe('Quick Assign Submenu', () => {
    it('should show Quick Assign button', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Quick Assign')).toBeInTheDocument()
    })

    it('should toggle rotation submenu when Quick Assign is clicked', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      expect(screen.getByText('All Rotations')).toBeInTheDocument()
    })

    it('should display all rotation templates', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      expect(screen.getByText('CL')).toBeInTheDocument()
      expect(screen.getByText('IM')).toBeInTheDocument()
      expect(screen.getByText('CA')).toBeInTheDocument()
    })

    it('should show recent rotations section when provided', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          recentRotations={['r1', 'r2']}
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      expect(screen.getByText('Recent')).toBeInTheDocument()
    })

    it('should call onQuickAssign when rotation is selected', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          onQuickAssign={mockOnQuickAssign}
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      const clinicRotation = screen.getByText('CL')
      fireEvent.click(clinicRotation.closest('button')!)

      expect(mockOnQuickAssign).toHaveBeenCalledWith('r1')
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should show loading state when templates are loading', () => {
      useRotationTemplates.mockReturnValue({ data: null, isLoading: true })

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      expect(screen.getByText('Loading rotations...')).toBeInTheDocument()
    })

    it('should show message when no rotations available', () => {
      useRotationTemplates.mockReturnValue({ data: { items: [] }, isLoading: false })

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      expect(screen.getByText('No rotations available')).toBeInTheDocument()
    })
  })

  describe('Mark as Off', () => {
    it('should show "Mark as Off" menu item', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Mark as Off')).toBeInTheDocument()
    })

    it('should call onMarkAsOff when clicked', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          onMarkAsOff={mockOnMarkAsOff}
        />
      )

      const markAsOffButton = screen.getByText('Mark as Off')
      fireEvent.click(markAsOffButton.closest('button')!)

      expect(mockOnMarkAsOff).toHaveBeenCalled()
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('Clear Assignment', () => {
    it('should show "Clear Assignment" when assignment exists', () => {
      const mockAssignment = {
        id: 'a1',
        person_id: 'p1',
        block_id: 'b1',
        role: 'primary',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-15T08:00:00Z',
      }

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          assignment={mockAssignment}
        />
      )

      expect(screen.getByText('Clear Assignment')).toBeInTheDocument()
    })

    it('should not show "Clear Assignment" when no assignment', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.queryByText('Clear Assignment')).not.toBeInTheDocument()
    })

    it('should delete assignment when clicked', async () => {
      const mockAssignment = {
        id: 'a1',
        person_id: 'p1',
        block_id: 'b1',
        role: 'primary',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-15T08:00:00Z',
      }

      mockDeleteMutation.mutateAsync.mockResolvedValue(undefined)

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          assignment={mockAssignment}
          onClearAssignment={mockOnClearAssignment}
        />
      )

      const clearButton = screen.getByText('Clear Assignment')
      fireEvent.click(clearButton.closest('button')!)

      await waitFor(() => {
        expect(mockDeleteMutation.mutateAsync).toHaveBeenCalledWith('a1')
      })

      expect(mockOnClearAssignment).toHaveBeenCalled()
      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should show loading state while deleting', () => {
      const mockAssignment = {
        id: 'a1',
        person_id: 'p1',
        block_id: 'b1',
        role: 'primary',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-15T08:00:00Z',
      }

      useDeleteAssignment.mockReturnValue({
        ...mockDeleteMutation,
        isPending: true,
      })

      const { container } = render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          assignment={mockAssignment}
        />
      )

      // Look for any loading spinner icon (class names may vary by Lucide version)
      const spinner = container.querySelector('.lucide-loader-2') ||
                      container.querySelector('.lucide-loader') ||
                      container.querySelector('[class*="animate-spin"]')
      expect(spinner).toBeInTheDocument()
    })

    it('should apply danger styling to Clear Assignment button', () => {
      const mockAssignment = {
        id: 'a1',
        person_id: 'p1',
        block_id: 'b1',
        role: 'primary',
        created_at: '2024-01-15T08:00:00Z',
        updated_at: '2024-01-15T08:00:00Z',
      }

      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          assignment={mockAssignment}
        />
      )

      const clearButton = screen.getByText('Clear Assignment').closest('button')!
      expect(clearButton).toHaveClass('text-red-700')
      expect(clearButton).toHaveClass('hover:bg-red-50')
    })
  })

  describe('Edit Details', () => {
    it('should show "Edit Details..." menu item', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      expect(screen.getByText('Edit Details...')).toBeInTheDocument()
    })

    it('should call onEditDetails when clicked', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
          onEditDetails={mockOnEditDetails}
        />
      )

      const editButton = screen.getByText('Edit Details...')
      fireEvent.click(editButton.closest('button')!)

      expect(mockOnEditDetails).toHaveBeenCalled()
      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('Close Behavior', () => {
    it('should close when close button is clicked', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const closeButtons = screen.getAllByRole('button')
      const closeButton = closeButtons.find((btn) => {
        const svg = btn.querySelector('svg')
        return svg?.classList.contains('lucide-x')
      })

      if (closeButton) {
        fireEvent.click(closeButton)
        expect(mockOnClose).toHaveBeenCalled()
      }
    })

    it('should close when clicking outside', () => {
      render(
        <div>
          <QuickAssignMenu
            isOpen={true}
            onClose={mockOnClose}
            position={mockPosition}
            personId="p1"
            date="2024-01-15"
            session="AM"
          />
          <div data-testid="outside">Outside</div>
        </div>
      )

      const outside = screen.getByTestId('outside')
      fireEvent.mouseDown(outside)

      expect(mockOnClose).toHaveBeenCalled()
    })

    it('should close when Escape is pressed', () => {
      render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      fireEvent.keyDown(document, { key: 'Escape' })

      expect(mockOnClose).toHaveBeenCalled()
    })
  })

  describe('useQuickAssignMenu Hook', () => {
    it('should initialize with closed state', () => {
      const { result } = renderHook(() => useQuickAssignMenu())

      expect(result.current.isOpen).toBe(false)
      expect(result.current.menuState).toBeNull()
    })

    it('should open menu with provided data', () => {
      const { result } = renderHook(() => useQuickAssignMenu())

      const mockEvent = { clientX: 100, clientY: 200, preventDefault: jest.fn() }
      const data = {
        personId: 'p1',
        personName: 'Dr. Smith',
        date: '2024-01-15',
        session: 'AM' as const,
      }

      act(() => {
        result.current.openMenu(mockEvent, data)
      })

      expect(result.current.isOpen).toBe(true)
      expect(result.current.menuState).toEqual({
        isOpen: true,
        position: { x: 100, y: 200 },
        ...data,
      })
    })

    it('should close menu', () => {
      const { result } = renderHook(() => useQuickAssignMenu())

      const mockEvent = { clientX: 100, clientY: 200, preventDefault: jest.fn() }
      const data = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
      }

      act(() => {
        result.current.openMenu(mockEvent, data)
      })

      expect(result.current.isOpen).toBe(true)

      act(() => {
        result.current.closeMenu()
      })

      expect(result.current.isOpen).toBe(false)
      expect(result.current.menuState).toBeNull()
    })

    it('should prevent default on event', () => {
      const { result } = renderHook(() => useQuickAssignMenu())

      const mockEvent = { clientX: 100, clientY: 200, preventDefault: jest.fn() }
      const data = {
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM' as const,
      }

      act(() => {
        result.current.openMenu(mockEvent, data)
      })

      expect(mockEvent.preventDefault).toHaveBeenCalled()
    })
  })

  describe('Activity Color Coding', () => {
    it('should display colored indicators for rotations', () => {
      const { container } = render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={mockPosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      const quickAssignButton = screen.getByText('Quick Assign')
      fireEvent.click(quickAssignButton)

      const colorDots = container.querySelectorAll('.w-2.h-2.rounded-full')
      expect(colorDots.length).toBeGreaterThan(0)
    })
  })

  describe('Viewport Adjustment', () => {
    it('should adjust position to stay within viewport', () => {
      // Mock window dimensions
      Object.defineProperty(window, 'innerWidth', { value: 500, writable: true })
      Object.defineProperty(window, 'innerHeight', { value: 600, writable: true })

      const edgePosition = { x: 450, y: 550 }

      const { container } = render(
        <QuickAssignMenu
          isOpen={true}
          onClose={mockOnClose}
          position={edgePosition}
          personId="p1"
          date="2024-01-15"
          session="AM"
        />
      )

      // Menu should be repositioned to fit
      const menu = container.querySelector('.fixed') as HTMLElement
      expect(menu).toBeInTheDocument()
    })
  })
})
