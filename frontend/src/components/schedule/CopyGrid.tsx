'use client'

import React, { useMemo, useRef, useEffect, useCallback } from 'react'
import { format, eachDayOfInterval, isWeekend } from 'date-fns'
import { useQuery } from '@tanstack/react-query'
import { ClipboardCopy, CheckCircle } from 'lucide-react'
import { get } from '@/lib/api'
import { usePeople, useRotationTemplates, ListResponse } from '@/lib/hooks'
import { useAssignmentsForRange } from '@/hooks/useAssignmentsForRange'
import { useHalfDayAssignments } from '@/hooks/useHalfDayAssignments'
import { useCopyGridSelection } from '@/hooks/useCopyGridSelection'
import { useCopyGridClipboard } from '@/hooks/useCopyGridClipboard'
import type { Person, RotationTemplate, Block } from '@/types/api'
import {
  ABBREVIATION_LENGTH,
  BLOCKS_STALE_TIME_MS,
  BLOCKS_GC_TIME_MS,
  PGY_LEVEL_1,
  PGY_LEVEL_2,
  PGY_LEVEL_3,
} from '@/constants/schedule'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorAlert } from '@/components/ErrorAlert'
import { EmptyState } from '@/components/EmptyState'

interface CopyGridProps {
  startDate: Date
  endDate: Date
  personFilter?: Set<string>
}

interface ProcessedAssignment {
  abbreviation: string
  activityType: string
  fontColor?: string
  backgroundColor?: string
}

function formatFacultyRole(role: string): string {
  const roleMap: Record<string, string> = {
    pd: 'PD', apd: 'APD', oic: 'OIC', dept_chief: 'Chief',
    sports_med: 'SM', core: 'Core', adjunct: 'Adj',
  }
  return roleMap[role] || role.toUpperCase()
}

/** Consolidate AM and PM abbreviations into one cell value */
function consolidateAmPm(am?: string, pm?: string): string {
  if (!am && !pm) return ''
  if (am === pm) return am || ''
  if (!am) return pm || ''
  if (!pm) return am || ''
  return `${am}/${pm}`
}

/** Get consolidated color — use AM color, fall back to PM */
function consolidateColor(
  amAssignment?: ProcessedAssignment,
  pmAssignment?: ProcessedAssignment
): { activityType: string; fontColor?: string; backgroundColor?: string } {
  const primary = amAssignment || pmAssignment
  return {
    activityType: primary?.activityType || 'default',
    fontColor: primary?.fontColor,
    backgroundColor: primary?.backgroundColor,
  }
}

// Rotation color map (same as ScheduleCell)
const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800',
  inpatient: 'bg-purple-100 text-purple-800',
  procedure: 'bg-red-100 text-red-800',
  conference: 'bg-gray-100 text-gray-800',
  elective: 'bg-green-100 text-green-800',
  call: 'bg-orange-100 text-orange-800',
  off: 'bg-white text-gray-400',
  leave: 'bg-amber-100 text-amber-800',
  vacation: 'bg-amber-100 text-amber-800',
  admin: 'bg-slate-50 text-slate-500',
  default: 'bg-slate-100 text-slate-700',
}

const tailwindToHex: Record<string, string> = {
  'black': '#000000', 'white': '#ffffff',
  'gray-100': '#f3f4f6', 'gray-200': '#e5e7eb', 'gray-400': '#9ca3af', 'gray-800': '#1f2937',
  'red-500': '#ef4444', 'green-100': '#dcfce7', 'green-500': '#22c55e', 'green-800': '#166534',
  'blue-300': '#93c5fd', 'sky-500': '#0ea5e9', 'purple-700': '#7c3aed',
  'amber-100': '#fef3c7', 'amber-800': '#92400e', 'yellow-300': '#fde047', 'emerald-200': '#a7f3d0',
}

function getActivityColorClass(activityType: string | undefined): string {
  if (!activityType) return rotationColors.default
  const lower = activityType.toLowerCase()
  if (rotationColors[lower]) return rotationColors[lower]
  for (const [key, color] of Object.entries(rotationColors)) {
    if (lower.includes(key)) return color
  }
  return rotationColors.default
}

function useBlocks(startDate: string, endDate: string) {
  return useQuery<ListResponse<Block>>({
    queryKey: ['blocks', startDate, endDate],
    queryFn: () => get<ListResponse<Block>>(`/blocks?start_date=${startDate}&end_date=${endDate}`),
    staleTime: BLOCKS_STALE_TIME_MS,
    gcTime: BLOCKS_GC_TIME_MS,
  })
}

interface PersonGroup {
  label: string
  people: Person[]
}

export function CopyGrid({ startDate, endDate, personFilter }: CopyGridProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const startDateStr = format(startDate, 'yyyy-MM-dd')
  const endDateStr = format(endDate, 'yyyy-MM-dd')

  // Fetch data (same as ScheduleGrid)
  const { data: blocksData, isLoading: blocksLoading, error: blocksError } = useBlocks(startDateStr, endDateStr)
  const { data: assignmentsData, isLoading: assignmentsLoading, error: assignmentsError } = useAssignmentsForRange(startDateStr, endDateStr)
  const { data: peopleData, isLoading: peopleLoading, error: peopleError } = usePeople()
  const { data: templatesData, isLoading: templatesLoading, error: templatesError } = useRotationTemplates()
  const { data: halfDayData } = useHalfDayAssignments({ startDate: startDateStr, endDate: endDateStr })

  // Days array
  const days = useMemo(() => eachDayOfInterval({ start: startDate, end: endDate }), [startDate, endDate])

  // Lookup maps
  const blockMap = useMemo(() => {
    const map = new Map<string, Block>()
    blocksData?.items?.forEach((b) => map.set(b.id, b))
    return map
  }, [blocksData])

  const templateMap = useMemo(() => {
    const map = new Map<string, RotationTemplate>()
    templatesData?.items?.forEach((t) => map.set(t.id, t))
    return map
  }, [templatesData])

  const personMap = useMemo(() => {
    const map = new Map<string, Person>()
    peopleData?.items?.forEach((p) => map.set(p.id, p))
    return map
  }, [peopleData])

  // Assignment lookup: personId -> dateStr -> timeOfDay -> ProcessedAssignment
  const assignmentLookup = useMemo(() => {
    const lookup = new Map<string, Map<string, Map<string, ProcessedAssignment>>>()

    // Block-level assignments
    assignmentsData?.items?.forEach((assignment) => {
      const block = blockMap.get(assignment.blockId)
      if (!block) return
      const template = assignment.rotationTemplateId ? templateMap.get(assignment.rotationTemplateId) : null

      const processed: ProcessedAssignment = {
        abbreviation: assignment.activityOverride || template?.displayAbbreviation || template?.abbreviation || template?.name?.substring(0, ABBREVIATION_LENGTH).toUpperCase() || '???',
        activityType: template?.activityType || 'default',
        fontColor: template?.fontColor || undefined,
        backgroundColor: template?.backgroundColor || undefined,
      }

      if (!lookup.has(assignment.personId)) lookup.set(assignment.personId, new Map())
      const pMap = lookup.get(assignment.personId)!
      if (!pMap.has(block.date)) pMap.set(block.date, new Map())
      pMap.get(block.date)!.set(block.timeOfDay, processed)
    })

    // Half-day overrides
    halfDayData?.assignments?.forEach((hda) => {
      if (!hda.activityCode) return
      const processed: ProcessedAssignment = {
        abbreviation: hda.displayAbbreviation || hda.activityCode,
        activityType: 'default',
      }
      if (!lookup.has(hda.personId)) lookup.set(hda.personId, new Map())
      const pMap = lookup.get(hda.personId)!
      if (!pMap.has(hda.date)) pMap.set(hda.date, new Map())
      pMap.get(hda.date)!.set(hda.timeOfDay, processed)
    })

    // Faculty role fallback
    personMap.forEach((person, personId) => {
      if (person.type !== 'faculty' || !person.facultyRole) return
      days.forEach((day) => {
        const dateStr = format(day, 'yyyy-MM-dd')
        for (const tod of ['AM', 'PM'] as const) {
          if (lookup.get(personId)?.get(dateStr)?.get(tod)) continue
          if (!lookup.has(personId)) lookup.set(personId, new Map())
          const pMap = lookup.get(personId)!
          if (!pMap.has(dateStr)) pMap.set(dateStr, new Map())
          pMap.get(dateStr)!.set(tod, {
            abbreviation: formatFacultyRole(person.facultyRole!),
            activityType: 'admin',
          })
        }
      })
    })

    return lookup
  }, [assignmentsData, blockMap, templateMap, halfDayData, personMap, days])

  // Group people by PGY
  const personGroups = useMemo((): PersonGroup[] => {
    if (!peopleData?.items) return []
    const hasFilter = personFilter && personFilter.size > 0
    const people = hasFilter ? peopleData.items.filter((p) => personFilter.has(p.id)) : peopleData.items

    const buckets: Record<string, Person[]> = { pgy1: [], pgy2: [], pgy3: [], other: [], faculty: [] }
    people.forEach((p) => {
      if (p.type === 'faculty') buckets.faculty.push(p)
      else if (p.pgyLevel === PGY_LEVEL_1) buckets.pgy1.push(p)
      else if (p.pgyLevel === PGY_LEVEL_2) buckets.pgy2.push(p)
      else if (p.pgyLevel === PGY_LEVEL_3) buckets.pgy3.push(p)
      else buckets.other.push(p)
    })
    const sortByName = (a: Person, b: Person) => a.name.localeCompare(b.name)
    Object.values(buckets).forEach((arr) => arr.sort(sortByName))

    const groups: PersonGroup[] = []
    if (buckets.pgy1.length) groups.push({ label: 'PGY-1', people: buckets.pgy1 })
    if (buckets.pgy2.length) groups.push({ label: 'PGY-2', people: buckets.pgy2 })
    if (buckets.pgy3.length) groups.push({ label: 'PGY-3', people: buckets.pgy3 })
    if (buckets.other.length) groups.push({ label: 'Residents (Other)', people: buckets.other })
    if (buckets.faculty.length) groups.push({ label: 'Faculty', people: buckets.faculty })
    return groups
  }, [peopleData, personFilter])

  // Flat people list for row indexing
  const flatPeople = useMemo(() => personGroups.flatMap((g) => g.people), [personGroups])

  // Consolidated getters
  const getAmPm = useCallback(
    (personId: string, dateStr: string): { am?: ProcessedAssignment; pm?: ProcessedAssignment } => {
      const dateMap = assignmentLookup.get(personId)?.get(dateStr)
      return { am: dateMap?.get('AM'), pm: dateMap?.get('PM') }
    },
    [assignmentLookup]
  )

  const getConsolidatedAbbrev = useCallback(
    (personId: string, dateStr: string): string => {
      const { am, pm } = getAmPm(personId, dateStr)
      return consolidateAmPm(am?.abbreviation, pm?.abbreviation)
    },
    [getAmPm]
  )

  // Selection and clipboard hooks
  const {
    isSelected, selectionBounds, hasSelection,
    selectAll, clearSelection,
    onCellMouseDown, onCellMouseMove, onCellMouseUp,
  } = useCopyGridSelection()

  const gridData = useMemo(
    () => ({ people: flatPeople, days, getAbbreviation: getConsolidatedAbbrev }),
    [flatPeople, days, getConsolidatedAbbrev]
  )

  const { copyStatus, lastCopiedSize } = useCopyGridClipboard(containerRef, selectionBounds, gridData)

  // Pre-compute row offsets per group (avoids mutable counter during render)
  const groupRowOffsets = useMemo(() => {
    const offsets: number[] = []
    let offset = 0
    personGroups.forEach((group) => {
      offsets.push(offset)
      offset += group.people.length
    })
    return offsets
  }, [personGroups])

  // Ctrl+A handler on the container
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault()
        selectAll(flatPeople.length, days.length)
      }
    }
    container.addEventListener('keydown', handleKeyDown)
    return () => container.removeEventListener('keydown', handleKeyDown)
  }, [selectAll, flatPeople.length, days.length])

  // Loading
  const isLoading = blocksLoading || assignmentsLoading || peopleLoading || templatesLoading
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="ml-2 text-gray-600">Loading schedule...</span>
      </div>
    )
  }

  // Error
  const error = blocksError || assignmentsError || peopleError || templatesError
  if (error) {
    return <div className="p-4"><ErrorAlert message={error instanceof Error ? error.message : 'Failed to load schedule data'} /></div>
  }

  // Empty
  if (personGroups.length === 0) {
    return <EmptyState title="No People Found" description="Add residents and faculty to see them in the schedule." />
  }

  return (
    <div
      ref={containerRef}
      className="relative focus:outline-none"
      tabIndex={0}
      onMouseUp={onCellMouseUp}
    >
      {/* Toolbar */}
      <div className="flex items-center gap-3 mb-3 px-1">
        <button
          onClick={() => selectAll(flatPeople.length, days.length)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <ClipboardCopy className="w-4 h-4" />
          Select All
        </button>
        {hasSelection && (
          <button
            onClick={clearSelection}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Clear
          </button>
        )}
        {copyStatus === 'copied' && (
          <span className="inline-flex items-center gap-1 text-sm text-green-700 bg-green-50 px-2.5 py-1 rounded-md">
            <CheckCircle className="w-4 h-4" />
            Copied {lastCopiedSize}
          </span>
        )}
        {hasSelection && copyStatus === 'idle' && (
          <span className="text-sm text-gray-400">
            {(selectionBounds!.endRow - selectionBounds!.startRow + 1)} x {(selectionBounds!.endCol - selectionBounds!.startCol + 1)} selected — Ctrl+C to copy
          </span>
        )}
        {!hasSelection && (
          <span className="text-sm text-gray-400">
            Click and drag to select cells, then Ctrl+C to copy to Excel
          </span>
        )}
      </div>

      {/* Grid */}
      <div className="overflow-auto border border-gray-200 rounded-lg bg-white" style={{ maxHeight: 'calc(100vh - 280px)' }}>
        <table className="border-collapse select-none" style={{ minWidth: `${days.length * 52 + 160}px` }}>
          {/* Header */}
          <thead className="sticky top-0 z-20 bg-gray-50">
            <tr>
              <th className="sticky left-0 z-30 bg-gray-50 px-3 py-2 text-left text-xs font-semibold text-gray-600 border-b border-r border-gray-200 min-w-[150px]">
                Name
              </th>
              {days.map((day, colIdx) => {
                const weekend = isWeekend(day)
                return (
                  <th
                    key={colIdx}
                    className={`px-1 py-2 text-center text-xs font-medium border-b border-gray-200 min-w-[48px] ${
                      weekend ? 'bg-gray-100 text-gray-500' : 'text-gray-600'
                    }`}
                  >
                    <div>{format(day, 'EEE')}</div>
                    <div>{format(day, 'M/d')}</div>
                  </th>
                )
              })}
            </tr>
          </thead>

          {/* Body */}
          <tbody>
            {personGroups.map((group, groupIdx) => {
              const groupRows = group.people.map((person, personIdx) => {
                const thisRowIdx = groupRowOffsets[groupIdx] + personIdx
                return (
                  <tr key={person.id} className="hover:bg-blue-50/20">
                    {/* Sticky name column */}
                    <td className="sticky left-0 z-10 bg-white px-3 py-1.5 border-r border-b border-gray-200 text-sm font-medium text-gray-900 whitespace-nowrap">
                      {person.name}
                      <span className="ml-1.5 text-xs text-gray-400">
                        {person.type === 'faculty' ? (person.facultyRole ? formatFacultyRole(person.facultyRole) : 'Faculty') : `PGY-${person.pgyLevel}`}
                      </span>
                    </td>
                    {/* Day cells */}
                    {days.map((day, colIdx) => {
                      const dateStr = format(day, 'yyyy-MM-dd')
                      const { am, pm } = getAmPm(person.id, dateStr)
                      const abbrev = consolidateAmPm(am?.abbreviation, pm?.abbreviation)
                      const { activityType, fontColor, backgroundColor } = consolidateColor(am, pm)
                      const selected = isSelected(thisRowIdx, colIdx)
                      const weekend = isWeekend(day)

                      // Custom color from template
                      let customStyle: React.CSSProperties | undefined
                      let colorClass = ''
                      if (fontColor && backgroundColor) {
                        const textHex = tailwindToHex[fontColor] || fontColor
                        const bgHex = tailwindToHex[backgroundColor] || backgroundColor
                        customStyle = { color: textHex, backgroundColor: bgHex }
                      } else if (abbrev) {
                        colorClass = getActivityColorClass(activityType)
                      }

                      return (
                        <td
                          key={colIdx}
                          data-row={thisRowIdx}
                          data-col={colIdx}
                          onMouseDown={onCellMouseDown}
                          onMouseMove={onCellMouseMove}
                          className={`
                            px-0.5 py-1 text-center text-xs border-b border-gray-100 cursor-cell
                            ${weekend && !abbrev ? 'bg-gray-50' : ''}
                            ${selected ? 'ring-2 ring-inset ring-blue-400 bg-blue-50' : ''}
                            ${!selected && colorClass}
                          `}
                          style={!selected ? customStyle : undefined}
                          title={abbrev || undefined}
                        >
                          {abbrev}
                        </td>
                      )
                    })}
                  </tr>
                )
              })

              return (
                <React.Fragment key={group.label}>
                  {/* Group separator */}
                  {groupIdx > 0 && (
                    <tr>
                      <td
                        colSpan={days.length + 1}
                        className="bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-500 border-b border-gray-200"
                      >
                        {group.label}
                      </td>
                    </tr>
                  )}
                  {groupIdx === 0 && (
                    <tr>
                      <td
                        colSpan={days.length + 1}
                        className="bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-500 border-b border-gray-200"
                      >
                        {group.label}
                      </td>
                    </tr>
                  )}
                  {groupRows}
                </React.Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
