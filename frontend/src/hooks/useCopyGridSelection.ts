'use client'

import { useState, useCallback, useRef } from 'react'

export interface SelectionBounds {
  startRow: number
  endRow: number
  startCol: number
  endCol: number
}

interface CellCoord {
  row: number
  col: number
}

interface UseCopyGridSelectionReturn {
  /** Whether a specific cell is in the current selection */
  isSelected: (row: number, col: number) => boolean
  /** Current selection bounds, or null if no selection */
  selectionBounds: SelectionBounds | null
  /** Whether any cells are selected */
  hasSelection: boolean
  /** Select all data cells */
  selectAll: (totalRows: number, totalCols: number) => void
  /** Clear the current selection */
  clearSelection: () => void
  /** Mouse event handlers to attach to grid cells via data-row/data-col attributes */
  onCellMouseDown: (e: React.MouseEvent) => void
  onCellMouseMove: (e: React.MouseEvent) => void
  onCellMouseUp: () => void
}

function getCellCoord(e: React.MouseEvent): CellCoord | null {
  const target = (e.target as HTMLElement).closest('[data-row][data-col]') as HTMLElement | null
  if (!target) return null
  const row = parseInt(target.dataset.row!, 10)
  const col = parseInt(target.dataset.col!, 10)
  if (isNaN(row) || isNaN(col)) return null
  return { row, col }
}

function computeBounds(anchor: CellCoord, current: CellCoord): SelectionBounds {
  return {
    startRow: Math.min(anchor.row, current.row),
    endRow: Math.max(anchor.row, current.row),
    startCol: Math.min(anchor.col, current.col),
    endCol: Math.max(anchor.col, current.col),
  }
}

export function useCopyGridSelection(): UseCopyGridSelectionReturn {
  const [anchor, setAnchor] = useState<CellCoord | null>(null)
  const [current, setCurrent] = useState<CellCoord | null>(null)
  const isDragging = useRef(false)

  const selectionBounds: SelectionBounds | null =
    anchor && current ? computeBounds(anchor, current) : null

  const hasSelection = selectionBounds !== null

  const isSelected = useCallback(
    (row: number, col: number): boolean => {
      if (!selectionBounds) return false
      return (
        row >= selectionBounds.startRow &&
        row <= selectionBounds.endRow &&
        col >= selectionBounds.startCol &&
        col <= selectionBounds.endCol
      )
    },
    [selectionBounds]
  )

  const selectAll = useCallback((totalRows: number, totalCols: number) => {
    setAnchor({ row: 0, col: 0 })
    setCurrent({ row: totalRows - 1, col: totalCols - 1 })
  }, [])

  const clearSelection = useCallback(() => {
    setAnchor(null)
    setCurrent(null)
    isDragging.current = false
  }, [])

  const onCellMouseDown = useCallback((e: React.MouseEvent) => {
    const coord = getCellCoord(e)
    if (!coord) return

    // Shift+click extends from existing anchor
    if (e.shiftKey && anchor) {
      setCurrent(coord)
      return
    }

    setAnchor(coord)
    setCurrent(coord)
    isDragging.current = true

    // Prevent text selection during drag
    e.preventDefault()
  }, [anchor])

  const onCellMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging.current) return
    const coord = getCellCoord(e)
    if (!coord) return
    setCurrent(coord)
  }, [])

  const onCellMouseUp = useCallback(() => {
    isDragging.current = false
  }, [])

  return {
    isSelected,
    selectionBounds,
    hasSelection,
    selectAll,
    clearSelection,
    onCellMouseDown,
    onCellMouseMove,
    onCellMouseUp,
  }
}
