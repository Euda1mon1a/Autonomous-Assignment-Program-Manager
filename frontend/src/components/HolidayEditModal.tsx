'use client'

import { useState, useEffect } from 'react'
import { X, Plus, Trash2, Calendar } from 'lucide-react'
import { format, parseISO, isValid } from 'date-fns'

export interface Holiday {
  id: string
  name: string
  date: string // YYYY-MM-DD format
  isCustom?: boolean
}

// Default federal holidays (relative dates calculated for current year)
const getDefaultHolidays = (year: number): Holiday[] => [
  { id: 'new-years', name: "New Year's Day", date: `${year}-01-01` },
  { id: 'mlk', name: 'Martin Luther King Jr. Day', date: getNthWeekdayOfMonth(year, 0, 1, 3) }, // 3rd Monday of January
  { id: 'presidents', name: "Presidents' Day", date: getNthWeekdayOfMonth(year, 1, 1, 3) }, // 3rd Monday of February
  { id: 'memorial', name: 'Memorial Day', date: getLastWeekdayOfMonth(year, 4, 1) }, // Last Monday of May
  { id: 'juneteenth', name: 'Juneteenth', date: `${year}-06-19` },
  { id: 'independence', name: 'Independence Day', date: `${year}-07-04` },
  { id: 'labor', name: 'Labor Day', date: getNthWeekdayOfMonth(year, 8, 1, 1) }, // 1st Monday of September
  { id: 'columbus', name: 'Columbus Day', date: getNthWeekdayOfMonth(year, 9, 1, 2) }, // 2nd Monday of October
  { id: 'veterans', name: 'Veterans Day', date: `${year}-11-11` },
  { id: 'thanksgiving', name: 'Thanksgiving Day', date: getNthWeekdayOfMonth(year, 10, 4, 4) }, // 4th Thursday of November
  { id: 'christmas', name: 'Christmas Day', date: `${year}-12-25` },
]

// Helper to get the nth weekday of a month (0=Sunday, 1=Monday, etc.)
function getNthWeekdayOfMonth(year: number, month: number, weekday: number, n: number): string {
  const firstDay = new Date(year, month, 1)
  const firstWeekday = firstDay.getDay()
  let date = 1 + ((weekday - firstWeekday + 7) % 7) + (n - 1) * 7
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
}

// Helper to get the last weekday of a month
function getLastWeekdayOfMonth(year: number, month: number, weekday: number): string {
  const lastDay = new Date(year, month + 1, 0)
  const lastDate = lastDay.getDate()
  const lastWeekday = lastDay.getDay()
  const diff = (lastWeekday - weekday + 7) % 7
  const date = lastDate - diff
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`
}

interface HolidayEditModalProps {
  isOpen: boolean
  onClose: () => void
  holidays: Holiday[]
  onSave: (holidays: Holiday[]) => void
  academicYearStart?: string // e.g., "2024-07-01"
  academicYearEnd?: string // e.g., "2025-06-30"
}

export function HolidayEditModal({
  isOpen,
  onClose,
  holidays,
  onSave,
  academicYearStart,
  academicYearEnd,
}: HolidayEditModalProps) {
  const [editedHolidays, setEditedHolidays] = useState<Holiday[]>([])
  const [newHolidayName, setNewHolidayName] = useState('')
  const [newHolidayDate, setNewHolidayDate] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Calculate years covered by academic year
  const startYear = academicYearStart ? new Date(academicYearStart).getFullYear() : new Date().getFullYear()
  const endYear = academicYearEnd ? new Date(academicYearEnd).getFullYear() : startYear + 1

  // Initialize with current holidays or defaults
  useEffect(() => {
    if (isOpen) {
      if (holidays.length > 0) {
        setEditedHolidays([...holidays])
      } else {
        // Generate default holidays for both years in academic year
        const defaultHolidays = [
          ...getDefaultHolidays(startYear),
          ...getDefaultHolidays(endYear),
        ]
        // Filter to only include holidays within academic year range
        const filtered = defaultHolidays.filter((h) => {
          if (!academicYearStart || !academicYearEnd) return true
          return h.date >= academicYearStart && h.date <= academicYearEnd
        })
        setEditedHolidays(filtered)
      }
      setNewHolidayName('')
      setNewHolidayDate('')
      setError(null)
    }
  }, [isOpen, holidays, academicYearStart, academicYearEnd, startYear, endYear])

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  const handleToggleHoliday = (id: string) => {
    setEditedHolidays((prev) =>
      prev.map((h) => (h.id === id ? { ...h, disabled: !h.disabled } : h))
    )
  }

  const handleRemoveHoliday = (id: string) => {
    setEditedHolidays((prev) => prev.filter((h) => h.id !== id))
  }

  const handleAddHoliday = () => {
    setError(null)

    if (!newHolidayName.trim()) {
      setError('Please enter a holiday name')
      return
    }

    if (!newHolidayDate) {
      setError('Please select a date')
      return
    }

    // Validate date
    const date = parseISO(newHolidayDate)
    if (!isValid(date)) {
      setError('Invalid date')
      return
    }

    // Check if date is within academic year
    if (academicYearStart && academicYearEnd) {
      if (newHolidayDate < academicYearStart || newHolidayDate > academicYearEnd) {
        setError('Date must be within the academic year')
        return
      }
    }

    // Check for duplicate dates
    if (editedHolidays.some((h) => h.date === newHolidayDate)) {
      setError('A holiday already exists on this date')
      return
    }

    const newHoliday: Holiday = {
      id: `custom-${Date.now()}`,
      name: newHolidayName.trim(),
      date: newHolidayDate,
      isCustom: true,
    }

    setEditedHolidays((prev) => [...prev, newHoliday].sort((a, b) => a.date.localeCompare(b.date)))
    setNewHolidayName('')
    setNewHolidayDate('')
  }

  const handleSave = () => {
    onSave(editedHolidays)
    onClose()
  }

  const handleResetToDefaults = () => {
    const defaultHolidays = [
      ...getDefaultHolidays(startYear),
      ...getDefaultHolidays(endYear),
    ]
    const filtered = defaultHolidays.filter((h) => {
      if (!academicYearStart || !academicYearEnd) return true
      return h.date >= academicYearStart && h.date <= academicYearEnd
    })
    setEditedHolidays(filtered)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold">Edit Holidays</h2>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Add new holiday form */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Add Custom Holiday</h3>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                placeholder="Holiday name"
                value={newHolidayName}
                onChange={(e) => setNewHolidayName(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="date"
                value={newHolidayDate}
                onChange={(e) => setNewHolidayDate(e.target.value)}
                min={academicYearStart}
                max={academicYearEnd}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleAddHoliday}
                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add
              </button>
            </div>
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>

          {/* Holidays list */}
          <div className="space-y-2">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">
                Holidays ({editedHolidays.length})
              </h3>
              <button
                onClick={handleResetToDefaults}
                className="text-xs text-blue-600 hover:underline"
              >
                Reset to defaults
              </button>
            </div>

            {editedHolidays.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No holidays configured</p>
            ) : (
              editedHolidays.map((holiday) => (
                <div
                  key={holiday.id}
                  className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 truncate">
                        {holiday.name}
                      </span>
                      {holiday.isCustom && (
                        <span className="px-1.5 py-0.5 text-[10px] font-medium bg-blue-100 text-blue-700 rounded">
                          Custom
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {format(parseISO(holiday.date), 'EEEE, MMMM d, yyyy')}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemoveHoliday(holiday.id)}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Remove holiday"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  )
}
