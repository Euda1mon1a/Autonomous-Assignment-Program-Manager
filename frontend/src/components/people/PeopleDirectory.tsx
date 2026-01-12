'use client';

/**
 * PeopleDirectory Component
 *
 * Read-only directory view of all people (Tier 0).
 * Displays residents and faculty with search, filtering, and export capabilities.
 * No edit or delete operations available in this view.
 *
 * WCAG 2.1 AA Compliance:
 * - Proper focus management for interactive elements
 * - Sufficient color contrast ratios
 * - Screen reader accessible content
 */
import { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  User,
  GraduationCap,
  Mail,
  Users,
  X,
} from 'lucide-react';
import { usePeople, type PeopleFilters } from '@/hooks/usePeople';
import { useDebounce } from '@/hooks/useDebounce';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ExportButton } from '@/components/ExportButton';
import { EmptyState } from '@/components/EmptyState';
import type { Person } from '@/types/api';

// ============================================================================
// Types
// ============================================================================

type PersonTypeFilter = 'all' | 'resident' | 'faculty';

interface DirectoryFilters {
  type: PersonTypeFilter;
  pgyLevel: number | '';
  search: string;
}

// ============================================================================
// Constants
// ============================================================================

const exportColumns = [
  { key: 'name', header: 'Name' },
  { key: 'type', header: 'Type' },
  { key: 'pgyLevel', header: 'PGY Level' },
  { key: 'email', header: 'Email' },
];

// ============================================================================
// Subcomponents
// ============================================================================

interface PersonCardProps {
  person: Person;
}

function PersonCard({ person }: PersonCardProps) {
  const isResident = person.type === 'resident';

  return (
    <article
      className="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg p-4 hover:shadow-md dark:hover:shadow-slate-900/50 transition-shadow"
      aria-label={`${person.name}, ${isResident ? `PGY-${person.pgyLevel} Resident` : 'Faculty'}`}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div
          className={`
            flex-shrink-0 p-3 rounded-full
            ${isResident ? 'bg-blue-100 dark:bg-blue-500/20' : 'bg-purple-100 dark:bg-purple-500/20'}
          `}
          aria-hidden="true"
        >
          {isResident ? (
            <GraduationCap className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          ) : (
            <User className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-900 dark:text-white truncate">
            {person.name}
          </h3>
          <p className="text-sm text-slate-600 dark:text-slate-300 mt-0.5">
            {isResident ? (
              <span className="inline-flex items-center gap-1">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
                  PGY-{person.pgyLevel}
                </span>
                <span>Resident</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1">
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-400">
                  Faculty
                </span>
                {person.facultyRole && (
                  <span className="text-slate-500 dark:text-slate-400">
                    ({person.facultyRole.toUpperCase()})
                  </span>
                )}
              </span>
            )}
          </p>

          {/* Contact Info */}
          {person.email && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-2 flex items-center gap-1.5">
              <Mail className="w-4 h-4" aria-hidden="true" />
              <a
                href={`mailto:${person.email}`}
                className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded"
              >
                {person.email}
              </a>
            </p>
          )}

          {/* Specialties */}
          {person.specialties && person.specialties.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {person.specialties.map((specialty, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                >
                  {specialty}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PeopleDirectory() {
  // Filters state
  const [filters, setFilters] = useState<DirectoryFilters>({
    type: 'all',
    pgyLevel: '',
    search: '',
  });

  // Debounce search for performance
  const debouncedSearch = useDebounce(filters.search, 300);

  // Build API filters
  const apiFilters: PeopleFilters | undefined =
    filters.type === 'all'
      ? undefined
      : { role: filters.type };

  // Fetch people
  const {
    data: peopleData,
    isLoading,
    isError,
    error,
    refetch,
  } = usePeople(apiFilters);

  // Client-side filtering for search and PGY level
  const filteredPeople = useMemo(() => {
    if (!peopleData?.items) return [];

    let filtered = [...peopleData.items];

    // Search filter
    if (debouncedSearch) {
      const searchLower = debouncedSearch.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(searchLower) ||
          p.email?.toLowerCase().includes(searchLower)
      );
    }

    // PGY level filter
    if (filters.pgyLevel !== '') {
      filtered = filtered.filter((p) => p.pgyLevel === filters.pgyLevel);
    }

    // Sort alphabetically by name
    filtered.sort((a, b) => a.name.localeCompare(b.name));

    return filtered;
  }, [peopleData?.items, debouncedSearch, filters.pgyLevel]);

  // Prepare export data
  const exportData = useMemo(() => {
    return filteredPeople as unknown as Record<string, unknown>[];
  }, [filteredPeople]);

  // Clear search handler
  const handleClearSearch = () => {
    setFilters((prev) => ({ ...prev, search: '' }));
  };

  return (
    <div className="space-y-6">
      {/* Filters Bar */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />
          <input
            type="search"
            placeholder="Search by name or email..."
            value={filters.search}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, search: e.target.value }))
            }
            className="w-full pl-10 pr-10 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            aria-label="Search people"
          />
          {filters.search && (
            <button
              onClick={handleClearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Type Filter */}
        <div className="flex items-center gap-2">
          <Filter
            className="w-4 h-4 text-slate-400 dark:text-slate-500"
            aria-hidden="true"
          />
          <select
            value={filters.type}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                type: e.target.value as PersonTypeFilter,
                // Reset PGY filter when switching to faculty
                pgyLevel: e.target.value === 'faculty' ? '' : prev.pgyLevel,
              }))
            }
            className="px-3 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter by type"
          >
            <option value="all">All Types</option>
            <option value="resident">Residents</option>
            <option value="faculty">Faculty</option>
          </select>
        </div>

        {/* PGY Level Filter (only for residents) */}
        {(filters.type === 'all' || filters.type === 'resident') && (
          <select
            value={filters.pgyLevel}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                pgyLevel: e.target.value ? Number(e.target.value) : '',
              }))
            }
            className="px-3 py-2 bg-white dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filter by PGY level"
          >
            <option value="">All PGY Levels</option>
            {[1, 2, 3, 4, 5].map((level) => (
              <option key={level} value={level}>
                PGY-{level}
              </option>
            ))}
          </select>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Stats */}
        <div className="text-sm text-slate-600 dark:text-slate-400">
          {filteredPeople.length} {filteredPeople.length === 1 ? 'person' : 'people'}
          {peopleData?.total && peopleData.total !== filteredPeople.length && (
            <span> of {peopleData.total}</span>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <ExportButton
            data={exportData}
            filename="people-directory"
            columns={exportColumns}
          />
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="p-2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
            title="Refresh"
            aria-label="Refresh people list"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      ) : isError ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
          <p className="text-red-700 dark:text-red-400 mb-4">
            {error?.message || 'Failed to load people directory'}
          </p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-100 dark:bg-red-800/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-800/50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Retry
          </button>
        </div>
      ) : filteredPeople.length === 0 ? (
        <div className="bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg p-8">
          <EmptyState
            icon={Users}
            title={filters.search || filters.pgyLevel ? 'No matches found' : 'No people yet'}
            description={
              filters.search || filters.pgyLevel
                ? 'Try adjusting your search or filter criteria.'
                : 'People will appear here once added to the system.'
            }
          />
        </div>
      ) : (
        <div
          className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          role="list"
          aria-label="People directory"
        >
          {filteredPeople.map((person) => (
            <div key={person.id} role="listitem">
              <PersonCard person={person} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
