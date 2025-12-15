'use client'

import { useState, useMemo, useRef, useEffect, useId } from 'react'
import { ChevronDown, Search, User, Users, X } from 'lucide-react'
import { usePeople } from '@/lib/hooks'
import { useAuth } from '@/contexts/AuthContext'
import type { Person } from '@/types/api'

export interface PersonFilterProps {
  selectedPersonId: string | null
  onSelect: (personId: string | null) => void
}

interface GroupedPeople {
  residents: Map<number, Person[]>
  faculty: Person[]
}

export function PersonFilter({ selectedPersonId, onSelect }: PersonFilterProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const listboxId = useId()

  const { user } = useAuth()
  const { data: peopleData, isLoading } = usePeople()

  const people = peopleData?.items ?? []

  // Group people by type and PGY level
  const groupedPeople = useMemo<GroupedPeople>(() => {
    const residents = new Map<number, Person[]>()
    const faculty: Person[] = []

    people.forEach((person) => {
      if (person.type === 'resident' && person.pgy_level !== null) {
        const existing = residents.get(person.pgy_level) ?? []
        residents.set(person.pgy_level, [...existing, person])
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
    return people.filter((person) =>
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
    if (selectedPersonId === 'me') return 'My Schedule'
    if (selectedPerson) return selectedPerson.name
    return 'All People'
  }, [selectedPersonId, selectedPerson])

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

  const handleSelect = (personId: string | null) => {
    onSelect(personId)
    setIsOpen(false)
    setSearchQuery('')
  }

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
        {selectedPersonId === 'me' ? (
          <User className="w-4 h-4 text-blue-600" />
        ) : selectedPersonId ? (
          <User className="w-4 h-4 text-gray-500" />
        ) : (
          <Users className="w-4 h-4 text-gray-500" />
        )}
        <span className="text-sm font-medium text-gray-700">{displayText}</span>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          id={listboxId}
          role="listbox"
          aria-label="Filter by person"
          onKeyDown={handleKeyDown}
          className="absolute z-50 mt-1 w-72 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
        >
          {/* Search Input */}
          {people.length > 10 && (
            <div className="p-2 border-b border-gray-100">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search people..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-8 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={clearSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                  >
                    <X className="w-3 h-3 text-gray-400" />
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Options List */}
          <div className="max-h-80 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-gray-500 text-sm">Loading...</div>
            ) : filteredPeople ? (
              // Search Results
              filteredPeople.length > 0 ? (
                <div className="py-1">
                  {filteredPeople.map((person) => (
                    <OptionItem
                      key={person.id}
                      person={person}
                      isSelected={selectedPersonId === person.id}
                      onSelect={() => handleSelect(person.id)}
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
                {/* All People Option */}
                <div className="py-1">
                  <button
                    type="button"
                    role="option"
                    aria-selected={selectedPersonId === null}
                    onClick={() => handleSelect(null)}
                    className={`
                      w-full flex items-center gap-3 px-4 py-2 text-sm text-left
                      hover:bg-gray-50 transition-colors
                      ${selectedPersonId === null ? 'bg-blue-50 text-blue-700' : 'text-gray-700'}
                    `}
                  >
                    <Users className="w-4 h-4" />
                    <span className="font-medium">All People</span>
                  </button>

                  {/* My Schedule Option */}
                  {user && (
                    <button
                      type="button"
                      role="option"
                      aria-selected={selectedPersonId === 'me'}
                      onClick={() => handleSelect('me')}
                      className={`
                        w-full flex items-center gap-3 px-4 py-2 text-sm text-left
                        hover:bg-gray-50 transition-colors
                        ${selectedPersonId === 'me' ? 'bg-blue-50 text-blue-700' : 'text-gray-700'}
                      `}
                    >
                      <User className="w-4 h-4" />
                      <span className="font-medium">My Schedule</span>
                    </button>
                  )}
                </div>

                {/* Separator */}
                <div className="border-t border-gray-100 my-1" />

                {/* Residents by PGY Level */}
                {pgyLevels.length > 0 && (
                  <div className="py-1">
                    <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      Residents
                    </div>
                    {pgyLevels.map((level) => (
                      <div key={level}>
                        <div className="px-4 py-1 text-xs font-medium text-gray-400">
                          PGY-{level}
                        </div>
                        {groupedPeople.residents.get(level)?.map((person) => (
                          <OptionItem
                            key={person.id}
                            person={person}
                            isSelected={selectedPersonId === person.id}
                            onSelect={() => handleSelect(person.id)}
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
                      <div className="px-4 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Faculty
                      </div>
                      {groupedPeople.faculty.map((person) => (
                        <OptionItem
                          key={person.id}
                          person={person}
                          isSelected={selectedPersonId === person.id}
                          onSelect={() => handleSelect(person.id)}
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

interface OptionItemProps {
  person: Person
  isSelected: boolean
  onSelect: () => void
  indent?: boolean
}

function OptionItem({ person, isSelected, onSelect, indent = false }: OptionItemProps) {
  return (
    <button
      type="button"
      role="option"
      aria-selected={isSelected}
      onClick={onSelect}
      className={`
        w-full flex items-center gap-3 px-4 py-2 text-sm text-left
        hover:bg-gray-50 transition-colors
        ${indent ? 'pl-8' : ''}
        ${isSelected ? 'bg-blue-50 text-blue-700' : 'text-gray-700'}
      `}
    >
      <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600">
        {person.name.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{person.name}</div>
        {person.email && (
          <div className="text-xs text-gray-500 truncate">{person.email}</div>
        )}
      </div>
    </button>
  )
}
