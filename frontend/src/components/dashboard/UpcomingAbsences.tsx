'use client'

import Link from 'next/link'
import { format, addDays, parseISO, isWithinInterval } from 'date-fns'
import { CalendarOff, User } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAbsences, usePeople } from '@/lib/hooks'
import { EmptyState } from '@/components/EmptyState'

const absenceTypeBadgeColors: Record<string, string> = {
  // Planned leave
  vacation: 'bg-blue-100 text-blue-800',
  conference: 'bg-green-100 text-green-800',
  // Medical
  sick: 'bg-red-100 text-red-800',
  medical: 'bg-red-100 text-red-800',
  convalescent: 'bg-red-200 text-red-900',
  maternity_paternity: 'bg-pink-100 text-pink-800',
  // Emergency (blocking - Hawaii reality)
  family_emergency: 'bg-orange-100 text-orange-800',
  emergency_leave: 'bg-orange-200 text-orange-900',
  bereavement: 'bg-gray-200 text-gray-800',
  // Military
  deployment: 'bg-purple-100 text-purple-800',
  tdy: 'bg-indigo-100 text-indigo-800',
}

const absenceTypeLabels: Record<string, string> = {
  // Planned leave
  vacation: 'Vacation',
  conference: 'Conference',
  // Medical
  sick: 'Sick',
  medical: 'Medical',
  convalescent: 'Convalescent',
  maternity_paternity: 'Parental Leave',
  // Emergency (blocking - Hawaii reality)
  family_emergency: 'Family Emergency',
  emergency_leave: 'Emergency',
  bereavement: 'Bereavement',
  // Military
  deployment: 'Deployment',
  tdy: 'TDY',
}

export function UpcomingAbsences() {
  const { data: absences, isLoading: absencesLoading } = useAbsences()
  const { data: people, isLoading: peopleLoading } = usePeople()

  const isLoading = absencesLoading || peopleLoading

  const today = new Date()
  const nextWeek = addDays(today, 7)

  // Filter absences in the next 7 days
  const upcomingAbsences = absences?.items
    ?.filter((absence) => {
      const startDate = parseISO(absence.start_date)
      const endDate = parseISO(absence.end_date)

      // Check if absence overlaps with the next 7 days
      return (
        isWithinInterval(today, { start: startDate, end: endDate }) ||
        isWithinInterval(startDate, { start: today, end: nextWeek }) ||
        isWithinInterval(endDate, { start: today, end: nextWeek })
      )
    })
    .slice(0, 5) ?? []

  const getPersonName = (personId: string) => {
    return people?.items?.find((p) => p.id === personId)?.name ?? 'Unknown'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.3 }}
      className="glass-panel p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Upcoming Absences (7 days)</h3>
        <CalendarOff className="w-5 h-5 text-amber-600" />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse flex items-center gap-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      ) : upcomingAbsences.length === 0 ? (
        <EmptyState
          icon={CalendarOff}
          title="No upcoming absences"
          description="No absences scheduled for the next 7 days"
        />
      ) : (
        <div className="space-y-3">
          {upcomingAbsences.map((absence) => (
            <div key={absence.id} className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {getPersonName(absence.person_id)}
                </p>
                <p className="text-xs text-gray-500">
                  {format(parseISO(absence.start_date), 'MMM d')} -{' '}
                  {format(parseISO(absence.end_date), 'MMM d')}
                </p>
              </div>
              <span
                className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
                  absenceTypeBadgeColors[absence.absence_type] ?? 'bg-gray-100 text-gray-800'
                }`}
              >
                {absenceTypeLabels[absence.absence_type] ?? absence.absence_type}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-200/50">
        <Link
          href="/absences"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View All Absences &rarr;
        </Link>
      </div>
    </motion.div>
  )
}
