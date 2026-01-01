'use client'

import { useState, useRef, useEffect } from 'react'
import { Download, ChevronDown, Loader2 } from 'lucide-react'
import { exportToCSV, exportToJSON, type Column } from '@/lib/export'

interface ExportButtonProps {
  data: Record<string, unknown>[]
  filename: string
  columns: Column[]
}

export function ExportButton({ data, filename, columns }: ExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close dropdown on escape key
  useEffect(() => {
    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey)
      return () => document.removeEventListener('keydown', handleEscapeKey)
    }
  }, [isOpen])

  const handleExport = async (format: 'csv' | 'json') => {
    if (!data || data.length === 0) {
      return
    }

    setIsExporting(true)

    try {
      // Small delay for UX feedback
      await new Promise(resolve => setTimeout(resolve, 200))

      if (format === 'csv') {
        exportToCSV(data, filename, columns)
      } else {
        exportToJSON(data, filename)
      }
    } finally {
      setIsExporting(false)
      setIsOpen(false)
    }
  }

  const isDisabled = !data || data.length === 0

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isDisabled || isExporting}
        className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label={isExporting ? 'Exporting data...' : 'Export data menu'}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setIsOpen(!isOpen)
          }
        }}
      >
        {isExporting ? (
          <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
        ) : (
          <Download className="w-4 h-4" aria-hidden="true" />
        )}
        Export
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-40 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10"
          role="menu"
          aria-label="Export format options"
        >
          <button
            onClick={() => handleExport('csv')}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            role="menuitem"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                handleExport('csv')
              } else if (e.key === 'ArrowDown') {
                e.preventDefault()
                ;(e.currentTarget.nextElementSibling as HTMLButtonElement)?.focus()
              }
            }}
          >
            Export as CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            role="menuitem"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                handleExport('json')
              } else if (e.key === 'ArrowUp') {
                e.preventDefault()
                ;(e.currentTarget.previousElementSibling as HTMLButtonElement)?.focus()
              }
            }}
          >
            Export as JSON
          </button>
        </div>
      )}
    </div>
  )
}
