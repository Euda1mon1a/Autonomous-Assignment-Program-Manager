'use client'

import { format } from 'date-fns'
import { ScheduleSummary } from '@/components/dashboard/ScheduleSummary'
import { ComplianceAlert } from '@/components/dashboard/ComplianceAlert'
import { UpcomingAbsences } from '@/components/dashboard/UpcomingAbsences'
import { QuickActions } from '@/components/dashboard/QuickActions'

export default function DashboardPage() {
  const today = new Date()

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">{format(today, 'EEEE, MMMM d, yyyy')}</p>
      </div>

      {/* Dashboard Grid - 2 columns on desktop, 1 on mobile */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ScheduleSummary />
        <ComplianceAlert />
        <UpcomingAbsences />
        <QuickActions />
      </div>
    </div>
  )
}
