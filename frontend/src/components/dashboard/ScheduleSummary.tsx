'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format, startOfWeek, addDays } from 'date-fns'
import { Calendar, Users, CheckCircle, AlertCircle } from 'lucide-react'
import { motion } from 'framer-motion'
import { useSchedule, usePeople } from '@/lib/hooks'
import { EmptyState } from '@/components/EmptyState'
import { GenerateScheduleDialog } from '@/components/GenerateScheduleDialog'

export function ScheduleSummary() {
  const [isGenerateOpen, setIsGenerateOpen] = useState(false)
  const today = new Date()
  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekEnd = addDays(weekStart, 6)

  const { data: schedule, isLoading: scheduleLoading } = useSchedule(weekStart, weekEnd)
  const { data: people, isLoading: peopleLoading } = usePeople()

  const isLoading = scheduleLoading || peopleLoading

  // Count unique residents and attendings scheduled this week
  const scheduledResidents = new Set<string>()
  const scheduledAttendings = new Set<string>()

  schedule?.items?.forEach((assignment) => {
    const person = people?.items?.find((p) => p.id === assignment.person_id)
    if (person?.type === 'resident') {
      scheduledResidents.add(assignment.person_id)
    } else if (person?.type === 'faculty') {
      scheduledAttendings.add(assignment.person_id)
    }
  })

  const hasSchedule = (schedule?.total ?? 0) > 0
  const totalResidents = people?.items?.filter((p) => p.type === 'resident').length ?? 0
  const totalFaculty = people?.items?.filter((p) => p.type === 'faculty').length ?? 0

  // Determine coverage status
  const residentCoverage = totalResidents > 0 ? (scheduledResidents.size / totalResidents) * 100 : 0
  const isFullyStaffed = residentCoverage >= 80

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">This Week&apos;s Schedule</h3>
        <Calendar className="w-5 h-5 text-blue-600" />
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="animate-pulse h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="animate-pulse h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="animate-pulse h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      ) : !hasSchedule ? (
        <EmptyState
          icon={Calendar}
          title="No schedule generated"
          description={`${format(weekStart, 'MMM d')} - ${format(weekEnd, 'MMM d, yyyy')}`}
          action={{
            label: 'Generate Schedule',
            onClick: () => setIsGenerateOpen(true),
          }}
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm">
            <Users className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600">
              <span className="font-medium text-gray-900">{scheduledResidents.size}</span> residents scheduled
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Users className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600">
              <span className="font-medium text-gray-900">{scheduledAttendings.size}</span> attendings
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Calendar className="w-4 h-4 text-gray-400" />
            <span className="text-gray-600">
              <span className="font-medium text-gray-900">{schedule?.total ?? 0}</span> total assignments
            </span>
          </div>

          {/* Coverage Status */}
          <div className={`flex items-center gap-2 px-3 py-2 rounded-md ${
            isFullyStaffed ? 'bg-green-50' : 'bg-amber-50'
          }`}>
            {isFullyStaffed ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-700">Fully Staffed</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span className="text-sm text-amber-700">Coverage Gaps</span>
              </>
            )}
          </div>
        </div>
      )}

      <div className="mt-4 pt-4 border-t">
        <Link
<<<<<<< HEAD
          href="/schedule"
=======
          href="/"
>>>>>>> origin/docs/session-14-summary
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View Full Schedule &rarr;
        </Link>
      </div>

      <GenerateScheduleDialog
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        defaultStartDate={format(weekStart, 'yyyy-MM-dd')}
        defaultEndDate={format(weekEnd, 'yyyy-MM-dd')}
      />
    </motion.div>
  )
}
