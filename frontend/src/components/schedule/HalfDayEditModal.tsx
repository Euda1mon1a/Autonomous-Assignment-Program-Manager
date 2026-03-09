'use client'

import { useState } from 'react'
import { useActivitiesByCategory } from '@/hooks/useActivities'
import { useUpdateHalfDayAssignment } from '@/hooks/useHalfDayAssignments'
import type { HalfDayAssignment } from '@/hooks/useHalfDayAssignments'
import { ACTIVITY_CATEGORY_LABELS, type ActivityCategory } from '@/types/activity'

interface HalfDayEditModalProps {
  assignment: HalfDayAssignment
  isOpen: boolean
  onClose: () => void
}

export function HalfDayEditModal({ assignment, isOpen, onClose }: HalfDayEditModalProps) {
  const [selectedCode, setSelectedCode] = useState(
    assignment.activityCode ?? ''
  )
  const [reason, setReason] = useState('')
  const { data: grouped } = useActivitiesByCategory()
  const mutation = useUpdateHalfDayAssignment()

  if (!isOpen) return null

  const canSave = !!assignment.id

  const handleSave = () => {
    if (!selectedCode || !canSave) return
    mutation.mutate(
      {
        id: assignment.id,
        data: {
          activityCode: selectedCode,
          overrideReason: reason || null,
        },
      },
      { onSuccess: () => onClose() }
    )
  }

  const categoryOrder: ActivityCategory[] = [
    'clinical',
    'educational',
    'administrative',
    'time_off',
  ]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="Edit half-day assignment"
      tabIndex={-1}
      onClick={onClose}
      onKeyDown={(e) => { if (e.key === 'Escape') onClose() }}
    >
      <div
        role="document"
        tabIndex={-1}
        className="bg-white rounded-lg shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Edit Assignment</h3>
          <p className="text-sm text-gray-500 mt-1">
            {assignment.personName} &middot; {assignment.date} {assignment.timeOfDay}
          </p>
          {assignment.source === 'preload' && (
            <p className="text-xs text-amber-600 mt-1">
              This is a preloaded assignment. Overriding will mark it as manual.
            </p>
          )}
        </div>

        {/* Activity Dropdown */}
        <label htmlFor="activity-select" className="block text-sm font-medium text-gray-700 mb-1">
          Activity
        </label>
        <select
          id="activity-select"
          value={selectedCode}
          onChange={(e) => setSelectedCode(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        >
          <option value="" disabled>Select activity...</option>
          {grouped && categoryOrder.map((cat) => {
            const activities = grouped[cat]
            if (!activities || activities.length === 0) return null
            return (
              <optgroup key={cat} label={ACTIVITY_CATEGORY_LABELS[cat]}>
                {activities.map((a) => (
                  <option key={a.id} value={a.code}>
                    {a.displayAbbreviation ? `${a.displayAbbreviation} — ${a.name}` : a.name}
                  </option>
                ))}
              </optgroup>
            )
          })}
        </select>

        {/* Override Reason */}
        <label htmlFor="override-reason" className="block text-sm font-medium text-gray-700 mt-4 mb-1">
          Reason (optional)
        </label>
        <input
          id="override-reason"
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="e.g., Sick call coverage"
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />

        {!canSave && (
          <p className="text-sm text-amber-600 mt-2">
            This slot has no half-day record yet. Generate the schedule first to enable editing.
          </p>
        )}

        {mutation.isError && (
          <p className="text-sm text-red-600 mt-2">
            {mutation.error?.message || 'Failed to update assignment'}
          </p>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!canSave || !selectedCode || mutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
