'use client'

import { useState } from 'react'
import { Calendar, Download, Link2, Loader2, Copy, Check } from 'lucide-react'
import { useToast } from '@/contexts/ToastContext'

interface CalendarExportButtonProps {
  /** Person ID for export */
  personId?: string
  /** Rotation ID for export */
  rotationId?: string
  /** Start date in YYYY-MM-DD format */
  startDate?: string
  /** End date in YYYY-MM-DD format */
  endDate?: string
  /** Activity types to include */
  includeTypes?: string[]
  /** Optional class name */
  className?: string
}

/**
 * Button to export schedule to ICS calendar format.
 *
 * Supports both one-time download and subscription URLs for
 * automatic calendar updates in Google Calendar, Outlook, and Apple Calendar.
 */
export function CalendarExportButton({
  personId,
  rotationId,
  startDate,
  endDate,
  includeTypes,
  className = '',
}: CalendarExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [isCreatingSubscription, setIsCreatingSubscription] = useState(false)
  const [subscriptionUrl, setSubscriptionUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const { toast } = useToast()

  // Default to next 6 months if dates not provided
  const getDefaultDates = () => {
    const today = new Date()
    const sixMonthsLater = new Date(today)
    sixMonthsLater.setMonth(sixMonthsLater.getMonth() + 6)

    return {
      start: startDate || today.toISOString().split('T')[0],
      end: endDate || sixMonthsLater.toISOString().split('T')[0],
    }
  }

  const handleDownload = async () => {
    setIsExporting(true)

    try {
      const dates = getDefaultDates()
      let url = ''

      if (personId) {
        url = `/api/calendar/export/person/${personId}?start_date=${dates.start}&end_date=${dates.end}`
        if (includeTypes && includeTypes.length > 0) {
          url += `&${includeTypes.map((t) => `include_types=${t}`).join('&')}`
        }
      } else if (rotationId) {
        url = `/api/calendar/export/rotation/${rotationId}?start_date=${dates.start}&end_date=${dates.end}`
      } else {
        throw new Error('Either personId or rotationId must be provided')
      }

      const response = await fetch(url)

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to export calendar')
      }

      // Download the ICS file
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `schedule_${dates.start}_${dates.end}.ics`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      toast.success('Calendar exported successfully')
      setIsOpen(false)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed'
      toast.error(errorMessage)
    } finally {
      setIsExporting(false)
    }
  }

  const handleCreateSubscription = async () => {
    if (!personId) {
      toast.error('Subscription only available for person calendars')
      return
    }

    setIsCreatingSubscription(true)

    try {
      const response = await fetch('/api/calendar/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          person_id: personId,
          expires_days: null, // Never expires
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create subscription')
      }

      const data = await response.json()
      setSubscriptionUrl(data.subscription_url)
      toast.success('Subscription URL created')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Subscription creation failed'
      toast.error(errorMessage)
    } finally {
      setIsCreatingSubscription(false)
    }
  }

  const handleCopyUrl = async () => {
    if (!subscriptionUrl) return

    try {
      await navigator.clipboard.writeText(subscriptionUrl)
      setCopied(true)
      toast.success('Subscription URL copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      toast.error('Failed to copy URL')
    }
  }

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-4 py-2
          bg-blue-600 hover:bg-blue-700
          text-white font-medium rounded-lg
          transition-colors
          ${className}
        `}
      >
        <Calendar className="w-4 h-4" />
        Export Calendar
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 p-4 z-50">
            <h3 className="font-semibold text-gray-900 mb-3">Export Calendar</h3>

            <div className="space-y-3">
              {/* Download Option */}
              <div className="border-b border-gray-200 pb-3">
                <p className="text-sm text-gray-600 mb-2">
                  Download ICS file to import into your calendar app
                </p>
                <button
                  onClick={handleDownload}
                  disabled={isExporting}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
                >
                  {isExporting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Download ICS
                    </>
                  )}
                </button>
              </div>

              {/* Subscription Option - Only for person calendars */}
              {personId && (
                <div>
                  <p className="text-sm text-gray-600 mb-2">
                    Create subscription URL for automatic updates
                  </p>

                  {!subscriptionUrl ? (
                    <button
                      onClick={handleCreateSubscription}
                      disabled={isCreatingSubscription}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
                    >
                      {isCreatingSubscription ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <Link2 className="w-4 h-4" />
                          Create Subscription
                        </>
                      )}
                    </button>
                  ) : (
                    <div className="space-y-2">
                      <div className="p-2 bg-gray-50 rounded border border-gray-200">
                        <p className="text-xs text-gray-600 mb-1 font-medium">
                          Subscription URL:
                        </p>
                        <p className="text-xs text-gray-800 break-all font-mono">
                          {subscriptionUrl}
                        </p>
                      </div>

                      <button
                        onClick={handleCopyUrl}
                        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md transition-colors text-sm"
                      >
                        {copied ? (
                          <>
                            <Check className="w-4 h-4 text-green-600" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy URL
                          </>
                        )}
                      </button>

                      <div className="text-xs text-gray-500 mt-2">
                        <p className="font-medium mb-1">How to subscribe:</p>
                        <ul className="list-disc list-inside space-y-1">
                          <li>Google Calendar: Add by URL</li>
                          <li>Outlook: Subscribe to calendar</li>
                          <li>Apple Calendar: File &gt; New Calendar Subscription</li>
                        </ul>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/**
 * Simple calendar export button with minimal options.
 * Just downloads the ICS file directly.
 */
export function SimpleCalendarExportButton({
  personId,
  rotationId,
  startDate,
  endDate,
  className = '',
}: CalendarExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false)
  const { toast } = useToast()

  const handleExport = async () => {
    setIsExporting(true)

    try {
      const today = new Date()
      const sixMonthsLater = new Date(today)
      sixMonthsLater.setMonth(sixMonthsLater.getMonth() + 6)

      const dates = {
        start: startDate || today.toISOString().split('T')[0],
        end: endDate || sixMonthsLater.toISOString().split('T')[0],
      }

      let url = ''
      if (personId) {
        url = `/api/calendar/export/person/${personId}?start_date=${dates.start}&end_date=${dates.end}`
      } else if (rotationId) {
        url = `/api/calendar/export/rotation/${rotationId}?start_date=${dates.start}&end_date=${dates.end}`
      } else {
        throw new Error('Either personId or rotationId must be provided')
      }

      const response = await fetch(url)

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to export calendar')
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `schedule_${dates.start}_${dates.end}.ics`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)

      toast.success('Calendar exported successfully')
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed'
      toast.error(errorMessage)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <button
      onClick={handleExport}
      disabled={isExporting}
      className={`
        flex items-center gap-2 px-4 py-2
        bg-blue-600 hover:bg-blue-700
        disabled:bg-blue-400 disabled:cursor-not-allowed
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
          <Calendar className="w-4 h-4" />
          Export to Calendar
        </>
      )}
    </button>
  )
}
