'use client'

import { useMemo } from 'react'

/**
 * Color coding for rotation types
 * Colors are designed for quick visual identification - humans work on heuristics
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

/**
 * Get the color class for a given activity type
 */
function getActivityColor(activityType: string | undefined | null): string {
  if (!activityType) return rotationColors.default

  const activityLower = activityType.toLowerCase()

  // Check for exact matches first
  if (rotationColors[activityLower]) {
    return rotationColors[activityLower]
  }

  // Check for partial matches
  for (const [key, color] of Object.entries(rotationColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }

  return rotationColors.default
}

interface CellAssignment {
  abbreviation: string
  /** User-facing abbreviation for schedule grid (short codes like C, FMIT) */
  display_abbreviation?: string
  activityType: string
  fontColor?: string
  backgroundColor?: string
  templateName?: string
  role?: string
  notes?: string
}

interface ScheduleCellProps {
  assignment?: CellAssignment
  isWeekend: boolean
  isToday: boolean
  timeOfDay: 'AM' | 'PM'
}

/**
 * Individual cell in the schedule grid
 * Shows the rotation abbreviation with color coding
 */
export function ScheduleCell({
  assignment,
  isWeekend,
  isToday,
  timeOfDay,
}: ScheduleCellProps) {
  // Map Tailwind color names to hex values
  const tailwindToHex: Record<string, string> = {
    'black': '#000000',
    'white': '#ffffff',
    'gray-100': '#f3f4f6',
    'gray-200': '#e5e7eb',
    'gray-400': '#9ca3af',
    'gray-800': '#1f2937',
    'red-500': '#ef4444',
    'green-100': '#dcfce7',
    'green-500': '#22c55e',
    'green-800': '#166534',
    'blue-300': '#93c5fd',
    'sky-500': '#0ea5e9',
    'purple-700': '#7c3aed',
    'amber-100': '#fef3c7',
    'amber-800': '#92400e',
    'yellow-300': '#fde047',
    'emerald-200': '#a7f3d0',
  }

  // Memoize the color class and style calculation
  const { colorClass, customStyle } = useMemo(() => {
    if (!assignment) return { colorClass: '', customStyle: undefined }

    // Use custom colors from database if available
    if (assignment.fontColor && assignment.backgroundColor) {
      const textHex = tailwindToHex[assignment.fontColor] || assignment.fontColor
      const bgHex = tailwindToHex[assignment.backgroundColor] || assignment.backgroundColor
      return {
        colorClass: 'border',
        customStyle: {
          color: textHex,
          backgroundColor: bgHex,
          borderColor: bgHex === '#ffffff' ? '#e5e7eb' : bgHex === '#000000' ? '#374151' : bgHex,
        }
      }
    }

    // Fall back to activity-type-based colors
    return { colorClass: getActivityColor(assignment.activityType), customStyle: undefined }
  }, [assignment])

  // Base cell styles
  const baseStyles = useMemo(() => {
    let styles = 'px-1 py-1.5 text-center border-r border-gray-200 min-w-[50px]'

    // Weekend shading
    if (isWeekend) {
      styles += ' bg-gray-50/50'
    }

    // Today highlight
    if (isToday) {
      styles += ' bg-blue-50/30'
    }

    // Right border for PM cells
    if (timeOfDay === 'PM') {
      styles += ' border-r-2 border-r-gray-300'
    }

    return styles
  }, [isWeekend, isToday, timeOfDay])

  // Empty cell
  if (!assignment) {
    return (
      <td className={baseStyles}>
        <div className="text-gray-300 text-xs">-</div>
      </td>
    )
  }

  // Build tooltip content
  const tooltipContent = [
    assignment.templateName || assignment.abbreviation,
    assignment.activityType && `Type: ${assignment.activityType}`,
    assignment.role && assignment.role !== 'primary' && `Role: ${assignment.role}`,
    assignment.notes && `Note: ${assignment.notes}`,
  ]
    .filter(Boolean)
    .join('\n')

  // Prefer display_abbreviation (short codes like C, FMIT) over abbreviation (may include time suffix like C-AM)
  const displayCode = assignment.display_abbreviation || assignment.abbreviation

  return (
    <td className={baseStyles}>
      <div
        className={`
          inline-block px-1.5 py-0.5 rounded text-xs font-medium border
          ${colorClass}
          cursor-default transition-all hover:scale-105 hover:shadow-sm
        `}
        style={customStyle}
        title={tooltipContent}
      >
        {displayCode}
      </div>
    </td>
  )
}

/**
 * Separator row between PGY groups
 */
export function ScheduleSeparatorRow({
  label,
  columnCount,
}: {
  label?: string
  columnCount: number
}) {
  return (
    <tr className="bg-gray-100/50 border-y border-gray-300">
      <td
        colSpan={1 + columnCount * 2}
        className="py-1 px-4 text-xs font-medium text-gray-500 uppercase tracking-wider"
      >
        {label || ''}
      </td>
    </tr>
  )
}
