'use client'

import { useState } from 'react'
import { FileSpreadsheet, Download, Loader2 } from 'lucide-react'
import { exportToLegacyXlsx } from '@/lib/export'

interface ExcelExportButtonProps {
  /** Start date in YYYY-MM-DD format */
  startDate: string
  /** End date in YYYY-MM-DD format */
  endDate: string
  /** Block number for header display */
  blockNumber?: number
  /** List of federal holiday dates in YYYY-MM-DD format */
  federalHolidays?: string[]
  /** Optional class name */
  className?: string
}

/**
 * Button to export schedule in legacy Excel format.
 *
 * This exports the schedule in the historical format used for
 * distribution, with AM/PM columns, color coding, and proper
 * PGY level grouping.
 */
export function ExcelExportButton({
  startDate,
  endDate,
  blockNumber,
  federalHolidays,
  className = '',
}: ExcelExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setIsExporting(true)
    setError(null)

    try {
      await exportToLegacyXlsx(startDate, endDate, blockNumber, federalHolidays)
    } catch (err) {
      console.error('Export failed:', err)
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={handleExport}
        disabled={isExporting}
        className={`
          flex items-center gap-2 px-4 py-2
          bg-green-600 hover:bg-green-700
          disabled:bg-green-400 disabled:cursor-not-allowed
          text-white font-medium rounded-lg
          transition-colors
          ${className}
        `}
      >
        {isExporting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Exporting...
          </>
        ) : (
          <>
            <FileSpreadsheet className="w-4 h-4" />
            Export Excel
          </>
        )}
      </button>

      {error && (
        <div className="absolute top-full left-0 mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  )
}

/**
 * Excel export with date range picker dropdown
 */
export function ExcelExportDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [blockNumber, setBlockNumber] = useState<number | undefined>()
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Set default dates to current 4-week block
  const setDefaultDates = () => {
    const today = new Date()
    // Find the start of the current block (assuming blocks start on specific dates)
    // For simplicity, just use today as start and 27 days later as end
    const start = new Date(today)
    const end = new Date(today)
    end.setDate(end.getDate() + 27)

    setStartDate(start.toISOString().split('T')[0])
    setEndDate(end.toISOString().split('T')[0])
  }

  const handleExport = async () => {
    if (!startDate || !endDate) {
      setError('Please select start and end dates')
      return
    }

    setIsExporting(true)
    setError(null)

    try {
      await exportToLegacyXlsx(startDate, endDate, blockNumber)
      setIsOpen(false)
    } catch (err) {
      console.error('Export failed:', err)
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="relative">
      <button
        onClick={() => {
          if (!isOpen) setDefaultDates()
          setIsOpen(!isOpen)
        }}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors"
      >
        <FileSpreadsheet className="w-4 h-4" />
        Export Excel
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
            <h3 className="font-semibold text-gray-900 mb-3">Export Schedule</h3>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Block Number (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  max="13"
                  value={blockNumber || ''}
                  onChange={(e) => setBlockNumber(e.target.value ? parseInt(e.target.value) : undefined)}
                  placeholder="Auto-calculated"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}

              <button
                onClick={handleExport}
                disabled={isExporting || !startDate || !endDate}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
              >
                {isExporting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Exporting...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    Download Excel
                  </>
                )}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
