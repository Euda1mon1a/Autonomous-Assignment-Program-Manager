'use client'

import Link from 'next/link'
import { useMemo } from 'react'
import { format, addDays, parseISO, isWithinInterval, differenceInDays } from 'date-fns'
import { CalendarOff, User, AlertTriangle, Users } from 'lucide-react'
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

// Impact levels based on concurrent absences and roles
type ImpactLevel = 'low' | 'medium' | 'high' | 'critical'

const impactColors: Record<ImpactLevel, string> = {
  low: 'bg-green-100 text-green-700 border-green-200',
  medium: 'bg-amber-100 text-amber-700 border-amber-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
}

interface AbsenceWithImpact {
  id: string
  person_id: string
  person_name: string
  person_role?: string
  absence_type: string
  start_date: string
  end_date: string
  days: number
  impact: ImpactLevel
  concurrent_count: number
}

export function UpcomingAbsences() {
  const { data: absences, isLoading: absencesLoading } = useAbsences()
  const { data: people, isLoading: peopleLoading } = usePeople()

  const isLoading = absencesLoading || peopleLoading

  const today = new Date()
  const nextWeek = addDays(today, 7)

  // Calculate absences with coverage impact
  const absencesWithImpact = useMemo<AbsenceWithImpact[]>(() => {
    if (!absences?.items || !people?.items) return []

    const upcomingAbsences = absences.items.filter((absence) => {
      // Guard against missing dates
      if (!absence.startDate || !absence.endDate) return false

      const startDate = parseISO(absence.startDate)
      const endDate = parseISO(absence.endDate)

      return (
        isWithinInterval(today, { start: startDate, end: endDate }) ||
        isWithinInterval(startDate, { start: today, end: nextWeek }) ||
        isWithinInterval(endDate, { start: today, end: nextWeek })
      )
    })

    // Calculate concurrent absences for each date
    const dateAbsenceCounts = new Map<string, number>()
    upcomingAbsences.forEach((absence) => {
      const start = parseISO(absence.startDate)
      const end = parseISO(absence.endDate)
      let current = start

      while (current <= end && current <= nextWeek) {
        if (current >= today) {
          const dateKey = format(current, 'yyyy-MM-dd')
          dateAbsenceCounts.set(dateKey, (dateAbsenceCounts.get(dateKey) || 0) + 1)
        }
        current = addDays(current, 1)
      }
    })

    return upcomingAbsences
      .map((absence) => {
        const person = people.items?.find((p) => p.id === absence.personId)
        const startDate = parseISO(absence.startDate)
        const endDate = parseISO(absence.endDate)
        const days = differenceInDays(endDate, startDate) + 1

        // Find max concurrent absences during this person's absence
        let maxConcurrent = 0
        let current = startDate
        while (current <= endDate) {
          const dateKey = format(current, 'yyyy-MM-dd')
          const count = dateAbsenceCounts.get(dateKey) || 0
          maxConcurrent = Math.max(maxConcurrent, count)
          current = addDays(current, 1)
        }

        // Calculate impact based on concurrent absences and type
        const personType = person?.type?.toLowerCase() || ''
        const isCriticalRole = personType === 'faculty'
        let impact: ImpactLevel = 'low'

        if (maxConcurrent >= 4 || (maxConcurrent >= 2 && isCriticalRole)) {
          impact = 'critical'
        } else if (maxConcurrent >= 3 || (maxConcurrent >= 2 && days >= 5)) {
          impact = 'high'
        } else if (maxConcurrent >= 2 || days >= 5) {
          impact = 'medium'
        }

        return {
          id: absence.id,
          person_id: absence.personId,
          person_name: person?.name ?? 'Unknown',
          person_role: person?.type,
          absence_type: absence.absenceType,
          start_date: absence.startDate,
          end_date: absence.endDate,
          days,
          impact,
          concurrent_count: maxConcurrent,
        }
      })
      .sort((a, b) => {
        // Sort by impact (critical first) then by date
        const impactOrder = { critical: 0, high: 1, medium: 2, low: 3 }
        if (impactOrder[a.impact] !== impactOrder[b.impact]) {
          return impactOrder[a.impact] - impactOrder[b.impact]
        }
        return a.startDate.localeCompare(b.startDate)
      })
      .slice(0, 5)
  }, [absences, people, today, nextWeek])

  // Summary stats
  const stats = useMemo(() => {
    const criticalCount = absencesWithImpact.filter((a) => a.impact === 'critical').length
    const highCount = absencesWithImpact.filter((a) => a.impact === 'high').length
    return { criticalCount, highCount, total: absencesWithImpact.length }
  }, [absencesWithImpact])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.3 }}
      className="glass-panel p-6"
      role="region"
      aria-labelledby="upcoming-absences-heading"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 id="upcoming-absences-heading" className="text-lg font-semibold text-gray-900">Upcoming Absences (7 days)</h3>
        <CalendarOff className="w-5 h-5 text-amber-600" aria-hidden="true" />
      </div>

      {/* Impact Summary Banner */}
      {!isLoading && stats.total > 0 && (stats.criticalCount > 0 || stats.highCount > 0) && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg" role="alert">
          <div className="flex items-center gap-2 text-sm">
            <AlertTriangle className="w-4 h-4 text-amber-600" aria-hidden="true" />
            <span className="font-medium text-amber-800">Coverage Alert:</span>
            <span className="text-amber-700">
              {stats.criticalCount > 0 && (
                <span className="text-red-700 font-medium">{stats.criticalCount} critical</span>
              )}
              {stats.criticalCount > 0 && stats.highCount > 0 && ', '}
              {stats.highCount > 0 && (
                <span className="text-orange-700">{stats.highCount} high impact</span>
              )}
              {' '} absences this week
            </span>
          </div>
        </div>
      )}

      <div aria-live="polite" aria-atomic="true">
        {isLoading ? (
          <div className="space-y-3" role="status" aria-label="Loading absence data">
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
        ) : absencesWithImpact.length === 0 ? (
          <EmptyState
            icon={CalendarOff}
            title="No upcoming absences"
            description="No absences scheduled for the next 7 days"
          />
        ) : (
          <div className="space-y-3">
            {absencesWithImpact.map((absence) => (
              <div key={absence.id} className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center" aria-hidden="true">
                  <User className="w-4 h-4 text-gray-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {absence.personName}
                    </p>
                    {/* Impact indicator */}
                    {(absence.impact === 'critical' || absence.impact === 'high') && (
                      <span
                        className={`flex-shrink-0 px-1.5 py-0.5 rounded text-xs font-medium border ${impactColors[absence.impact]}`}
                        role="status"
                        aria-label={`${absence.impact} impact: ${absence.concurrent_count} concurrent absences`}
                      >
                        {absence.impact === 'critical' ? 'Critical' : 'High'}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    {format(parseISO(absence.startDate), 'MMM d')} -{' '}
                    {format(parseISO(absence.endDate), 'MMM d')}
                    <span className="text-gray-400"> • {absence.days}d</span>
                    {absence.concurrent_count > 1 && (
                      <span className="text-amber-600">
                        {' '}• <Users className="w-3 h-3 inline" aria-hidden="true" /> {absence.concurrent_count} out
                      </span>
                    )}
                  </p>
                </div>
                <span
                  className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-medium ${
                    absenceTypeBadgeColors[absence.absenceType] ?? 'bg-gray-100 text-gray-800'
                  }`}
                  aria-label={`Absence type: ${absenceTypeLabels[absence.absenceType] ?? absence.absenceType}`}
                >
                  {absenceTypeLabels[absence.absenceType] ?? absence.absenceType}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200/50">
        <Link
          href="/absences"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          aria-label="View complete absence calendar and history"
        >
          View All Absences &rarr;
        </Link>
      </div>
    </motion.div>
  )
}
