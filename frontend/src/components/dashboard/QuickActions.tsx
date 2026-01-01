'use client'

import { useState } from 'react'
import Link from 'next/link'
import { format, startOfWeek, addDays } from 'date-fns'
import { Calendar, UserPlus, FileText, Zap, FileSpreadsheet, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import { GenerateScheduleDialog } from '@/components/GenerateScheduleDialog'
import { exportToLegacyXlsx } from '@/lib/export'

export function QuickActions() {
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const today = new Date()
  const weekStart = startOfWeek(today, { weekStartsOn: 1 })
  const weekEnd = addDays(weekStart, 6)
  const startDateStr = format(weekStart, 'yyyy-MM-dd')
  const endDateStr = format(weekEnd, 'yyyy-MM-dd')

  // Calculate 4-week block dates for export
  const blockStart = startOfWeek(today, { weekStartsOn: 1 })
  const blockEnd = addDays(blockStart, 27) // 4 weeks
  const blockStartStr = format(blockStart, 'yyyy-MM-dd')
  const blockEndStr = format(blockEnd, 'yyyy-MM-dd')

  const handleExportExcel = async () => {
    setIsExporting(true)
    try {
      await exportToLegacyXlsx(blockStartStr, blockEndStr)
    } catch (error) {
      // console.error('Export failed:', error)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut', delay: 0.1 }}
      className="glass-panel p-6"
    >
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

        <button
          onClick={handleExportExcel}
          disabled={isExporting}
          className="flex flex-col items-center justify-center p-4 bg-green-50 hover:bg-green-100 disabled:bg-green-50/50 rounded-lg transition-colors group"
        >
          {isExporting ? (
            <Loader2 className="w-6 h-6 text-green-600 mb-2 animate-spin" />
          ) : (
            <FileSpreadsheet className="w-6 h-6 text-green-600 mb-2 group-hover:scale-110 transition-transform" />
          )}
          <span className="text-sm font-medium text-green-800">
            {isExporting ? 'Exporting...' : 'Export Excel'}
          </span>
        </button>

        <Link
          href="/people"
          className="flex flex-col items-center justify-center p-4 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors group"
        >
          <UserPlus className="w-6 h-6 text-purple-600 mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-medium text-purple-800">Add Person</span>
        </Link>

        <Link
          href="/templates"
          className="flex flex-col items-center justify-center p-4 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors group"
        >
          <FileText className="w-6 h-6 text-amber-600 mb-2 group-hover:scale-110 transition-transform" />
          <span className="text-sm font-medium text-amber-800">View Templates</span>
        </Link>
      </div>

      <GenerateScheduleDialog
        isOpen={isGenerateDialogOpen}
        onClose={() => setIsGenerateDialogOpen(false)}
        defaultStartDate={startDateStr}
        defaultEndDate={endDateStr}
      />
    </motion.div>
  )
}
