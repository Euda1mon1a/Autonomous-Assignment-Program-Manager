'use client';

import type { PersonClinicCoverage, AssignmentInfoV2 } from './types';

interface ClinicCoverageTableProps {
  locations: PersonClinicCoverage[];  // Actually person-centric data now
  searchQuery?: string;
}

/**
 * Color coding for rotation types
 * Matches DayView rotationColors for consistency
 */
const rotationColors: Record<string, string> = {
  clinic: 'bg-blue-100 text-blue-800 border-blue-300',
  clinical: 'bg-blue-100 text-blue-800 border-blue-300',
  inpatient: 'bg-purple-100 text-purple-800 border-purple-300',
  procedure: 'bg-red-100 text-red-800 border-red-300',
  conference: 'bg-gray-100 text-gray-800 border-gray-300',
  academic: 'bg-gray-100 text-gray-800 border-gray-300',
  elective: 'bg-green-100 text-green-800 border-green-300',
  call: 'bg-orange-100 text-orange-800 border-orange-300',
  off: 'bg-white text-gray-400 border-gray-200',
  leave: 'bg-amber-100 text-amber-800 border-amber-300',
  vacation: 'bg-amber-100 text-amber-800 border-amber-300',
  recovery: 'bg-slate-100 text-slate-600 border-slate-300',
  default: 'bg-slate-100 text-slate-700 border-slate-300',
};

function getActivityColor(activity: string): string {
  const activityLower = activity.toLowerCase();

  // Check exact match first
  if (rotationColors[activityLower]) {
    return rotationColors[activityLower];
  }

  // Check for partial matches
  for (const [key, color] of Object.entries(rotationColors)) {
    if (activityLower.includes(key)) {
      return color;
    }
  }
  return rotationColors.default;
}

/**
 * Assignment Card - colored card showing activity type
 */
function AssignmentCard({ assignment }: { assignment: AssignmentInfoV2 | null }) {
  if (!assignment) {
    return (
      <div className="flex-1 p-4 bg-gray-50 rounded-lg border border-dashed border-gray-200 min-h-[80px] flex items-center justify-center">
        <span className="text-gray-400 text-sm">No assignment</span>
      </div>
    );
  }

  const colorClass = getActivityColor(assignment.activity);

  return (
    <div className={`flex-1 p-4 rounded-lg border-l-4 min-h-[80px] ${colorClass}`}>
      <div className="font-semibold text-lg">{assignment.activity}</div>
      <div className="text-sm opacity-80 mt-1">
        {assignment.abbreviation} • {assignment.role}
      </div>
    </div>
  );
}

/**
 * Clinic Coverage Component (DayView Style)
 *
 * Displays clinic staffing as Person | AM Card | PM Card format.
 * Two-column layout: AM on left, PM on right.
 * Matches the Schedule DayView layout for consistency.
 */
export function ClinicCoverageTable({ locations: people, searchQuery }: ClinicCoverageTableProps) {
  // Filter people based on search query
  const filteredPeople = people.filter((person) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();

    // Check person name
    if (person.person.name.toLowerCase().includes(query)) return true;

    // Check AM activity
    if (person.am?.activity.toLowerCase().includes(query)) return true;

    // Check PM activity
    if (person.pm?.activity.toLowerCase().includes(query)) return true;

    return false;
  });

  if (filteredPeople.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {searchQuery ? (
          <p>No staff match &quot;{searchQuery}&quot;</p>
        ) : (
          <p>No clinic coverage data available for this date.</p>
        )}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* AM Section */}
      <div role="region" aria-label="Morning assignments">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <h3 className="text-lg font-semibold text-gray-900">Morning (AM)</h3>
        </div>
        <div className="space-y-3">
          {filteredPeople.map((personData) => (
            <div
              key={`am-${personData.person.id}`}
              className="flex items-stretch gap-3"
            >
              {/* Person label */}
              <div className="w-36 py-4 flex flex-col justify-center">
                <div className="font-medium text-gray-900 truncate">
                  {personData.person.name}
                </div>
                <div className="text-xs text-gray-500">
                  {personData.person.pgy_level
                    ? `PGY-${personData.person.pgy_level}`
                    : 'Faculty'}
                </div>
              </div>
              {/* Assignment card */}
              <AssignmentCard assignment={personData.am} />
            </div>
          ))}
        </div>
      </div>

      {/* PM Section */}
      <div role="region" aria-label="Afternoon assignments">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 rounded-full bg-blue-400" />
          <h3 className="text-lg font-semibold text-gray-900">Afternoon (PM)</h3>
        </div>
        <div className="space-y-3">
          {filteredPeople.map((personData) => (
            <div
              key={`pm-${personData.person.id}`}
              className="flex items-stretch gap-3"
            >
              {/* Person label */}
              <div className="w-36 py-4 flex flex-col justify-center">
                <div className="font-medium text-gray-900 truncate">
                  {personData.person.name}
                </div>
                <div className="text-xs text-gray-500">
                  {personData.person.pgy_level
                    ? `PGY-${personData.person.pgy_level}`
                    : 'Faculty'}
                </div>
              </div>
              {/* Assignment card */}
              <AssignmentCard assignment={personData.pm} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
