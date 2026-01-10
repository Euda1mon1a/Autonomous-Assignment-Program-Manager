'use client';

/**
 * BulkPreferenceModal Component
 *
 * Modal for applying scheduling preferences to multiple templates at once.
 * Supports copying preferences from a source template or adding custom preferences.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  X,
  Settings,
  Loader2,
  AlertTriangle,
  Copy,
  Plus,
  Trash2,
  ChevronDown,
  Info,
} from 'lucide-react';
import type {
  RotationTemplate,
  RotationPreferenceCreate,
  PreferenceType,
  PreferenceWeight,
} from '@/types/admin-templates';
import { PREFERENCE_TYPE_DEFINITIONS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface BulkPreferenceModalProps {
  /** Whether modal is open */
  isOpen: boolean;
  /** Templates to apply preferences to */
  selectedTemplates: RotationTemplate[];
  /** All templates (for source selection) */
  allTemplates: RotationTemplate[];
  /** Callback to close modal */
  onClose: () => void;
  /** Callback when preferences are applied */
  onApply: (
    templateIds: string[],
    preferences: RotationPreferenceCreate[],
    mode: 'replace' | 'merge'
  ) => Promise<void>;
  /** Whether apply is in progress */
  isApplying?: boolean;
  /** Function to fetch preferences for a template */
  fetchPreferences?: (templateId: string) => Promise<RotationPreferenceCreate[]>;
}

type PreferenceMode = 'copy' | 'custom';
type ApplyMode = 'replace' | 'merge';

// ============================================================================
// Constants
// ============================================================================

const WEIGHT_OPTIONS: { value: PreferenceWeight; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'bg-slate-500' },
  { value: 'medium', label: 'Medium', color: 'bg-blue-500' },
  { value: 'high', label: 'High', color: 'bg-amber-500' },
  { value: 'required', label: 'Required', color: 'bg-red-500' },
];

interface EditablePreference extends RotationPreferenceCreate {
  _id: string;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface PreferenceRowProps {
  preference: EditablePreference;
  onChange: (updates: Partial<RotationPreferenceCreate>) => void;
  onRemove: () => void;
  availableTypes: PreferenceType[];
}

function PreferenceRow({
  preference,
  onChange,
  onRemove,
  availableTypes,
}: PreferenceRowProps) {
  const typeDef = PREFERENCE_TYPE_DEFINITIONS.find(
    (d) => d.type === preference.preferenceType
  );

  return (
    <div className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700">
      <div className="flex-1 min-w-0">
        <select
          value={preference.preferenceType}
          onChange={(e) =>
            onChange({ preferenceType: e.target.value as PreferenceType })
          }
          className="w-full px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
        >
          <option value={preference.preferenceType}>
            {typeDef?.label || preference.preferenceType}
          </option>
          {availableTypes
            .filter((t) => t !== preference.preferenceType)
            .map((type) => {
              const def = PREFERENCE_TYPE_DEFINITIONS.find((d) => d.type === type);
              return (
                <option key={type} value={type}>
                  {def?.label || type}
                </option>
              );
            })}
        </select>
        <p className="text-xs text-slate-400 mt-1 truncate">
          {typeDef?.description}
        </p>
      </div>

      <select
        value={preference.weight}
        onChange={(e) => onChange({ weight: e.target.value as PreferenceWeight })}
        className="px-2 py-1.5 bg-slate-700 border border-slate-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
      >
        {WEIGHT_OPTIONS.map((w) => (
          <option key={w.value} value={w.value}>
            {w.label}
          </option>
        ))}
      </select>

      <button
        type="button"
        onClick={onRemove}
        className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
        title="Remove preference"
        aria-label="Remove"
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function BulkPreferenceModal({
  isOpen,
  selectedTemplates,
  allTemplates,
  onClose,
  onApply,
  isApplying = false,
  fetchPreferences,
}: BulkPreferenceModalProps) {
  const [mode, setMode] = useState<PreferenceMode>('custom');
  const [applyMode, setApplyMode] = useState<ApplyMode>('merge');
  const [sourceTemplateId, setSourceTemplateId] = useState<string>('');
  const [sourcePreferences, setSourcePreferences] = useState<RotationPreferenceCreate[]>([]);
  const [customPreferences, setCustomPreferences] = useState<EditablePreference[]>([]);
  const [isLoadingSource, setIsLoadingSource] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter out selected templates from source options
  const sourceOptions = useMemo(
    () => allTemplates.filter((t) => !selectedTemplates.some((s) => s.id === t.id)),
    [allTemplates, selectedTemplates]
  );

  // Get available preference types for custom mode
  const availableTypes = useMemo(() => {
    const usedTypes = customPreferences.map((p) => p.preferenceType);
    return PREFERENCE_TYPE_DEFINITIONS.map((d) => d.type).filter(
      (t) => !usedTypes.includes(t)
    );
  }, [customPreferences]);

  const handleSourceChange = useCallback(
    async (templateId: string) => {
      setSourceTemplateId(templateId);
      setSourcePreferences([]);
      setError(null);

      if (!templateId || !fetchPreferences) return;

      setIsLoadingSource(true);
      try {
        const preferences = await fetchPreferences(templateId);
        setSourcePreferences(preferences);
      } catch {
        setError('Failed to load preferences from source template');
      } finally {
        setIsLoadingSource(false);
      }
    },
    [fetchPreferences]
  );

  const handleAddPreference = useCallback(() => {
    if (availableTypes.length === 0) return;

    const newPref: EditablePreference = {
      _id: `pref-${Date.now()}`,
      preferenceType: availableTypes[0],
      weight: 'medium',
      isActive: true,
    };
    setCustomPreferences((prev) => [...prev, newPref]);
  }, [availableTypes]);

  const handleUpdatePreference = useCallback(
    (id: string, updates: Partial<RotationPreferenceCreate>) => {
      setCustomPreferences((prev) =>
        prev.map((p) => (p._id === id ? { ...p, ...updates } : p))
      );
    },
    []
  );

  const handleRemovePreference = useCallback((id: string) => {
    setCustomPreferences((prev) => prev.filter((p) => p._id !== id));
  }, []);

  const handleApply = useCallback(async () => {
    if (isApplying) return;

    const templateIds = selectedTemplates.map((t) => t.id);
    const preferences =
      mode === 'copy'
        ? sourcePreferences
        : customPreferences.map(({ _id, ...rest }) => rest);

    if (preferences.length === 0) {
      setError('Please add at least one preference');
      return;
    }

    await onApply(templateIds, preferences, applyMode);
  }, [
    selectedTemplates,
    mode,
    sourcePreferences,
    customPreferences,
    applyMode,
    isApplying,
    onApply,
  ]);

  const handleClose = useCallback(() => {
    if (isApplying) return;
    onClose();
    // Reset state
    setMode('custom');
    setApplyMode('merge');
    setSourceTemplateId('');
    setSourcePreferences([]);
    setCustomPreferences([]);
    setError(null);
  }, [isApplying, onClose]);

  if (!isOpen) return null;

  const currentPreferences = mode === 'copy' ? sourcePreferences : customPreferences;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="bulk-preference-title"
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-500/20 rounded-lg">
              <Settings className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h2 id="bulk-preference-title" className="text-lg font-semibold text-white">
                Apply Preferences
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
              <Settings className="w-4 h-4" />
              Custom Preferences
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

          {/* Apply mode selection */}
          <div className="p-3 bg-slate-900/50 rounded-lg">
            <p className="text-xs font-medium text-slate-400 mb-2">Apply Mode</p>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="applyMode"
                  value="merge"
                  checked={applyMode === 'merge'}
                  onChange={() => setApplyMode('merge')}
                  className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                />
                <div>
                  <span className="text-sm text-white">Merge</span>
                  <p className="text-xs text-slate-400">Add to existing preferences</p>
                </div>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="applyMode"
                  value="replace"
                  checked={applyMode === 'replace'}
                  onChange={() => setApplyMode('replace')}
                  className="w-4 h-4 text-violet-500 focus:ring-violet-500 focus:ring-offset-slate-800"
                />
                <div>
                  <span className="text-sm text-white">Replace</span>
                  <p className="text-xs text-slate-400">Remove existing preferences first</p>
                </div>
              </label>
            </div>
          </div>

          {/* Copy mode source selection */}
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
                  Loading preferences...
                </div>
              )}

              {sourcePreferences.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">
                    Found {sourcePreferences.length} preference{sourcePreferences.length !== 1 ? 's' : ''}:
                  </p>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {sourcePreferences.map((p, i) => {
                      const typeDef = PREFERENCE_TYPE_DEFINITIONS.find(
                        (d) => d.type === p.preferenceType
                      );
                      const weightOpt = WEIGHT_OPTIONS.find((w) => w.value === p.weight);
                      return (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-700"
                        >
                          <span className="text-sm text-white">
                            {typeDef?.label || p.preferenceType}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium text-white ${weightOpt?.color}`}
                          >
                            {p.weight}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {sourceTemplateId && !isLoadingSource && sourcePreferences.length === 0 && (
                <div className="flex items-start gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <Info className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-amber-300">
                    This template has no preferences configured.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Custom preferences mode */}
          {mode === 'custom' && (
            <div className="p-4 bg-slate-900/50 rounded-lg space-y-3">
              {customPreferences.length === 0 ? (
                <div className="text-center py-4">
                  <Settings className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-sm text-slate-400">No preferences added yet</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {customPreferences.map((pref) => (
                    <PreferenceRow
                      key={pref._id}
                      preference={pref}
                      onChange={(updates) => handleUpdatePreference(pref._id, updates)}
                      onRemove={() => handleRemovePreference(pref._id)}
                      availableTypes={availableTypes}
                    />
                  ))}
                </div>
              )}

              {availableTypes.length > 0 && (
                <button
                  type="button"
                  onClick={handleAddPreference}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 border-2 border-dashed border-slate-600 hover:border-violet-500/50 rounded-lg text-slate-400 hover:text-white transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Add Preference
                </button>
              )}
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
            disabled={isApplying || currentPreferences.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isApplying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Settings className="w-4 h-4" />
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

export default BulkPreferenceModal;
