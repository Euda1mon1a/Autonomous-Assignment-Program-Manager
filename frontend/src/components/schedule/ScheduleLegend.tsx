'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Info } from 'lucide-react'

/**
 * Rotation type color definitions matching ScheduleCell.tsx
 * These colors help users quickly identify different activity types
 */
const rotationLegendItems = [
  { type: 'clinic', label: 'Clinic', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  { type: 'inpatient', label: 'Inpatient', color: 'bg-purple-100 text-purple-800 border-purple-300' },
  { type: 'procedure', label: 'Procedure', color: 'bg-red-100 text-red-800 border-red-300' },
  { type: 'conference', label: 'Conference', color: 'bg-gray-100 text-gray-800 border-gray-300' },
  { type: 'elective', label: 'Elective', color: 'bg-green-100 text-green-800 border-green-300' },
  { type: 'call', label: 'Call', color: 'bg-orange-100 text-orange-800 border-orange-300' },
  { type: 'off', label: 'Off', color: 'bg-white text-gray-400 border-gray-200' },
  { type: 'leave', label: 'Leave/Vacation', color: 'bg-amber-100 text-amber-800 border-amber-300' },
]

interface ScheduleLegendProps {
  /** Compact mode shows fewer items initially */
  compact?: boolean
  /** Show as a horizontal or vertical list */
  orientation?: 'horizontal' | 'vertical'
  /** Additional CSS classes */
  className?: string
}

/**
 * Schedule Legend Component
 *
 * Displays a color-coded legend for rotation types used in the schedule grid.
 * Helps users understand what each color represents at a glance.
 */
export function ScheduleLegend({
  compact = false,
  orientation = 'horizontal',
  className = '',
}: ScheduleLegendProps) {
  const [isExpanded, setIsExpanded] = useState(!compact)

  const displayItems = isExpanded ? rotationLegendItems : rotationLegendItems.slice(0, 4)

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-3 ${className}`} role="region" aria-label="Activity color legend">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <Info className="w-4 h-4 text-gray-400" aria-hidden="true" />
          <span>Activity Legend</span>
        </div>
        {compact && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            aria-label={isExpanded ? 'Collapse legend' : 'Expand legend'}
            aria-expanded={isExpanded}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-500" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" aria-hidden="true" />
            )}
          </button>
        )}
      </div>

      <div
        className={`
          flex gap-2
          ${orientation === 'vertical' ? 'flex-col' : 'flex-wrap'}
        `}
      >
        {displayItems.map((item) => (
          <div
            key={item.type}
            className="flex items-center gap-1.5"
            role="listitem"
          >
            <span
              className={`
                inline-block px-2 py-0.5 rounded text-xs font-medium border
                ${item.color}
              `}
              aria-hidden="true"
            >
              {item.type.substring(0, 3).toUpperCase()}
            </span>
            <span className="text-xs text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>

      {compact && !isExpanded && rotationLegendItems.length > 4 && (
        <button
          onClick={() => setIsExpanded(true)}
          className="mt-2 text-xs text-blue-600 hover:text-blue-800"
        >
          +{rotationLegendItems.length - 4} more...
        </button>
      )}
    </div>
  )
}

/**
 * Compact inline legend for use in schedule headers
 */
export function ScheduleLegendInline({ className = '' }: { className?: string }) {
  return (
    <div className={`flex flex-wrap gap-3 ${className}`} role="list" aria-label="Activity type legend">
      {rotationLegendItems.slice(0, 6).map((item) => (
        <div key={item.type} className="flex items-center gap-1" role="listitem">
          <span
            className={`w-3 h-3 rounded border ${item.color.split(' ')[0]} ${item.color.split(' ')[2]}`}
            aria-hidden="true"
          />
          <span className="text-xs text-gray-500">{item.label}</span>
        </div>
      ))}
    </div>
  )
}

export { rotationLegendItems }
