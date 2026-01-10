'use client';

/**
 * FacultyWeeklyEditor - Visual editor for faculty weekly activity patterns.
 *
 * Features:
 * - 7x2 grid showing AM/PM slots for each day
 * - Toggle between Template mode (default pattern) and Week-specific mode
 * - Activity palette filtered by faculty role permissions
 * - Click-to-assign, Shift+click to toggle lock
 * - Priority slider for soft constraints
 * - Shows Dr. [Last Name] with role info in header
 */

import { useState, useCallback, useMemo, useEffect } from 'react';
import { Loader2, Lock, X, Calendar, Settings, Save, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  useFacultyTemplate,
  useUpdateFacultyTemplate,
  useEffectiveFacultyWeek,
  useCreateFacultyOverride,
  useDeleteFacultyOverride,
  usePermittedActivities,
} from '@/hooks/useFacultyActivities';
import type {
  DayOfWeek,
  TimeOfDay,
  FacultyRole,
  EffectiveSlot,
  FacultyTemplateSlotRequest,
} from '@/types/faculty-activity';
import {
  DAY_LABELS_SHORT,
  DAY_LABELS,
  FACULTY_ROLE_LABELS,
  getSlotKey,
  createEmptySlot,
  isWeekend,
} from '@/types/faculty-activity';
import type { Activity } from '@/types/activity';

// ============================================================================
// Types
// ============================================================================

interface FacultyWeeklyEditorProps {
  /** Faculty member's UUID */
  personId: string;
  /** Faculty member's name (for display) */
  personName: string;
  /** Faculty role */
  facultyRole: FacultyRole | null;
  /** Initial mode */
  initialMode?: 'template' | 'week';
  /** Initial week start (for week mode) */
  initialWeekStart?: string;
  /** Callback when editor should close */
  onClose?: () => void;
  /** Read-only mode */
  readOnly?: boolean;
}

interface SlotCellProps {
  slot: EffectiveSlot;
  activity: Activity | null;
  isSelected: boolean;
  readOnly?: boolean;
  onClick: () => void;
  onToggleLock: () => void;
}

// ============================================================================
// Constants
// ============================================================================

/** Display order: Mon-Sun (work week first) */
const DISPLAY_ORDER: DayOfWeek[] = [1, 2, 3, 4, 5, 6, 0];

/** Get Monday of the current week */
function getCurrentWeekStart(): string {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust for Sunday
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().split('T')[0];
}

/** Add/subtract weeks from a date string */
function adjustWeek(dateStr: string, weeks: number): string {
  const date = new Date(dateStr);
  date.setDate(date.getDate() + weeks * 7);
  return date.toISOString().split('T')[0];
}

/** Format date for display */
function formatWeekRange(weekStart: string): string {
  const start = new Date(weekStart);
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  return `${start.toLocaleDateString('en-US', opts)} - ${end.toLocaleDateString('en-US', opts)}`;
}

// ============================================================================
// Sub-components
// ============================================================================

/**
 * Individual slot cell in the grid.
 */
function SlotCell({
  slot,
  activity,
  isSelected,
  readOnly = false,
  onClick,
  onToggleLock,
}: SlotCellProps) {
  const bgColor = activity?.backgroundColor ? `bg-${activity.backgroundColor}` : 'bg-gray-100';
  const textColor = activity?.fontColor ? `text-${activity.fontColor}` : 'text-gray-500';
  const isLocked = slot.isLocked;
  const isFromOverride = slot.source === 'override';

  const handleClick = (e: React.MouseEvent) => {
    if (readOnly) return;
    if (e.shiftKey) {
      onToggleLock();
      return;
    }
    onClick();
  };

  return (
    <div
      className={`
        relative h-12 border rounded cursor-pointer transition-all group
        ${isSelected ? 'ring-2 ring-cyan-500' : ''}
        ${isLocked ? 'border-amber-400' : 'border-slate-600'}
        ${isFromOverride ? 'border-dashed' : ''}
        ${readOnly ? 'cursor-default' : 'hover:shadow-md'}
        ${activity ? bgColor : 'bg-slate-700'}
      `}
      onClick={handleClick}
      role="button"
      tabIndex={readOnly ? -1 : 0}
      aria-label={`${DAY_LABELS_SHORT[slot.dayOfWeek]} ${slot.timeOfDay}: ${
        activity?.name ?? 'Empty'
      }${isLocked ? ' (locked)' : ''}`}
      title={readOnly ? undefined : 'Shift+click to toggle lock'}
    >
      {/* Content */}
      <div className={`flex items-center justify-center h-full ${activity ? textColor : 'text-slate-500'}`}>
        {activity ? (
          <span className="text-xs font-medium truncate px-1">
            {activity.displayAbbreviation ?? activity.code?.toUpperCase() ?? activity.name.slice(0, 4)}
          </span>
        ) : (
          <span className="text-xs text-slate-500">-</span>
        )}
      </div>

      {/* Locked indicator */}
      {isLocked && (
        <Lock className="absolute top-0.5 right-0.5 w-3 h-3 text-amber-400" />
      )}

      {/* Override indicator */}
      {isFromOverride && (
        <div className="absolute bottom-0.5 left-0.5 w-2 h-2 bg-cyan-400 rounded-full" />
      )}
    </div>
  );
}

/**
 * Activity palette for selection.
 */
function ActivityPalette({
  activities,
  selectedId,
  onSelect,
}: {
  activities: Activity[];
  selectedId: string | null;
  onSelect: (activity: Activity | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5 p-2 bg-slate-800 rounded-lg">
      {/* Clear button */}
      <button
        onClick={() => onSelect(null)}
        className={`
          px-2 py-1 text-xs rounded transition-colors
          ${selectedId === null ? 'ring-2 ring-cyan-500 bg-slate-600' : 'bg-slate-700 hover:bg-slate-600'}
          text-slate-300
        `}
      >
        Clear
      </button>

      {activities.map((activity) => {
        const bgClass = activity.backgroundColor ? `bg-${activity.backgroundColor}` : 'bg-slate-600';
        const textClass = activity.fontColor ? `text-${activity.fontColor}` : 'text-white';

        return (
          <button
            key={activity.id}
            onClick={() => onSelect(activity)}
            className={`
              px-2 py-1 text-xs rounded transition-colors
              ${selectedId === activity.id ? 'ring-2 ring-cyan-500' : ''}
              ${bgClass} ${textClass}
            `}
            title={activity.name}
          >
            {activity.displayAbbreviation ?? activity.code}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Mode toggle between template and week-specific.
 */
function ModeToggle({
  mode,
  onModeChange,
}: {
  mode: 'template' | 'week';
  onModeChange: (mode: 'template' | 'week') => void;
}) {
  return (
    <div className="flex bg-slate-800 rounded-lg p-0.5">
      <button
        onClick={() => onModeChange('template')}
        className={`
          flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors
          ${mode === 'template' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}
        `}
      >
        <Settings className="w-3.5 h-3.5" />
        Template
      </button>
      <button
        onClick={() => onModeChange('week')}
        className={`
          flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors
          ${mode === 'week' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'}
        `}
      >
        <Calendar className="w-3.5 h-3.5" />
        Week
      </button>
    </div>
  );
}

/**
 * Week navigator for week-specific mode.
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
        onClick={() => onWeekChange(adjustWeek(weekStart, -1))}
        className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        aria-label="Previous week"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      <span className="text-sm text-slate-300 min-w-[140px] text-center">
        {formatWeekRange(weekStart)}
      </span>
      <button
        onClick={() => onWeekChange(adjustWeek(weekStart, 1))}
        className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
        aria-label="Next week"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

/**
 * Slot details panel for priority and notes.
 */
function SlotDetailsPanel({
  slot,
  activity,
  priority,
  notes,
  onPriorityChange,
  onNotesChange,
  onClose,
}: {
  slot: EffectiveSlot;
  activity: Activity | null;
  priority: number;
  notes: string;
  onPriorityChange: (priority: number) => void;
  onNotesChange: (notes: string) => void;
  onClose: () => void;
}) {
  return (
    <div className="p-3 bg-slate-800 rounded-lg space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-white">
          {DAY_LABELS[slot.dayOfWeek]} {slot.timeOfDay}
          {activity && <span className="text-slate-400 ml-1">- {activity.name}</span>}
        </h4>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-700 rounded text-slate-400"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-2">
        <div>
          <label className="block text-xs text-slate-400 mb-1">
            Priority: {priority} ({priority <= 30 ? 'Low' : priority <= 60 ? 'Medium' : priority <= 90 ? 'High' : 'Critical'})
          </label>
          <input
            type="range"
            min={0}
            max={100}
            value={priority}
            onChange={(e) => onPriorityChange(parseInt(e.target.value))}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-400 mb-1">Notes</label>
          <input
            type="text"
            value={notes}
            onChange={(e) => onNotesChange(e.target.value)}
            placeholder="Optional notes..."
            className="w-full text-sm bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-white placeholder-slate-500 focus:ring-cyan-500 focus:border-cyan-500"
          />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function FacultyWeeklyEditor({
  personId,
  personName,
  facultyRole,
  initialMode = 'template',
  initialWeekStart,
  onClose,
  readOnly = false,
}: FacultyWeeklyEditorProps) {
  // State
  const [mode, setMode] = useState<'template' | 'week'>(initialMode);
  const [weekStart, setWeekStart] = useState(initialWeekStart ?? getCurrentWeekStart());
  const [selectedSlotKey, setSelectedSlotKey] = useState<string | null>(null);
  const [selectedActivityId, setSelectedActivityId] = useState<string | null>(null);
  const [localSlots, setLocalSlots] = useState<Map<string, Partial<EffectiveSlot>>>(new Map());
  const [slotPriority, setSlotPriority] = useState(50);
  const [slotNotes, setSlotNotes] = useState('');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Data fetching
  const { data: templateData, isLoading: templateLoading } = useFacultyTemplate(personId);
  const { data: effectiveData, isLoading: effectiveLoading } = useEffectiveFacultyWeek(
    personId,
    weekStart,
    1 // Week number within block
  );
  const { data: permissionsData } = usePermittedActivities(facultyRole ?? 'core');

  // Mutations
  const updateTemplate = useUpdateFacultyTemplate();
  const createOverride = useCreateFacultyOverride();

  // Derived data
  const isLoading = mode === 'template' ? templateLoading : effectiveLoading;
  const slots: EffectiveSlot[] = useMemo(() => {
    if (mode === 'template') {
      // Build effective slots from template data
      const result: EffectiveSlot[] = [];
      for (let day = 0; day <= 6; day++) {
        for (const time of ['AM', 'PM'] as TimeOfDay[]) {
          const templateSlot = templateData?.slots.find(
            (s) => s.dayOfWeek === day && s.timeOfDay === time
          );
          result.push({
            dayOfWeek: day as DayOfWeek,
            timeOfDay: time,
            activityId: templateSlot?.activityId ?? null,
            activity: templateSlot?.activity ?? null,
            isLocked: templateSlot?.isLocked ?? false,
            priority: templateSlot?.priority ?? 50,
            source: templateSlot ? 'template' : null,
            notes: templateSlot?.notes ?? null,
          });
        }
      }
      return result;
    } else {
      return effectiveData?.slots ?? [];
    }
  }, [mode, templateData, effectiveData]);

  const activities = permissionsData?.activities ?? [];

  // Get merged slot (local changes + remote data)
  const getMergedSlot = useCallback(
    (day: DayOfWeek, time: TimeOfDay): EffectiveSlot => {
      const key = getSlotKey(day, time);
      const baseSlot = slots.find((s) => s.dayOfWeek === day && s.timeOfDay === time)
        ?? createEmptySlot(day, time);
      const localChanges = localSlots.get(key);
      if (localChanges) {
        return { ...baseSlot, ...localChanges };
      }
      return baseSlot;
    },
    [slots, localSlots]
  );

  // Handlers
  const handleSlotClick = useCallback(
    (day: DayOfWeek, time: TimeOfDay) => {
      const key = getSlotKey(day, time);
      const slot = getMergedSlot(day, time);

      if (selectedSlotKey === key) {
        // Clicking same slot again - deselect
        setSelectedSlotKey(null);
        return;
      }

      // If we have an activity selected, assign it
      if (selectedActivityId !== null || selectedActivityId === null) {
        const activity = activities.find((a) => a.id === selectedActivityId) ?? null;
        setLocalSlots((prev) => {
          const next = new Map(prev);
          next.set(key, {
            ...slot,
            activityId: selectedActivityId,
            activity,
          });
          return next;
        });
        setHasUnsavedChanges(true);
      }

      // Select this slot for details editing
      setSelectedSlotKey(key);
      setSlotPriority(slot.priority);
      setSlotNotes(slot.notes ?? '');
    },
    [selectedSlotKey, selectedActivityId, activities, getMergedSlot]
  );

  const handleToggleLock = useCallback(
    (day: DayOfWeek, time: TimeOfDay) => {
      const key = getSlotKey(day, time);
      const slot = getMergedSlot(day, time);
      setLocalSlots((prev) => {
        const next = new Map(prev);
        next.set(key, {
          ...slot,
          isLocked: !slot.isLocked,
        });
        return next;
      });
      setHasUnsavedChanges(true);
    },
    [getMergedSlot]
  );

  const handlePriorityChange = useCallback(
    (priority: number) => {
      setSlotPriority(priority);
      if (selectedSlotKey) {
        const [day, time] = selectedSlotKey.split('_');
        const slot = getMergedSlot(parseInt(day) as DayOfWeek, time as TimeOfDay);
        setLocalSlots((prev) => {
          const next = new Map(prev);
          next.set(selectedSlotKey, {
            ...slot,
            priority,
          });
          return next;
        });
        setHasUnsavedChanges(true);
      }
    },
    [selectedSlotKey, getMergedSlot]
  );

  const handleNotesChange = useCallback(
    (notes: string) => {
      setSlotNotes(notes);
      if (selectedSlotKey) {
        const [day, time] = selectedSlotKey.split('_');
        const slot = getMergedSlot(parseInt(day) as DayOfWeek, time as TimeOfDay);
        setLocalSlots((prev) => {
          const next = new Map(prev);
          next.set(selectedSlotKey, {
            ...slot,
            notes: notes || null,
          });
          return next;
        });
        setHasUnsavedChanges(true);
      }
    },
    [selectedSlotKey, getMergedSlot]
  );

  const handleSave = useCallback(async () => {
    try {
      if (mode === 'template') {
        // Build slots array from local changes
        const slotsToUpdate: FacultyTemplateSlotRequest[] = [];
        localSlots.forEach((changes, key) => {
          const [day, time] = key.split('_');
          slotsToUpdate.push({
            dayOfWeek: parseInt(day) as DayOfWeek,
            timeOfDay: time as TimeOfDay,
            activityId: changes.activityId,
            isLocked: changes.isLocked ?? false,
            priority: changes.priority ?? 50,
            notes: changes.notes,
          });
        });

        if (slotsToUpdate.length > 0) {
          await updateTemplate.mutateAsync({
            personId,
            slots: slotsToUpdate,
            clearExisting: false,
          });
        }
      } else {
        // Create overrides for each changed slot
        for (const [key, changes] of localSlots.entries()) {
          const [day, time] = key.split('_');
          await createOverride.mutateAsync({
            personId,
            override: {
              effectiveDate: weekStart,
              dayOfWeek: parseInt(day) as DayOfWeek,
              timeOfDay: time as TimeOfDay,
              activityId: changes.activityId,
              isLocked: changes.isLocked ?? false,
              overrideReason: changes.notes,
            },
          });
        }
      }

      setLocalSlots(new Map());
      setHasUnsavedChanges(false);
      onClose?.(); // Close modal on success
    } catch (err) {
      console.error('Failed to save:', err);
      // Error will be shown by TanStack Query error handling
    }
  }, [mode, personId, weekStart, localSlots, updateTemplate, createOverride, onClose]);

  const handleCancel = useCallback(() => {
    setLocalSlots(new Map());
    setHasUnsavedChanges(false);
    setSelectedSlotKey(null);
    onClose?.();
  }, [onClose]);

  // Get selected slot for details panel
  const selectedSlot = selectedSlotKey
    ? (() => {
        const [day, time] = selectedSlotKey.split('_');
        return getMergedSlot(parseInt(day) as DayOfWeek, time as TimeOfDay);
      })()
    : null;

  const selectedActivity = selectedSlot?.activityId
    ? activities.find((a) => a.id === selectedSlot.activityId) ?? null
    : null;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl max-w-3xl mx-auto">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Dr. {personName.split(' ').pop()}
            </h2>
            {facultyRole && (
              <span className="text-xs text-slate-400">
                {FACULTY_ROLE_LABELS[facultyRole]}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <ModeToggle mode={mode} onModeChange={setMode} />
            {onClose && (
              <button
                onClick={handleCancel}
                className="p-2 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>

        {mode === 'week' && (
          <WeekNavigator weekStart={weekStart} onWeekChange={setWeekStart} />
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-48">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
          </div>
        ) : (
          <>
            {/* Activity Palette */}
            <div className="mb-4">
              <label className="block text-xs text-slate-400 mb-2">
                Select activity to assign (click slots to apply)
              </label>
              <ActivityPalette
                activities={activities}
                selectedId={selectedActivityId}
                onSelect={(a) => setSelectedActivityId(a?.id ?? null)}
              />
            </div>

            {/* Grid */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="text-xs text-slate-400 font-medium p-1 w-12"></th>
                    {DISPLAY_ORDER.map((day) => (
                      <th
                        key={day}
                        className={`text-xs font-medium p-1 ${
                          isWeekend(day) ? 'text-slate-500' : 'text-slate-300'
                        }`}
                      >
                        {DAY_LABELS_SHORT[day]}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(['AM', 'PM'] as TimeOfDay[]).map((time) => (
                    <tr key={time}>
                      <td className="text-xs text-slate-400 font-medium p-1 text-center">
                        {time}
                      </td>
                      {DISPLAY_ORDER.map((day) => {
                        const slot = getMergedSlot(day, time);
                        const key = getSlotKey(day, time);
                        return (
                          <td key={key} className="p-0.5">
                            <SlotCell
                              slot={slot}
                              activity={slot.activity}
                              isSelected={selectedSlotKey === key}
                              readOnly={readOnly}
                              onClick={() => handleSlotClick(day, time)}
                              onToggleLock={() => handleToggleLock(day, time)}
                            />
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Slot Details Panel */}
            {selectedSlot && (
              <div className="mt-4">
                <SlotDetailsPanel
                  slot={selectedSlot}
                  activity={selectedActivity}
                  priority={slotPriority}
                  notes={slotNotes}
                  onPriorityChange={handlePriorityChange}
                  onNotesChange={handleNotesChange}
                  onClose={() => setSelectedSlotKey(null)}
                />
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      {!readOnly && (
        <div className="p-4 border-t border-slate-700 flex items-center justify-between">
          <div className="text-xs text-slate-500">
            {hasUnsavedChanges ? (
              <span className="text-amber-400">Unsaved changes</span>
            ) : (
              <span>Shift+click to toggle lock</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!hasUnsavedChanges || updateTemplate.isPending || createOverride.isPending}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded transition-colors
                ${hasUnsavedChanges
                  ? 'bg-cyan-600 text-white hover:bg-cyan-500'
                  : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                }
              `}
            >
              {(updateTemplate.isPending || createOverride.isPending) ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Save
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default FacultyWeeklyEditor;
