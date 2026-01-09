'use client'

import { useState, useMemo, useRef, useEffect, useId, useCallback } from 'react'
import { ChevronDown, Search, User, Users, X, Check, CheckSquare, Square } from 'lucide-react'
import { usePeople } from '@/lib/hooks'
import type { Person } from '@/types/api'

export interface MultiSelectPersonFilterProps {
  selectedPersonIds: Set<string>
  onSelectionChange: (personIds: Set<string>) => void
  /** If true, show only residents. If false, show all people. */
  residentsOnly?: boolean
  /** Label to show when nothing is selected */
  emptyLabel?: string
}

interface GroupedPeople {
  residents: Map<number, Person[]>
  faculty: Person[]
}

export function MultiSelectPersonFilter({
  selectedPersonIds,
  onSelectionChange,
  residentsOnly = false,
  emptyLabel = 'All People',
}: MultiSelectPersonFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const listboxId = useId()

  const { data: peopleData, isLoading } = usePeople()

  const people = useMemo(() => {
    const all = peopleData?.items ?? []
    return residentsOnly ? all.filter((p) => p.type === 'resident') : all
  }, [peopleData, residentsOnly])

  // Group people by type and PGY level
  const groupedPeople = useMemo<GroupedPeople>(() => {
    const residents = new Map<number, Person[]>()
    const faculty: Person[] = []

    people.forEach((person) => {
      if (person.type === 'resident' && person.pgyLevel !== null) {
        const existing = residents.get(person.pgyLevel) ?? []
        residents.set(person.pgyLevel, [...existing, person])
      } else if (person.type === 'faculty' && !residentsOnly) {
        faculty.push(person)
      }
    })

    // Sort each PGY group by name
    residents.forEach((group, level) => {
      residents.set(level, group.sort((a, b) => a.name.localeCompare(b.name)))
    })
    faculty.sort((a, b) => a.name.localeCompare(b.name))

    return { residents, faculty }
  }, [people, residentsOnly])

  // Filter people based on search query
  const filteredPeople = useMemo(() => {
    if (!searchQuery.trim()) return null

    const query = searchQuery.toLowerCase()
    return people.filter(
      (person) =>
        person.name.toLowerCase().includes(query) || person.email?.toLowerCase().includes(query)
    )
  }, [people, searchQuery])

  // Get display text for button
  const displayText = useMemo(() => {
    const count = selectedPersonIds.size
    if (count === 0) return emptyLabel
    if (count === 1) {
      const personId = Array.from(selectedPersonIds)[0]
      const person = people.find((p) => p.id === personId)
      return person?.name ?? 'Selected'
    }
    return `${count} selected`
  }, [selectedPersonIds, people, emptyLabel])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchQuery('')
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  // Handle keyboard navigation
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false)
      setSearchQuery('')
    }
  }

  const togglePerson = useCallback(
    (personId: string) => {
      const newSet = new Set(selectedPersonIds)
      if (newSet.has(personId)) {
        newSet.delete(personId)
      } else {
        newSet.add(personId)
      }
      onSelectionChange(newSet)
    },
    [selectedPersonIds, onSelectionChange]
  )

  const selectAll = useCallback(() => {
    const allIds = new Set(people.map((p) => p.id))
    onSelectionChange(allIds)
  }, [people, onSelectionChange])

  const clearAll = useCallback(() => {
    onSelectionChange(new Set())
  }, [onSelectionChange])

  const clearSearch = () => {
    setSearchQuery('')
    searchInputRef.current?.focus()
  }

  // Get sorted PGY levels
  const pgyLevels = Array.from(groupedPeople.residents.keys()).sort((a, b) => a - b)

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls={listboxId}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-md border
          bg-white hover:bg-gray-50 transition-colors
          focus:outline-none focus:ring-2 focus:ring-blue-500
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : 'border-gray-300'}
        `}
      >
        {selectedPersonIds.size === 0 ? (
          <Users className="w-4 h-4 text-gray-500" aria-hidden="true" />
        ) : selectedPersonIds.size === 1 ? (
          <User className="w-4 h-4 text-blue-600" aria-hidden="true" />
        ) : (
          <Users className="w-4 h-4 text-blue-600" aria-hidden="true" />
        )}
        <span className="text-sm font-medium text-gray-700">{displayText}</span>
        {selectedPersonIds.size > 0 && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              clearAll()
            }}
            className="p-0.5 hover:bg-gray-200 rounded"
            aria-label="Clear selection"
          >
            <X className="w-3 h-3 text-gray-400" aria-hidden="true" />
          </button>
        )}
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          id={listboxId}
          role="listbox"
          aria-label="Filter by people"
          aria-multiselectable="true"
          onKeyDown={handleKeyDown}
          className="absolute z-50 mt-1 w-80 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
        >
          {/* Search Input */}
          <div className="p-2 border-b border-gray-100">
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                aria-hidden="true"
              />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search people..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-8 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Search people by name or email"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                  aria-label="Clear search"
                >
                  <X className="w-3 h-3 text-gray-400" aria-hidden="true" />
                </button>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2 px-2 py-1.5 border-b border-gray-100 bg-gray-50">
            <button
              type="button"
              onClick={selectAll}
              className="px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={clearAll}
              className="px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded"
            >
              Clear All
            </button>
            <span className="ml-auto text-xs text-gray-500">
              {selectedPersonIds.size} / {people.length}
            </span>
          </div>

          {/* Options List */}
          <div className="max-h-80 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500 text-sm">Loading...</div>
            ) : filteredPeople ? (
              // Search Results
              filteredPeople.length > 0 ? (
                <div className="py-1">
                  {filteredPeople.map((person) => (
                    <CheckboxItem
                      key={person.id}
                      person={person}
                      isSelected={selectedPersonIds.has(person.id)}
                      onToggle={() => togglePerson(person.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="p-4 text-center text-gray-500 text-sm">
                  No people found matching &quot;{searchQuery}&quot;
                </div>
              )
            ) : (
              // Grouped List
              <>
                {/* Residents by PGY Level */}
                {pgyLevels.length > 0 && (
                  <div className="py-1">
                    <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Residents
                    </div>
                    {pgyLevels.map((level) => (
                      <div key={level}>
                        <div className="px-4 py-1 text-xs font-medium text-gray-400 flex items-center justify-between">
                          <span>PGY-{level}</span>
                          <span className="text-gray-300">
                            {groupedPeople.residents
                              .get(level)
                              ?.filter((p) => selectedPersonIds.has(p.id)).length ?? 0}
                            /{groupedPeople.residents.get(level)?.length ?? 0}
                          </span>
                        </div>
                        {groupedPeople.residents.get(level)?.map((person) => (
                          <CheckboxItem
                            key={person.id}
                            person={person}
                            isSelected={selectedPersonIds.has(person.id)}
                            onToggle={() => togglePerson(person.id)}
                            indent
                          />
                        ))}
                      </div>
                    ))}
                  </div>
                )}

                {/* Faculty */}
                {groupedPeople.faculty.length > 0 && (
                  <>
                    <div className="border-t border-gray-100 my-1" />
                    <div className="py-1">
                      <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center justify-between">
                        <span>Faculty</span>
                        <span className="text-gray-300 font-normal">
                          {groupedPeople.faculty.filter((p) => selectedPersonIds.has(p.id)).length}/
                          {groupedPeople.faculty.length}
                        </span>
                      </div>
                      {groupedPeople.faculty.map((person) => (
                        <CheckboxItem
                          key={person.id}
                          person={person}
                          isSelected={selectedPersonIds.has(person.id)}
                          onToggle={() => togglePerson(person.id)}
                        />
                      ))}
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

interface CheckboxItemProps {
  person: Person
  isSelected: boolean
  onToggle: () => void
  indent?: boolean
}

function CheckboxItem({ person, isSelected, onToggle, indent = false }: CheckboxItemProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={isSelected}
      onClick={onToggle}
      className={`
        w-full flex items-center gap-3 px-4 py-2 text-sm text-left
        hover:bg-gray-50 transition-colors
        ${indent ? 'pl-8' : ''}
        ${isSelected ? 'bg-blue-50' : ''}
      `}
    >
      {/* Checkbox */}
      <div className="flex-shrink-0">
        {isSelected ? (
          <CheckSquare className="w-4 h-4 text-blue-600" aria-hidden="true" />
        ) : (
          <Square className="w-4 h-4 text-gray-300" aria-hidden="true" />
        )}
      </div>

      {/* Avatar */}
      <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600 flex-shrink-0">
        {person.name.charAt(0).toUpperCase()}
      </div>

      {/* Name and details */}
      <div className="flex-1 min-w-0">
        <div className={`font-medium truncate ${isSelected ? 'text-blue-700' : 'text-gray-700'}`}>
          {person.name}
        </div>
        {person.type === 'faculty' && person.facultyRole && (
          <div className="text-xs text-gray-500 truncate capitalize">
            {person.facultyRole.replace('_', ' ')}
          </div>
        )}
      </div>

      {/* Selected indicator */}
      {isSelected && <Check className="w-4 h-4 text-blue-600 flex-shrink-0" aria-hidden="true" />}
    </button>
  )
}

export default MultiSelectPersonFilter
