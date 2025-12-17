'use client'

import Link from 'next/link'
import { format, startOfMonth, endOfMonth } from 'date-fns'
import { ShieldCheck, ShieldAlert, AlertTriangle, ShieldOff } from 'lucide-react'
import { motion } from 'framer-motion'
import { useValidateSchedule } from '@/lib/hooks'
import { EmptyState } from '@/components/EmptyState'

export function ComplianceAlert() {
  const today = new Date()
  const startDate = format(startOfMonth(today), 'yyyy-MM-dd')
  const endDate = format(endOfMonth(today), 'yyyy-MM-dd')

  const { data: validation, isLoading, isError } = useValidateSchedule(startDate, endDate)

  const violationCount = validation?.total_violations ?? 0
  const hasViolations = violationCount > 0
  const isClean = !hasViolations && validation?.valid
  const hasNoData = !validation || validation.valid === undefined

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.2 }}
      className="glass-panel p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Compliance Status</h3>
        {isClean ? (
          <ShieldCheck className="w-5 h-5 text-green-600" />
        ) : (
          <ShieldAlert className="w-5 h-5 text-red-600" />
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="animate-pulse h-12 bg-gray-200 rounded"></div>
          <div className="animate-pulse h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      ) : isError ? (
        <div className="text-center py-4">
          <AlertTriangle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Unable to load compliance data</p>
        </div>
      ) : hasNoData ? (
        <EmptyState
          icon={ShieldOff}
          title="No compliance data"
          description="Generate a schedule to view compliance status"
        />
      ) : isClean ? (
        <div className="text-center py-4">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-100 mb-3">
            <ShieldCheck className="w-6 h-6 text-green-600" />
          </div>
          <p className="text-green-700 font-medium">All Clear</p>
          <p className="text-sm text-gray-500 mt-1">
            No ACGME violations for {format(today, 'MMMM yyyy')}
          </p>
        </div>
      ) : (
        <div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="flex-shrink-0">
                <ShieldAlert className="w-8 h-8 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-red-700">{violationCount}</p>
                <p className="text-sm text-red-600">
                  Violation{violationCount !== 1 ? 's' : ''} Found
                </p>
              </div>
            </div>
          </div>

          {/* Show top violations */}
          {validation?.violations && validation.violations.length > 0 && (
            <div className="space-y-2">
              {validation.violations.slice(0, 2).map((violation, idx) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-600 line-clamp-1">{violation.message}</span>
                </div>
              ))}
              {validation.violations.length > 2 && (
                <p className="text-xs text-gray-500 pl-6">
                  +{validation.violations.length - 2} more
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-gray-200/50">
        <Link
          href="/compliance"
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View Compliance Details &rarr;
        </Link>
      </div>
    </motion.div>
  )
}
