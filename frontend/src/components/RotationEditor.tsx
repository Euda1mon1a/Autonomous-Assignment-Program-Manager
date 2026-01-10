'use client';

/**
 * RotationEditor - Unified editor for rotation weekly patterns + activity requirements.
 *
 * Combines:
 * - Week tabs for switching between weeks 1-4 or "All Weeks"
 * - 7x2 grid for weekly patterns with activity selection
 * - Dynamic activity requirement sliders
 * - Total half-days balance indicator
 *
 * Layout:
 * +-------------------------------------------------------------+
 * |  [Week 1] [Week 2] [Week 3] [Week 4] [All Weeks]            |
 * +------------------------------+------------------------------+
 * |  Weekly Pattern Grid (7x2)   |  Activity Requirements       |
 * |                              |  FM Clinic   [====--] 4/10   |
 * |  Mon Tue Wed Thu Fri Sat Sun |  Specialty   [=====-] 5/10   |
 * |  AM [C] [C] [L] [S] [S] [-] [-]  Academics   [=-----] 1/10   |
 * |  PM [S] [S] [-] [C] [C] [-] [-]  + Add Activity              |
 * +------------------------------+------------------------------+
 * |  Total: 10/10 Balanced       [Cancel] [Save]                |
 * +-------------------------------------------------------------+
 */

import { useState, useCallback, useMemo } from 'react';
import { Loader2, Lock, Plus, Trash2, ChevronDown, AlertCircle, CheckCircle } from 'lucide-react';
import type {
  WeeklyPatternGrid,
  WeeklyPatternSlot,
  DayOfWeek,
  WeeklyPatternTimeOfDay,
  WeekNumber,
} from '@/types/weekly-pattern';
import type {
  Activity,
  ActivityRequirement,
  ActivityRequirementCreateRequest,
  ApplicableWeeks,
} from '@/types/activity';
import {
  DAY_ABBREVIATIONS,
  hasWeekSpecificPatterns,
} from '@/types/weekly-pattern';
import {
  formatApplicableWeeks,
  getPriorityLabel,
  getPriorityColor,
} from '@/types/activity';

// ============================================================================
// Types
// ============================================================================

interface RotationEditorProps {
  /** Template ID being edited */
  templateId: string;
  /** Current weekly pattern */
  pattern: WeeklyPatternGrid;
  /** Available activities for selection */
  activities: Activity[];
  /** Current activity requirements */
  requirements: ActivityRequirement[];
  /** Loading state */
  isLoading?: boolean;
  /** Saving state */
  isSaving?: boolean;
  /** Read-only mode */
  readOnly?: boolean;
  /** Callback when pattern changes */
  onPatternChange: (pattern: WeeklyPatternGrid) => void;
  /** Callback when requirements change */
  onRequirementsChange: (requirements: ActivityRequirementCreateRequest[]) => void;
  /** Callback when save is requested */
  onSave?: () => void;
  /** Callback when cancel is requested */
  onCancel?: () => void;
}

// ============================================================================
// Constants
// ============================================================================

const DISPLAY_ORDER: DayOfWeek[] = [1, 2, 3, 4, 5, 6, 0]; // Mon-Sun
const TARGET_HALFDAYS = 10;

// ============================================================================
// Helper Functions
// ============================================================================

function findActivity(activities: Activity[], activityId: string | null): Activity | null {
  if (!activityId) return null;
  return activities.find((a) => a.id === activityId) ?? null;
}

function getSlotFromPattern(
  pattern: WeeklyPatternGrid,
  day: DayOfWeek,
  time: WeeklyPatternTimeOfDay,
  weekNumber: WeekNumber = null
): WeeklyPatternSlot | undefined {
  // First try to find a week-specific slot
  if (weekNumber !== null) {
    const weekSpecific = pattern.slots.find(
      (s) => s.dayOfWeek === day && s.timeOfDay === time && s.weekNumber === weekNumber
    );
    if (weekSpecific) return weekSpecific;
  }
  // Fall back to generic slot
  return pattern.slots.find(
    (s) => s.dayOfWeek === day && s.timeOfDay === time && (s.weekNumber === null || s.weekNumber === undefined)
  );
}

// ============================================================================
// Sub-Components
// ============================================================================

/**
 * Week tabs for switching between weeks.
 */
function WeekTabs({
  selectedWeek,
  onWeekChange,
  samePatternAllWeeks,
  onToggleSamePattern,
}: {
  selectedWeek: WeekNumber;
  onWeekChange: (week: WeekNumber) => void;
  samePatternAllWeeks: boolean;
  onToggleSamePattern: () => void;
}) {
  const weeks: Array<{ value: WeekNumber; label: string }> = [
    { value: null, label: 'All Weeks' },
    { value: 1, label: 'Week 1' },
    { value: 2, label: 'Week 2' },
    { value: 3, label: 'Week 3' },
    { value: 4, label: 'Week 4' },
  ];

  return (
    <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
      <div className="flex items-center gap-1">
        {weeks.map((week) => (
          <button
            key={week.value ?? 'all'}
            type="button"
            onClick={() => onWeekChange(week.value)}
            disabled={samePatternAllWeeks && week.value !== null}
            className={`
              px-3 py-1.5 text-sm font-medium rounded-md transition-colors
              ${selectedWeek === week.value
                ? 'bg-blue-100 text-blue-700'
                : samePatternAllWeeks && week.value !== null
                  ? 'text-gray-300 cursor-not-allowed'
                  : 'text-gray-600 hover:bg-gray-100'
              }
            `}
          >
            {week.label}
          </button>
        ))}
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={samePatternAllWeeks}
          onChange={onToggleSamePattern}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4"
        />
        <span className="text-gray-600">Same all weeks</span>
      </label>
    </div>
  );
}

/**
 * Activity selector dropdown.
 */
function ActivitySelector({
  activities,
  selectedId,
  onSelect,
  disabled,
}: {
  activities: Activity[];
  selectedId: string | null;
  onSelect: (activityId: string | null) => void;
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <select
        value={selectedId ?? ''}
        onChange={(e) => onSelect(e.target.value || null)}
        disabled={disabled}
        className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
      >
        <option value="">Select activity...</option>
        <option value="">-- Clear --</option>
        {activities.map((activity) => (
          <option key={activity.id} value={activity.id}>
            {activity.displayAbbreviation ?? activity.name} - {activity.name}
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Activity palette for quick selection.
 */
function ActivityPalette({
  activities,
  selectedId,
  onSelect,
}: {
  activities: Activity[];
  selectedId: string | null;
  onSelect: (activityId: string | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5 p-2 border rounded-lg bg-white">
      {/* Clear option */}
      <button
        type="button"
        className={`
          px-2 py-1 text-xs font-medium rounded border transition-colors
          ${selectedId === null ? 'ring-2 ring-blue-500 bg-gray-100' : 'bg-white hover:bg-gray-50'}
        `}
        onClick={() => onSelect(null)}
      >
        Clear
      </button>

      {/* Activity options */}
      {activities.map((activity) => {
        const bgClass = activity.backgroundColor ?? 'bg-gray-100';
        const textClass = activity.fontColor ?? 'text-gray-700';
        return (
          <button
            key={activity.id}
            type="button"
            className={`
              px-2 py-1 text-xs font-medium rounded border transition-colors
              ${bgClass} ${textClass}
              ${selectedId === activity.id ? 'ring-2 ring-blue-500' : 'hover:shadow-sm'}
            `}
            onClick={() => onSelect(activity.id)}
            title={activity.name}
          >
            {activity.displayAbbreviation ?? activity.name.slice(0, 4)}
            {activity.isProtected && <Lock className="inline w-3 h-3 ml-0.5" />}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Single slot cell in the grid.
 */
function SlotCell({
  slot,
  activity,
  isSelected,
  readOnly,
  onClick,
  onToggleProtected,
}: {
  slot: WeeklyPatternSlot;
  activity: Activity | null;
  isSelected: boolean;
  readOnly?: boolean;
  onClick: () => void;
  onToggleProtected: () => void;
}) {
  const bgColor = activity?.backgroundColor ?? 'bg-gray-50';
  const textColor = activity?.fontColor ?? 'text-gray-400';
  const isProtected = slot.isProtected || activity?.isProtected;

  const handleClick = (e: React.MouseEvent) => {
    if (readOnly) return;
    if (e.shiftKey) {
      onToggleProtected();
      return;
    }
    onClick();
  };

  return (
    <div
      className={`
        relative h-12 border rounded cursor-pointer transition-all
        ${isSelected ? 'ring-2 ring-blue-500' : ''}
        ${isProtected ? 'border-amber-400' : 'border-gray-200'}
        ${readOnly ? 'cursor-default' : 'hover:shadow-md'}
        ${bgColor}
      `}
      onClick={handleClick}
      role="button"
      tabIndex={readOnly ? -1 : 0}
      title={`${activity?.name ?? 'Empty'}${isProtected ? ' (protected)' : ''}\nShift+click to toggle protection`}
    >
      <div className={`flex items-center justify-center h-full ${textColor}`}>
        {activity ? (
          <span className="text-xs font-medium truncate px-1">
            {activity.displayAbbreviation ?? activity.name.slice(0, 4)}
          </span>
        ) : (
          <span className="text-xs text-gray-300">-</span>
        )}
      </div>

      {isProtected && (
        <Lock className="absolute top-0.5 right-0.5 w-3 h-3 text-amber-500" />
      )}
    </div>
  );
}

/**
 * Weekly pattern grid.
 */
function PatternGrid({
  pattern,
  activities,
  selectedWeek,
  selectedActivityId,
  readOnly,
  onSlotClick,
  onToggleProtected,
}: {
  pattern: WeeklyPatternGrid;
  activities: Activity[];
  selectedWeek: WeekNumber;
  selectedActivityId: string | null;
  readOnly?: boolean;
  onSlotClick: (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => void;
  onToggleProtected: (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => void;
}) {
  const [selectedSlot, setSelectedSlot] = useState<{day: DayOfWeek; time: WeeklyPatternTimeOfDay} | null>(null);

  const handleSlotClick = (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
    const newSelected = selectedSlot?.day === day && selectedSlot?.time === time ? null : { day, time };
    setSelectedSlot(newSelected);
    onSlotClick(day, time);
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="w-10 p-1 text-xs font-medium text-gray-500"></th>
            {DISPLAY_ORDER.map((day) => (
              <th key={day} className="p-1 text-xs font-medium text-gray-500 text-center">
                {DAY_ABBREVIATIONS[day]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(['AM', 'PM'] as WeeklyPatternTimeOfDay[]).map((time) => (
            <tr key={time}>
              <td className="p-1 text-xs font-medium text-gray-500 text-right">{time}</td>
              {DISPLAY_ORDER.map((day) => {
                const slot = getSlotFromPattern(pattern, day, time, selectedWeek);
                if (!slot) return <td key={day}></td>;

                // Get activity from slot - try activity_id first, fall back to activityType
                const activityId = (slot as WeeklyPatternSlot & { activity_id?: string }).activity_id;
                const activity = activityId
                  ? findActivity(activities, activityId)
                  : slot.activityType
                    ? activities.find((a) => a.code === slot.activityType)
                    : null;

                const isSelected = selectedSlot?.day === day && selectedSlot?.time === time;

                return (
                  <td key={day} className="p-0.5">
                    <SlotCell
                      slot={slot}
                      activity={activity}
                      isSelected={isSelected}
                      readOnly={readOnly}
                      onClick={() => handleSlotClick(day, time)}
                      onToggleProtected={() => onToggleProtected(day, time)}
                    />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Single activity requirement row with slider.
 */
function RequirementRow({
  requirement,
  activity,
  onUpdate,
  onDelete,
  readOnly,
}: {
  requirement: ActivityRequirementCreateRequest & { id?: string };
  activity: Activity;
  onUpdate: (updates: Partial<ActivityRequirementCreateRequest>) => void;
  onDelete: () => void;
  readOnly?: boolean;
}) {
  const [showDetails, setShowDetails] = useState(false);

  const target = requirement.targetHalfdays ?? 0;
  const min = requirement.minHalfdays ?? 0;
  const max = requirement.maxHalfdays ?? 14;
  const priority = requirement.priority ?? 50;

  return (
    <div className="p-3 border rounded-lg bg-white space-y-2">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded ${activity.backgroundColor ?? 'bg-gray-100'} ${activity.fontColor ?? 'text-gray-700'}`}
          >
            {activity.displayAbbreviation ?? activity.code}
          </span>
          <span className="text-sm font-medium text-gray-700">{activity.name}</span>
          {activity.isProtected && <Lock className="w-3 h-3 text-amber-500" />}
        </div>

        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 text-xs rounded ${getPriorityColor(priority)}`}>
            {getPriorityLabel(priority)}
          </span>
          {!readOnly && (
            <button
              type="button"
              onClick={onDelete}
              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
              title="Remove requirement"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Target slider */}
      <div className="flex items-center gap-3">
        <label className="text-xs text-gray-500 w-16">Target:</label>
        <input
          type="range"
          min={0}
          max={14}
          value={target}
          onChange={(e) => onUpdate({ targetHalfdays: parseInt(e.target.value) })}
          disabled={readOnly}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />
        <span className="text-sm font-medium w-8 text-right">{target}</span>
      </div>

      {/* Expandable details */}
      <button
        type="button"
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
      >
        <ChevronDown className={`w-3 h-3 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
        {showDetails ? 'Hide' : 'Show'} constraints
      </button>

      {showDetails && (
        <div className="pt-2 border-t space-y-3">
          {/* Min/Max */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Min half-days</label>
              <input
                type="number"
                min={0}
                max={14}
                value={min}
                onChange={(e) => onUpdate({ minHalfdays: parseInt(e.target.value) })}
                disabled={readOnly}
                className="w-full px-2 py-1 text-sm border rounded focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Max half-days</label>
              <input
                type="number"
                min={0}
                max={14}
                value={max}
                onChange={(e) => onUpdate({ maxHalfdays: parseInt(e.target.value) })}
                disabled={readOnly}
                className="w-full px-2 py-1 text-sm border rounded focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Priority */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Priority (0-100)</label>
            <input
              type="range"
              min={0}
              max={100}
              value={priority}
              onChange={(e) => onUpdate({ priority: parseInt(e.target.value) })}
              disabled={readOnly}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
              <span>Critical</span>
            </div>
          </div>

          {/* Applicable weeks */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Applicable weeks: {formatApplicableWeeks(requirement.applicableWeeks ?? null)}
            </label>
            <div className="flex gap-2">
              {[1, 2, 3, 4].map((week) => (
                <label key={week} className="flex items-center gap-1 text-xs">
                  <input
                    type="checkbox"
                    checked={!requirement.applicableWeeks || requirement.applicableWeeks.includes(week)}
                    onChange={(e) => {
                      const current = requirement.applicableWeeks ?? [1, 2, 3, 4];
                      const newWeeks = e.target.checked
                        ? [...current, week].filter((v, i, a) => a.indexOf(v) === i).sort()
                        : current.filter((w) => w !== week);
                      onUpdate({ applicableWeeks: newWeeks.length === 4 ? null : newWeeks });
                    }}
                    disabled={readOnly}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-3 h-3"
                  />
                  Wk {week}
                </label>
              ))}
            </div>
          </div>

          {/* Prefer full days */}
          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={requirement.preferFullDays ?? true}
              onChange={(e) => onUpdate({ preferFullDays: e.target.checked })}
              disabled={readOnly}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-3 h-3"
            />
            Prefer full days (AM+PM together)
          </label>
        </div>
      )}
    </div>
  );
}

/**
 * Activity requirements panel.
 */
function RequirementsPanel({
  requirements,
  activities,
  onAdd,
  onUpdate,
  onDelete,
  readOnly,
}: {
  requirements: (ActivityRequirementCreateRequest & { id?: string })[];
  activities: Activity[];
  onAdd: (activityId: string) => void;
  onUpdate: (index: number, updates: Partial<ActivityRequirementCreateRequest>) => void;
  onDelete: (index: number) => void;
  readOnly?: boolean;
}) {
  const [showAddDropdown, setShowAddDropdown] = useState(false);

  // Calculate total target half-days
  const totalTarget = useMemo(() => {
    return requirements.reduce((sum, req) => sum + (req.targetHalfdays ?? 0), 0);
  }, [requirements]);

  const isBalanced = totalTarget === TARGET_HALFDAYS;

  // Get activities not yet added
  const availableActivities = useMemo(() => {
    const usedIds = new Set(requirements.map((r) => r.activityId));
    return activities.filter((a) => !usedIds.has(a.id));
  }, [activities, requirements]);

  return (
    <div className="space-y-4">
      {/* Total bar */}
      <div className="p-3 rounded-lg bg-slate-50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-700">Total Half-Days</span>
          <span className={`text-lg font-bold ${isBalanced ? 'text-emerald-600' : 'text-amber-600'}`}>
            {totalTarget} / {TARGET_HALFDAYS}
          </span>
        </div>
        <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isBalanced ? 'bg-emerald-500' : totalTarget > TARGET_HALFDAYS ? 'bg-red-500' : 'bg-amber-500'
            }`}
            style={{ width: `${Math.min((totalTarget / TARGET_HALFDAYS) * 100, 100)}%` }}
          />
        </div>
        <div className="flex items-center gap-1 mt-1">
          {isBalanced ? (
            <CheckCircle className="h-3 w-3 text-emerald-500" />
          ) : (
            <AlertCircle className="h-3 w-3 text-amber-500" />
          )}
          <span className="text-xs text-slate-500">
            {isBalanced
              ? 'Balanced'
              : totalTarget > TARGET_HALFDAYS
              ? `${totalTarget - TARGET_HALFDAYS} over`
              : `${TARGET_HALFDAYS - totalTarget} under`}
          </span>
        </div>
      </div>

      {/* Requirements list */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {requirements.map((req, index) => {
          const activity = activities.find((a) => a.id === req.activityId);
          if (!activity) return null;

          return (
            <RequirementRow
              key={req.id ?? `new-${index}`}
              requirement={req}
              activity={activity}
              onUpdate={(updates) => onUpdate(index, updates)}
              onDelete={() => onDelete(index)}
              readOnly={readOnly}
            />
          );
        })}
      </div>

      {/* Add button */}
      {!readOnly && availableActivities.length > 0 && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowAddDropdown(!showAddDropdown)}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Activity Requirement
          </button>

          {showAddDropdown && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
              {availableActivities.map((activity) => (
                <button
                  key={activity.id}
                  type="button"
                  onClick={() => {
                    onAdd(activity.id);
                    setShowAddDropdown(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                >
                  <span
                    className={`px-2 py-0.5 text-xs rounded ${activity.backgroundColor ?? 'bg-gray-100'} ${activity.fontColor ?? 'text-gray-700'}`}
                  >
                    {activity.displayAbbreviation ?? activity.code}
                  </span>
                  {activity.name}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {requirements.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">
          No activity requirements configured. Add activities to define scheduling constraints.
        </p>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function RotationEditor({
  templateId,
  pattern,
  activities,
  requirements,
  isLoading = false,
  isSaving = false,
  readOnly = false,
  onPatternChange,
  onRequirementsChange,
  onSave,
  onCancel,
}: RotationEditorProps) {
  // Week state
  const [selectedWeek, setSelectedWeek] = useState<WeekNumber>(null);
  const [samePatternAllWeeks, setSamePatternAllWeeks] = useState(
    () => pattern.samePatternAllWeeks ?? !hasWeekSpecificPatterns(pattern)
  );

  // Activity selection state
  const [selectedActivityId, setSelectedActivityId] = useState<string | null>(null);

  // Local requirements state for editing
  const [localRequirements, setLocalRequirements] = useState<
    (ActivityRequirementCreateRequest & { id?: string })[]
  >(() =>
    requirements.map((r) => ({
      id: r.id,
      activityId: r.activityId,
      minHalfdays: r.minHalfdays,
      maxHalfdays: r.maxHalfdays,
      targetHalfdays: r.targetHalfdays,
      applicableWeeks: r.applicableWeeks,
      preferFullDays: r.preferFullDays,
      preferredDays: r.preferredDays,
      avoidDays: r.avoidDays,
      priority: r.priority,
    }))
  );

  // Handle week toggle
  const handleToggleSamePattern = useCallback(() => {
    setSamePatternAllWeeks((prev) => {
      const newValue = !prev;
      if (newValue) {
        setSelectedWeek(null);
      }
      onPatternChange({ ...pattern, samePatternAllWeeks: newValue });
      return newValue;
    });
  }, [pattern, onPatternChange]);

  // Handle slot click - paint with selected activity
  const handleSlotClick = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
      if (readOnly) return;

      const newSlots = pattern.slots.map((slot) => {
        if (slot.dayOfWeek === day && slot.timeOfDay === time) {
          return {
            ...slot,
            activityType: selectedActivityId
              ? activities.find((a) => a.id === selectedActivityId)?.code ?? null
              : null,
          };
        }
        return slot;
      });

      onPatternChange({ ...pattern, slots: newSlots });
    },
    [pattern, selectedActivityId, activities, onPatternChange, readOnly]
  );

  // Handle protection toggle
  const handleToggleProtected = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
      if (readOnly) return;

      const newSlots = pattern.slots.map((slot) => {
        if (slot.dayOfWeek === day && slot.timeOfDay === time) {
          return { ...slot, isProtected: !slot.isProtected };
        }
        return slot;
      });

      onPatternChange({ ...pattern, slots: newSlots });
    },
    [pattern, onPatternChange, readOnly]
  );

  // Handle adding a requirement
  const handleAddRequirement = useCallback((activityId: string) => {
    setLocalRequirements((prev) => [
      ...prev,
      {
        activityId,
        minHalfdays: 0,
        maxHalfdays: 14,
        targetHalfdays: 0,
        applicableWeeks: null,
        preferFullDays: true,
        preferredDays: null,
        avoidDays: null,
        priority: 50,
      },
    ]);
  }, []);

  // Handle updating a requirement
  const handleUpdateRequirement = useCallback(
    (index: number, updates: Partial<ActivityRequirementCreateRequest>) => {
      setLocalRequirements((prev) =>
        prev.map((req, i) => (i === index ? { ...req, ...updates } : req))
      );
    },
    []
  );

  // Handle deleting a requirement
  const handleDeleteRequirement = useCallback((index: number) => {
    setLocalRequirements((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // Handle save
  const handleSave = useCallback(() => {
    onRequirementsChange(localRequirements);
    onSave?.();
  }, [localRequirements, onRequirementsChange, onSave]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Week tabs */}
      <WeekTabs
        selectedWeek={selectedWeek}
        onWeekChange={setSelectedWeek}
        samePatternAllWeeks={samePatternAllWeeks}
        onToggleSamePattern={handleToggleSamePattern}
      />

      {/* Main content: Grid + Requirements side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Weekly Pattern Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Weekly Pattern</h3>

          {/* Activity palette */}
          {!readOnly && (
            <ActivityPalette
              activities={activities}
              selectedId={selectedActivityId}
              onSelect={setSelectedActivityId}
            />
          )}

          {/* Grid */}
          <PatternGrid
            pattern={pattern}
            activities={activities}
            selectedWeek={selectedWeek}
            selectedActivityId={selectedActivityId}
            readOnly={readOnly}
            onSlotClick={handleSlotClick}
            onToggleProtected={handleToggleProtected}
          />

          <p className="text-xs text-gray-500">
            Click an activity above, then click grid cells to paint. Shift+click to toggle protection.
          </p>
        </div>

        {/* Right: Activity Requirements */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Activity Requirements</h3>

          <RequirementsPanel
            requirements={localRequirements}
            activities={activities}
            onAdd={handleAddRequirement}
            onUpdate={handleUpdateRequirement}
            onDelete={handleDeleteRequirement}
            readOnly={readOnly}
          />
        </div>
      </div>

      {/* Action buttons */}
      {!readOnly && (onSave || onCancel) && (
        <div className="flex justify-end gap-3 pt-4 border-t">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
            >
              Cancel
            </button>
          )}
          {onSave && (
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isSaving && <Loader2 className="w-4 h-4 animate-spin" />}
              Save Changes
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default RotationEditor;
