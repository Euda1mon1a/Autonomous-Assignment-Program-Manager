'use client';

import React, { useCallback, useState } from 'react';
import type {
  WeeklyPatternGrid,
  WeeklyPatternSlot,
  DayOfWeek,
  WeeklyPatternTimeOfDay,
  RotationTemplateRef,
} from '@/types/weekly-pattern';
import {
  DAY_ABBREVIATIONS,
  getSlot,
  updateSlot,
} from '@/types/weekly-pattern';

// ============================================================================
// Types
// ============================================================================

export interface WeeklyGridEditorProps {
  /** ID of the rotation template being edited */
  templateId: string;
  /** Current weekly pattern grid */
  pattern: WeeklyPatternGrid;
  /** Callback when pattern changes */
  onChange: (pattern: WeeklyPatternGrid) => void;
  /** Available rotation templates for selection */
  availableTemplates?: RotationTemplateRef[];
  /** Whether the editor is in read-only mode */
  readOnly?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export interface GridCellProps {
  /** Slot data for this cell */
  slot: WeeklyPatternSlot;
  /** Template info for the assigned rotation (if any) */
  template: RotationTemplateRef | null;
  /** Whether this cell is currently selected */
  isSelected: boolean;
  /** Whether the editor is read-only */
  readOnly: boolean;
  /** Click handler */
  onClick: () => void;
}

// ============================================================================
// Subcomponents
// ============================================================================

/**
 * Individual grid cell representing a day/time slot
 */
function GridCell({
  slot,
  template,
  isSelected,
  readOnly,
  onClick,
}: GridCellProps) {
  const bgColor = template?.backgroundColor || 'bg-gray-50';
  const textColor = template?.fontColor || 'text-gray-400';
  const label = template?.displayAbbreviation || '-';

  const selectedStyles = isSelected
    ? 'ring-2 ring-blue-500 ring-offset-1'
    : '';

  const hoverStyles = readOnly
    ? ''
    : 'hover:ring-2 hover:ring-blue-300 cursor-pointer';

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={readOnly}
      className={`
        w-full h-12 rounded-md font-medium text-sm
        flex items-center justify-center
        transition-all duration-150
        ${bgColor} ${textColor}
        ${selectedStyles} ${hoverStyles}
        disabled:cursor-default
      `}
      aria-label={`${DAY_ABBREVIATIONS[slot.dayOfWeek]} ${slot.timeOfDay}: ${template?.name || 'Empty'}`}
    >
      {label}
    </button>
  );
}

/**
 * Template selector dropdown for assigning rotations to slots
 */
function TemplateSelector({
  selectedId,
  templates,
  onSelect,
  onClear,
}: {
  selectedId: string | null;
  templates: RotationTemplateRef[];
  onSelect: (templateId: string) => void;
  onClear: () => void;
}) {
  return (
    <div className="flex flex-col gap-2 p-3 bg-white border border-gray-200 rounded-lg shadow-lg min-w-[200px]">
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
        Assign Rotation
      </div>

      {templates.map((template) => (
        <button
          key={template.id}
          type="button"
          onClick={() => onSelect(template.id)}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-md text-sm
            transition-colors duration-150
            ${selectedId === template.id ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50'}
          `}
        >
          <span
            className={`w-3 h-3 rounded ${template.backgroundColor || 'bg-gray-200'}`}
          />
          <span className="flex-1 text-left">{template.name}</span>
          <span className="text-xs text-gray-400">
            {template.displayAbbreviation}
          </span>
        </button>
      ))}

      <hr className="border-gray-200 my-1" />

      <button
        type="button"
        onClick={onClear}
        className="flex items-center gap-2 px-3 py-2 rounded-md text-sm text-gray-600 hover:bg-gray-50"
      >
        <span className="w-3 h-3 rounded bg-gray-200" />
        <span>Clear slot</span>
      </button>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

/**
 * WeeklyGridEditor - 7x2 grid for editing weekly rotation patterns
 *
 * Displays a grid of Mon-Sun x AM/PM slots where users can assign
 * rotation templates. Each cell shows the rotation's color and abbreviation.
 * Clicking a cell opens a selector to assign or change the rotation.
 *
 * @example
 * ```tsx
 * function PatternEditor({ templateId }: Props) {
 *   const { data: patternData } = useWeeklyPattern(templateId);
 *   const { data: templates } = useAvailableTemplates();
 *   const { mutate: updatePattern } = useUpdateWeeklyPattern();
 *
 *   const handleChange = (newPattern: WeeklyPatternGrid) => {
 *     updatePattern({ templateId, pattern: newPattern });
 *   };
 *
 *   return (
 *     <WeeklyGridEditor
 *       templateId={templateId}
 *       pattern={patternData?.pattern ?? createEmptyPattern()}
 *       onChange={handleChange}
 *       availableTemplates={templates}
 *     />
 *   );
 * }
 * ```
 */
export function WeeklyGridEditor({
  templateId: _templateId, // Reserved for future API integration
  pattern,
  onChange,
  availableTemplates = [],
  readOnly = false,
  className = '',
}: WeeklyGridEditorProps) {
  // Track selected cell for template assignment
  const [selectedCell, setSelectedCell] = useState<{
    dayOfWeek: DayOfWeek;
    timeOfDay: WeeklyPatternTimeOfDay;
  } | null>(null);

  // Get template info by ID
  const getTemplateById = useCallback(
    (id: string | null): RotationTemplateRef | null => {
      if (!id) return null;
      return availableTemplates.find((t) => t.id === id) || null;
    },
    [availableTemplates]
  );

  // Handle cell click
  const handleCellClick = useCallback(
    (dayOfWeek: DayOfWeek, timeOfDay: WeeklyPatternTimeOfDay) => {
      if (readOnly) return;

      // Toggle selection
      if (
        selectedCell?.dayOfWeek === dayOfWeek &&
        selectedCell?.timeOfDay === timeOfDay
      ) {
        setSelectedCell(null);
      } else {
        setSelectedCell({ dayOfWeek, timeOfDay });
      }
    },
    [readOnly, selectedCell]
  );

  // Handle template selection
  const handleTemplateSelect = useCallback(
    (rotationTemplateId: string | null) => {
      if (!selectedCell) return;

      const newPattern = updateSlot(
        pattern,
        selectedCell.dayOfWeek,
        selectedCell.timeOfDay,
        rotationTemplateId
      );

      onChange(newPattern);
      setSelectedCell(null);
    },
    [selectedCell, pattern, onChange]
  );

  // Get the currently selected slot's template ID
  const selectedSlot = selectedCell
    ? getSlot(pattern, selectedCell.dayOfWeek, selectedCell.timeOfDay)
    : null;

  // Days of the week (0-6)
  const days: DayOfWeek[] = [0, 1, 2, 3, 4, 5, 6];
  const times: WeeklyPatternTimeOfDay[] = ['AM', 'PM'];

  return (
    <div className={`relative ${className}`}>
      {/* Grid Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Weekly Pattern
        </h3>
        <p className="text-sm text-gray-500">
          Click a cell to assign a rotation template
        </p>
      </div>

      {/* Grid Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="w-16 px-2 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time
              </th>
              {days.map((day) => (
                <th
                  key={day}
                  className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {DAY_ABBREVIATIONS[day]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {times.map((time) => (
              <tr key={time}>
                <td className="px-2 py-2 text-sm font-medium text-gray-700">
                  {time}
                </td>
                {days.map((day) => {
                  const slot = getSlot(pattern, day, time);
                  if (!slot) return null;

                  const template = getTemplateById(slot.rotationTemplateId);
                  const isSelected =
                    selectedCell?.dayOfWeek === day &&
                    selectedCell?.timeOfDay === time;

                  return (
                    <td key={`${day}-${time}`} className="px-1 py-1">
                      <GridCell
                        slot={slot}
                        template={template}
                        isSelected={isSelected}
                        readOnly={readOnly}
                        onClick={() => handleCellClick(day, time)}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Template Selector Popover */}
      {selectedCell && !readOnly && (
        <div className="absolute z-10 mt-2 right-0">
          <TemplateSelector
            selectedId={selectedSlot?.rotationTemplateId || null}
            templates={availableTemplates}
            onSelect={handleTemplateSelect}
            onClear={() => handleTemplateSelect(null)}
          />
        </div>
      )}

      {/* Legend */}
      {availableTemplates.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
            Legend
          </div>
          <div className="flex flex-wrap gap-3">
            {availableTemplates.map((template) => (
              <div
                key={template.id}
                className="flex items-center gap-1.5 text-sm"
              >
                <span
                  className={`w-3 h-3 rounded ${template.backgroundColor || 'bg-gray-200'}`}
                />
                <span className="text-gray-600">
                  {template.displayAbbreviation}: {template.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * WeeklyGridEditorSkeleton - Loading state for the grid editor
 */
export function WeeklyGridEditorSkeleton() {
  const days = [0, 1, 2, 3, 4, 5, 6];
  const times = ['AM', 'PM'];

  return (
    <div className="animate-pulse">
      <div className="mb-4">
        <div className="h-6 w-32 bg-gray-200 rounded mb-2" />
        <div className="h-4 w-48 bg-gray-100 rounded" />
      </div>

      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="w-16 px-2 py-2">
              <div className="h-4 w-8 bg-gray-100 rounded" />
            </th>
            {days.map((day) => (
              <th key={day} className="px-2 py-2">
                <div className="h-4 w-8 bg-gray-100 rounded mx-auto" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {times.map((time) => (
            <tr key={time}>
              <td className="px-2 py-2">
                <div className="h-4 w-8 bg-gray-100 rounded" />
              </td>
              {days.map((day) => (
                <td key={`${day}-${time}`} className="px-1 py-1">
                  <div className="h-12 bg-gray-100 rounded-md" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default WeeklyGridEditor;
