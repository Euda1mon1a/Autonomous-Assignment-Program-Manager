'use client'

import { useMemo } from 'react'
import { AlertTriangle, CheckCircle, TrendingUp, Info, Calendar } from 'lucide-react'
import { motion } from 'framer-motion'

interface ScheduledHourMetrics {
  thisWeek: number
  lastWeek: number
  fourWeekAverage: number
  daysOffThisWeek: number
}

interface WorkHoursCalculatorProps {
  /** Scheduled assignments in the current period */
  assignments: Array<{
    date: string
    timeOfDay: 'AM' | 'PM'
    activity: string
  }>
  /** Hours per half-day block (default: 4 for AM/PM) */
  hoursPerBlock?: number
  /** Maximum allowed weekly hours (ACGME: 80) */
  maxWeeklyHours?: number
  /** Show detailed breakdown */
  showDetails?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Standard hours by activity type for schedule-based estimation.
 * These are planning estimates, not actual logged hours.
 *
 * Note: Actual duty hours are logged in MyEvaluations.
 * This calculator provides transparency into scheduled workload
 * to help identify potential ACGME compliance issues proactively.
 */
const SCHEDULED_ACTIVITY_HOURS: Record<string, number> = {
  call: 12,      // Call shifts typically scheduled for 12h
  inpatient: 5,  // Inpatient half-day ~5h
  clinic: 4,     // Clinic session ~4h
  procedure: 4,  // Procedure block ~4h
  conference: 2, // Didactic sessions ~2h
  elective: 4,   // Elective rotation ~4h
  default: 4,    // Default half-day estimate
}

function getScheduledHoursForActivity(activity: string): number {
  const activityLower = activity.toLowerCase()
  for (const [key, hours] of Object.entries(SCHEDULED_ACTIVITY_HOURS)) {
    if (activityLower.includes(key)) return hours
  }
  return SCHEDULED_ACTIVITY_HOURS.default
}

/**
 * Scheduled Work Hours Calculator Component
 *
 * Displays PROJECTED work hours based on schedule assignments for
 * proactive ACGME compliance monitoring and transparency.
 *
 * IMPORTANT: This shows SCHEDULED hours, not actual duty hours.
 * - Scheduled hours = what the schedule projects
 * - Actual duty hours = logged in MyEvaluations
 *
 * Purpose: Help residents and program leaders identify potential
 * ACGME violations BEFORE they occur, enabling proactive adjustment.
 */
export function WorkHoursCalculator({
  assignments,
  hoursPerBlock: _hoursPerBlock = 4,
  maxWeeklyHours = 80,
  showDetails = true,
  className = '',
}: WorkHoursCalculatorProps) {
  const metrics = useMemo<ScheduledHourMetrics>(() => {
    const now = new Date()
    const startOfThisWeek = new Date(now)
    startOfThisWeek.setDate(now.getDate() - now.getDay())
    startOfThisWeek.setHours(0, 0, 0, 0)

    const startOfLastWeek = new Date(startOfThisWeek)
    startOfLastWeek.setDate(startOfLastWeek.getDate() - 7)

    const startOf4WeeksAgo = new Date(startOfThisWeek)
    startOf4WeeksAgo.setDate(startOf4WeeksAgo.getDate() - 28)

    let thisWeekHours = 0
    let lastWeekHours = 0
    let fourWeekHours = 0
    const daysWithAssignmentsThisWeek = new Set<string>()

    assignments.forEach((assignment) => {
      const assignmentDate = new Date(assignment.date)
      const hours = getScheduledHoursForActivity(assignment.activity)

      // This week
      if (assignmentDate >= startOfThisWeek) {
        thisWeekHours += hours
        daysWithAssignmentsThisWeek.add(assignment.date)
      }
      // Last week
      else if (assignmentDate >= startOfLastWeek && assignmentDate < startOfThisWeek) {
        lastWeekHours += hours
      }
      // Include in 4-week calculation
      if (assignmentDate >= startOf4WeeksAgo) {
        fourWeekHours += hours
      }
    })

    // Calculate scheduled days off (7 days minus days with assignments)
    const daysOffThisWeek = 7 - daysWithAssignmentsThisWeek.size

    return {
      thisWeek: thisWeekHours,
      lastWeek: lastWeekHours,
      fourWeekAverage: fourWeekHours / 4,
      daysOffThisWeek,
    }
  }, [assignments])

  const getComplianceStatus = (hours: number) => {
    if (hours >= maxWeeklyHours) return 'danger'
    if (hours >= maxWeeklyHours * 0.9) return 'warning' // 90% threshold
    return 'safe'
  }

  const status = getComplianceStatus(metrics.fourWeekAverage)

  const statusColors = {
    safe: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    danger: 'bg-red-50 border-red-200 text-red-800',
  }

  const statusIcons = {
    safe: <CheckCircle className="w-5 h-5 text-green-600" />,
    warning: <AlertTriangle className="w-5 h-5 text-amber-600" />,
    danger: <AlertTriangle className="w-5 h-5 text-red-600" />,
  }

  const weekDiff = metrics.thisWeek - metrics.lastWeek
  const weekTrend = weekDiff > 0 ? 'up' : weekDiff < 0 ? 'down' : 'same'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <div>
              <h3 className="font-semibold text-gray-900">Scheduled Hours</h3>
              <p className="text-xs text-gray-500">Based on assignments</p>
            </div>
          </div>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColors[status]}`}
          >
            {status === 'safe' && 'On Track'}
            {status === 'warning' && 'Review Needed'}
            {status === 'danger' && 'Action Required'}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="p-4 grid grid-cols-2 gap-4">
        {/* This Week */}
        <div className="space-y-1">
          <div className="text-sm text-gray-500">This Week (Scheduled)</div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-gray-900">
              {metrics.thisWeek.toFixed(0)}
            </span>
            <span className="text-sm text-gray-500">hours</span>
            {weekTrend !== 'same' && (
              <span
                className={`flex items-center text-xs ${
                  weekTrend === 'up' ? 'text-red-600' : 'text-green-600'
                }`}
              >
                <TrendingUp
                  className={`w-3 h-3 ${weekTrend === 'down' ? 'rotate-180' : ''}`}
                />
                {Math.abs(weekDiff).toFixed(0)}
              </span>
            )}
          </div>
        </div>

        {/* 4-Week Average (ACGME) */}
        <div className="space-y-1">
          <div className="flex items-center gap-1 text-sm text-gray-500">
            4-Week Projection
            <div className="relative group">
              <Info className="w-3 h-3 text-gray-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 hidden group-hover:block w-56 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-10">
                ACGME limit: ≤80 hours/week averaged over 4 weeks. This shows scheduled hours for proactive planning.
              </div>
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold ${
                status === 'danger'
                  ? 'text-red-600'
                  : status === 'warning'
                    ? 'text-amber-600'
                    : 'text-gray-900'
              }`}
            >
              {metrics.fourWeekAverage.toFixed(1)}
            </span>
            <span className="text-sm text-gray-500">/ {maxWeeklyHours}</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="px-4 pb-4">
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              status === 'danger'
                ? 'bg-red-500'
                : status === 'warning'
                  ? 'bg-amber-500'
                  : 'bg-green-500'
            }`}
            style={{
              width: `${Math.min((metrics.fourWeekAverage / maxWeeklyHours) * 100, 100)}%`,
            }}
          />
        </div>
        <div className="mt-1 flex justify-between text-xs text-gray-400">
          <span>0h</span>
          <span>{maxWeeklyHours}h ACGME limit</span>
        </div>
      </div>

      {/* Additional Details */}
      {showDetails && (
        <div className="px-4 pb-4 pt-2 border-t border-gray-100 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Scheduled days off:</span>{' '}
            <span
              className={`font-medium ${
                metrics.daysOffThisWeek >= 1 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {metrics.daysOffThisWeek}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Last week:</span>{' '}
            <span className="font-medium text-gray-900">{metrics.lastWeek.toFixed(0)}h</span>
          </div>
        </div>
      )}

      {/* Status Banner */}
      {status !== 'safe' && (
        <div className={`p-3 flex items-center gap-2 ${statusColors[status]}`}>
          {statusIcons[status]}
          <span className="text-sm">
            {status === 'warning' &&
              `Schedule projects ${((metrics.fourWeekAverage / maxWeeklyHours) * 100).toFixed(0)}% of limit - consider adjustments`}
            {status === 'danger' &&
              `Schedule exceeds ACGME limit - review with program director before finalizing`}
          </span>
        </div>
      )}

      {/* Disclaimer */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
        <p className="text-xs text-gray-500 text-center">
          Estimated from schedule. Actual duty hours logged in MyEvaluations.
        </p>
      </div>
    </motion.div>
  )
}
