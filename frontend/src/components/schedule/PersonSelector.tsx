'use client';

import { useState, useMemo, useRef, useEffect } from 'react';
import { ChevronDown, Search, User, X } from 'lucide-react';
import type { Person } from '@/types/api';
import type { RiskTier } from '@/components/ui/RiskBar';

export interface PersonSelectorProps {
  /** List of people to select from */
  people: Person[];
  /** Currently selected person ID */
  selectedPersonId: string | null;
  /** Callback when selection changes */
  onSelect: (personId: string) => void;
  /** Current user's tier level - selector only visible for tier 1+ */
  tier: RiskTier;
  /** Whether the selector is loading */
  isLoading?: boolean;
  /** Whether to show the selector even for tier 0 (defaults to false) */
  forceShow?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * PersonSelector component for selecting a person's schedule to view.
 *
 * SECURITY: This component is only visible to Tier 1+ users (coordinators, admins).
 * Tier 0 users (residents, faculty viewing their own) never see the selector.
 * NO CSS hiding is used - the component simply doesn't render for Tier 0.
 *
 * WCAG 2.1 AA Compliance:
 * - Keyboard navigable with proper focus management
 * - Proper ARIA attributes for combobox pattern
 * - Visible focus indicators
 * - 4.5:1 contrast ratios maintained
 */
export function PersonSelector({
  people,
  selectedPersonId,
  onSelect,
  tier,
  isLoading = false,
  forceShow = false,
  className = '',
}: PersonSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const listboxIdRef = useRef(`person-selector-listbox-${Math.random().toString(36).slice(2)}`);
  const listboxId = listboxIdRef.current;

  // Determine if we should render (all hooks must be called before this)
  const shouldRender = tier > 0 || forceShow;

  // Find selected person
  const selectedPerson = useMemo(() => {
    if (!shouldRender) return null;
    return people.find((p) => p.id === selectedPersonId) ?? null;
  }, [people, selectedPersonId, shouldRender]);

  // Filter and sort people based on search query
  const filteredPeople = useMemo(() => {
    if (!shouldRender) return [];

    const query = searchQuery.toLowerCase().trim();

    let filtered = people;
    if (query) {
      filtered = people.filter((person) => {
        const nameMatch = person.name.toLowerCase().includes(query);
        const emailMatch = person.email?.toLowerCase().includes(query) ?? false;
        const typeMatch = person.type.toLowerCase().includes(query);
        const pgyMatch = person.pgyLevel
          ? `pgy${person.pgyLevel}`.includes(query) || `pgy-${person.pgyLevel}`.includes(query)
          : false;
        return nameMatch || emailMatch || typeMatch || pgyMatch;
      });
    }

    // Sort: residents by PGY level descending, then faculty, alphabetically within groups
    return [...filtered].sort((a, b) => {
      // Residents first
      if (a.type !== b.type) {
        return a.type === 'resident' ? -1 : 1;
      }
      // Within residents, sort by PGY level descending
      if (a.type === 'resident' && b.type === 'resident') {
        const pgyDiff = (b.pgyLevel ?? 0) - (a.pgyLevel ?? 0);
        if (pgyDiff !== 0) return pgyDiff;
      }
      // Alphabetical within same type/PGY
      return a.name.localeCompare(b.name);
    });
  }, [people, searchQuery, shouldRender]);

  // Close dropdown when clicking outside
  useEffect(() => {
    if (!shouldRender) return;

    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchQuery('');
        setFocusedIndex(-1);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [shouldRender]);

  // Reset focused index when filtered list changes
  useEffect(() => {
    if (!shouldRender) return;
    setFocusedIndex(-1);
  }, [searchQuery, shouldRender]);

  // Scroll focused item into view
  useEffect(() => {
    if (!shouldRender) return;
    if (focusedIndex >= 0 && listRef.current) {
      const focusedElement = listRef.current.children[focusedIndex] as HTMLElement;
      focusedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [focusedIndex, shouldRender]);

  // SECURITY: Don't render for Tier 0 unless explicitly forced
  // This is NOT CSS hiding - the component genuinely doesn't mount
  // All hooks are called above this point to comply with Rules of Hooks
  if (!shouldRender) {
    return null;
  }

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      // Focus input when opening
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setSearchQuery('');
      setFocusedIndex(-1);
    }
  };

  const handleSelect = (person: Person) => {
    onSelect(person.id);
    setIsOpen(false);
    setSearchQuery('');
    setFocusedIndex(-1);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setFocusedIndex((prev) =>
            prev < filteredPeople.length - 1 ? prev + 1 : prev
          );
        }
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (isOpen) {
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : 0));
        }
        break;
      case 'Enter':
        event.preventDefault();
        if (isOpen && focusedIndex >= 0 && filteredPeople[focusedIndex]) {
          handleSelect(filteredPeople[focusedIndex]);
        } else if (!isOpen) {
          setIsOpen(true);
        }
        break;
      case 'Escape':
        event.preventDefault();
        setIsOpen(false);
        setSearchQuery('');
        setFocusedIndex(-1);
        break;
      case 'Tab':
        if (isOpen) {
          setIsOpen(false);
          setSearchQuery('');
        }
        break;
    }
  };

  const formatPersonLabel = (person: Person): string => {
    if (person.type === 'resident' && person.pgyLevel) {
      return `${person.name} (PGY-${person.pgyLevel})`;
    }
    return `${person.name} (Faculty)`;
  };

  return (
    <div
      ref={containerRef}
      className={`relative ${className}`}
      onKeyDown={handleKeyDown}
    >
      {/* Trigger Button */}
      <button
        type="button"
        onClick={handleToggle}
        disabled={isLoading}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg border
          bg-white text-gray-900 border-gray-300
          hover:bg-gray-50 hover:border-gray-400
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors min-w-[200px]
        `}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-controls={listboxId}
        aria-label="Select person to view schedule"
      >
        <User className="w-4 h-4 text-gray-500 flex-shrink-0" />
        <span className="flex-1 text-left truncate">
          {isLoading
            ? 'Loading...'
            : selectedPerson
              ? formatPersonLabel(selectedPerson)
              : 'Select person...'}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          className="absolute z-50 mt-1 w-full min-w-[280px] bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
          role="presentation"
        >
          {/* Search Input */}
          <div className="p-2 border-b border-gray-100">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by name, email, or PGY..."
                className="w-full pl-9 pr-8 py-2 text-sm border border-gray-200 rounded-md
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                aria-label="Search people"
                aria-controls={listboxId}
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                  aria-label="Clear search"
                >
                  <X className="w-3 h-3 text-gray-400" />
                </button>
              )}
            </div>
          </div>

          {/* People List */}
          <ul
            ref={listRef}
            id={listboxId}
            role="listbox"
            aria-label="Select a person"
            className="max-h-64 overflow-y-auto py-1"
          >
            {filteredPeople.length === 0 ? (
              <li className="px-4 py-3 text-sm text-gray-500 text-center">
                No people found
              </li>
            ) : (
              filteredPeople.map((person, index) => {
                const isSelected = person.id === selectedPersonId;
                const isFocused = index === focusedIndex;

                return (
                  <li
                    key={person.id}
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => handleSelect(person)}
                    onMouseEnter={() => setFocusedIndex(index)}
                    className={`
                      flex items-center gap-3 px-4 py-2 cursor-pointer
                      ${isSelected ? 'bg-blue-50 text-blue-900' : 'text-gray-900'}
                      ${isFocused && !isSelected ? 'bg-gray-100' : ''}
                      ${!isSelected && !isFocused ? 'hover:bg-gray-50' : ''}
                    `}
                  >
                    <div
                      className={`
                        w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                        ${person.type === 'resident' ? 'bg-blue-100' : 'bg-purple-100'}
                      `}
                    >
                      <User
                        className={`w-4 h-4 ${person.type === 'resident' ? 'text-blue-600' : 'text-purple-600'}`}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{person.name}</div>
                      <div className="text-xs text-gray-500 truncate">
                        {person.type === 'resident'
                          ? `PGY-${person.pgyLevel}`
                          : 'Faculty'}
                        {person.email && ` - ${person.email}`}
                      </div>
                    </div>
                    {isSelected && (
                      <span className="text-blue-600 text-sm font-medium">Selected</span>
                    )}
                  </li>
                );
              })
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
