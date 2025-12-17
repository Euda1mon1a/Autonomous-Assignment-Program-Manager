'use client'

import React, { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react'
import {
  DndContext,
  DragStartEvent,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  useSensor,
  useSensors,
  PointerSensor,
  KeyboardSensor,
  closestCenter,
  MeasuringStrategy,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { put } from '@/lib/api'
import type { Assignment, Block } from '@/types/api'

// Types for drag operations
export interface DragAssignment {
  id: string
  personId: string
  personName: string
  blockId: string
  date: string
  timeOfDay: 'AM' | 'PM'
  abbreviation: string
  activityType: string
  rotationTemplateId: string | null
  role: string
}

export interface DropTarget {
  personId: string
  date: string
  timeOfDay: 'AM' | 'PM'
  blockId?: string
}

interface DragFeedback {
  type: 'success' | 'warning' | 'error'
  message: string
}

interface ScheduleDragContextValue {
  activeAssignment: DragAssignment | null
  overTarget: DropTarget | null
  feedback: DragFeedback | null
  isDragging: boolean
  isUpdating: boolean
}

const ScheduleDragContext = createContext<ScheduleDragContextValue | null>(null)

export function useScheduleDrag() {
  const context = useContext(ScheduleDragContext)
  if (!context) {
    throw new Error('useScheduleDrag must be used within ScheduleDragProvider')
  }
  return context
}

interface ScheduleDragProviderProps {
  children: ReactNode
  blockLookup: Map<string, Block>
  onAssignmentMove?: (assignmentId: string, newBlockId: string) => void
}

export function ScheduleDragProvider({
  children,
  blockLookup,
  onAssignmentMove,
}: ScheduleDragProviderProps) {
  const queryClient = useQueryClient()
  const [activeAssignment, setActiveAssignment] = useState<DragAssignment | null>(null)
  const [overTarget, setOverTarget] = useState<DropTarget | null>(null)
  const [feedback, setFeedback] = useState<DragFeedback | null>(null)

  // Configure sensors for drag detection
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // Minimum drag distance before activating
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // Mutation for updating assignment
  const updateAssignment = useMutation({
    mutationFn: async ({ assignmentId, newBlockId }: { assignmentId: string; newBlockId: string }) => {
      return put<Assignment>(`/assignments/${assignmentId}`, { block_id: newBlockId })
    },

    // Optimistic update - update UI immediately
    onMutate: async ({ assignmentId, newBlockId }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['assignments'] })

      // Snapshot previous value for rollback
      const previousAssignments = queryClient.getQueryData(['assignments'])

      // Optimistically update cache
      queryClient.setQueryData(['assignments'], (old: any) => {
        if (!old?.items) return old
        return {
          ...old,
          items: old.items.map((assign: Assignment) =>
            assign.id === assignmentId
              ? { ...assign, block_id: newBlockId }
              : assign
          )
        }
      })

      // Return context for rollback
      return { previousAssignments }
    },

    onSuccess: (data, variables) => {
      setFeedback({ type: 'success', message: 'Assignment moved successfully' })
      onAssignmentMove?.(variables.assignmentId, variables.newBlockId)
      setTimeout(() => setFeedback(null), 3000)
    },

    // Rollback on error
    onError: (err, variables, context) => {
      if (context?.previousAssignments) {
        queryClient.setQueryData(['assignments'], context.previousAssignments)
      }
      // Show error toast
      const errorMessage = (err as Error).message || 'Failed to move assignment'
      setFeedback({ type: 'error', message: `Move failed - changes reverted: ${errorMessage}` })
      setTimeout(() => setFeedback(null), 5000)
    },

    // Refetch after success or error to ensure sync
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] })
    },
  })

  // Find block ID for a given date and time of day
  const findBlockId = useCallback((date: string, timeOfDay: 'AM' | 'PM'): string | undefined => {
    const entries = Array.from(blockLookup.entries())
    for (let i = 0; i < entries.length; i++) {
      const [id, block] = entries[i]
      if (block.date === date && block.time_of_day === timeOfDay) {
        return id
      }
    }
    return undefined
  }, [blockLookup])

  // Handle drag start
  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event
    const data = active.data.current as DragAssignment | undefined
    if (data) {
      setActiveAssignment(data)
    }
  }, [])

  // Handle drag over
  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { over } = event
    if (over) {
      const target = over.data.current as DropTarget | undefined
      setOverTarget(target || null)
    } else {
      setOverTarget(null)
    }
  }, [])

  // Handle drag end
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event

    if (over && activeAssignment) {
      const target = over.data.current as DropTarget | undefined

      if (target && target.personId === activeAssignment.personId) {
        // Find the block ID for the target date/time
        const newBlockId = findBlockId(target.date, target.timeOfDay)

        if (newBlockId && newBlockId !== activeAssignment.blockId) {
          // Perform the move
          updateAssignment.mutate({
            assignmentId: activeAssignment.id,
            newBlockId,
          })
        }
      } else if (target && target.personId !== activeAssignment.personId) {
        setFeedback({
          type: 'warning',
          message: 'Cannot move assignment to a different person',
        })
        setTimeout(() => setFeedback(null), 3000)
      }
    }

    setActiveAssignment(null)
    setOverTarget(null)
  }, [activeAssignment, findBlockId, updateAssignment])

  // Handle drag cancel
  const handleDragCancel = useCallback(() => {
    setActiveAssignment(null)
    setOverTarget(null)
  }, [])

  const contextValue = useMemo<ScheduleDragContextValue>(() => ({
    activeAssignment,
    overTarget,
    feedback,
    isDragging: activeAssignment !== null,
    isUpdating: updateAssignment.isPending,
  }), [activeAssignment, overTarget, feedback, updateAssignment.isPending])

  return (
    <ScheduleDragContext.Provider value={contextValue}>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
        measuring={{
          droppable: {
            strategy: MeasuringStrategy.Always,
          },
        }}
      >
        {children}
        <DragOverlay dropAnimation={null}>
          {activeAssignment && (
            <DragPreview assignment={activeAssignment} />
          )}
        </DragOverlay>
      </DndContext>

      {/* Feedback Toast */}
      {feedback && (
        <div
          className={`
            fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg
            ${feedback.type === 'success' ? 'bg-green-500 text-white' : ''}
            ${feedback.type === 'warning' ? 'bg-amber-500 text-white' : ''}
            ${feedback.type === 'error' ? 'bg-red-500 text-white' : ''}
            animate-in fade-in slide-in-from-bottom-4 duration-300
          `}
        >
          {feedback.message}
        </div>
      )}
    </ScheduleDragContext.Provider>
  )
}

// Drag preview component shown while dragging
function DragPreview({ assignment }: { assignment: DragAssignment }) {
  const colorClasses = getActivityColorClasses(assignment.activityType)

  return (
    <div
      className={`
        inline-block px-2 py-1 rounded text-sm font-medium border-2
        shadow-lg transform scale-105 cursor-grabbing
        ${colorClasses}
      `}
    >
      {assignment.abbreviation}
    </div>
  )
}

// Color utility function
function getActivityColorClasses(activityType: string): string {
  const colors: Record<string, string> = {
    clinic: 'bg-blue-100 text-blue-800 border-blue-400',
    inpatient: 'bg-purple-100 text-purple-800 border-purple-400',
    procedure: 'bg-red-100 text-red-800 border-red-400',
    conference: 'bg-gray-100 text-gray-800 border-gray-400',
    elective: 'bg-green-100 text-green-800 border-green-400',
    call: 'bg-orange-100 text-orange-800 border-orange-400',
    off: 'bg-white text-gray-400 border-gray-300',
    leave: 'bg-amber-100 text-amber-800 border-amber-400',
    vacation: 'bg-amber-100 text-amber-800 border-amber-400',
  }
  return colors[activityType?.toLowerCase()] || 'bg-slate-100 text-slate-700 border-slate-400'
}
