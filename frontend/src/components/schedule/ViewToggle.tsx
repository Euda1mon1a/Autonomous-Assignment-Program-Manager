'use client'

import React, { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Calendar, CalendarDays, LayoutGrid, Columns } from 'lucide-react'

export type ScheduleView = 'day' | 'week' | 'month' | 'block'

export interface ViewToggleProps {
  currentView: ScheduleView
  onChange: (view: ScheduleView) => void
}

const VIEW_STORAGE_KEY = 'schedule-view-preference'

const viewOptions: { value: ScheduleView; label: string; icon: React.ReactNode }[] = [
  { value: 'day', label: 'Day', icon: <Calendar className="w-4 h-4" /> },
  { value: 'week', label: 'Week', icon: <Columns className="w-4 h-4" /> },
  { value: 'month', label: 'Month', icon: <CalendarDays className="w-4 h-4" /> },
  { value: 'block', label: 'Block', icon: <LayoutGrid className="w-4 h-4" /> },
]

export function ViewToggle({ currentView, onChange }: ViewToggleProps) {
  const router = useRouter()
  const searchParams = useSearchParams()

  // Initialize from URL param or localStorage on mount
  useEffect(() => {
    const urlView = searchParams.get('view') as ScheduleView | null
    const storedView = localStorage.getItem(VIEW_STORAGE_KEY) as ScheduleView | null

    if (urlView && isValidView(urlView) && urlView !== currentView) {
      onChange(urlView)
    } else if (storedView && isValidView(storedView) && storedView !== currentView) {
      onChange(storedView)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleViewChange = (view: ScheduleView) => {
    // Update localStorage
    localStorage.setItem(VIEW_STORAGE_KEY, view)

    // Update URL param
    const params = new URLSearchParams(searchParams.toString())
    params.set('view', view)
    router.push(`?${params.toString()}`, { scroll: false })

    // Call the onChange handler
    onChange(view)
  }

  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-1">
      {viewOptions.map((option) => (
        <button
          key={option.value}
          onClick={() => handleViewChange(option.value)}
          className={`
            inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium
            transition-all duration-150 ease-in-out
            ${
              currentView === option.value
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }
          `}
          aria-pressed={currentView === option.value}
          title={`Switch to ${option.label} view`}
        >
          {option.icon}
          <span className="hidden sm:inline">{option.label}</span>
        </button>
      ))}
    </div>
  )
}

function isValidView(view: string): view is ScheduleView {
  return ['day', 'week', 'month', 'block'].includes(view)
}

// Hook for managing view state with localStorage and URL sync
export function useScheduleView(defaultView: ScheduleView = 'block'): [ScheduleView, (view: ScheduleView) => void] {
  const [view, setView] = React.useState<ScheduleView>(defaultView)

  useEffect(() => {
    // Check URL first, then localStorage
    const urlParams = new URLSearchParams(window.location.search)
    const urlView = urlParams.get('view')
    const storedView = localStorage.getItem(VIEW_STORAGE_KEY)

    if (urlView && isValidView(urlView)) {
      setView(urlView)
    } else if (storedView && isValidView(storedView)) {
      setView(storedView)
    }
  }, [])

  return [view, setView]
}
