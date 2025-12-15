'use client'

import { useState } from 'react'
import { format, startOfMonth, endOfMonth, addMonths, subMonths } from 'date-fns'
import { CheckCircle, XCircle, AlertTriangle, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'
import { useValidateSchedule } from '@/lib/hooks'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import type { Violation } from '@/types/api'

export default function CompliancePage() {
  const [selectedMonth, setSelectedMonth] = useState(new Date())
  const startDate = format(startOfMonth(selectedMonth), 'yyyy-MM-dd')
  const endDate = format(endOfMonth(selectedMonth), 'yyyy-MM-dd')

  const { data: validation, isLoading, isError, error, refetch } = useValidateSchedule(startDate, endDate)

  const goToPreviousMonth = () => setSelectedMonth(subMonths(selectedMonth, 1))
  const goToNextMonth = () => setSelectedMonth(addMonths(selectedMonth, 1))
  const goToCurrentMonth = () => setSelectedMonth(new Date())

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ACGME Compliance</h1>
          <p className="text-gray-600">
            Validate schedule against ACGME requirements
          </p>
        </div>

        {/* Month Navigation */}
        <div className="flex items-center gap-2">
          <button
            onClick={goToPreviousMonth}
            className="p-2 hover:bg-gray-100 rounded-md"
            aria-label="Previous month"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={goToCurrentMonth}
            className="btn-secondary text-sm min-w-[140px]"
          >
            {format(selectedMonth, 'MMMM yyyy')}
          </button>
          <button
            onClick={goToNextMonth}
            className="p-2 hover:bg-gray-100 rounded-md"
            aria-label="Next month"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <ComplianceCard
          title="80-Hour Rule"
          description="Max 80 hours/week (4-week average)"
          status={validation?.violations?.filter((v: Violation) => v.type === '80_HOUR_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === '80_HOUR_VIOLATION').length || 0}
          isLoading={isLoading}
        />
        <ComplianceCard
          title="1-in-7 Rule"
          description="One day off every 7 days"
          status={validation?.violations?.filter((v: Violation) => v.type === '1_IN_7_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === '1_IN_7_VIOLATION').length || 0}
          isLoading={isLoading}
        />
        <ComplianceCard
          title="Supervision Ratios"
          description="PGY-1: 1:2, PGY-2/3: 1:4"
          status={validation?.violations?.filter((v: Violation) => v.type === 'SUPERVISION_RATIO_VIOLATION').length === 0 ? 'pass' : 'fail'}
          count={validation?.violations?.filter((v: Violation) => v.type === 'SUPERVISION_RATIO_VIOLATION').length || 0}
          isLoading={isLoading}
        />
      </div>

      {/* Violations List */}
      <div className="card">
        <div className="border-b pb-4 mb-4">
          <h2 className="font-semibold text-lg">
            {validation?.valid ? 'No Violations' : 'Violations Requiring Attention'}
          </h2>
          <p className="text-sm text-gray-500">
            Coverage Rate: {validation?.coverage_rate?.toFixed(1) || 0}%
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <p className="text-gray-600 mb-4">
              {error?.message || 'Failed to load compliance data'}
            </p>
            <button
              onClick={() => refetch()}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        ) : validation?.violations?.length === 0 ? (
          <div className="text-center py-8 text-green-600">
            <CheckCircle className="w-12 h-12 mx-auto mb-2" />
            <p className="font-medium">All ACGME requirements met!</p>
          </div>
        ) : (
          <div className="divide-y">
            {validation?.violations?.map((violation: Violation, idx: number) => (
              <ViolationRow key={idx} violation={violation} />
            ))}
          </div>
        )}
        </div>
      </div>
    </ProtectedRoute>
  )
}

function ComplianceCard({
  title,
  description,
  status,
  count,
  isLoading,
}: {
  title: string
  description: string
  status: 'pass' | 'fail'
  count: number
  isLoading: boolean
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        {isLoading ? (
          <div className="animate-pulse w-8 h-8 bg-gray-200 rounded-full"></div>
        ) : status === 'pass' ? (
          <CheckCircle className="w-8 h-8 text-green-500" />
        ) : (
          <XCircle className="w-8 h-8 text-red-500" />
        )}
      </div>
      {!isLoading && count > 0 && (
        <p className="mt-2 text-sm text-red-600">
          {count} violation{count > 1 ? 's' : ''} found
        </p>
      )}
    </div>
  )
}

function ViolationRow({ violation }: { violation: Violation }) {
  const severityColors: Record<Violation['severity'], string> = {
    CRITICAL: 'bg-red-100 text-red-800',
    HIGH: 'bg-orange-100 text-orange-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    LOW: 'bg-gray-100 text-gray-800',
  }

  return (
    <div className="py-4 flex items-start gap-4">
      <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${severityColors[violation.severity]}`}>
            {violation.severity}
          </span>
          <span className="text-sm font-medium text-gray-900">
            {violation.type.replace(/_/g, ' ')}
          </span>
        </div>
        <p className="mt-1 text-sm text-gray-600">{violation.message}</p>
        {violation.person_name && (
          <p className="text-xs text-gray-500 mt-1">Person: {violation.person_name}</p>
        )}
      </div>
    </div>
  )
}
