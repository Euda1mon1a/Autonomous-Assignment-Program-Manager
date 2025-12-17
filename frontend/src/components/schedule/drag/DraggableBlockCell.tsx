'use client'

import { useMemo } from 'react'
import { useDraggable, useDroppable } from '@dnd-kit/core'
import { CSS } from '@dnd-kit/utilities'
import { useScheduleDrag, DragAssignment, DropTarget } from './ScheduleDragProvider'

interface CellAssignment {
  id: string
  abbreviation: string
  activityType: string
  templateName?: string
  role?: string
  notes?: string
  personId: string
  personName: string
  blockId: string
  rotationTemplateId: string | null
}

interface DraggableBlockCellProps {
  assignment?: CellAssignment
  personId: string
  personName: string
  date: string
  timeOfDay: 'AM' | 'PM'
  isWeekend: boolean
  isToday?: boolean
  isHoliday?: boolean
  holidayName?: string
  compact?: boolean
}

/**
 * Color coding for rotation types
 */
const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800 border-blue-300',
  inpatient: 'bg-purple-100 text-purple-800 border-purple-300',
  procedure: 'bg-red-100 text-red-800 border-red-300',
  conference: 'bg-gray-100 text-gray-800 border-gray-300',
  elective: 'bg-green-100 text-green-800 border-green-300',
  call: 'bg-orange-100 text-orange-800 border-orange-300',
  off: 'bg-white text-gray-400 border-gray-200',
  leave: 'bg-amber-100 text-amber-800 border-amber-300',
  vacation: 'bg-amber-100 text-amber-800 border-amber-300',
  default: 'bg-slate-100 text-slate-700 border-slate-300',
}

function getActivityColor(activityType: string | undefined | null): string {
  if (!activityType) return rotationColors.default
  const activityLower = activityType.toLowerCase()
  if (rotationColors[activityLower]) {
    return rotationColors[activityLower]
  }
  for (const [key, color] of Object.entries(rotationColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }
  return rotationColors.default
}

export function DraggableBlockCell({
  assignment,
  personId,
  personName: _personName, // Used in drag data
  date,
  timeOfDay,
  isWeekend,
  isToday = false,
  isHoliday = false,
  holidayName,
  compact = false,
}: DraggableBlockCellProps) {
  const { activeAssignment, isDragging } = useScheduleDrag()
  // Note: _personName is destructured but accessed through the props destructure for consistency

  // Create unique ID for this cell
  const cellId = `${personId}-${date}-${timeOfDay}`

  // Droppable setup
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: `drop-${cellId}`,
    data: {
      personId,
      date,
      timeOfDay,
    } as DropTarget,
  })

  // Draggable setup (only if has assignment)
  const dragData: DragAssignment | undefined = assignment ? {
    id: assignment.id,
    personId: assignment.personId,
    personName: assignment.personName,
    blockId: assignment.blockId,
    date,
    timeOfDay,
    abbreviation: assignment.abbreviation,
    activityType: assignment.activityType,
    rotationTemplateId: assignment.rotationTemplateId,
    role: assignment.role || 'primary',
  } : undefined

  const {
    attributes,
    listeners,
    setNodeRef: setDragRef,
    transform,
    isDragging: isCellDragging,
  } = useDraggable({
    id: assignment?.id || `empty-${cellId}`,
    data: dragData,
    disabled: !assignment,
  })

  // Combine refs
  const setNodeRef = (node: HTMLElement | null) => {
    setDropRef(node)
    setDragRef(node)
  }

  // Determine if this cell is a valid drop target
  const isValidDropTarget = useMemo(() => {
    if (!activeAssignment) return false
    // Can only drop on same person's cells
    return activeAssignment.personId === personId
  }, [activeAssignment, personId])

  // Calculate styles
  const colorClass = useMemo(() => {
    return assignment ? getActivityColor(assignment.activityType) : ''
  }, [assignment])

  const baseStyles = useMemo(() => {
    let styles = compact
      ? 'px-0.5 py-0.5 text-center border-r border-gray-200 min-w-[36px] max-w-[40px]'
      : 'px-1 py-1 text-center border-r border-gray-200 min-w-[44px]'

    // Weekend shading
    if (isWeekend) {
      styles += ' bg-gray-50/70'
    }

    // Holiday shading
    if (isHoliday) {
      styles += ' bg-amber-50/50'
    }

    // Today highlight
    if (isToday) {
      styles += ' bg-blue-50/40'
    }

    // Right border for PM cells (day separator)
    if (timeOfDay === 'PM') {
      styles += ' border-r-2 border-r-gray-300'
    }

    // Drop target highlight
    if (isOver && isValidDropTarget) {
      styles += ' ring-2 ring-blue-400 ring-inset bg-blue-50'
    } else if (isDragging && isValidDropTarget && !isCellDragging) {
      styles += ' bg-blue-50/30'
    }

    return styles
  }, [isWeekend, isHoliday, isToday, timeOfDay, isOver, isValidDropTarget, isDragging, isCellDragging, compact])

  // Transform style for dragging
  const style = transform ? {
    transform: CSS.Translate.toString(transform),
    zIndex: isCellDragging ? 100 : undefined,
  } : undefined

  // Empty cell
  if (!assignment) {
    return (
      <td
        ref={setNodeRef}
        className={`${baseStyles} transition-colors duration-150`}
        title={holidayName || (isWeekend ? 'Weekend' : undefined)}
      >
        <div className="text-gray-300 text-xs select-none">-</div>
      </td>
    )
  }

  // Build tooltip content
  const tooltipContent = [
    assignment.templateName || assignment.abbreviation,
    assignment.activityType && `Type: ${assignment.activityType}`,
    assignment.role && assignment.role !== 'primary' && `Role: ${assignment.role}`,
    assignment.notes && `Note: ${assignment.notes}`,
    holidayName && `Holiday: ${holidayName}`,
    'Drag to move within this row',
  ]
    .filter(Boolean)
    .join('\n')

  return (
    <td
      ref={setNodeRef}
      className={`${baseStyles} transition-colors duration-150`}
      style={style}
      {...attributes}
      {...listeners}
    >
      <div
        className={`
          inline-block px-1 py-0.5 rounded font-medium border
          ${compact ? 'text-[10px]' : 'text-xs'}
          ${colorClass}
          ${isCellDragging ? 'opacity-40' : ''}
          cursor-grab active:cursor-grabbing
          transition-all hover:scale-105 hover:shadow-sm
          select-none
        `}
        title={tooltipContent}
      >
        {assignment.abbreviation}
      </div>
    </td>
  )
}

/**
 * Separator row between groups in the academic year view
 */
export function YearViewSeparatorRow({
  label,
  columnCount,
}: {
  label?: string
  columnCount: number
}) {
  return (
    <tr className="bg-gray-100/70 border-y border-gray-300 sticky top-[60px] z-20">
      <td
        colSpan={1 + columnCount * 2}
        className="py-1.5 px-4 text-xs font-semibold text-gray-600 uppercase tracking-wider"
      >
        {label || ''}
      </td>
    </tr>
  )
}
