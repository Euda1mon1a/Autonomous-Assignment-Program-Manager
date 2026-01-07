'use client'

import { useMemo, useState } from 'react'
import { useQueries } from '@tanstack/react-query'
import { AlertTriangle, Calendar, Loader2, RefreshCw } from 'lucide-react'
import { get } from '@/lib/api'
import { useBlockRanges, usePeople, useRotationTemplates } from '@/hooks'
import type { Person, RotationTemplate } from '@/types/api'

// ============================================================================
// Types
// ============================================================================

interface BlockAssignmentResponse {
  id: string
  block_number: number
  academic_year: number
  resident_id: string
  rotation_template_id: string | null
  has_leave: boolean
  leave_days: number
  assignment_reason: string
  notes: string | null
  resident: {
    id: string
    name: string
    pgy_level: number | null
  } | null
  rotation_template: {
    id: string
    name: string
    activity_type: string
    leave_eligible: boolean
  } | null
}

interface BlockSchedulerDashboard {
  block_number: number
  academic_year: number
  block_start_date: string | null
  block_end_date: string | null
  current_assignments: BlockAssignmentResponse[]
  total_residents: number
  unassigned_residents: number
}

interface BlockAnnualViewProps {
  academicYear?: number
  personFilter?: Set<string>
  onBlockClick?: (blockNumber: number) => void
}

// ============================================================================
// Helper Functions
// ============================================================================

function getCurrentAcademicYear(): number {
  const now = new Date()
  const month = now.getMonth()
  // Academic year starts July 1st
  // July (6) through December (11) = current calendar year
  // January (0) through June (5) = previous calendar year
  return month >= 6 ? now.getFullYear() : now.getFullYear() - 1
}

function getActivityColor(activityType: string | undefined): { bg: string; text: string; border: string } {
  switch (activityType) {
    case 'clinic':
    case 'fm_clinic':
      return { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200' }
    case 'inpatient':
      return { bg: 'bg-purple-50', text: 'text-purple-800', border: 'border-purple-200' }
    case 'procedure':
      return { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200' }
    case 'call':
    case 'on_call':
      return { bg: 'bg-orange-50', text: 'text-orange-800', border: 'border-orange-200' }
    case 'elective':
      return { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200' }
    case 'conference':
    case 'didactics':
      return { bg: 'bg-gray-50', text: 'text-gray-800', border: 'border-gray-200' }
    case 'leave':
    case 'vacation':
      return { bg: 'bg-amber-50', text: 'text-amber-800', border: 'border-amber-200' }
    default:
      return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200' }
  }
}

// ============================================================================
// Component
// ============================================================================

export function BlockAnnualView({
  academicYear = getCurrentAcademicYear(),
  personFilter,
  onBlockClick,
}: BlockAnnualViewProps) {
  const [showBlock0, setShowBlock0] = useState(true)

  // Fetch block ranges to know which blocks exist
  const { data: blockRanges, isLoading: blocksLoading } = useBlockRanges()

  // Fetch all people (we'll filter to residents)
  const { data: peopleData, isLoading: peopleLoading } = usePeople()

  // Fetch rotation templates for color mapping
  const { data: templatesData } = useRotationTemplates()

  // Get residents only, sorted by PGY level then name
  const residents = useMemo(() => {
    if (!peopleData?.items) return []
    return peopleData.items
      .filter((p: Person) => p.type === 'resident')
      .sort((a: Person, b: Person) => {
        // Sort by PGY level (ascending), then by name
        const pgyDiff = (a.pgy_level ?? 99) - (b.pgy_level ?? 99)
        if (pgyDiff !== 0) return pgyDiff
        return a.name.localeCompare(b.name)
      })
  }, [peopleData])

  // Filter residents if filter is provided
  const filteredResidents = useMemo(() => {
    if (!personFilter || personFilter.size === 0) return residents
    return residents.filter((r: Person) => personFilter.has(r.id))
  }, [residents, personFilter])

  // Build template map for colors
  const templateMap = useMemo(() => {
    const map = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((t: RotationTemplate) => map.set(t.id, t))
    return map
  }, [templatesData])

  // Determine which blocks to show (0-13 or 1-13)
  const blockNumbers = useMemo(() => {
    const blocks = showBlock0
      ? [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
      : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    return blocks
  }, [showBlock0])

  // Fetch dashboard for each block in parallel
  const dashboardQueries = useQueries({
    queries: blockNumbers.map((blockNum) => ({
      queryKey: ['block-scheduler-dashboard', blockNum, academicYear],
      queryFn: () =>
        get<BlockSchedulerDashboard>(
          `/block-scheduler/dashboard?block_number=${blockNum}&academic_year=${academicYear}`
        ),
      staleTime: 5 * 60 * 1000,
      retry: 1,
    })),
  })

  // Combine all assignments from all blocks
  const assignmentsByResident = useMemo(() => {
    const map = new Map<string, Map<number, BlockAssignmentResponse>>()

    dashboardQueries.forEach((query, idx) => {
      if (query.data?.current_assignments) {
        const blockNum = blockNumbers[idx]
        query.data.current_assignments.forEach((assignment) => {
          if (!map.has(assignment.resident_id)) {
            map.set(assignment.resident_id, new Map())
          }
          map.get(assignment.resident_id)!.set(blockNum, assignment)
        })
      }
    })

    return map
  }, [dashboardQueries, blockNumbers])

  // Get block dates for headers
  const blockDates = useMemo(() => {
    const dates = new Map<number, { start: string; end: string }>()
    blockRanges?.forEach((range) => {
      dates.set(range.block_number, {
        start: range.start_date,
        end: range.end_date,
      })
    })
    return dates
  }, [blockRanges])

  // Loading state
  const isLoading = blocksLoading || peopleLoading || dashboardQueries.some((q) => q.isLoading)
  const hasError = dashboardQueries.some((q) => q.isError)

  // Group residents by PGY level
  const residentsByPgy = useMemo(() => {
    const groups = new Map<number, Person[]>()
    filteredResidents.forEach((r: Person) => {
      const pgy = r.pgy_level ?? 0
      if (!groups.has(pgy)) groups.set(pgy, [])
      groups.get(pgy)!.push(r)
    })
    return Array.from(groups.entries()).sort((a, b) => a[0] - b[0])
  }, [filteredResidents])

  // Render cell for a single resident/block combination
  const renderCell = (residentId: string, blockNum: number) => {
    const assignment = assignmentsByResident.get(residentId)?.get(blockNum)

    if (!assignment) {
      return (
        <div className="h-full w-full flex items-center justify-center text-gray-300 text-xs">
          —
        </div>
      )
    }

    // Get rotation info
    const template = assignment.rotation_template_id
      ? templateMap.get(assignment.rotation_template_id)
      : null
    const abbreviation =
      template?.display_abbreviation ||
      template?.abbreviation ||
      template?.name?.substring(0, 4) ||
      assignment.rotation_template?.name?.substring(0, 4) ||
      '???'
    const activityType = template?.activity_type || assignment.rotation_template?.activity_type
    const colors = getActivityColor(activityType)

    // Show leave indicator
    if (assignment.has_leave) {
      return (
        <div
          className={`h-full w-full flex items-center justify-center px-1 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}
          title={`${assignment.rotation_template?.name || 'Unknown'} (${assignment.leave_days} leave days)`}
        >
          <span className="truncate">{abbreviation}</span>
          <span className="ml-0.5 text-amber-500">★</span>
        </div>
      )
    }

    return (
      <div
        className={`h-full w-full flex items-center justify-center px-1 py-0.5 rounded text-xs font-medium ${colors.bg} ${colors.text} border ${colors.border}`}
        title={template?.name || assignment.rotation_template?.name || 'Unknown Rotation'}
      >
        <span className="truncate">{abbreviation}</span>
      </div>
    )
  }

  // Format date for header
  const formatBlockHeader = (blockNum: number) => {
    const dates = blockDates.get(blockNum)
    if (!dates) return `Block ${blockNum}`
    // Format as "Jan 1 - Jan 28"
    const start = new Date(dates.start + 'T00:00:00')
    const end = new Date(dates.end + 'T00:00:00')
    const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    return (
      <div className="text-center">
        <div className="font-semibold">{blockNum === 0 ? 'Block 0' : `Block ${blockNum}`}</div>
        <div className="text-[10px] text-gray-500">
          {startStr} - {endStr}
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading annual schedule...</span>
      </div>
    )
  }

  if (hasError) {
    return (
      <div className="flex items-center justify-center h-64 text-red-600">
        <AlertTriangle className="w-6 h-6 mr-2" />
        <span>Error loading schedule data. Please try again.</span>
        <button
          onClick={() => dashboardQueries.forEach((q) => q.refetch())}
          className="ml-4 px-3 py-1 bg-red-100 hover:bg-red-200 rounded text-sm"
        >
          <RefreshCw className="w-4 h-4 inline mr-1" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-800">
            <Calendar className="w-5 h-5 inline mr-2" />
            Academic Year {academicYear}-{academicYear + 1}
          </h2>
          <span className="text-sm text-gray-500">
            {filteredResidents.length} resident{filteredResidents.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={showBlock0}
              onChange={(e) => setShowBlock0(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Show Block 0 (Orientation)
          </label>
        </div>
      </div>

      {/* Block 0 Warning */}
      {showBlock0 && (
        <div className="mb-4 bg-amber-50 border-l-4 border-amber-400 p-3 text-sm">
          <div className="flex items-start">
            <AlertTriangle className="w-4 h-4 text-amber-500 mr-2 mt-0.5 flex-shrink-0" />
            <div>
              <strong className="text-amber-800">Block 0 (Orientation Period):</strong>
              <span className="text-amber-700 ml-1">
                Variable-length period at the start of the academic year. Duration is computed for
                scheduling efficiency. Contact admin with questions.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="mb-4 flex flex-wrap items-center gap-3 text-xs">
        <span className="text-gray-500 font-medium">Legend:</span>
        {[
          { label: 'Clinic', type: 'clinic' },
          { label: 'Inpatient', type: 'inpatient' },
          { label: 'Procedure', type: 'procedure' },
          { label: 'Call', type: 'call' },
          { label: 'Elective', type: 'elective' },
          { label: 'Conference', type: 'conference' },
        ].map(({ label, type }) => {
          const colors = getActivityColor(type)
          return (
            <span key={type} className="inline-flex items-center gap-1">
              <span
                className={`w-3 h-3 rounded ${colors.bg} border ${colors.border}`}
              ></span>
              {label}
            </span>
          )
        })}
        <span className="inline-flex items-center gap-1">
          <span className="text-amber-500">★</span>
          Has Leave
        </span>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-auto border rounded-lg bg-white">
        <table className="min-w-full border-collapse text-sm">
          <thead className="bg-gray-50 sticky top-0 z-10">
            <tr>
              <th className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-700 bg-gray-100 sticky left-0 z-20 min-w-[150px]">
                Resident
              </th>
              {blockNumbers.map((blockNum) => (
                <th
                  key={blockNum}
                  className={`border border-gray-200 px-2 py-2 text-xs font-medium text-gray-600 min-w-[80px] ${
                    blockNum === 0 ? 'bg-amber-50' : 'bg-gray-50'
                  } ${onBlockClick ? 'cursor-pointer hover:bg-blue-50' : ''}`}
                  onClick={() => onBlockClick?.(blockNum)}
                >
                  {formatBlockHeader(blockNum)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {residentsByPgy.map(([pgyLevel, pgyResidents]) => (
              <>
                {/* PGY Level Header */}
                <tr key={`pgy-${pgyLevel}`} className="bg-gray-100">
                  <td
                    colSpan={blockNumbers.length + 1}
                    className="border border-gray-200 px-3 py-1 font-semibold text-gray-600 text-xs"
                  >
                    PGY-{pgyLevel}
                    <span className="ml-2 text-gray-400 font-normal">
                      ({pgyResidents.length} resident{pgyResidents.length !== 1 ? 's' : ''})
                    </span>
                  </td>
                </tr>
                {/* Resident Rows */}
                {pgyResidents.map((resident: Person) => (
                  <tr key={resident.id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 px-3 py-1 font-medium text-gray-800 bg-white sticky left-0 z-10">
                      <div className="truncate max-w-[140px]" title={resident.name}>
                        {resident.name}
                      </div>
                    </td>
                    {blockNumbers.map((blockNum) => (
                      <td
                        key={blockNum}
                        className={`border border-gray-200 p-1 ${
                          blockNum === 0 ? 'bg-amber-50/30' : ''
                        }`}
                      >
                        {renderCell(resident.id, blockNum)}
                      </td>
                    ))}
                  </tr>
                ))}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default BlockAnnualView
