'use client'

import { useState, useMemo } from 'react'
import { Search, ChevronDown } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { get } from '@/lib/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'
import { FacultyWeeklyEditor } from '@/components/FacultyWeeklyEditor'
import type { Person } from '@/types/api'
import type { FacultyRole } from '@/types/faculty-activity'

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
    queryFn: () => get('/people?type=faculty&limit=100'),
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
        <FacultyWeeklyEditor
          personId={selectedFaculty.id}
          personName={selectedFaculty.name}
          facultyRole={selectedFaculty.facultyRole as FacultyRole | null}
          readOnly={!canEdit}
        />
      )}
    </div>
  )
}
