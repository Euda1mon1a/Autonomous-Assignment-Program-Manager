import { renderHook, act, waitFor } from '@/test-utils'
import { render, screen, fireEvent } from '@/test-utils'
import {
  useCellActions,
  useLongPress,
  ScheduleCellWrapper,
  getRecentRotations,
  addRecentRotation,
  clearRecentRotations,
} from '@/components/schedule/CellActions'
import { AssignmentRole } from '@/types/api'

// Mock the context and hooks
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/lib/hooks', () => ({
  useCreateAssignment: jest.fn(),
  useUpdateAssignment: jest.fn(),
  useDeleteAssignment: jest.fn(),
}))

const { useAuth } = require('@/contexts/AuthContext')
const { useCreateAssignment, useUpdateAssignment, useDeleteAssignment } = require('@/lib/hooks')

describe('CellActions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('useCellActions Hook', () => {
    const mockCreateMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    const mockUpdateMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    const mockDeleteMutation = {
      mutateAsync: jest.fn(),
      isPending: false,
    }

    beforeEach(() => {
      useCreateAssignment.mockReturnValue(mockCreateMutation)
      useUpdateAssignment.mockReturnValue(mockUpdateMutation)
      useDeleteAssignment.mockReturnValue(mockDeleteMutation)
    })

    describe('Permissions', () => {
      it('should allow edits when user is admin', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.canEdit).toBe(true)
      })

      it('should allow edits when user is coordinator', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'coordinator' } })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.canEdit).toBe(true)
      })

      it('should not allow edits when user is resident', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.canEdit).toBe(false)
      })

      it('should not allow edits when user is faculty', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'faculty' } })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.canEdit).toBe(false)
      })
    })

    describe('createAssignment', () => {
      it('should create assignment when user has permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        mockCreateMutation.mutateAsync.mockResolvedValue({ id: 'a1' })

        const { result } = renderHook(() => useCellActions())

        const assignmentData = {
          blockId: 'b1',
          personId: 'p1',
          role: AssignmentRole.PRIMARY,
        }

        await act(async () => {
          const assignment = await result.current.createAssignment(assignmentData)
          expect(assignment).toEqual({ id: 'a1' })
        })

        expect(mockCreateMutation.mutateAsync).toHaveBeenCalledWith(assignmentData)
      })

      it('should throw error when user lacks permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

        const { result } = renderHook(() => useCellActions())

        const assignmentData = {
          blockId: 'b1',
          personId: 'p1',
          role: AssignmentRole.PRIMARY,
        }

        await expect(
          result.current.createAssignment(assignmentData)
        ).rejects.toThrow('You do not have permission to create assignments')
      })
    })

    describe('updateAssignment', () => {
      it('should update assignment when user has permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        mockUpdateMutation.mutateAsync.mockResolvedValue({ id: 'a1', notes: 'Updated' })

        const { result } = renderHook(() => useCellActions())

        const updateData = { notes: 'Updated' }

        await act(async () => {
          const assignment = await result.current.updateAssignment('a1', updateData)
          expect(assignment).toEqual({ id: 'a1', notes: 'Updated' })
        })

        expect(mockUpdateMutation.mutateAsync).toHaveBeenCalledWith({
          id: 'a1',
          data: updateData,
        })
      })

      it('should throw error when user lacks permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

        const { result } = renderHook(() => useCellActions())

        await expect(
          result.current.updateAssignment('a1', { notes: 'Updated' })
        ).rejects.toThrow('You do not have permission to update assignments')
      })
    })

    describe('deleteAssignment', () => {
      it('should delete assignment when user has permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        mockDeleteMutation.mutateAsync.mockResolvedValue(undefined)

        const { result } = renderHook(() => useCellActions())

        await act(async () => {
          await result.current.deleteAssignment('a1')
        })

        expect(mockDeleteMutation.mutateAsync).toHaveBeenCalledWith('a1')
      })

      it('should throw error when user lacks permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

        const { result } = renderHook(() => useCellActions())

        await expect(
          result.current.deleteAssignment('a1')
        ).rejects.toThrow('You do not have permission to delete assignments')
      })
    })

    describe('clearAssignment', () => {
      it('should call deleteAssignment', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        mockDeleteMutation.mutateAsync.mockResolvedValue(undefined)

        const { result } = renderHook(() => useCellActions())

        await act(async () => {
          await result.current.clearAssignment('a1')
        })

        expect(mockDeleteMutation.mutateAsync).toHaveBeenCalledWith('a1')
      })
    })

    describe('markAsOff', () => {
      it('should create OFF assignment when user has permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        mockCreateMutation.mutateAsync.mockResolvedValue({ id: 'a1' })

        const { result } = renderHook(() => useCellActions())

        await act(async () => {
          await result.current.markAsOff('b1', 'p1')
        })

        expect(mockCreateMutation.mutateAsync).toHaveBeenCalledWith({
          blockId: 'b1',
          personId: 'p1',
          role: 'primary',
          activityOverride: 'OFF',
          createdBy: 'u1',
        })
      })

      it('should throw error when user lacks permission', async () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

        const { result } = renderHook(() => useCellActions())

        await expect(
          result.current.markAsOff('b1', 'p1')
        ).rejects.toThrow('You do not have permission to modify assignments')
      })
    })

    describe('isLoading', () => {
      it('should be true when create is pending', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        useCreateAssignment.mockReturnValue({ ...mockCreateMutation, isPending: true })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.isLoading).toBe(true)
      })

      it('should be true when update is pending', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        useUpdateAssignment.mockReturnValue({ ...mockUpdateMutation, isPending: true })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.isLoading).toBe(true)
      })

      it('should be true when delete is pending', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        useDeleteAssignment.mockReturnValue({ ...mockDeleteMutation, isPending: true })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.isLoading).toBe(true)
      })

      it('should be false when no mutations are pending', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })

        const { result } = renderHook(() => useCellActions())

        expect(result.current.isLoading).toBe(false)
      })
    })

    describe('Click Handlers', () => {
      it('should call onEditModalOpen when cell is clicked and user can edit', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        const onEditModalOpen = jest.fn()

        const { result } = renderHook(() => useCellActions({ onEditModalOpen }))

        const cellData = {
          personId: 'p1',
          date: '2024-01-15',
          session: 'AM' as const,
        }

        act(() => {
          result.current.handlers.onCellClick(cellData)
        })

        expect(onEditModalOpen).toHaveBeenCalledWith(cellData)
      })

      it('should not call onEditModalOpen when user cannot edit', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })
        const onEditModalOpen = jest.fn()

        const { result } = renderHook(() => useCellActions({ onEditModalOpen }))

        const cellData = {
          personId: 'p1',
          date: '2024-01-15',
          session: 'AM' as const,
        }

        act(() => {
          result.current.handlers.onCellClick(cellData)
        })

        expect(onEditModalOpen).not.toHaveBeenCalled()
      })

      it('should call onQuickMenuOpen on right-click when user can edit', () => {
        useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
        const onQuickMenuOpen = jest.fn()

        const { result } = renderHook(() => useCellActions({ onQuickMenuOpen }))

        const cellData = {
          personId: 'p1',
          date: '2024-01-15',
          session: 'AM' as const,
        }

        const mockEvent = {
          preventDefault: jest.fn(),
          stopPropagation: jest.fn(),
          clientX: 100,
          clientY: 200,
        } as any

        act(() => {
          result.current.handlers.onCellRightClick(mockEvent, cellData)
        })

        expect(mockEvent.preventDefault).toHaveBeenCalled()
        expect(mockEvent.stopPropagation).toHaveBeenCalled()
        expect(onQuickMenuOpen).toHaveBeenCalledWith(mockEvent, cellData)
      })
    })
  })

  describe('useLongPress Hook', () => {
    beforeEach(() => {
      jest.useFakeTimers()
    })

    afterEach(() => {
      jest.useRealTimers()
    })

    it('should call onLongPress after delay', () => {
      const onLongPress = jest.fn()
      const { result } = renderHook(() => useLongPress({ onLongPress, delay: 500 }))

      const mockEvent = { clientX: 100, clientY: 200 } as any

      act(() => {
        result.current.onMouseDown(mockEvent)
      })

      expect(onLongPress).not.toHaveBeenCalled()

      act(() => {
        jest.advanceTimersByTime(500)
      })

      expect(onLongPress).toHaveBeenCalledWith({ clientX: 100, clientY: 200 })
    })

    it('should call onClick when released before delay', () => {
      const onLongPress = jest.fn()
      const onClick = jest.fn()
      const { result } = renderHook(() => useLongPress({ onLongPress, onClick, delay: 500 }))

      const mockEvent = { clientX: 100, clientY: 200 } as any

      act(() => {
        result.current.onMouseDown(mockEvent)
      })

      act(() => {
        jest.advanceTimersByTime(200)
      })

      act(() => {
        result.current.onMouseUp()
      })

      expect(onLongPress).not.toHaveBeenCalled()
      expect(onClick).toHaveBeenCalled()
    })

    it('should not call onClick when disabled', () => {
      const onLongPress = jest.fn()
      const onClick = jest.fn()
      const { result } = renderHook(() =>
        useLongPress({ onLongPress, onClick, delay: 500, disabled: true })
      )

      const mockEvent = { clientX: 100, clientY: 200 } as any

      act(() => {
        result.current.onMouseDown(mockEvent)
      })

      act(() => {
        result.current.onMouseUp()
      })

      expect(onClick).not.toHaveBeenCalled()
    })

    it('should cancel long press on mouse leave', () => {
      const onLongPress = jest.fn()
      const { result } = renderHook(() => useLongPress({ onLongPress, delay: 500 }))

      const mockEvent = { clientX: 100, clientY: 200 } as any

      act(() => {
        result.current.onMouseDown(mockEvent)
      })

      act(() => {
        jest.advanceTimersByTime(200)
      })

      act(() => {
        result.current.onMouseLeave()
      })

      act(() => {
        jest.advanceTimersByTime(500)
      })

      expect(onLongPress).not.toHaveBeenCalled()
    })

    it('should handle touch events', () => {
      const onLongPress = jest.fn()
      const { result } = renderHook(() => useLongPress({ onLongPress, delay: 500 }))

      const mockEvent = { touches: [{ clientX: 100, clientY: 200 }] } as any

      act(() => {
        result.current.onTouchStart(mockEvent)
      })

      act(() => {
        jest.advanceTimersByTime(500)
      })

      expect(onLongPress).toHaveBeenCalledWith({ clientX: 100, clientY: 200 })
    })
  })

  describe('ScheduleCellWrapper Component', () => {
    beforeEach(() => {
      useAuth.mockReturnValue({ user: { id: 'u1', role: 'admin' } })
    })

    it('should render children', () => {
      render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      expect(screen.getByText('Cell Content')).toBeInTheDocument()
    })

    it('should apply cursor-pointer when user can edit', () => {
      const { container } = render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('cursor-pointer')
    })

    it('should not apply cursor-pointer when user cannot edit', () => {
      useAuth.mockReturnValue({ user: { id: 'u1', role: 'resident' } })

      const { container } = render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).not.toHaveClass('cursor-pointer')
    })

    it('should call onClick when clicked', () => {
      const onClick = jest.fn()

      render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          onClick={onClick}
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = screen.getByText('Cell Content').parentElement!
      fireEvent.click(wrapper)

      expect(onClick).toHaveBeenCalledWith({
        personId: 'p1',
        date: '2024-01-15',
        session: 'AM',
        personName: undefined,
        blockId: undefined,
        assignment: undefined,
      })
    })

    it('should call onRightClick on context menu', () => {
      const onRightClick = jest.fn()

      render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          onRightClick={onRightClick}
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = screen.getByText('Cell Content').parentElement!
      fireEvent.contextMenu(wrapper)

      expect(onRightClick).toHaveBeenCalled()
    })

    it('should handle keyboard navigation with Enter key', () => {
      const onClick = jest.fn()

      render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          onClick={onClick}
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = screen.getByText('Cell Content').parentElement!
      fireEvent.keyDown(wrapper, { key: 'Enter' })

      expect(onClick).toHaveBeenCalled()
    })

    it('should handle keyboard navigation with Space key', () => {
      const onClick = jest.fn()

      render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          onClick={onClick}
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = screen.getByText('Cell Content').parentElement!
      fireEvent.keyDown(wrapper, { key: ' ' })

      expect(onClick).toHaveBeenCalled()
    })

    it('should apply custom className', () => {
      const { container } = render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          className="custom-class"
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).toHaveClass('custom-class')
    })

    it('should not be interactive when disabled', () => {
      const onClick = jest.fn()

      const { container } = render(
        <ScheduleCellWrapper
          personId="p1"
          date="2024-01-15"
          session="AM"
          onClick={onClick}
          disabled
        >
          <div>Cell Content</div>
        </ScheduleCellWrapper>
      )

      const wrapper = container.firstChild as HTMLElement
      expect(wrapper).not.toHaveClass('cursor-pointer')

      fireEvent.click(wrapper)
      expect(onClick).not.toHaveBeenCalled()
    })
  })

  describe('Recent Rotations Storage', () => {
    // Mock localStorage for these tests
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
      Object.defineProperty(window, 'localStorage', {
        value: localStorageMock,
        writable: true,
      })
      localStorageMock.clear()
    })

    it('should return empty array when localStorage is empty', () => {
      const rotations = getRecentRotations()
      expect(rotations).toEqual([])
    })

    it('should add rotation to recent list', () => {
      addRecentRotation('r1')
      const rotations = getRecentRotations()
      expect(rotations).toEqual(['r1'])
    })

    it('should move rotation to front if already exists', () => {
      addRecentRotation('r1')
      addRecentRotation('r2')
      addRecentRotation('r1')

      const rotations = getRecentRotations()
      expect(rotations).toEqual(['r1', 'r2'])
    })

    it('should limit to 10 recent rotations', () => {
      for (let i = 0; i < 15; i++) {
        addRecentRotation(`r${i}`)
      }

      const rotations = getRecentRotations()
      expect(rotations).toHaveLength(10)
      expect(rotations[0]).toBe('r14')
    })

    it('should clear recent rotations', () => {
      addRecentRotation('r1')
      addRecentRotation('r2')
      clearRecentRotations()

      const rotations = getRecentRotations()
      expect(rotations).toEqual([])
    })
  })
})
