'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { format, parseISO, isToday, startOfDay, addMonths } from 'date-fns'
import { Calendar, ChevronRight, Clock, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useAssignments, usePeople, useRotationTemplates } from '@/lib/hooks'
import { EmptyState } from '@/components/EmptyState'

// Number of upcoming assignments to show
const UPCOMING_COUNT = 5

// Activity type to color mapping
const activityColors: Record<string, string> = {
  clinic: 'bg-clinic-light text-clinic-dark',
  inpatient: 'bg-inpatient-light text-inpatient-dark',
  call: 'bg-call-light text-call-dark',
  leave: 'bg-leave-light text-leave-dark',
  conference: 'bg-gray-100 text-gray-700',
  default: 'bg-blue-50 text-blue-700',
}

function getActivityColor(activity: string): string {
  const activityLower = activity.toLowerCase()

  for (const [key, color] of Object.entries(activityColors)) {
    if (activityLower.includes(key)) {
      return color
    }
  }

  return activityColors.default
}

interface UpcomingAssignment {
  id: string
  date: string
  dateObj: Date
  time_of_day: 'AM' | 'PM'
  activity: string
  abbreviation: string
}

export function MyScheduleWidget() {
  const { user } = useAuth()

  // Get date range for fetching (today to 3 months from now)
  const today = startOfDay(new Date())
  const endDate = addMonths(today, 3)
  const startDateStr = format(today, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch data
  const { data: peopleData, isLoading: peopleLoading } = usePeople()
  const { data: templatesData, isLoading: templatesLoading } = useRotationTemplates()

  // Find the person record matching the logged-in user
  const currentPerson = useMemo(() => {
    if (!user || !peopleData?.items) return null

    // Match by email or username
    return peopleData.items.find(
      (p) => p.email === user.email || p.name.toLowerCase() === user.username.toLowerCase()
    ) ?? null
  }, [user, peopleData])

  // Fetch assignments for the current person
  const { data: assignmentsData, isLoading: assignmentsLoading } = useAssignments(
    currentPerson ? {
      person_id: currentPerson.id,
      start_date: startDateStr,
      end_date: endDateStr,
    } : undefined,
    { enabled: !!currentPerson }
  )

  const isLoading = peopleLoading || templatesLoading || assignmentsLoading

  // Build rotation template lookup
  const templateMap = useMemo(() => {
    const map = new Map<string, { name: string; abbreviation: string; activity_type: string }>()
    templatesData?.items?.forEach((t) => {
      map.set(t.id, {
        name: t.name,
        abbreviation: t.abbreviation || t.name.substring(0, 3).toUpperCase(),
        activity_type: t.activity_type,
      })
    })
    return map
  }, [templatesData])

  // Transform and filter assignments to upcoming only
  const upcomingAssignments = useMemo<UpcomingAssignment[]>(() => {
    if (!assignmentsData?.items) return []

    const now = startOfDay(new Date())

    // We need block data to get dates - for now assume block_id format includes date
    // In a real implementation, you'd have a blocks endpoint or embedded block data
    // For this component, we'll work with what we have and show a simplified view

    const assignments = assignmentsData.items
      .map((assignment) => {
        const template = assignment.rotation_template_id
          ? templateMap.get(assignment.rotation_template_id)
          : null

        // Extract date from block_id if possible, or use created_at as fallback
        // In production, the API should return block data with date/time_of_day
        const dateStr = assignment.created_at.split('T')[0]
        const dateObj = parseISO(dateStr)

        return {
          id: assignment.id,
          date: dateStr,
          dateObj,
          time_of_day: 'AM' as const, // Default - would come from block data
          activity: assignment.activity_override || template?.activity_type || 'Assignment',
          abbreviation: template?.abbreviation || 'ASN',
        }
      })
      .filter((a) => a.dateObj >= now)
      .sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime())
      .slice(0, UPCOMING_COUNT)

    return assignments
  }, [assignmentsData, templateMap])

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">My Schedule</h3>
          <User className="w-5 h-5 text-blue-600" />
        </div>
        <div className="space-y-3">
          <div className="animate-pulse h-12 bg-gray-100 rounded-md"></div>
          <div className="animate-pulse h-12 bg-gray-100 rounded-md"></div>
          <div className="animate-pulse h-12 bg-gray-100 rounded-md"></div>
        </div>
      </div>
    )
  }

  // Not logged in or no matching person
  if (!user || !currentPerson) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">My Schedule</h3>
          <User className="w-5 h-5 text-gray-400" />
        </div>
        <div className="text-center py-6 text-gray-500">
          <User className="w-10 h-10 mx-auto mb-2 text-gray-300" />
          <p className="text-sm">Log in to see your schedule</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">My Schedule</h3>
        <Calendar className="w-5 h-5 text-blue-600" />
      </div>

      {/* Content */}
      {upcomingAssignments.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No upcoming assignments"
          description="You don't have any scheduled assignments"
        />
      ) : (
        <div className="space-y-2">
          {upcomingAssignments.map((assignment) => {
            const isTodayAssignment = isToday(assignment.dateObj)

            return (
              <div
                key={assignment.id}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-colors
                  ${isTodayAssignment ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 hover:bg-gray-100'}
                `}
              >
                {/* Date */}
                <div className="flex-shrink-0 w-14 text-center">
                  <div className={`text-xs font-medium ${isTodayAssignment ? 'text-blue-600' : 'text-gray-500'}`}>
                    {isTodayAssignment ? 'Today' : format(assignment.dateObj, 'EEE')}
                  </div>
                  <div className={`text-lg font-bold ${isTodayAssignment ? 'text-blue-700' : 'text-gray-900'}`}>
                    {format(assignment.dateObj, 'd')}
                  </div>
                  <div className={`text-xs ${isTodayAssignment ? 'text-blue-500' : 'text-gray-400'}`}>
                    {format(assignment.dateObj, 'MMM')}
                  </div>
                </div>

                {/* Divider */}
                <div className={`w-px h-12 ${isTodayAssignment ? 'bg-blue-200' : 'bg-gray-200'}`} />

                {/* Assignment Details */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`
                        inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
                        ${getActivityColor(assignment.activity)}
                      `}
                    >
                      {assignment.abbreviation}
                    </span>
                    <span className="text-xs text-gray-500">{assignment.time_of_day}</span>
                  </div>
                  <div className="text-sm text-gray-700 mt-0.5 truncate">
                    {assignment.activity}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Footer Link */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <Link
          href={currentPerson ? `/schedule/${currentPerson.id}` : '/schedule?person=me'}
          className="flex items-center justify-between text-sm text-blue-600 hover:text-blue-800 font-medium group"
        >
          <span>View Full Schedule</span>
          <ChevronRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>
    </div>
  )
}
