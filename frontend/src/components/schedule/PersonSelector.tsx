'use client'

import { useState, useMemo, useRef, useEffect, useId } from 'react'
import { ChevronDown, Search, User, Users, X } from 'lucide-react'
import type { Person } from '@/types/api'

export interface PersonSelectorProps {
  people: Person[]
  selectedPersonId: string | null
  onSelect: (personId: string | null) => void
  tier: number
  isLoading?: boolean
  className?: string
}

interface GroupedPeople {
  residents: Map<number, Person[]>
  faculty: Person[]
}

/**
 * PersonSelector - Tier-aware person selection dropdown
 *
 * Only renders for Tier 1+ users (coordinators/admins).
 * Tier 0 users (residents/faculty) should not see this component at all.
 */
export function PersonSelector({
  people,
  selectedPersonId,
  onSelect,
  tier,
  isLoading = false,
  className = '',
}: PersonSelectorProps) {
  // All hooks must be called unconditionally (React rules of hooks)
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const listboxId = useId()

  // Group people by type and PGY level
  const groupedPeople = useMemo<GroupedPeople>(() => {
    const residents = new Map<number, Person[]>()
    const faculty: Person[] = []

    people.forEach((person) => {
      if (person.type === 'resident' && person.pgyLevel !== null) {
        const existing = residents.get(person.pgyLevel) ?? []
        residents.set(person.pgyLevel, [...existing, person])
      } else if (person.type === 'faculty') {
        faculty.push(person)
      }
    })

    // Sort each PGY group by name
    residents.forEach((group, level) => {
      residents.set(level, group.sort((a, b) => a.name.localeCompare(b.name)))
    })
    faculty.sort((a, b) => a.name.localeCompare(b.name))

    return { residents, faculty }
  }, [people])

  // Filter people based on search query
  const filteredPeople = useMemo(() => {
    if (!searchQuery.trim()) return null

    const query = searchQuery.toLowerCase()
    return people.filter(
      (person) =>
        person.name.toLowerCase().includes(query) ||
        person.email?.toLowerCase().includes(query)
    )
  }, [people, searchQuery])

  // Get selected person details
  const selectedPerson = useMemo(() => {
    if (!selectedPersonId) return null
    return people.find((p) => p.id === selectedPersonId) ?? null
  }, [people, selectedPersonId])

  // Get display text for button
  const displayText = useMemo(() => {
    if (selectedPerson) return selectedPerson.name
    return 'Select Person'
  }, [selectedPerson])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
        setSearchQuery('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus search input when opening
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  // Tier 0 users should not see the selector - check AFTER all hooks
  if (tier < 1) {
    return null
  }

  const handleSelect = (personId: string | null) => {
    onSelect(personId)
    setIsOpen(false)
    setSearchQuery('')
  }

  const renderPersonOption = (person: Person) => (
    <button
      key={person.id}
      type="button"
      role="option"
      aria-selected={selectedPersonId === person.id}
      className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 ${
        selectedPersonId === person.id
          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
          : 'text-gray-700 dark:text-gray-300'
      }`}
      onClick={() => handleSelect(person.id)}
    >
      <User className="h-4 w-4 flex-shrink-0" />
      <span className="truncate">{person.name}</span>
    </button>
  )

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
      >
        <Users className="h-4 w-4" />
        <span className="truncate max-w-[200px]">
          {isLoading ? 'Loading...' : displayText}
        </span>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          id={listboxId}
          role="listbox"
          className="absolute z-50 mt-1 w-72 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
        >
          {/* Search input */}
          <div className="p-2 border-b border-gray-200 dark:border-gray-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search people..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>

          {/* Results */}
          <div className="max-h-64 overflow-y-auto">
            {filteredPeople ? (
              // Search results
              filteredPeople.length > 0 ? (
                filteredPeople.map(renderPersonOption)
              ) : (
                <div className="px-3 py-4 text-sm text-gray-500 text-center">
                  No results found
                </div>
              )
            ) : (
              // Grouped view
              <>
                {/* Residents by PGY */}
                {Array.from(groupedPeople.residents.entries())
                  .sort(([a], [b]) => b - a) // PGY-3 first
                  .map(([pgyLevel, residents]) => (
                    <div key={`pgy-${pgyLevel}`}>
                      <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 uppercase tracking-wider">
                        PGY-{pgyLevel}
                      </div>
                      {residents.map(renderPersonOption)}
                    </div>
                  ))}

                {/* Faculty */}
                {groupedPeople.faculty.length > 0 && (
                  <div>
                    <div className="px-3 py-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 uppercase tracking-wider">
                      Faculty
                    </div>
                    {groupedPeople.faculty.map(renderPersonOption)}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
