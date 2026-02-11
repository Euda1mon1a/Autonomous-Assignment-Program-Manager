import { render, screen, fireEvent } from '@/test-utils'
import { renderHook, act } from '@/test-utils'
import { ViewToggle, useScheduleView } from '@/components/schedule/ViewToggle'
import { useRouter, useSearchParams } from 'next/navigation'

// Mock Next.js navigation hooks
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

describe('ViewToggle', () => {
  const mockRouter = {
    push: jest.fn(),
  }

  const mockSearchParams = {
    get: jest.fn(),
    toString: jest.fn(() => ''),
  }

  // Mock localStorage
  const localStorageMock = (() => {
    let store: Record<string, string> = {}
    return {
      getItem: (key: string) => store[key] || null,
      setItem: (key: string, value: string) => { store[key] = value },
      removeItem: (key: string) => { delete store[key] },
      clear: () => { store = {} },
    }
  })()

  beforeEach(() => {
    jest.clearAllMocks()
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    })
    localStorageMock.clear()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)
  })

  describe('View Options Rendering', () => {
    it('should render all standard view options', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      // Component uses aria-label, not title
      expect(screen.getByLabelText('Switch to Day view')).toBeInTheDocument()
      expect(screen.getByLabelText('Switch to Week view')).toBeInTheDocument()
      expect(screen.getByLabelText('Switch to Month view')).toBeInTheDocument()
      expect(screen.getByLabelText('Switch to Block view')).toBeInTheDocument()
    })

    it('should render annual view options (block-annual and block-week)', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      expect(screen.getByLabelText('Switch to Academic Year view')).toBeInTheDocument()
      expect(screen.getByLabelText('Switch to Block Week view')).toBeInTheDocument()
    })

    it('should display icons for all views', () => {
      const onChange = jest.fn()
      const { container } = render(<ViewToggle currentView="block" onChange={onChange} />)

      // Check for SVG icons (lucide-react icons)
      const icons = container.querySelectorAll('svg')
      expect(icons.length).toBeGreaterThan(0)
    })

    it('should show separator between standard and annual views', () => {
      const onChange = jest.fn()
      const { container } = render(<ViewToggle currentView="block" onChange={onChange} />)

      const separators = container.querySelectorAll('.bg-gray-300')
      expect(separators.length).toBeGreaterThan(0)
    })
  })

  describe('Active View Highlighting', () => {
    it('should highlight the current view', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const blockButton = screen.getByLabelText('Switch to Block view')
      expect(blockButton).toHaveClass('bg-white')
      expect(blockButton).toHaveClass('text-blue-600')
    })

    it('should not highlight inactive views', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      expect(dayButton).not.toHaveClass('bg-white')
      expect(dayButton).toHaveClass('text-gray-600')
    })

    it('should update highlighting when view changes', () => {
      const onChange = jest.fn()
      const { rerender } = render(<ViewToggle currentView="block" onChange={onChange} />)

      rerender(<ViewToggle currentView="day" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      expect(dayButton).toHaveClass('bg-white')
      expect(dayButton).toHaveClass('text-blue-600')
    })

    it('should set aria-pressed to true for active view', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="month" onChange={onChange} />)

      const monthButton = screen.getByLabelText('Switch to Month view')
      expect(monthButton).toHaveAttribute('aria-pressed', 'true')
    })

    it('should set aria-pressed to false for inactive views', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="month" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      expect(dayButton).toHaveAttribute('aria-pressed', 'false')
    })
  })

  describe('View Change Interactions', () => {
    it('should call onChange when view button is clicked', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const weekButton = screen.getByLabelText('Switch to Week view')
      fireEvent.click(weekButton)

      expect(onChange).toHaveBeenCalledWith('week')
    })

    it('should update localStorage when view changes', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const monthButton = screen.getByLabelText('Switch to Month view')
      fireEvent.click(monthButton)

      expect(localStorage.getItem('schedule-view-preference')).toBe('month')
    })

    it('should update URL parameter when view changes', () => {
      const onChange = jest.fn()
      mockSearchParams.toString.mockReturnValue('foo=bar')

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const weekButton = screen.getByLabelText('Switch to Week view')
      fireEvent.click(weekButton)

      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('view=week'),
        { scroll: false }
      )
    })

    it('should call onChange for block-annual view', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const ayButton = screen.getByLabelText('Switch to Academic Year view')
      fireEvent.click(ayButton)

      expect(onChange).toHaveBeenCalledWith('block-annual')
    })
  })

  describe('Initialization from URL', () => {
    it('should initialize from URL param if present', () => {
      mockSearchParams.get.mockReturnValue('month')
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      // Wait for useEffect to run
      expect(onChange).toHaveBeenCalledWith('month')
    })

    it('should not change view if URL param is invalid', () => {
      mockSearchParams.get.mockReturnValue('invalid-view')
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      expect(onChange).not.toHaveBeenCalled()
    })

    it('should prefer URL param over localStorage', () => {
      localStorage.setItem('schedule-view-preference', 'day')
      mockSearchParams.get.mockReturnValue('month')
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      expect(onChange).toHaveBeenCalledWith('month')
    })

    it('should fall back to localStorage if no URL param', () => {
      localStorage.setItem('schedule-view-preference', 'week')
      mockSearchParams.get.mockReturnValue(null)
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      expect(onChange).toHaveBeenCalledWith('week')
    })
  })

  describe('Responsive Behavior', () => {
    it('should hide labels on small screens for standard views', () => {
      const onChange = jest.fn()
      render(<ViewToggle currentView="block" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      const label = dayButton.querySelector('.hidden.sm\\:inline')
      expect(label).toBeInTheDocument()
    })

    it('should hide labels on small screens for block views', () => {
      const onChange = jest.fn()
      render(<ViewToggle currentView="block" onChange={onChange} />)

      const blockButton = screen.getByLabelText('Switch to Block view')
      const label = blockButton.querySelector('.hidden.sm\\:inline')
      expect(label).toBeInTheDocument()
    })
  })

  describe('Button Styling', () => {
    it('should apply rounded styling to button groups', () => {
      const onChange = jest.fn()
      const { container } = render(<ViewToggle currentView="block" onChange={onChange} />)

      const buttonGroups = container.querySelectorAll('.rounded-lg')
      expect(buttonGroups.length).toBeGreaterThanOrEqual(2)
    })

    it('should apply hover effects to inactive buttons', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      expect(dayButton.className).toContain('hover:')
    })

    it('should apply shadow to active button', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const blockButton = screen.getByLabelText('Switch to Block view')
      expect(blockButton).toHaveClass('shadow-sm')
    })
  })

  describe('useScheduleView Hook', () => {
    beforeEach(() => {
      // Mock window.location for the hook
      delete (window as any).location
      window.location = { search: '' } as any
      localStorageMock.clear()
    })

    it('should initialize with default view', () => {
      const { result } = renderHook(() => useScheduleView('month'))

      expect(result.current[0]).toBe('month')
    })

    it('should update view when setter is called', () => {
      const { result } = renderHook(() => useScheduleView('block'))

      act(() => {
        result.current[1]('week')
      })

      expect(result.current[0]).toBe('week')
    })

    it('should load view from localStorage on mount', () => {
      localStorage.setItem('schedule-view-preference', 'day')

      const { result } = renderHook(() => useScheduleView('block'))

      // Wait for effect to run
      expect(result.current[0]).toBe('day')
    })

    it('should prefer URL param over localStorage in hook', () => {
      localStorage.setItem('schedule-view-preference', 'day')
      window.location.search = '?view=month'

      const { result } = renderHook(() => useScheduleView('block'))

      expect(result.current[0]).toBe('month')
    })

    it('should ignore invalid views in localStorage', () => {
      localStorage.setItem('schedule-view-preference', 'invalid-view')

      const { result } = renderHook(() => useScheduleView('block'))

      expect(result.current[0]).toBe('block')
    })

    it('should use default when no stored preference', () => {
      const { result } = renderHook(() => useScheduleView('block'))

      expect(result.current[0]).toBe('block')
    })
  })

  describe('View Validation', () => {
    it('should accept all visible view values', () => {
      const onChange = jest.fn()

      // Only visible views are rendered as buttons
      const visibleViews = [
        { value: 'block-annual', label: 'Academic Year' },
        { value: 'block', label: 'Block' },
        { value: 'block-week', label: 'Block Week' },
        { value: 'month', label: 'Month' },
        { value: 'week', label: 'Week' },
        { value: 'day', label: 'Day' },
      ]

      render(<ViewToggle currentView="block" onChange={onChange} />)

      visibleViews.forEach(({ value, label }) => {
        const button = screen.getByLabelText(`Switch to ${label} view`)
        fireEvent.click(button)
        expect(onChange).toHaveBeenCalledWith(value)
        onChange.mockClear()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have button role for all view options', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(6)
    })

    it('should have descriptive aria-labels for all buttons', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      const dayButton = screen.getByLabelText('Switch to Day view')
      const weekButton = screen.getByLabelText('Switch to Week view')
      const monthButton = screen.getByLabelText('Switch to Month view')
      const blockButton = screen.getByLabelText('Switch to Block view')

      expect(dayButton).toBeInTheDocument()
      expect(weekButton).toBeInTheDocument()
      expect(monthButton).toBeInTheDocument()
      expect(blockButton).toBeInTheDocument()
    })
  })

  describe('Label Display', () => {
    it('should show short labels for views', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      // These should be present but may be hidden on small screens
      expect(screen.getByText('Day')).toBeInTheDocument()
      expect(screen.getByText('Month')).toBeInTheDocument()
    })

    it('should show abbreviated labels for block views', () => {
      const onChange = jest.fn()

      render(<ViewToggle currentView="block" onChange={onChange} />)

      expect(screen.getByText('AY')).toBeInTheDocument()
    })
  })
})
