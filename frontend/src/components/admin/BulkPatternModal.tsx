'use client';

/**
 * BulkPatternModal Component
 *
 * Modal for applying scheduling patterns to multiple templates at once.
 * Allows copying patterns from a source template or applying custom patterns.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  X,
  Calendar,
  Loader2,
  AlertTriangle,
  Copy,
  ChevronDown,
  Info,
} from 'lucide-react';
import type {
  RotationTemplate,
  PatternType,
  SettingType,
} from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface SchedulePattern {
  id?: string;
  pattern_type: PatternType;
  setting: SettingType;
  days_of_week: number[];
  start_block?: number;
  end_block?: number;
  recurrence_weeks?: number;
  notes?: string;
}

export interface BulkPatternModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Templates to apply patterns to */
  selectedTemplates: RotationTemplate[];
  /** All templates (for source selection) */
  allTemplates: RotationTemplate[];
  /** Callback to close modal */
  onClose: () => void;
  /** Callback when patterns are applied */
  onApply: (templateIds: string[], patterns: SchedulePattern[]) => Promise<void>;
  /** Whether apply is in progress */
  isApplying?: boolean;
  /** Function to fetch patterns for a template */
  fetchPatterns?: (templateId: string) => Promise<SchedulePattern[]>;
}

type PatternMode = 'copy' | 'custom';

// ============================================================================
// Constants
// ============================================================================

const PATTERN_TYPES: { value: PatternType; label: string; description: string }[] = [
  { value: 'regular', label: 'Regular', description: 'Fixed weekly pattern' },
  { value: 'split', label: 'Split', description: 'AM/PM split assignments' },
  { value: 'mirrored', label: 'Mirrored', description: 'Alternating week pattern' },
  { value: 'alternating', label: 'Alternating', description: 'Bi-weekly rotation' },
];

const SETTING_TYPES: { value: SettingType; label: string }[] = [
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'outpatient', label: 'Outpatient' },
];

const DAYS_OF_WEEK = [
  { value: 0, label: 'Sun', short: 'S' },
  { value: 1, label: 'Mon', short: 'M' },
  { value: 2, label: 'Tue', short: 'T' },
  { value: 3, label: 'Wed', short: 'W' },
  { value: 4, label: 'Thu', short: 'T' },
  { value: 5, label: 'Fri', short: 'F' },
  { value: 6, label: 'Sat', short: 'S' },
];

const DEFAULT_PATTERN: SchedulePattern = {
  pattern_type: 'regular',
  setting: 'outpatient',
  days_of_week: [1, 2, 3, 4, 5], // Mon-Fri
  recurrence_weeks: 1,
};

// ============================================================================
// Subcomponents
// ============================================================================

interface DaySelectorProps {
  selected: number[];
  onChange: (days: number[]) => void;
  disabled?: boolean;
}

function DaySelector({ selected, onChange, disabled = false }: DaySelectorProps) {
  const handleToggle = (day: number) => {
    if (disabled) return;
    if (selected.includes(day)) {
      onChange(selected.filter((d) => d !== day));
    } else {
      onChange([...selected, day].sort((a, b) => a - b));
    }
  };

  return (
    <div className="flex gap-1">
      {DAYS_OF_WEEK.map((day) => (
        <button
          key={day.value}
          type="button"
          onClick={() => handleToggle(day.value)}
          disabled={disabled}
          className={`
            w-8 h-8 rounded-full text-xs font-medium transition-colors
            ${
              selected.includes(day.value)
                ? 'bg-violet-500 text-white'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          title={day.label}
        >
          {day.short}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkPatternModal({
  isOpen,
  selectedTemplates,
  allTemplates,
  onClose,
  onApply,
  isApplying = false,
  fetchPatterns,
}: BulkPatternModalProps) {
  const [mode, setMode] = useState<PatternMode>('custom');
  const [sourceTemplateId, setSourceTemplateId] = useState<string>('');
  const [sourcePatterns, setSourcePatterns] = useState<SchedulePattern[]>([]);
  const [customPattern, setCustomPattern] = useState<SchedulePattern>(DEFAULT_PATTERN);
  const [isLoadingSource, setIsLoadingSource] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter out selected templates from source options
  const sourceOptions = useMemo(
    () => allTemplates.filter((t) => !selectedTemplates.some((s) => s.id === t.id)),
    [allTemplates, selectedTemplates]
  );

  const handleSourceChange = useCallback(
    async (templateId: string) => {
      setSourceTemplateId(templateId);
      setSourcePatterns([]);
      setError(null);

      if (!templateId || !fetchPatterns) return;

      setIsLoadingSource(true);
      try {
        const patterns = await fetchPatterns(templateId);
        setSourcePatterns(patterns);
      } catch {
        setError('Failed to load patterns from source template');
      } finally {
        setIsLoadingSource(false);
      }
    },
    [fetchPatterns]
  );

  const handleUpdatePattern = useCallback(
    (updates: Partial<SchedulePattern>) => {
      setCustomPattern((prev) => ({ ...prev, ...updates }));
    },
    []
  );

  const handleApply = useCallback(async () => {
    if (isApplying) return;

    const templateIds = selectedTemplates.map((t) => t.id);
    const patterns = mode === 'copy' ? sourcePatterns : [customPattern];

    if (mode === 'copy' && sourcePatterns.length === 0) {
      setError('Please select a source template with patterns');
      return;
    }

    await onApply(templateIds, patterns);
  }, [selectedTemplates, mode, sourcePatterns, customPattern, isApplying, onApply]);

  const handleClose = useCallback(() => {
    if (isApplying) return;
    onClose();
    // Reset state
    setMode('custom');
    setSourceTemplateId('');
    setSourcePatterns([]);
    setCustomPattern(DEFAULT_PATTERN);
    setError(null);
  }, [isApplying, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulk-pattern-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h2 id="bulk-pattern-title" className="text-lg font-semibold text-white">
                Apply Patterns
              </h2>
              <p className="text-sm text-slate-400">
                {selectedTemplates.length} template{selectedTemplates.length !== 1 ? 's' : ''} selected
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isApplying}
            className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Mode selection */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode('custom')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors ${
                mode === 'custom'
                  ? 'border-violet-500 bg-violet-500/10 text-white'
                  : 'border-slate-700 text-slate-400 hover:border-slate-600'
              }`}
            >
              <Calendar className="w-4 h-4" />
              Custom Pattern
            </button>
            <button
              type="button"
              onClick={() => setMode('copy')}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 transition-colors ${
                mode === 'copy'
                  ? 'border-violet-500 bg-violet-500/10 text-white'
                  : 'border-slate-700 text-slate-400 hover:border-slate-600'
              }`}
            >
              <Copy className="w-4 h-4" />
              Copy from Template
            </button>
          </div>

          {/* Copy mode */}
          {mode === 'copy' && (
            <div className="p-4 bg-slate-900/50 rounded-lg space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Source Template
                </label>
                <div className="relative">
                  <select
                    value={sourceTemplateId}
                    onChange={(e) => handleSourceChange(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white pr-10 focus:outline-none focus:ring-2 focus:ring-violet-500 appearance-none"
                  >
                    <option value="">Select a template...</option>
                    {sourceOptions.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              {isLoadingSource && (
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Loading patterns...
                </div>
              )}

              {sourcePatterns.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">
                    Found {sourcePatterns.length} pattern{sourcePatterns.length !== 1 ? 's' : ''}:
                  </p>
                  <div className="space-y-2">
                    {sourcePatterns.map((p, i) => (
                      <div
                        key={i}
                        className="p-2 bg-slate-800 rounded border border-slate-700 text-sm"
                      >
                        <span className="text-white font-medium">
                          {PATTERN_TYPES.find((pt) => pt.value === p.pattern_type)?.label}
                        </span>
                        <span className="text-slate-400 ml-2">
                          ({SETTING_TYPES.find((st) => st.value === p.setting)?.label})
                        </span>
                        <span className="text-slate-500 ml-2">
                          {p.days_of_week.map((d) => DAYS_OF_WEEK[d].short).join('')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {sourceTemplateId && !isLoadingSource && sourcePatterns.length === 0 && (
                <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <Info className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-amber-300">
                    This template has no patterns configured.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Custom pattern mode */}
          {mode === 'custom' && (
            <div className="p-4 bg-slate-900/50 rounded-lg space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Pattern Type
                  </label>
                  <select
                    value={customPattern.pattern_type}
                    onChange={(e) =>
                      handleUpdatePattern({
                        pattern_type: e.target.value as PatternType,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    {PATTERN_TYPES.map((pt) => (
                      <option key={pt.value} value={pt.value}>
                        {pt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Setting
                  </label>
                  <select
                    value={customPattern.setting}
                    onChange={(e) =>
                      handleUpdatePattern({
                        setting: e.target.value as SettingType,
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    {SETTING_TYPES.map((st) => (
                      <option key={st.value} value={st.value}>
                        {st.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Days of Week
                </label>
                <DaySelector
                  selected={customPattern.days_of_week}
                  onChange={(days) => handleUpdatePattern({ days_of_week: days })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Recurrence (weeks)
                  </label>
                  <input
                    type="number"
                    value={customPattern.recurrence_weeks ?? 1}
                    onChange={(e) =>
                      handleUpdatePattern({
                        recurrence_weeks: parseInt(e.target.value) || 1,
                      })
                    }
                    min={1}
                    max={12}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Notes (optional)
                </label>
                <input
                  type="text"
                  value={customPattern.notes ?? ''}
                  onChange={(e) =>
                    handleUpdatePattern({ notes: e.target.value || undefined })
                  }
                  placeholder="Add any notes about this pattern..."
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-red-300">{error}</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-slate-700">
          <button
            type="button"
            onClick={handleClose}
            disabled={isApplying}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleApply}
            disabled={isApplying || (mode === 'copy' && sourcePatterns.length === 0)}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isApplying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                Apply to {selectedTemplates.length} Template
                {selectedTemplates.length !== 1 ? 's' : ''}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default BulkPatternModal;
