'use client';

/**
 * FacultyPanel - Edit any faculty's weekly template (Tier 1+)
 *
 * Allows coordinators and admins to select any faculty member
 * and edit their weekly activity template.
 */

import { useState, useMemo } from 'react';
import { Calendar, Search, Loader2, ChevronDown, User } from 'lucide-react';
import { useFaculty } from '@/hooks/usePeople';
import { FacultyWeeklyEditor } from '@/components/FacultyWeeklyEditor';
import type { FacultyRole } from '@/types/faculty-activity';

// Role display names for badges
const FACULTY_ROLE_LABELS: Record<string, string> = {
  pd: 'Program Director',
  apd: 'Assoc. Program Director',
  oic: 'OIC',
  core: 'Core Faculty',
  adjunct: 'Adjunct',
  clinical_staff: 'Clinical Staff',
};

export function FacultyPanel() {
  const [selectedFacultyId, setSelectedFacultyId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Fetch faculty list
  const { data: facultyData, isLoading: facultyLoading } = useFaculty();

  // Filter faculty by search term
  const filteredFaculty = useMemo(() => {
    const faculty = facultyData?.items ?? [];
    if (!searchTerm) return faculty;

    const search = searchTerm.toLowerCase();
    return faculty.filter(
      (f) =>
        f.name.toLowerCase().includes(search) ||
        f.email?.toLowerCase().includes(search) ||
        f.facultyRole?.toLowerCase().includes(search)
    );
  }, [facultyData, searchTerm]);

  // Get selected faculty details
  const selectedFaculty = useMemo(() => {
    if (!selectedFacultyId || !facultyData?.items) return null;
    return facultyData.items.find((f) => f.id === selectedFacultyId) ?? null;
  }, [selectedFacultyId, facultyData]);

  // Loading state
  if (facultyLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Faculty Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Faculty Member
        </label>

        <div className="relative">
          {/* Search/Select Input */}
          <div
            className="relative cursor-pointer"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          >
            <div className="w-full px-4 py-2.5 pr-10 border border-gray-300 rounded-lg bg-white flex items-center gap-3">
              {selectedFaculty ? (
                <>
                  <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">
                      {selectedFaculty.name}
                    </div>
                    {selectedFaculty.facultyRole && (
                      <div className="text-xs text-gray-500">
                        {FACULTY_ROLE_LABELS[selectedFaculty.facultyRole] ??
                          selectedFaculty.facultyRole}
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <span className="text-gray-500">Choose a faculty member...</span>
              )}
            </div>
            <ChevronDown
              className={`absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-transform ${
                isDropdownOpen ? 'rotate-180' : ''
              }`}
            />
          </div>

          {/* Dropdown */}
          {isDropdownOpen && (
            <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-hidden">
              {/* Search Input */}
              <div className="p-2 border-b border-gray-100">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search faculty..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-md focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
                    autoFocus
                  />
                </div>
              </div>

              {/* Faculty List */}
              <div className="max-h-60 overflow-y-auto">
                {filteredFaculty.length === 0 ? (
                  <div className="p-4 text-center text-gray-500 text-sm">
                    {searchTerm ? 'No faculty match your search.' : 'No faculty members found.'}
                  </div>
                ) : (
                  filteredFaculty.map((faculty) => (
                    <button
                      key={faculty.id}
                      onClick={() => {
                        setSelectedFacultyId(faculty.id);
                        setIsDropdownOpen(false);
                        setSearchTerm('');
                      }}
                      className={`w-full px-4 py-3 flex items-center gap-3 hover:bg-amber-50 transition-colors ${
                        selectedFacultyId === faculty.id ? 'bg-amber-50' : ''
                      }`}
                    >
                      <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                        <User className="w-4 h-4 text-gray-500" />
                      </div>
                      <div className="flex-1 min-w-0 text-left">
                        <div className="font-medium text-gray-900 truncate">
                          {faculty.name}
                        </div>
                        <div className="flex items-center gap-2">
                          {faculty.facultyRole && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                              {FACULTY_ROLE_LABELS[faculty.facultyRole] ?? faculty.facultyRole}
                            </span>
                          )}
                          {faculty.email && (
                            <span className="text-xs text-gray-400 truncate">
                              {faculty.email}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Click outside to close */}
        {isDropdownOpen && (
          <div
            className="fixed inset-0 z-40"
            onClick={() => {
              setIsDropdownOpen(false);
              setSearchTerm('');
            }}
          />
        )}
      </div>

      {/* Faculty Weekly Editor */}
      {selectedFaculty ? (
        <FacultyWeeklyEditor
          personId={selectedFaculty.id}
          personName={selectedFaculty.name}
          facultyRole={(selectedFaculty.facultyRole as FacultyRole) ?? null}
          readOnly={false}
        />
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <div className="text-center">
            <Calendar className="w-12 h-12 text-amber-400 mx-auto mb-4" />
            <h2 className="text-lg font-medium text-gray-900 mb-2">
              Faculty Weekly Templates
            </h2>
            <p className="text-gray-500">
              Select a faculty member above to view and edit their weekly activity template.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
