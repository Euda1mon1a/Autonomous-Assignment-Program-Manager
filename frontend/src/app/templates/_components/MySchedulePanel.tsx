'use client';

/**
 * MySchedulePanel - User's own weekly schedule (read-only)
 *
 * Shows the current user's faculty activity template in read-only mode.
 * Users must contact a coordinator to request changes.
 */

import { useMemo } from 'react';
import { User, Info, Loader2, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { usePeople } from '@/hooks/usePeople';
import { FacultyWeeklyEditor } from '@/components/FacultyWeeklyEditor';
import type { FacultyRole } from '@/types/faculty-activity';

export function MySchedulePanel() {
  const { user } = useAuth();

  // Fetch people to find current user's person record
  const { data: peopleData, isLoading: peopleLoading } = usePeople();

  // Find the person record matching the logged-in user
  const currentPerson = useMemo(() => {
    if (!user || !peopleData?.items) return null;

    // Match by email or username
    return (
      peopleData.items.find(
        (p) =>
          p.email === user.email || p.name.toLowerCase() === user.username.toLowerCase()
      ) ?? null
    );
  }, [user, peopleData]);

  // Check if user is faculty (has faculty role)
  const isFaculty = useMemo(() => {
    if (!currentPerson) return false;
    // facultyRole exists only for faculty members
    return !!currentPerson.facultyRole;
  }, [currentPerson]);

  // Loading state
  if (peopleLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // Not logged in
  if (!user) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Not Logged In</h3>
        <p className="text-gray-500">Please log in to view your schedule.</p>
      </div>
    );
  }

  // Person record not found
  if (!currentPerson) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <User className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">Profile Not Found</h3>
        <p className="text-gray-500">
          Your user account ({user.email}) is not linked to a person record.
          Please contact an administrator.
        </p>
      </div>
    );
  }

  // Not faculty - no weekly template
  if (!isFaculty) {
    return (
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-blue-800">
              Weekly activity templates are available for faculty members. As a{' '}
              {currentPerson.type || 'resident'}, your schedule is managed through
              rotation assignments.
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <User className="w-12 h-12 text-blue-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Welcome, {currentPerson.name}
          </h3>
          <p className="text-gray-500">
            View your rotation assignments in the Schedule section.
          </p>
        </div>
      </div>
    );
  }

  // Faculty member - show weekly editor in read-only mode
  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-blue-800">
            This is your default weekly activity template. To request changes, please
            contact your program coordinator.
          </p>
        </div>
      </div>

      {/* Faculty Weekly Editor - Read Only */}
      <FacultyWeeklyEditor
        personId={currentPerson.id}
        personName={currentPerson.name}
        facultyRole={(currentPerson.facultyRole as FacultyRole) ?? null}
        readOnly={true}
      />
    </div>
  );
}
