'use client'

import { useMemo } from 'react'
import { format, parseISO, startOfDay, isWithinInterval } from 'date-fns'
import { Phone, Mail, AlertCircle, Calendar, Users } from 'lucide-react'
import { useAssignments, usePeople, useRotationTemplates } from '@/lib/hooks'
import type { Person, Assignment } from '@/types/api'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { EmptyState } from '@/components/EmptyState'

export interface CallRosterProps {
  startDate: Date
  endDate: Date
  showOnlyOnCall?: boolean
}

interface OnCallAssignment {
  id: string
  date: string
  dateObj: Date
  time_of_day: 'AM' | 'PM'
  person: Person
  role: 'primary' | 'supervising' | 'backup'
  activity: string
  abbreviation: string
  notes?: string | null
}

// Role color coding based on seniority
// Red = Attending, Blue = Senior, Green = Intern
function getSeniorityColor(person: Person): { bg: string; text: string; border: string } {
  if (person.type === 'faculty') {
    // Attending - Red
    return {
      bg: 'bg-red-50',
      text: 'text-red-700',
      border: 'border-red-200',
    }
  }

  if (person.type === 'resident') {
    const pgyLevel = person.pgy_level || 1

    if (pgyLevel === 1) {
      // Intern - Green
      return {
        bg: 'bg-green-50',
        text: 'text-green-700',
        border: 'border-green-200',
      }
    } else {
      // Senior Resident - Blue
      return {
        bg: 'bg-blue-50',
        text: 'text-blue-700',
        border: 'border-blue-200',
      }
    }
  }

  // Default
  return {
    bg: 'bg-gray-50',
    text: 'text-gray-700',
    border: 'border-gray-200',
  }
}

function getRoleLabel(person: Person): string {
  if (person.type === 'faculty') {
    return 'Attending'
  }

  if (person.type === 'resident') {
    const pgyLevel = person.pgy_level || 1

    if (pgyLevel === 1) {
      return 'Intern'
    } else if (pgyLevel === 2 || pgyLevel === 3) {
      return `PGY-${pgyLevel}`
    } else {
      return `Senior PGY-${pgyLevel}`
    }
  }

  return 'Unknown'
}

export function CallRoster({ startDate, endDate, showOnlyOnCall = true }: CallRosterProps) {
  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch data
  const { data: assignmentsData, isLoading: assignmentsLoading, error: assignmentsError } = useAssignments({
    start_date: startDateStr,
    end_date: endDateStr,
  })

  const { data: peopleData, isLoading: peopleLoading } = usePeople()
  const { data: templatesData, isLoading: templatesLoading } = useRotationTemplates()

  const isLoading = assignmentsLoading || peopleLoading || templatesLoading

  // Build lookup maps
  const peopleMap = useMemo(() => {
    const map = new Map<string, Person>()
    peopleData?.items?.forEach((person) => {
      map.set(person.id, person)
    })
    return map
  }, [peopleData])

  const templateMap = useMemo(() => {
    const map = new Map<string, { name: string; abbreviation: string; activity_type: string }>()
    templatesData?.items?.forEach((template) => {
      map.set(template.id, {
        name: template.name,
        abbreviation: template.display_abbreviation || template.abbreviation || template.name.substring(0, 3).toUpperCase(),
        activity_type: template.activity_type,
      })
    })
    return map
  }, [templatesData])

  // Process and filter assignments
  const onCallAssignments = useMemo((): OnCallAssignment[] => {
    if (!assignmentsData?.items || !peopleMap.size) {
      return []
    }

    const assignments = assignmentsData.items
      .map((assignment): OnCallAssignment | null => {
        const person = peopleMap.get(assignment.person_id)
        if (!person) return null

        const template = assignment.rotation_template_id
          ? templateMap.get(assignment.rotation_template_id)
          : null

        const activity = assignment.activity_override || template?.activity_type || 'Assignment'

        // For now, use created_at as a proxy for date
        // In production, this would come from block data
        const dateStr = assignment.created_at.split('T')[0]
        const dateObj = parseISO(dateStr)

        // Filter by date range
        if (!isWithinInterval(dateObj, { start: startOfDay(startDate), end: startOfDay(endDate) })) {
          return null
        }

        // If showOnlyOnCall is true, filter for call-related activities
        if (showOnlyOnCall) {
          const activityLower = activity.toLowerCase()
          // Include assignments with 'call', 'on-call', or 'oncall' in the activity name
          // or primary role assignments (assuming primary role indicates on-call duty)
          if (!activityLower.includes('call') && !activityLower.includes('on-call') && assignment.role !== 'primary') {
            return null
          }
        }

        return {
          id: assignment.id,
          date: dateStr,
          dateObj,
          time_of_day: 'AM' as const, // Would come from block data
          person,
          role: assignment.role,
          activity,
          abbreviation: template?.abbreviation || 'CALL',
          notes: assignment.notes,
        }
      })
      .filter((a): a is OnCallAssignment => a !== null)
      .sort((a, b) => {
        // Sort by date first
        const dateCompare = a.dateObj.getTime() - b.dateObj.getTime()
        if (dateCompare !== 0) return dateCompare

        // Then by seniority (faculty > senior > intern)
        const aOrder = a.person.type === 'faculty' ? 0 : (a.person.pgy_level || 1)
        const bOrder = b.person.type === 'faculty' ? 0 : (b.person.pgy_level || 1)
        return aOrder - bOrder
      })

    return assignments
  }, [assignmentsData, peopleMap, templateMap, startDate, endDate, showOnlyOnCall])

  // Group assignments by date for easier viewing
  const assignmentsByDate = useMemo(() => {
    const grouped = new Map<string, OnCallAssignment[]>()

    onCallAssignments.forEach((assignment) => {
      const existing = grouped.get(assignment.date) || []
      existing.push(assignment)
      grouped.set(assignment.date, existing)
    })

    return Array.from(grouped.entries()).sort((a, b) =>
      parseISO(a[0]).getTime() - parseISO(b[0]).getTime()
    )
  }, [onCallAssignments])

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex flex-col items-center justify-center gap-4">
          <LoadingSpinner size="lg" />
          <p className="text-gray-500">Loading call roster...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (assignmentsError) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900 mb-1">Error Loading Call Roster</h3>
            <p className="text-sm text-red-700">
              {assignmentsError.message || 'Failed to load on-call assignments'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  // Empty state
  if (onCallAssignments.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <EmptyState
          icon={Users}
          title="No On-Call Assignments"
          description={`No on-call assignments found between ${format(startDate, 'MMM d, yyyy')} and ${format(endDate, 'MMM d, yyyy')}`}
        />
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
              <Phone className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">On-Call Roster</h2>
              <p className="text-sm text-gray-500">
                {format(startDate, 'MMM d, yyyy')} - {format(endDate, 'MMM d, yyyy')}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600">Attending</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-gray-600">Senior</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-600">Intern</span>
            </div>
          </div>
        </div>
      </div>

      {/* Call Roster Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Level
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Activity
              </th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Notes
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {assignmentsByDate.map(([date, assignments]) => {
              const dateObj = parseISO(date)
              const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6

              return assignments.map((assignment, idx) => {
                const colors = getSeniorityColor(assignment.person)
                const isFirstForDate = idx === 0

                return (
                  <tr
                    key={assignment.id}
                    className={`
                      transition-colors hover:bg-gray-50
                      ${isWeekend ? 'bg-gray-50/50' : ''}
                    `}
                  >
                    {/* Date (only show for first row of each date) */}
                    <td className="px-6 py-4">
                      {isFirstForDate && (
                        <div className="flex flex-col">
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-900">
                              {format(dateObj, 'MMM d')}
                            </span>
                          </div>
                          <span className={`text-xs ${isWeekend ? 'text-gray-500 font-medium' : 'text-gray-400'}`}>
                            {format(dateObj, 'EEEE')}
                          </span>
                        </div>
                      )}
                    </td>

                    {/* Person Name */}
                    <td className="px-6 py-4">
                      <div
                        className={`
                          inline-flex items-center px-3 py-1.5 rounded-lg font-medium border
                          ${colors.bg} ${colors.text} ${colors.border}
                        `}
                      >
                        {assignment.person.name}
                      </div>
                    </td>

                    {/* Level */}
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-700 font-medium">
                        {getRoleLabel(assignment.person)}
                      </span>
                    </td>

                    {/* Contact Info */}
                    <td className="px-6 py-4">
                      {assignment.person.email ? (
                        <a
                          href={`mailto:${assignment.person.email}`}
                          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          <Mail className="w-4 h-4" />
                          {assignment.person.email}
                        </a>
                      ) : (
                        <span className="text-sm text-gray-400 italic">No email</span>
                      )}
                    </td>

                    {/* Activity */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-call-light text-call-dark">
                          {assignment.abbreviation}
                        </span>
                        <span className="text-xs text-gray-500">
                          {assignment.role === 'backup' ? '(Backup)' : assignment.role === 'supervising' ? '(Supervising)' : ''}
                        </span>
                      </div>
                    </td>

                    {/* Notes */}
                    <td className="px-6 py-4">
                      {assignment.notes && (
                        <span className="text-sm text-gray-600">{assignment.notes}</span>
                      )}
                    </td>
                  </tr>
                )
              })
            })}
          </tbody>
        </table>
      </div>

      {/* Footer with summary */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            <span>
              {onCallAssignments.length} on-call assignment{onCallAssignments.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Quick reference for nursing staff to identify who to page
          </div>
        </div>
      </div>
    </div>
  )
}
