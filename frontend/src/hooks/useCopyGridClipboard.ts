'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { format } from 'date-fns'
import type { SelectionBounds } from './useCopyGridSelection'

interface GridData {
  /** Flat array of people in display order (matching row indices) */
  people: { id: string; name: string }[]
  /** Array of days in display order (matching column indices) */
  days: Date[]
  /** Get the consolidated abbreviation for a person on a date */
  getAbbreviation: (personId: string, dateStr: string) => string
}

interface UseCopyGridClipboardReturn {
  /** 'idle' | 'copied' — resets to idle after 2s */
  copyStatus: 'idle' | 'copied'
  /** e.g. "5 x 28" after last copy */
  lastCopiedSize: string
}

/**
 * Build a TSV string from the grid data within the selection bounds.
 * Always includes row headers (person names) and column headers (dates).
 * Exported for testing.
 */
export function buildTSV(
  gridData: GridData,
  bounds: SelectionBounds
): string {
  const { people, days, getAbbreviation } = gridData
  const lines: string[] = []

  // Header row: empty corner cell + selected date headers
  const headerCells = ['']
  for (let col = bounds.startCol; col <= bounds.endCol; col++) {
    const day = days[col]
    headerCells.push(day ? format(day, 'EEE M/d') : '')
  }
  lines.push(headerCells.join('\t'))

  // Data rows
  for (let row = bounds.startRow; row <= bounds.endRow; row++) {
    const person = people[row]
    if (!person) continue

    const rowCells = [person.name]
    for (let col = bounds.startCol; col <= bounds.endCol; col++) {
      const day = days[col]
      if (!day) {
        rowCells.push('')
        continue
      }
      const dateStr = format(day, 'yyyy-MM-dd')
      rowCells.push(getAbbreviation(person.id, dateStr))
    }
    lines.push(rowCells.join('\t'))
  }

  return lines.join('\n')
}

async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Fallback for non-secure contexts
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    const success = document.execCommand('copy')
    document.body.removeChild(textarea)
    return success
  }
}

export function useCopyGridClipboard(
  containerRef: React.RefObject<HTMLElement | null>,
  selectionBounds: SelectionBounds | null,
  gridData: GridData
): UseCopyGridClipboardReturn {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied'>('idle')
  const [lastCopiedSize, setLastCopiedSize] = useState('')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const handleCopy = useCallback(async () => {
    if (!selectionBounds) return

    const tsv = buildTSV(gridData, selectionBounds)
    const success = await copyToClipboard(tsv)

    if (success) {
      const rows = selectionBounds.endRow - selectionBounds.startRow + 1
      const cols = selectionBounds.endCol - selectionBounds.startCol + 1
      setLastCopiedSize(`${rows} x ${cols}`)
      setCopyStatus('copied')

      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => setCopyStatus('idle'), 2000)
    }
  }, [selectionBounds, gridData])

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+C / Cmd+C
      if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        if (selectionBounds) {
          e.preventDefault()
          handleCopy()
        }
      }
    }

    container.addEventListener('keydown', handleKeyDown)
    return () => container.removeEventListener('keydown', handleKeyDown)
  }, [containerRef, selectionBounds, handleCopy])

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  return { copyStatus, lastCopiedSize }
}
