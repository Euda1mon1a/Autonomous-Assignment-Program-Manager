'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format, startOfWeek, addDays } from 'date-fns'
import { Calendar, UserPlus, FileText, Zap } from 'lucide-react'
import { GenerateScheduleDialog } from '@/components/GenerateScheduleDialog'

export function QuickActions() {
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)

  const today = new Date()
  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekEnd = addDays(weekStart, 6)
  const startDateStr = format(weekStart, 'yyyy-MM-dd')
  const endDateStr = format(weekEnd, 'yyyy-MM-dd')

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
        <Zap className="w-5 h-5 text-amber-500" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          onClick={() => setIsGenerateDialogOpen(true)}
          className="flex flex-col items-center justify-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group"
        >
          <Calendar className="w-6 h-6 text-blue-600 mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-medium text-blue-800">Generate Schedule</span>
        </button>

        <Link
          href="/people"
          className="flex flex-col items-center justify-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors group"
        >
          <UserPlus className="w-6 h-6 text-green-600 mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-medium text-green-800">Add Person</span>
        </Link>

        <Link
          href="/templates"
          className="flex flex-col items-center justify-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors group"
        >
          <FileText className="w-6 h-6 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-medium text-purple-800">View Templates</span>
        </Link>

        <Link
          href="/compliance"
          className="flex flex-col items-center justify-center p-4 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors group"
        >
          <svg
            className="w-6 h-6 text-amber-600 mb-2 group-hover:scale-110 transition-transform"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          <span className="text-sm font-medium text-amber-800">Compliance</span>
        </Link>
      </div>

      <GenerateScheduleDialog
        isOpen={isGenerateDialogOpen}
        onClose={() => setIsGenerateDialogOpen(false)}
        defaultStartDate={startDateStr}
        defaultEndDate={endDateStr}
      />
    </div>
  )
}
