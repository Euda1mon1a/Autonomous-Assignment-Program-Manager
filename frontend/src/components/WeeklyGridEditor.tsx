'use client';

/**
 * WeeklyGridEditor - Visual 7x2 grid editor for weekly rotation patterns.
 *
 * Features:
 * - Interactive grid showing AM/PM slots for each day of the week
 * - Click-to-select rotation template for each slot
 * - Color-coded cells based on assigned template
 * - Protected slot indication
 * - Optimistic updates with rollback on error
 */

import { useState, useCallback, useMemo } from 'react';
import { Loader2, Lock, X, FileText } from 'lucide-react';
import type {
  WeeklyPatternGrid,
  WeeklyPatternSlot,
  DayOfWeek,
  WeeklyPatternTimeOfDay,
  RotationTemplateRef,
  WeekNumber,
} from '@/types/weekly-pattern';
import { DAY_ABBREVIATIONS, DAY_NAMES, updateSlot, toggleSlotProtected, updateSlotDetails, getSlot, hasWeekSpecificPatterns } from '@/types/weekly-pattern';

// ============================================================================
// Types
// ============================================================================

interface WeeklyGridEditorProps {
  /** Template ID for the pattern being edited */
  templateId: string;
  /** Current pattern grid */
  pattern: WeeklyPatternGrid;
  /** Available rotation templates for selection */
  templates: RotationTemplateRef[];
  /** Whether the editor is in loading state */
  isLoading?: boolean;
  /** Whether changes are being saved */
  isSaving?: boolean;
  /** Callback when pattern changes */
  onChange: (pattern: WeeklyPatternGrid) => void;
  /** Callback when save is requested */
  onSave?: () => void;
  /** Callback when changes should be discarded */
  onCancel?: () => void;
  /** Whether to show the template selector */
  showSelector?: boolean;
  /** Read-only mode */
  readOnly?: boolean;
  /** Whether to show week tabs for week-specific patterns */
  showWeekTabs?: boolean;
}

interface SlotCellProps {
  slot: WeeklyPatternSlot;
  template: RotationTemplateRef | null;
  isSelected: boolean;
  isProtected?: boolean;
  readOnly?: boolean;
  onClick: () => void;
  onClear: () => void;
  onToggleProtected: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get display days in order: Mon-Sun (work week first).
 * Backend uses 0=Sunday, so we reorder for display.
 */
const DISPLAY_ORDER: DayOfWeek[] = [1, 2, 3, 4, 5, 6, 0]; // Mon, Tue, Wed, Thu, Fri, Sat, Sun

/**
 * Find template by ID from templates list.
 */
function findTemplate(
  templates: RotationTemplateRef[],
  templateId: string | null
): RotationTemplateRef | null {
  if (!templateId) return null;
  return templates.find((t) => t.id === templateId) ?? null;
}

/**
 * Get slot from pattern by day and time.
 */
function getSlotFromPattern(
  pattern: WeeklyPatternGrid,
  day: DayOfWeek,
  time: WeeklyPatternTimeOfDay
): WeeklyPatternSlot | undefined {
  return pattern.slots.find(
    (s) => s.dayOfWeek === day && s.timeOfDay === time
  );
}

// ============================================================================
// Components
// ============================================================================

/**
 * Individual slot cell in the grid.
 */
function SlotCell({
  slot,
  template,
  isSelected,
  isProtected = false,
  readOnly = false,
  onClick,
  onClear,
  onToggleProtected,
}: SlotCellProps) {
  const bgColor = template?.backgroundColor ?? 'bg-gray-50';
  const textColor = template?.fontColor ?? 'text-gray-400';

  const handleClick = (e: React.MouseEvent) => {
    if (readOnly) return;
    // Shift+click toggles protection
    if (e.shiftKey) {
      onToggleProtected();
      return;
    }
    // Normal click for slot selection (if not protected)
    if (!isProtected) {
      onClick();
    }
  };

  return (
    <div
      className={`
        relative h-12 border rounded cursor-pointer transition-all
        ${isSelected ? 'ring-2 ring-blue-500' : ''}
        ${isProtected ? 'border-amber-400 bg-amber-50/50' : ''}
        ${readOnly ? 'cursor-default' : 'hover:shadow-md'}
        ${bgColor}
      `}
      onClick={handleClick}
      role="button"
      tabIndex={readOnly ? -1 : 0}
      aria-label={`${DAY_ABBREVIATIONS[slot.dayOfWeek]} ${slot.timeOfDay}: ${
        template?.name ?? 'Empty'
      }${isProtected ? ' (protected)' : ''}`}
      title={readOnly ? undefined : 'Shift+click to toggle protection'}
      onKeyDown={(e) => {
        if (readOnly) return;
        if (e.key === 'Enter' || e.key === ' ') {
          if (e.shiftKey) {
            onToggleProtected();
          } else if (!isProtected) {
            onClick();
          }
        }
      }}
    >
      {/* Content */}
      <div className={`flex items-center justify-center h-full ${textColor}`}>
        {template ? (
          <span className="text-xs font-medium truncate px-1">
            {template.displayAbbreviation ?? template.name.slice(0, 4)}
          </span>
        ) : (
          <span className="text-xs text-gray-300">-</span>
        )}
      </div>

      {/* Protected indicator */}
      {isProtected && (
        <Lock className="absolute top-0.5 right-0.5 w-3 h-3 text-amber-500" />
      )}

      {/* Notes indicator */}
      {slot.notes && (
        <FileText className="absolute bottom-0.5 right-0.5 w-3 h-3 text-blue-400" />
      )}

      {/* Clear button (only on hover if has template) */}
      {template && !isProtected && !readOnly && (
        <button
          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full
                     opacity-0 hover:opacity-100 group-hover:opacity-100 transition-opacity
                     flex items-center justify-center"
          onClick={(e) => {
            e.stopPropagation();
            onClear();
          }}
          aria-label="Clear slot"
        >
          <X className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}

/** Activity type options for slot override */
const ACTIVITY_TYPE_OPTIONS = [
  { value: '', label: 'Use template default' },
  { value: 'fm_clinic', label: 'FM Clinic' },
  { value: 'specialty', label: 'Specialty Clinic' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'conference', label: 'Conference' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'elective', label: 'Elective' },
  { value: 'call', label: 'Call' },
  { value: 'off', label: 'Off' },
];

/**
 * Slot details panel for editing notes and activity type.
 */
function SlotDetailsPanel({
  slot,
  dayOfWeek,
  timeOfDay,
  templateName,
  onUpdateDetails,
  onClose,
}: {
  slot: WeeklyPatternSlot;
  dayOfWeek: DayOfWeek;
  timeOfDay: WeeklyPatternTimeOfDay;
  templateName: string;
  onUpdateDetails: (updates: { notes?: string | null; activityType?: string | null }) => void;
  onClose: () => void;
}) {
  return (
    <div className="p-3 border rounded-lg bg-slate-50 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-slate-700">
          {DAY_NAMES[dayOfWeek]} {timeOfDay} - {templateName || 'Empty slot'}
        </h4>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-200 rounded"
          aria-label="Close details"
        >
          <X className="w-4 h-4 text-slate-500" />
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {/* Activity Type Override */}
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            Activity Type Override
          </label>
          <select
            value={slot.activityType || ''}
            onChange={(e) => onUpdateDetails({ activityType: e.target.value || null })}
            className="w-full text-sm border rounded px-2 py-1.5 focus:ring-blue-500 focus:border-blue-500"
          >
            {ACTIVITY_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Notes */}
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">
            Notes
          </label>
          <input
            type="text"
            value={slot.notes || ''}
            onChange={(e) => onUpdateDetails({ notes: e.target.value || null })}
            placeholder="e.g., Building B, Room 201"
            className="w-full text-sm border rounded px-2 py-1.5 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Shift+click slot to toggle protection • Click another slot to edit it
      </p>
    </div>
  );
}

/**
 * Week tabs for switching between weeks in week-specific mode.
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
    <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
      <div className="flex items-center gap-1">
        {weeks.map((week) => (
          <button
            key={week.value ?? 'all'}
            type="button"
            onClick={() => onWeekChange(week.value)}
            disabled={samePatternAllWeeks && week.value !== null}
            className={`
              px-2 py-1 text-xs font-medium rounded transition-colors
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

      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={samePatternAllWeeks}
          onChange={onToggleSamePattern}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
        />
        <span className="text-gray-600">Same all weeks</span>
      </label>
    </div>
  );
}

/**
 * Template selector dropdown/palette.
 */
function TemplateSelector({
  templates,
  selectedId,
  onSelect,
}: {
  templates: RotationTemplateRef[];
  selectedId: string | null;
  onSelect: (templateId: string | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2 p-3 border rounded-lg bg-white">
      {/* Clear option */}
      <button
        className={`
          px-3 py-1.5 text-xs font-medium rounded border transition-colors
          ${selectedId === null ? 'ring-2 ring-blue-500 bg-gray-100' : 'bg-white hover:bg-gray-50'}
        `}
        onClick={() => onSelect(null)}
      >
        Clear
      </button>

      {/* Template options */}
      {templates.map((template) => (
        <button
          key={template.id}
          className={`
            px-3 py-1.5 text-xs font-medium rounded border transition-colors
            ${template.backgroundColor ?? 'bg-gray-100'}
            ${template.fontColor ?? 'text-gray-700'}
            ${selectedId === template.id ? 'ring-2 ring-blue-500' : 'hover:shadow-sm'}
          `}
          onClick={() => onSelect(template.id)}
        >
          {template.displayAbbreviation ?? template.name.slice(0, 6)}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WeeklyGridEditor({
  templateId,
  pattern,
  templates,
  isLoading = false,
  isSaving = false,
  onChange,
  onSave,
  onCancel,
  showSelector = true,
  readOnly = false,
  showWeekTabs = false,
}: WeeklyGridEditorProps) {
  // Selected slot for editing
  const [selectedSlot, setSelectedSlot] = useState<{
    day: DayOfWeek;
    time: WeeklyPatternTimeOfDay;
  } | null>(null);

  // Currently selected template for painting
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    null
  );

  // Week-specific pattern state
  const [selectedWeek, setSelectedWeek] = useState<WeekNumber>(null);
  const [samePatternAllWeeks, setSamePatternAllWeeks] = useState(
    () => pattern.samePatternAllWeeks ?? !hasWeekSpecificPatterns(pattern)
  );

  // Handle toggle of same pattern mode
  const handleToggleSamePattern = useCallback(() => {
    setSamePatternAllWeeks((prev) => {
      const newValue = !prev;
      if (newValue) {
        // Switching to same pattern - select "All Weeks"
        setSelectedWeek(null);
      }
      // Update the pattern to reflect the change
      onChange({ ...pattern, samePatternAllWeeks: newValue });
      return newValue;
    });
  }, [pattern, onChange]);

  // Track if there are unsaved changes
  const hasChanges = useMemo(() => {
    // Could implement deep comparison here
    return false; // Simplified for now
  }, []);

  // Handle slot click
  const handleSlotClick = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
      if (readOnly) return;

      // If we have a selected template, paint it
      if (selectedTemplateId !== null || selectedSlot?.day === day && selectedSlot?.time === time) {
        const newPattern = updateSlot(pattern, day, time, selectedTemplateId);
        onChange(newPattern);
      }

      // Toggle selection
      if (selectedSlot?.day === day && selectedSlot?.time === time) {
        setSelectedSlot(null);
      } else {
        setSelectedSlot({ day, time });
      }
    },
    [pattern, selectedTemplateId, selectedSlot, onChange, readOnly]
  );

  // Handle clearing a slot
  const handleClearSlot = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
      const newPattern = updateSlot(pattern, day, time, null);
      onChange(newPattern);
    },
    [pattern, onChange]
  );

  // Handle toggling protected status
  const handleToggleProtected = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
      const newPattern = toggleSlotProtected(pattern, day, time);
      onChange(newPattern);
    },
    [pattern, onChange]
  );

  // Handle updating slot details (notes, activity type)
  const handleUpdateSlotDetails = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay, updates: { notes?: string | null; activityType?: string | null }) => {
      const newPattern = updateSlotDetails(pattern, day, time, updates);
      onChange(newPattern);
    },
    [pattern, onChange]
  );

  // Handle template selection
  const handleTemplateSelect = useCallback(
    (templateId: string | null) => {
      setSelectedTemplateId(templateId);

      // If a slot is selected, apply immediately
      if (selectedSlot) {
        const newPattern = updateSlot(
          pattern,
          selectedSlot.day,
          selectedSlot.time,
          templateId
        );
        onChange(newPattern);
        setSelectedSlot(null);
      }
    },
    [selectedSlot, pattern, onChange]
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Template Selector */}
      {showSelector && !readOnly && (
        <TemplateSelector
          templates={templates}
          selectedId={selectedTemplateId}
          onSelect={handleTemplateSelect}
        />
      )}

      {/* Week Tabs */}
      {showWeekTabs && !readOnly && (
        <WeekTabs
          selectedWeek={selectedWeek}
          onWeekChange={setSelectedWeek}
          samePatternAllWeeks={samePatternAllWeeks}
          onToggleSamePattern={handleToggleSamePattern}
        />
      )}

      {/* Grid */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="w-12 p-1 text-xs font-medium text-gray-500"></th>
              {DISPLAY_ORDER.map((day) => (
                <th
                  key={day}
                  className="p-1 text-xs font-medium text-gray-500 text-center"
                >
                  {DAY_ABBREVIATIONS[day]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(['AM', 'PM'] as WeeklyPatternTimeOfDay[]).map((time) => (
              <tr key={time}>
                <td className="p-1 text-xs font-medium text-gray-500 text-right">
                  {time}
                </td>
                {DISPLAY_ORDER.map((day) => {
                  const slot = getSlotFromPattern(pattern, day, time);
                  if (!slot) return <td key={day}></td>;

                  const template = findTemplate(
                    templates,
                    slot.rotationTemplateId
                  );
                  const isSelected =
                    selectedSlot?.day === day && selectedSlot?.time === time;

                  return (
                    <td key={day} className="p-0.5 group">
                      <SlotCell
                        slot={slot}
                        template={template}
                        isSelected={isSelected}
                        isProtected={slot.isProtected}
                        readOnly={readOnly}
                        onClick={() => handleSlotClick(day, time)}
                        onClear={() => handleClearSlot(day, time)}
                        onToggleProtected={() => handleToggleProtected(day, time)}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Slot Details Panel - shown when slot is selected */}
      {selectedSlot && !readOnly && (() => {
        const selectedSlotData = getSlot(pattern, selectedSlot.day, selectedSlot.time);
        const selectedTemplate = selectedSlotData
          ? findTemplate(templates, selectedSlotData.rotationTemplateId)
          : null;
        return selectedSlotData ? (
          <SlotDetailsPanel
            slot={selectedSlotData}
            dayOfWeek={selectedSlot.day}
            timeOfDay={selectedSlot.time}
            templateName={selectedTemplate?.name || ''}
            onUpdateDetails={(updates) =>
              handleUpdateSlotDetails(selectedSlot.day, selectedSlot.time, updates)
            }
            onClose={() => setSelectedSlot(null)}
          />
        ) : null;
      })()}

      {/* Action Buttons */}
      {!readOnly && (onSave || onCancel) && (
        <div className="flex justify-end gap-2 pt-2 border-t">
          {onCancel && (
            <button
              type="button"
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              onClick={onCancel}
              disabled={isSaving}
            >
              Cancel
            </button>
          )}
          {onSave && (
            <button
              type="button"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50"
              onClick={onSave}
              disabled={isSaving}
            >
              {isSaving ? (
                <>
                  <Loader2 className="inline w-4 h-4 mr-1 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Pattern'
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default WeeklyGridEditor;
