'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { format, addDays, parseISO, isToday, isTomorrow, isWithinInterval } from 'date-fns'
import { Calendar, ChevronRight, Clock, Sun, Moon } from 'lucide-react'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/contexts/AuthContext'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import type { Assignment, Block, Person, RotationTemplate } from '@/types/api'
import { EmptyState } from '@/components/EmptyState'

const activityColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-700 border-blue-200',
  inpatient: 'bg-purple-100 text-purple-700 border-purple-200',
  procedure: 'bg-red-100 text-red-700 border-red-200',
  conference: 'bg-gray-100 text-gray-700 border-gray-200',
  elective: 'bg-green-100 text-green-700 border-green-200',
  call: 'bg-orange-100 text-orange-700 border-orange-200',
  off: 'bg-white text-gray-400 border-gray-200',
  leave: 'bg-amber-100 text-amber-700 border-amber-200',
  default: 'bg-slate-100 text-slate-700 border-slate-200',
}

function getActivityColor(activity: string | undefined): string {
  if (!activity) return activityColors.default
  const lower = activity.toLowerCase()
  for (const [key, color] of Object.entries(activityColors)) {
    if (lower.includes(key)) return color
  }
  return activityColors.default
}

interface UpcomingAssignment {
  id: string
  date: string
  timeOfDay: 'AM' | 'PM'
  activity: string
  abbreviation: string
  notes?: string
}

interface UpcomingAssignmentsPreviewProps {
  /** Number of days to look ahead (default: 7) */
  daysAhead?: number
  /** Maximum number of assignments to show */
  maxItems?: number
  /** Additional CSS classes */
  className?: string
}

/**
 * Upcoming Assignments Preview Component
 *
 * Shows the next few scheduled assignments for the current user.
 * Provides quick visibility into upcoming work without navigating to full schedule.
 */
export function UpcomingAssignmentsPreview({
  daysAhead = 7,
  maxItems = 6,
  className = '',
}: UpcomingAssignmentsPreviewProps) {
  const { user } = useAuth()

  const today = new Date()
  const endDate = addDays(today, daysAhead)
  const startDateStr = format(today, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch data
  const { data: blocksData, isLoading: blocksLoading } = useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Block>>(`/blocks?start_date=${startDateStr}&end_date=${endDateStr}`),
    staleTime: 5 * 60 * 1000,
  })

  const { data: assignmentsData, isLoading: assignmentsLoading } = useQuery<ListResponse<Assignment>>({
    queryKey: ['assignments', startDateStr, endDateStr],
    queryFn: () => get<ListResponse<Assignment>>(`/assignments?start_date=${startDateStr}&end_date=${endDateStr}`),
    staleTime: 60 * 1000,
  })

  const { data: peopleData, isLoading: peopleLoading } = usePeople()
  const { data: templatesData, isLoading: templatesLoading } = useRotationTemplates()

  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading

  // Find current user's person record
  const currentPerson = useMemo<Person | null>(() => {
    if (!user || !peopleData?.items) return null
    return peopleData.items.find(
      (person) => person.email === user.email || person.id === user.id
    ) || null
  }, [user, peopleData])

  // Transform to upcoming assignments
  const upcomingAssignments = useMemo<UpcomingAssignment[]>(() => {
    if (!currentPerson || !blocksData?.items || !assignmentsData?.items) {
      return []
    }

    const blockMap = new Map<string, Block>()
    blocksData.items.forEach((block) => blockMap.set(block.id, block))

    const templateMap = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((template) => templateMap.set(template.id, template))

    const assignments: UpcomingAssignment[] = []

    assignmentsData.items
      .filter((assignment) => assignment.person_id === currentPerson.id)
      .forEach((assignment) => {
        const block = blockMap.get(assignment.block_id)
        if (!block) return

        const blockDate = parseISO(block.date)
        // Only include future/today assignments
        if (blockDate < today && !isToday(blockDate)) return

        const template = assignment.rotation_template_id
          ? templateMap.get(assignment.rotation_template_id)
          : null

        assignments.push({
          id: assignment.id,
          date: block.date,
          timeOfDay: block.time_of_day as 'AM' | 'PM',
          activity: template?.activity_type || 'default',
          abbreviation:
            assignment.activity_override ||
            template?.abbreviation ||
            template?.name?.substring(0, 3).toUpperCase() ||
            '???',
          notes: assignment.notes,
        })
      })

    return assignments
      .sort((a, b) => {
        if (a.date !== b.date) return a.date.localeCompare(b.date)
        return a.timeOfDay === 'AM' ? -1 : 1
      })
      .slice(0, maxItems)
  }, [currentPerson, blocksData, assignmentsData, templatesData, today, maxItems])

  const getDateLabel = (dateStr: string): string => {
    const date = parseISO(dateStr)
    if (isToday(date)) return 'Today'
    if (isTomorrow(date)) return 'Tomorrow'
    return format(date, 'EEE, MMM d')
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.2 }}
      className={`glass-panel p-6 ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Coming Up</h3>
        <Calendar className="w-5 h-5 text-blue-600" />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-3">
              <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      ) : !currentPerson ? (
        <EmptyState
          icon={Calendar}
          title="Profile not linked"
          description="Your account isn't linked to a person profile"
        />
      ) : upcomingAssignments.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No upcoming assignments"
          description={`Nothing scheduled for the next ${daysAhead} days`}
        />
      ) : (
        <div className="space-y-2">
          {upcomingAssignments.map((assignment, idx) => {
            const dateLabel = getDateLabel(assignment.date)
            const showDateHeader =
              idx === 0 ||
              upcomingAssignments[idx - 1].date !== assignment.date

            return (
              <div key={assignment.id}>
                {showDateHeader && (
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mt-3 mb-1 first:mt-0">
                    {dateLabel}
                  </div>
                )}
                <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                  <div
                    className={`
                      w-10 h-10 rounded-lg border flex items-center justify-center
                      ${getActivityColor(assignment.activity)}
                    `}
                  >
                    <span className="text-xs font-bold">{assignment.abbreviation}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 capitalize truncate">
                      {assignment.activity}
                    </p>
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      {assignment.timeOfDay === 'AM' ? (
                        <Sun className="w-3 h-3" />
                      ) : (
                        <Moon className="w-3 h-3" />
                      )}
                      <span>{assignment.timeOfDay}</span>
                      {assignment.notes && (
                        <>
                          <span className="text-gray-300">•</span>
                          <span className="truncate">{assignment.notes}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-200/50">
        <Link
          href="/my-schedule"
          className="flex items-center justify-between text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          <span>View Full Schedule</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>
    </motion.div>
  )
}
