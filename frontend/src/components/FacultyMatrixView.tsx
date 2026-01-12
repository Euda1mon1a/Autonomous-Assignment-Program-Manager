'use client';

/**
 * FacultyMatrixView - All-faculty overview showing weekly activity schedules.
 *
 * Features:
 * - Rows: Faculty members (Dr. Last Name)
 * - Columns: Days of selected week
 * - Cells: AM/PM stacked with activity abbreviations
 * - Click cell → opens FacultyWeeklyEditor modal
 * - Color coding from activity metadata
 * - Role filter and hide adjunct toggle
 * - Activity legend
 */

import React, { useState, useMemo, useCallback } from 'react';
import { Loader2, ChevronLeft, ChevronRight, Filter, Users, X, Edit2, Check, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useFacultyMatrix } from '@/hooks/useFacultyActivities';
import { useFairnessAudit, getWorkloadDeviation } from '@/hooks/useFairness';
import { useUpdatePerson } from '@/hooks/usePeople';
import {
  formatLocalDate,
  addDaysLocal,
  getMondayOfWeek,
  getFirstOfMonthLocal,
  getLastOfMonthLocal,
} from '@/lib/date-utils';
import type {
  DayOfWeek,
  FacultyRole,
  FacultyMatrixRow,
  EffectiveSlot,
} from '@/types/faculty-activity';
import {
  DAY_LABELS_SHORT,
  FACULTY_ROLE_LABELS,
  FACULTY_ROLES,
  isWeekend,
} from '@/types/faculty-activity';
import type { Activity } from '@/types/activity';
import { FacultyWeeklyEditor } from './FacultyWeeklyEditor';
import { showErrorToast } from '@/lib/errors/error-toast';

// ============================================================================
// Types
// ============================================================================

interface FacultyMatrixViewProps {
  /** Initial week start date */
  initialWeekStart?: string;
  /** Show include adjunct toggle */
  showAdjunctToggle?: boolean;
  /** Callback when faculty is selected */
  onFacultySelect?: (personId: string) => void;
  /** Show workload score badges next to faculty names */
  showWorkloadBadges?: boolean;
}

interface MatrixCellProps {
  slots: EffectiveSlot[];
  day: DayOfWeek;
  onClick: () => void;
}

// ============================================================================
// Constants
// ============================================================================

/** Display order: Mon-Sun (work week first) */
const DISPLAY_ORDER: DayOfWeek[] = [1, 2, 3, 4, 5, 6, 0];

/** Get Monday of the current week (using local timezone) */
function getCurrentWeekStart(): string {
  return getMondayOfWeek();
}

/** Add days to a date string (using local timezone) */
function addDays(dateStr: string, days: number): string {
  return addDaysLocal(dateStr, days);
}

/** Format date for display */
function formatWeekRange(weekStart: string): string {
  const start = new Date(weekStart);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  return `${start.toLocaleDateString('en-US', opts)} - ${end.toLocaleDateString('en-US', opts)}`;
}

/** Get end of week from start */
function getWeekEnd(weekStart: string): string {
  return addDays(weekStart, 6);
}

/** Normalize any date to the Monday of its week (using local timezone) */
function normalizeToMonday(dateStr: string): string {
  return getMondayOfWeek(new Date(dateStr));
}

// ============================================================================
// Sub-components
// ============================================================================

/**
 * Week navigator.
 */
function WeekNavigator({
  weekStart,
  onWeekChange,
}: {
  weekStart: string;
  onWeekChange: (weekStart: string) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onWeekChange(addDays(weekStart, -7))}
        className="p-2 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        aria-label="Previous week"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <span className="text-sm font-medium text-white min-w-[160px] text-center">
        {formatWeekRange(weekStart)}
      </span>
      <button
        onClick={() => onWeekChange(addDays(weekStart, 7))}
        className="p-2 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        aria-label="Next week"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
}

/**
 * Role filter dropdown.
 */
function RoleFilter({
  selectedRoles,
  onChange,
}: {
  selectedRoles: FacultyRole[];
  onChange: (roles: FacultyRole[]) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleRole = (role: FacultyRole) => {
    if (selectedRoles.includes(role)) {
      onChange(selectedRoles.filter((r) => r !== role));
    } else {
      onChange([...selectedRoles, role]);
    }
  };

  const selectAll = () => {
    onChange([...FACULTY_ROLES]);
    setIsOpen(false);
  };

  const clearAll = () => {
    onChange([]);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center gap-2 px-3 py-2 rounded text-sm transition-colors
          ${selectedRoles.length > 0 && selectedRoles.length < FACULTY_ROLES.length
            ? 'bg-cyan-600 text-white'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }
        `}
      >
        <Filter className="w-4 h-4" />
        <span>
          {selectedRoles.length === FACULTY_ROLES.length
            ? 'All Roles'
            : selectedRoles.length === 0
            ? 'None Selected'
            : `${selectedRoles.length} Roles`}
        </span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 top-full mt-1 z-20 w-56 bg-slate-800 rounded-lg shadow-xl border border-slate-700">
            <div className="p-2 border-b border-slate-700 flex gap-2">
              <button
                onClick={selectAll}
                className="text-xs text-cyan-400 hover:text-cyan-300"
              >
                Select All
              </button>
              <span className="text-slate-600">|</span>
              <button
                onClick={clearAll}
                className="text-xs text-slate-400 hover:text-white"
              >
                Clear
              </button>
            </div>
            <div className="p-2 max-h-48 overflow-y-auto">
              {FACULTY_ROLES.map((role) => (
                <label
                  key={role}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-700 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedRoles.includes(role)}
                    onChange={() => toggleRole(role)}
                    className="rounded border-slate-600 bg-slate-700 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">{FACULTY_ROLE_LABELS[role]}</span>
                </label>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Single cell in the matrix showing AM/PM activities.
 */
function MatrixCell({ slots, day, onClick }: MatrixCellProps) {
  const amSlot = slots.find((s) => s.dayOfWeek === day && s.timeOfDay === 'AM');
  const pmSlot = slots.find((s) => s.dayOfWeek === day && s.timeOfDay === 'PM');

  const getSlotDisplay = (slot?: EffectiveSlot) => {
    if (!slot?.activity) {
      return { text: '-', bg: '', textColor: 'text-slate-500' };
    }
    const activity = slot.activity;
    return {
      text: activity.displayAbbreviation ?? activity.code ?? activity.name.slice(0, 3),
      bg: activity.backgroundColor ? `bg-${activity.backgroundColor}` : 'bg-slate-600',
      textColor: activity.fontColor ? `text-${activity.fontColor}` : 'text-white',
    };
  };

  const am = getSlotDisplay(amSlot);
  const pm = getSlotDisplay(pmSlot);

  return (
    <td className="p-0.5">
      <button
        onClick={onClick}
        className={`
          w-full flex flex-col gap-0.5 p-1 rounded border transition-all
          hover:border-cyan-500 hover:shadow-md
          ${isWeekend(day) ? 'border-slate-700' : 'border-slate-600'}
        `}
      >
        <div
          className={`
            text-[10px] font-medium px-1 py-0.5 rounded
            ${am.bg || 'bg-slate-800'} ${am.textColor}
          `}
        >
          {am.text}
        </div>
        <div
          className={`
            text-[10px] font-medium px-1 py-0.5 rounded
            ${pm.bg || 'bg-slate-800'} ${pm.textColor}
          `}
        >
          {pm.text}
        </div>
      </button>
    </td>
  );
}

/**
 * Activity legend showing all unique activities in the matrix.
 */
function ActivityLegend({ faculty }: { faculty: FacultyMatrixRow[] }) {
  const activities = useMemo(() => {
    const activityMap = new Map<string, Activity>();
    for (const f of faculty) {
      for (const week of f.weeks) {
        for (const slot of week.slots) {
          if (slot.activity && !activityMap.has(slot.activity.id)) {
            activityMap.set(slot.activity.id, slot.activity);
          }
        }
      }
    }
    return Array.from(activityMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [faculty]);

  if (activities.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 p-3 bg-slate-800 rounded-lg">
      {activities.map((activity) => (
        <div
          key={activity.id}
          className={`
            flex items-center gap-1.5 px-2 py-1 rounded text-xs
            ${activity.backgroundColor ? `bg-${activity.backgroundColor}` : 'bg-slate-600'}
            ${activity.fontColor ? `text-${activity.fontColor}` : 'text-white'}
          `}
        >
          <span className="font-medium">
            {activity.displayAbbreviation ?? activity.code}
          </span>
          <span className="opacity-75">- {activity.name}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Workload score badge for faculty (Tier 3 quick glance).
 */
function WorkloadBadge({
  score,
  deviation,
}: {
  score: number;
  deviation: number;
}) {
  // Color based on deviation from mean
  let bgColor = 'bg-green-500/20 text-green-400 border-green-500/50';
  let icon: React.ReactNode = <CheckCircle2 className="w-3 h-3" />;

  if (Math.abs(deviation) > 25) {
    bgColor = 'bg-red-500/20 text-red-400 border-red-500/50';
    icon = <AlertCircle className="w-3 h-3" />;
  } else if (Math.abs(deviation) > 10) {
    bgColor = 'bg-amber-500/20 text-amber-400 border-amber-500/50';
    icon = null;
  }

  return (
    <div
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-medium ${bgColor}`}
      title={`Workload: ${score.toFixed(1)} (${deviation > 0 ? '+' : ''}${deviation.toFixed(0)}% from mean)`}
    >
      {icon}
      <span>{score.toFixed(1)}</span>
    </div>
  );
}

/**
 * Inline role editor dropdown.
 */
function InlineRoleEditor({
  personId,
  personName,
  currentRole,
  onSave,
  onCancel,
  isSaving,
}: {
  personId: string;
  personName: string;
  currentRole: FacultyRole | null;
  onSave: (role: FacultyRole) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const [selectedRole, setSelectedRole] = useState<FacultyRole>(currentRole ?? 'core');
  const lastName = personName.split(' ').pop();

  return (
    <div className="flex flex-col gap-1">
      <div className="text-sm font-medium text-white">Dr. {lastName}</div>
      <div className="flex items-center gap-1">
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value as FacultyRole)}
          disabled={isSaving}
          className="text-xs bg-slate-700 border border-slate-600 rounded px-1.5 py-0.5 text-white focus:ring-cyan-500 focus:border-cyan-500"
          autoFocus
        >
          {FACULTY_ROLES.filter(r => r !== 'adjunct').map((role) => (
            <option key={role} value={role}>
              {FACULTY_ROLE_LABELS[role]}
            </option>
          ))}
        </select>
        <button
          onClick={() => onSave(selectedRole)}
          disabled={isSaving}
          className="p-0.5 text-green-400 hover:text-green-300 disabled:opacity-50"
          title="Save"
          aria-label="Save role change"
        >
          {isSaving ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5" />
          )}
        </button>
        <button
          onClick={onCancel}
          disabled={isSaving}
          className="p-0.5 text-slate-400 hover:text-white disabled:opacity-50"
          title="Cancel"
          aria-label="Cancel role change"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

/**
 * Editor modal wrapper.
 */
function EditorModal({
  isOpen,
  onClose,
  personId,
  personName,
  facultyRole,
  weekStart,
}: {
  isOpen: boolean;
  onClose: () => void;
  personId: string;
  personName: string;
  facultyRole: FacultyRole | null;
  weekStart: string;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/70"
        onClick={onClose}
      />
      <div className="relative z-10 w-full max-w-3xl">
        <FacultyWeeklyEditor
          personId={personId}
          personName={personName}
          facultyRole={facultyRole}
          initialMode="week"
          initialWeekStart={weekStart}
          onClose={onClose}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function FacultyMatrixView({
  initialWeekStart,
  showAdjunctToggle = true,
  onFacultySelect,
  showWorkloadBadges = false,
}: FacultyMatrixViewProps) {
  // State
  const [weekStart, setWeekStart] = useState(
    normalizeToMonday(initialWeekStart ?? getCurrentWeekStart())
  );
  const [includeAdjunct, setIncludeAdjunct] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState<FacultyRole[]>([...FACULTY_ROLES]);
  const [editorState, setEditorState] = useState<{
    isOpen: boolean;
    personId: string;
    personName: string;
    facultyRole: FacultyRole | null;
  }>({
    isOpen: false,
    personId: '',
    personName: '',
    facultyRole: null,
  });
  const [editingRoleFor, setEditingRoleFor] = useState<string | null>(null);

  // Calculate current month date range for workload badges (using local timezone)
  const monthStart = getFirstOfMonthLocal();
  const monthEnd = getLastOfMonthLocal();

  // Data fetching
  const { data, isLoading, isError, error, refetch } = useFacultyMatrix(
    weekStart,
    getWeekEnd(weekStart),
    includeAdjunct
  );

  // Fetch workload data if badges enabled
  const { data: fairnessData } = useFairnessAudit(
    showWorkloadBadges ? monthStart : null,
    showWorkloadBadges ? monthEnd : null,
    true // Include titled faculty so their badges show
  );

  // Create workload lookup map
  const workloadMap = useMemo(() => {
    if (!fairnessData?.workloads) return new Map();
    const map = new Map<string, { score: number; deviation: number }>();
    for (const w of fairnessData.workloads) {
      const deviation = getWorkloadDeviation(w, fairnessData.workloadStats.mean);
      map.set(w.personId, { score: w.totalScore, deviation });
    }
    return map;
  }, [fairnessData]);

  // Mutations
  const updatePerson = useUpdatePerson();

  // Helper to get personId
  const getPersonId = (faculty: FacultyMatrixRow): string => {
    return faculty.personId;
  };

  // Filter faculty by selected roles
  const filteredFaculty = useMemo(() => {
    if (!data?.faculty) return [];
    return data.faculty.filter((f) => {
      const role = f.facultyRole;
      if (!role) return selectedRoles.length === FACULTY_ROLES.length;
      return selectedRoles.includes(role);
    });
  }, [data?.faculty, selectedRoles]);

  // Handlers
  const handleCellClick = useCallback(
    (faculty: FacultyMatrixRow) => {
      setEditorState({
        isOpen: true,
        personId: getPersonId(faculty),
        personName: faculty.name,
        facultyRole: faculty.facultyRole ?? null,
      });
      onFacultySelect?.(getPersonId(faculty));
    },
    [onFacultySelect]
  );

  const closeEditor = useCallback(() => {
    setEditorState((prev) => ({ ...prev, isOpen: false }));
  }, []);

  const handleRoleSave = useCallback(
    async (personId: string, newRole: FacultyRole) => {
      try {
        await updatePerson.mutateAsync({
          id: personId,
          // Cast to api.ts FacultyRole enum (same runtime values as string union)
          data: { facultyRole: newRole as unknown as import('@/types/api').FacultyRole },
        });
        setEditingRoleFor(null);
        refetch(); // Refresh the matrix data
      } catch (err) {
        console.error('Failed to update role:', err);
        showErrorToast(err);
      }
    },
    [updatePerson, refetch]
  );

  // Get slots for the current week
  const getWeekSlots = (faculty: FacultyMatrixRow): EffectiveSlot[] => {
    const week = faculty.weeks.find((w) => w.weekStart === weekStart);
    if (week) return week.slots;
    // Fallback: use first week if exact match fails (handles timezone edge cases)
    return faculty.weeks[0]?.slots ?? [];
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-500" />
            Faculty Activities
          </h2>
          <WeekNavigator weekStart={weekStart} onWeekChange={(w) => setWeekStart(normalizeToMonday(w))} />
        </div>

        <div className="flex items-center gap-3">
          <RoleFilter selectedRoles={selectedRoles} onChange={setSelectedRoles} />

          {showAdjunctToggle && (
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <input
                type="checkbox"
                checked={includeAdjunct}
                onChange={(e) => setIncludeAdjunct(e.target.checked)}
                className="rounded border-slate-600 bg-slate-700 text-cyan-500 focus:ring-cyan-500"
              />
              Include Adjunct
            </label>
          )}
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-400">
          Failed to load faculty matrix: {error?.message ?? 'Unknown error'}
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
        </div>
      )}

      {/* Matrix table */}
      {!isLoading && !isError && (
        <>
          <div className="overflow-x-auto bg-slate-900 rounded-lg">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left text-sm font-medium text-slate-400 p-3 sticky left-0 bg-slate-900 z-10 min-w-[160px]">
                    Faculty
                  </th>
                  {DISPLAY_ORDER.map((day) => (
                    <th
                      key={day}
                      className={`text-center text-sm font-medium p-3 min-w-[60px] ${
                        isWeekend(day) ? 'text-slate-500' : 'text-slate-300'
                      }`}
                    >
                      {DAY_LABELS_SHORT[day]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredFaculty.length === 0 ? (
                  <tr>
                    <td
                      colSpan={8}
                      className="text-center text-slate-500 py-12"
                    >
                      {selectedRoles.length === 0
                        ? 'No roles selected. Use the filter to select roles.'
                        : 'No faculty found for the selected criteria.'}
                    </td>
                  </tr>
                ) : (
                  filteredFaculty.map((faculty) => {
                    const slots = getWeekSlots(faculty);
                    const lastName = faculty.name.split(' ').pop();
                    const facultyId = getPersonId(faculty);
                    const isEditingRole = editingRoleFor === facultyId;
                    const workloadInfo = workloadMap.get(facultyId);

                    return (
                      <tr
                        key={facultyId}
                        className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"
                      >
                        <td className="p-2 sticky left-0 bg-slate-900 z-10">
                          {isEditingRole ? (
                            <InlineRoleEditor
                              personId={facultyId}
                              personName={faculty.name}
                              currentRole={faculty.facultyRole ?? null}
                              onSave={(role) => handleRoleSave(facultyId, role)}
                              onCancel={() => setEditingRoleFor(null)}
                              isSaving={updatePerson.isPending}
                            />
                          ) : (
                            <div className="flex items-center gap-2 group">
                              <button
                                onClick={() => handleCellClick(faculty)}
                                className="text-left flex-1"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium text-white group-hover:text-cyan-400 transition-colors">
                                    Dr. {lastName}
                                  </span>
                                  {showWorkloadBadges && workloadInfo && (
                                    <WorkloadBadge
                                      score={workloadInfo.score}
                                      deviation={workloadInfo.deviation}
                                    />
                                  )}
                                </div>
                                {faculty.facultyRole && (
                                  <div className="text-xs text-slate-500">
                                    {FACULTY_ROLE_LABELS[faculty.facultyRole]}
                                  </div>
                                )}
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setEditingRoleFor(facultyId);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-cyan-400 transition-all"
                                title="Edit role"
                                aria-label={`Edit role for ${faculty.name}`}
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                        </td>
                        {DISPLAY_ORDER.map((day) => (
                          <MatrixCell
                            key={day}
                            slots={slots}
                            day={day}
                            onClick={() => handleCellClick(faculty)}
                          />
                        ))}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Faculty count */}
          <div className="text-xs text-slate-500">
            Showing {filteredFaculty.length} of {data?.totalFaculty ?? 0} faculty members
          </div>

          {/* Legend */}
          {filteredFaculty.length > 0 && <ActivityLegend faculty={filteredFaculty} />}
        </>
      )}

      {/* Editor Modal */}
      <EditorModal
        isOpen={editorState.isOpen}
        onClose={closeEditor}
        personId={editorState.personId}
        personName={editorState.personName}
        facultyRole={editorState.facultyRole}
        weekStart={weekStart}
      />
    </div>
  );
}

export default FacultyMatrixView;
