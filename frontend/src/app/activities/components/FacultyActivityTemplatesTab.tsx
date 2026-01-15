'use client'

import { useState, useMemo } from 'react'
import { Search, ChevronDown } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { get } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import type { Person } from '@/types/api'

interface FacultyActivityTemplatesTabProps {
  canEdit: boolean
  canDelete: boolean
}

interface ListResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

/**
 * FacultyActivityTemplatesTab - Displays faculty weekly activity templates
 *
 * Faculty activity templates define default weekly patterns for faculty members.
 * Each faculty member has a 7-day by 2-slot (AM/PM) grid showing their typical activities.
 */
export function FacultyActivityTemplatesTab({
  canEdit,
  canDelete: _canDelete,
}: FacultyActivityTemplatesTabProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFacultyId, setSelectedFacultyId] = useState<string | null>(
    null
  )

  // Fetch faculty members
  const {
    data: peopleData,
    isLoading,
    error,
  } = useQuery<ListResponse<Person>>({
    queryKey: ['people', { type: 'faculty' }],
    queryFn: () => get('/api/people?type=faculty&limit=100'),
  })

  // Memoize faculty array to prevent dependency warnings
  const faculty = useMemo(
    () => peopleData?.items ?? [],
    [peopleData?.items]
  )

  // Filter faculty
  const filteredFaculty = useMemo(() => {
    if (!searchQuery) return faculty
    const query = searchQuery.toLowerCase()
    return faculty.filter(
      (f) =>
        f.name.toLowerCase().includes(query) ||
        f.email?.toLowerCase().includes(query)
    )
  }, [faculty, searchQuery])

  // Selected faculty
  const selectedFaculty = useMemo(() => {
    if (!selectedFacultyId) return null
    return faculty.find((f) => f.id === selectedFacultyId) ?? null
  }, [faculty, selectedFacultyId])

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return <ErrorAlert message="Failed to load faculty data" />
  }

  return (
    <div className="space-y-6">
      {/* Faculty selector */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search faculty..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Faculty dropdown */}
        <div className="relative">
          <select
            value={selectedFacultyId ?? ''}
            onChange={(e) => setSelectedFacultyId(e.target.value || null)}
            className="appearance-none pl-4 pr-10 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white min-w-[200px]"
          >
            <option value="">Select Faculty</option>
            {filteredFaculty.map((f) => (
              <option key={f.id} value={f.id}>
                {f.name}
              </option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        </div>
      </div>

      {/* Content */}
      {!selectedFaculty ? (
        <EmptyState
          title="Select a faculty member"
          description="Choose a faculty member to view and edit their weekly activity template"
        />
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {selectedFaculty.name}&apos;s Weekly Template
          </h3>

          {/* Weekly grid placeholder */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">
                    Slot
                  </th>
                  {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map(
                    (day) => (
                      <th
                        key={day}
                        className="px-4 py-2 text-center text-sm font-medium text-gray-600"
                      >
                        {day}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {['AM', 'PM'].map((slot) => (
                  <tr key={slot} className="border-t border-gray-200">
                    <td className="px-4 py-3 text-sm font-medium text-gray-600">
                      {slot}
                    </td>
                    {Array.from({ length: 7 }).map((_, dayIndex) => (
                      <td
                        key={dayIndex}
                        className="px-4 py-3 text-center border-l border-gray-200"
                      >
                        <button
                          type="button"
                          disabled={!canEdit}
                          className="w-full px-2 py-1 text-sm text-gray-500 bg-gray-50 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {canEdit ? 'Click to set' : '—'}
                        </button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-4 text-sm text-gray-500">
            Note: Full template editing is available in the Faculty Weekly
            Editor component.
          </p>
        </div>
      )}
    </div>
  )
}
