'use client';

/**
 * BulkWeeklyPatternModal Component
 *
 * Modal for bulk updating weekly patterns across multiple rotation templates.
 * Supports two modes:
 * - Overlay: Add/modify specific slots while preserving others
 * - Replace: Overwrite entire pattern with the provided slots
 *
 * Can target specific weeks (1-4) or apply to all weeks.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  X,
  Loader2,
  AlertCircle,
  CheckCircle,
  Calendar,
  Layers,
  Replace,
  Info,
  RotateCcw,
} from 'lucide-react';
import { useAvailableTemplates, useBulkUpdateWeeklyPatterns } from '@/hooks/useWeeklyPattern';
import type {
  BatchPatternSlot,
  DayOfWeek,
  WeeklyPatternTimeOfDay,
  RotationTemplateRef,
} from '@/types/weekly-pattern';
import { DAY_ABBREVIATIONS } from '@/types/weekly-pattern';
import { ACTIVITY_TYPE_CONFIGS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

interface RotationTemplate {
  id: string;
  name: string;
}

interface BulkWeeklyPatternModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Selected templates to update */
  selectedTemplates: RotationTemplate[];
  /** Callback when modal should close */
  onClose: () => void;
  /** Callback when update is complete */
  onComplete?: () => void;
}

type UpdateMode = 'overlay' | 'replace';
type SelectorMode = 'templates' | 'activities';

interface SlotSelection {
  day: DayOfWeek;
  time: WeeklyPatternTimeOfDay;
  templateId: string | null;
  activityType: string | null;
}

// ============================================================================
// Constants
// ============================================================================

const DAYS: DayOfWeek[] = [1, 2, 3, 4, 5, 6, 0]; // Mon-Sun (display order)
const TIMES: WeeklyPatternTimeOfDay[] = ['AM', 'PM'];
const WEEKS = [1, 2, 3, 4] as const;

// ============================================================================
// Subcomponents
// ============================================================================

interface SlotCellProps {
  day: DayOfWeek;
  time: WeeklyPatternTimeOfDay;
  selection: SlotSelection | undefined;
  template: RotationTemplateRef | null;
  onClick: () => void;
}

function SlotCell({ day, time, selection, template, onClick }: SlotCellProps) {
  const isSelected = !!selection;

  // Determine colors and label based on selection type
  let bgColor = 'bg-slate-800';
  let textColor = 'text-slate-500';
  let label = '-';

  if (isSelected) {
    if (selection.templateId && template) {
      // Template mode
      bgColor = template.backgroundColor || 'bg-slate-700';
      textColor = template.fontColor || 'text-white';
      label = template.displayAbbreviation || template.name.substring(0, 3);
    } else if (selection.activityType) {
      // Activity mode
      const actConfig = ACTIVITY_TYPE_CONFIGS.find((c) => c.type === selection.activityType);
      if (actConfig) {
        bgColor = actConfig.bgColor;
        textColor = actConfig.color;
        label = actConfig.label.substring(0, 3).toUpperCase();
      }
    } else {
      // Clear selection
      bgColor = 'bg-slate-600';
      textColor = 'text-slate-300';
      label = 'CLR';
    }
  }

  const displayTitle = isSelected
    ? selection.templateId
      ? template?.name || 'Template'
      : selection.activityType
        ? ACTIVITY_TYPE_CONFIGS.find((c) => c.type === selection.activityType)?.label || selection.activityType
        : 'Clear'
    : 'Click to assign';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        w-full h-10 rounded font-medium text-xs
        flex items-center justify-center
        transition-all duration-150
        ${bgColor} ${textColor}
        ${isSelected ? 'ring-2 ring-violet-500 ring-offset-1 ring-offset-slate-900' : ''}
        hover:ring-2 hover:ring-violet-400 hover:ring-offset-1 hover:ring-offset-slate-900
        cursor-pointer
      `}
      title={`${DAY_ABBREVIATIONS[day]} ${time}: ${displayTitle}`}
    >
      {label}
    </button>
  );
}

interface TemplateSelectorProps {
  templates: RotationTemplateRef[];
  selectedTemplateId: string | null;
  onSelect: (templateId: string | null) => void;
}

function TemplateSelector({ templates, selectedTemplateId, onSelect }: TemplateSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onSelect(null)}
        className={`
          px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
          ${selectedTemplateId === null
            ? 'bg-slate-600 text-white ring-2 ring-violet-500'
            : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
          }
        `}
      >
        Clear
      </button>
      {templates.map((t) => (
        <button
          key={t.id}
          onClick={() => onSelect(t.id)}
          className={`
            px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
            ${t.backgroundColor || 'bg-slate-700'} ${t.fontColor || 'text-white'}
            ${selectedTemplateId === t.id
              ? 'ring-2 ring-violet-500'
              : 'hover:ring-2 hover:ring-slate-500'
            }
          `}
        >
          {t.displayAbbreviation || t.name.substring(0, 3)}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkWeeklyPatternModal({
  isOpen,
  selectedTemplates,
  onClose,
  onComplete,
}: BulkWeeklyPatternModalProps) {
  // State
  const [mode, setMode] = useState<UpdateMode>('overlay');
  const [selectorMode, setSelectorMode] = useState<SelectorMode>('activities');
  const [selectedWeeks, setSelectedWeeks] = useState<number[]>([]);
  const [sameAllWeeks, setSameAllWeeks] = useState(true);
  const [selections, setSelections] = useState<SlotSelection[]>([]);
  const [paintTemplateId, setPaintTemplateId] = useState<string | null>(null);
  const [paintActivityType, setPaintActivityType] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [applyCount, setApplyCount] = useState(0);

  // Queries
  const { data: availableTemplates = [], isLoading: templatesLoading } = useAvailableTemplates({
    enabled: isOpen,
  });

  // Mutations
  const bulkUpdate = useBulkUpdateWeeklyPatterns();

  // Handlers
  const handleWeekToggle = useCallback((week: number) => {
    setSelectedWeeks((prev) =>
      prev.includes(week) ? prev.filter((w) => w !== week) : [...prev, week]
    );
  }, []);

  const handleCellClick = useCallback((day: DayOfWeek, time: WeeklyPatternTimeOfDay) => {
    const currentPaint = selectorMode === 'templates' ? paintTemplateId : paintActivityType;

    setSelections((prev) => {
      const existing = prev.find((s) => s.day === day && s.time === time);
      if (existing) {
        // If clicking same cell with same value, remove it
        const existingValue = selectorMode === 'templates' ? existing.templateId : existing.activityType;
        if (existingValue === currentPaint) {
          return prev.filter((s) => !(s.day === day && s.time === time));
        }
        // Otherwise update
        return prev.map((s) =>
          s.day === day && s.time === time
            ? {
                ...s,
                templateId: selectorMode === 'templates' ? paintTemplateId : null,
                activityType: selectorMode === 'activities' ? paintActivityType : null,
              }
            : s
        );
      }
      // Add new selection
      return [...prev, {
        day,
        time,
        templateId: selectorMode === 'templates' ? paintTemplateId : null,
        activityType: selectorMode === 'activities' ? paintActivityType : null,
      }];
    });
    // Clear any success message when user makes changes
    setSuccessMessage(null);
    setStatus('idle');
  }, [selectorMode, paintTemplateId, paintActivityType]);

  const handleClearSelections = useCallback(() => {
    setSelections([]);
  }, []);

  const handleApply = useCallback(async () => {
    if (selections.length === 0) {
      setErrorMessage('Please select at least one slot to update');
      setStatus('error');
      return;
    }

    if (!sameAllWeeks && selectedWeeks.length === 0) {
      setErrorMessage('Please select at least one week');
      setStatus('error');
      return;
    }

    setStatus('idle');
    setErrorMessage(null);
    setSuccessMessage(null);

    // Convert selections to BatchPatternSlot format
    const slots: BatchPatternSlot[] = selections.map((s) => ({
      day_of_week: s.day,
      time_of_day: s.time,
      linked_template_id: s.templateId,
      activity_type: s.activityType || (s.templateId ? 'scheduled' : 'off'),
    }));

    const weekLabel = sameAllWeeks
      ? 'all weeks'
      : `week${selectedWeeks.length > 1 ? 's' : ''} ${selectedWeeks.sort().join(', ')}`;

    try {
      const result = await bulkUpdate.mutateAsync({
        template_ids: selectedTemplates.map((t) => t.id),
        mode,
        slots,
        week_numbers: sameAllWeeks ? null : selectedWeeks,
        dry_run: false,
      });

      // Success - stay open for another pass
      setStatus('success');
      setSuccessMessage(
        `Updated ${result.successful} template(s) for ${weekLabel}. ` +
        `Configure another pass or click Done.`
      );
      setSelections([]); // Clear for next pass
      setApplyCount((c) => c + 1);
      onComplete?.(); // Notify parent to refresh data
    } catch (error) {
      setStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Failed to update patterns');
    }
  }, [selections, selectedWeeks, sameAllWeeks, mode, selectedTemplates, bulkUpdate, onComplete]);

  const handleClose = useCallback(() => {
    setSelections([]);
    setSelectedWeeks([]);
    setSameAllWeeks(true);
    setMode('overlay');
    setSelectorMode('activities');
    setPaintTemplateId(null);
    setPaintActivityType(null);
    setStatus('idle');
    setErrorMessage(null);
    setSuccessMessage(null);
    setApplyCount(0);
    onClose();
  }, [onClose]);

  // Derive template map for quick lookup
  const templateMap = useMemo(() => {
    const map = new Map<string, RotationTemplateRef>();
    availableTemplates.forEach((t) => map.set(t.id, t));
    return map;
  }, [availableTemplates]);

  // Get slot selection helper
  const getSelection = useCallback(
    (day: DayOfWeek, time: WeeklyPatternTimeOfDay) =>
      selections.find((s) => s.day === day && s.time === time),
    [selections]
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Calendar className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Bulk Edit Weekly Patterns</h2>
              <p className="text-sm text-slate-400">
                Applying to {selectedTemplates.length} template{selectedTemplates.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={bulkUpdate.isPending}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Success Banner */}
          {successMessage && (
            <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm text-green-300">{successMessage}</p>
                {applyCount > 0 && (
                  <p className="text-xs text-green-400/70 mt-1">
                    {applyCount} update{applyCount !== 1 ? 's' : ''} applied this session
                  </p>
                )}
              </div>
              <button
                onClick={() => setSuccessMessage(null)}
                className="text-green-400 hover:text-green-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Error State */}
          {status === 'error' && errorMessage && (
            <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
              <p className="text-sm text-red-300">{errorMessage}</p>
            </div>
          )}

          <>
              {/* Mode Toggle */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Update Mode</label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setMode('overlay')}
                    className={`
                      flex-1 flex items-center gap-3 p-4 rounded-lg border transition-colors
                      ${mode === 'overlay'
                        ? 'bg-violet-500/20 border-violet-500 text-white'
                        : 'bg-slate-700/50 border-slate-600 text-slate-300 hover:border-slate-500'
                      }
                    `}
                  >
                    <Layers className="w-5 h-5" />
                    <div className="text-left">
                      <div className="font-medium">Overlay</div>
                      <div className="text-xs text-slate-400">Add/modify slots, preserve others</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setMode('replace')}
                    className={`
                      flex-1 flex items-center gap-3 p-4 rounded-lg border transition-colors
                      ${mode === 'replace'
                        ? 'bg-violet-500/20 border-violet-500 text-white'
                        : 'bg-slate-700/50 border-slate-600 text-slate-300 hover:border-slate-500'
                      }
                    `}
                  >
                    <Replace className="w-5 h-5" />
                    <div className="text-left">
                      <div className="font-medium">Replace</div>
                      <div className="text-xs text-slate-400">Overwrite entire pattern</div>
                    </div>
                  </button>
                </div>
              </div>

              {/* Week Selection */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Apply to Weeks</label>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sameAllWeeks}
                      onChange={(e) => setSameAllWeeks(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-violet-600 focus:ring-violet-500 focus:ring-offset-slate-800"
                    />
                    <span className="text-sm text-slate-300">Same pattern all weeks</span>
                  </label>
                </div>
                {!sameAllWeeks && (
                  <div className="flex gap-3 mt-2">
                    {WEEKS.map((week) => (
                      <label
                        key={week}
                        className={`
                          flex items-center justify-center w-20 py-2 rounded-lg cursor-pointer transition-colors
                          ${selectedWeeks.includes(week)
                            ? 'bg-violet-500/20 border-violet-500 text-white'
                            : 'bg-slate-700/50 border-slate-600 text-slate-400'
                          }
                          border
                        `}
                      >
                        <input
                          type="checkbox"
                          checked={selectedWeeks.includes(week)}
                          onChange={() => handleWeekToggle(week)}
                          className="sr-only"
                        />
                        Week {week}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Selector Mode Toggle */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-slate-300">Paint Mode</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectorMode('activities')}
                    className={`
                      px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                      ${selectorMode === 'activities'
                        ? 'bg-violet-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }
                    `}
                  >
                    Activity Types
                  </button>
                  <button
                    onClick={() => setSelectorMode('templates')}
                    className={`
                      px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                      ${selectorMode === 'templates'
                        ? 'bg-violet-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      }
                    `}
                  >
                    Linked Templates
                  </button>
                </div>
                <p className="text-xs text-slate-500">
                  {selectorMode === 'activities'
                    ? 'Set what activity happens in a slot (Clinic, Conference, etc.)'
                    : 'Link slot to another rotation template'
                  }
                </p>
              </div>

              {/* Activity Type Selector */}
              {selectorMode === 'activities' && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-300">
                    Select activity to paint
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => setPaintActivityType(null)}
                      className={`
                        px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                        ${paintActivityType === null
                          ? 'bg-slate-600 text-white ring-2 ring-violet-500'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                        }
                      `}
                    >
                      Clear
                    </button>
                    {ACTIVITY_TYPE_CONFIGS.map((config) => (
                      <button
                        key={config.type}
                        onClick={() => setPaintActivityType(config.type)}
                        className={`
                          px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                          ${config.bgColor} ${config.color}
                          ${paintActivityType === config.type
                            ? 'ring-2 ring-violet-500'
                            : 'hover:ring-2 hover:ring-slate-500'
                          }
                        `}
                      >
                        {config.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Template Selector */}
              {selectorMode === 'templates' && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-300">
                    Select template to paint
                  </label>
                  {templatesLoading ? (
                    <div className="flex items-center gap-2 text-slate-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Loading templates...
                    </div>
                  ) : (
                    <TemplateSelector
                      templates={availableTemplates}
                      selectedTemplateId={paintTemplateId}
                      onSelect={setPaintTemplateId}
                    />
                  )}
                </div>
              )}

              {/* Grid Editor */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-sm font-medium text-slate-300">
                    Click slots to assign
                  </label>
                  {selections.length > 0 && (
                    <button
                      onClick={handleClearSelections}
                      className="text-xs text-slate-400 hover:text-white transition-colors"
                    >
                      Clear all ({selections.length} slots)
                    </button>
                  )}
                </div>

                <div className="bg-slate-900 rounded-lg p-4">
                  {/* Header row */}
                  <div className="grid grid-cols-8 gap-1 mb-2">
                    <div className="text-xs text-slate-500 text-center"></div>
                    {DAYS.map((day) => (
                      <div key={day} className="text-xs text-slate-400 text-center font-medium">
                        {DAY_ABBREVIATIONS[day]}
                      </div>
                    ))}
                  </div>

                  {/* Time rows */}
                  {TIMES.map((time) => (
                    <div key={time} className="grid grid-cols-8 gap-1 mb-1">
                      <div className="text-xs text-slate-500 text-center self-center">{time}</div>
                      {DAYS.map((day) => {
                        const selection = getSelection(day, time);
                        const template = selection?.templateId
                          ? templateMap.get(selection.templateId) || null
                          : null;
                        return (
                          <SlotCell
                            key={`${day}-${time}`}
                            day={day}
                            time={time}
                            selection={selection}
                            template={template}
                            onClick={() => handleCellClick(day, time)}
                          />
                        );
                      })}
                    </div>
                  ))}
                </div>

                {/* Preview text */}
                {selections.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <Info className="w-3 h-3" />
                    Will {mode === 'overlay' ? 'modify' : 'set'} {selections.length} slot
                    {selections.length !== 1 ? 's' : ''} on {selectedTemplates.length} template
                    {selectedTemplates.length !== 1 ? 's' : ''}
                    {!sameAllWeeks && selectedWeeks.length > 0 && (
                      <span>
                        {' '}
                        (Week{selectedWeeks.length !== 1 ? 's' : ''} {selectedWeeks.sort().join(', ')})
                      </span>
                    )}
                  </div>
                )}
              </div>
            </>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-slate-700">
          {/* Left side - Reset button if changes have been applied */}
          <div>
            {applyCount > 0 && (
              <button
                onClick={() => {
                  setSelections([]);
                  setSelectedWeeks([]);
                  setSameAllWeeks(true);
                  setSuccessMessage(null);
                }}
                className="flex items-center gap-2 px-3 py-2 text-slate-400 hover:text-white text-sm transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Reset for new pass
              </button>
            )}
          </div>

          {/* Right side - Action buttons */}
          <div className="flex items-center gap-3">
            {applyCount > 0 ? (
              <button
                onClick={handleClose}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Done ({applyCount} applied)
              </button>
            ) : (
              <button
                onClick={handleClose}
                disabled={bulkUpdate.isPending}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleApply}
              disabled={bulkUpdate.isPending || selections.length === 0}
              className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {bulkUpdate.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Apply to {selectedTemplates.length} Template{selectedTemplates.length !== 1 ? 's' : ''}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BulkWeeklyPatternModal;
