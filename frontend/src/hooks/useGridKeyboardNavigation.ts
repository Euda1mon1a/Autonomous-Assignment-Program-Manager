/**
 * Grid Keyboard Navigation Hook
 *
 * Implements WAI-ARIA Grid pattern keyboard navigation:
 * - Arrow keys move focus between cells
 * - Tab/Shift+Tab move focus in/out of the grid
 * - Enter/Space activate the focused cell
 * - Home/End move to first/last cell in row
 *
 * @see https://www.w3.org/WAI/ARIA/apg/patterns/grid/
 */

import { useCallback, useEffect, useRef, useState } from 'react'

export interface GridPosition {
  row: number
  col: number
}

export interface UseGridKeyboardNavigationOptions {
  /** Total number of rows (data rows, excluding header) */
  rowCount: number
  /** Total number of columns (data columns, excluding row header) */
  colCount: number
  /** Callback when Enter/Space is pressed on a cell */
  onCellActivate?: (position: GridPosition) => void
}

export interface UseGridKeyboardNavigationReturn {
  /** Currently focused cell position (null if grid not focused) */
  focusedCell: GridPosition | null
  /** Props to spread on the grid container (table element) */
  gridProps: {
    ref: React.RefCallback<HTMLElement>
    onKeyDown: (e: React.KeyboardEvent) => void
    role: 'grid'
  }
  /** Get props for a specific cell */
  /* eslint-disable @typescript-eslint/naming-convention -- HTML data-* and aria-* attributes require hyphenated names */
  getCellProps: (row: number, col: number) => {
    tabIndex: number
    'data-row': number
    'data-col': number
    onFocus: () => void
    onClick: () => void
    role: 'gridcell'
    'aria-selected': boolean
  }
  /* eslint-enable @typescript-eslint/naming-convention */
  /** Set focus to a specific cell */
  setFocusedCell: (position: GridPosition | null) => void
}

/**
 * Hook providing WAI-ARIA compliant keyboard navigation for grid components.
 *
 * Uses a roving tabIndex pattern: only the active cell has tabIndex=0,
 * all other cells have tabIndex=-1. This allows Tab to move focus
 * in/out of the grid while arrow keys navigate within.
 */
export function useGridKeyboardNavigation({
  rowCount,
  colCount,
  onCellActivate,
}: UseGridKeyboardNavigationOptions): UseGridKeyboardNavigationReturn {
  const [focusedCell, setFocusedCell] = useState<GridPosition | null>(null)
  const gridRef = useRef<HTMLElement | null>(null)

  // Clamp or clear focused cell when grid dimensions shrink (e.g., person filter)
  useEffect(() => {
    if (!focusedCell) return
    if (rowCount === 0 || colCount === 0) {
      setFocusedCell(null)
      return
    }
    if (focusedCell.row >= rowCount || focusedCell.col >= colCount) {
      setFocusedCell({
        row: Math.min(focusedCell.row, rowCount - 1),
        col: Math.min(focusedCell.col, colCount - 1),
      })
    }
  }, [rowCount, colCount]) // eslint-disable-line react-hooks/exhaustive-deps -- focusedCell intentionally excluded to avoid infinite loop

  const focusCell = useCallback(
    (row: number, col: number) => {
      // Clamp to valid range
      const clampedRow = Math.max(0, Math.min(row, rowCount - 1))
      const clampedCol = Math.max(0, Math.min(col, colCount - 1))
      setFocusedCell({ row: clampedRow, col: clampedCol })

      // Focus the DOM element (scoped to this grid container)
      requestAnimationFrame(() => {
        const container = gridRef.current ?? document
        const cell = container.querySelector(
          `[data-row="${clampedRow}"][data-col="${clampedCol}"]`
        ) as HTMLElement | null
        cell?.focus()
      })
    },
    [rowCount, colCount]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (rowCount === 0 || colCount === 0) return

      const current = focusedCell || { row: 0, col: 0 }

      switch (e.key) {
        case 'ArrowRight': {
          e.preventDefault()
          const nextCol = current.col + 1
          if (nextCol < colCount) {
            focusCell(current.row, nextCol)
          }
          break
        }

        case 'ArrowLeft': {
          e.preventDefault()
          const prevCol = current.col - 1
          if (prevCol >= 0) {
            focusCell(current.row, prevCol)
          }
          break
        }

        case 'ArrowDown': {
          e.preventDefault()
          const nextRow = current.row + 1
          if (nextRow < rowCount) {
            focusCell(nextRow, current.col)
          }
          break
        }

        case 'ArrowUp': {
          e.preventDefault()
          const prevRow = current.row - 1
          if (prevRow >= 0) {
            focusCell(prevRow, current.col)
          }
          break
        }

        case 'Home': {
          e.preventDefault()
          focusCell(current.row, 0)
          break
        }

        case 'End': {
          e.preventDefault()
          focusCell(current.row, colCount - 1)
          break
        }

        case 'Enter':
        case ' ': {
          e.preventDefault()
          if (focusedCell) {
            onCellActivate?.(focusedCell)
          }
          break
        }

        default:
          break
      }
    },
    [focusedCell, rowCount, colCount, focusCell, onCellActivate]
  )

  const getCellProps = useCallback(
    (row: number, col: number) => {
      const isFocused =
        focusedCell !== null &&
        focusedCell.row === row &&
        focusedCell.col === col

      // Roving tabIndex: first cell gets 0 if nothing focused, focused cell gets 0
      const isFirstCell = row === 0 && col === 0
      const tabIndex = isFocused ? 0 : focusedCell === null && isFirstCell ? 0 : -1

      /* eslint-disable @typescript-eslint/naming-convention -- HTML data-* and aria-* attributes */
      return {
        tabIndex,
        'data-row': row,
        'data-col': col,
        onFocus: () => setFocusedCell({ row, col }),
        onClick: () => {
          setFocusedCell({ row, col })
          onCellActivate?.({ row, col })
        },
        role: 'gridcell' as const,
        'aria-selected': isFocused,
      }
      /* eslint-enable @typescript-eslint/naming-convention */
    },
    [focusedCell, onCellActivate]
  )

  const gridProps = {
    ref: (el: HTMLElement | null) => {
      gridRef.current = el
    },
    onKeyDown: handleKeyDown,
    role: 'grid' as const,
  }

  return {
    focusedCell,
    gridProps,
    getCellProps,
    setFocusedCell,
  }
}
