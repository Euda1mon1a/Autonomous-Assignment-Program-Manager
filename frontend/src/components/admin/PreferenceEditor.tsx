'use client';

/**
 * PreferenceEditor Component
 *
 * Manages scheduling preferences for a rotation template including
 * preference types, weights, and configuration options.
 */
import React, { useState, useCallback, useMemo } from 'react';
import {
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Save,
  AlertTriangle,
  Loader2,
  Settings,
  Info,
} from 'lucide-react';
import type {
  RotationPreference,
  RotationPreferenceCreate,
  PreferenceType,
  PreferenceWeight,
} from '@/types/admin-templates';
import { PREFERENCE_TYPE_DEFINITIONS } from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

export interface PreferenceEditorProps {
  /** Template ID being edited */
  templateId: string;
  /** Template name for display */
  templateName: string;
  /** Current preferences */
  preferences: RotationPreference[];
  /** Whether preferences are loading */
  isLoading?: boolean;
  /** Callback to save preferences */
  onSave: (preferences: RotationPreferenceCreate[]) => void;
  /** Whether save is in progress */
  isSaving?: boolean;
  /** Callback to close editor */
  onClose?: () => void;
}

interface EditablePreference {
  id: string;
  preference_type: PreferenceType;
  weight: PreferenceWeight;
  config_json: Record<string, unknown>;
  is_active: boolean;
  description: string | null;
  isNew?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const WEIGHT_OPTIONS: { value: PreferenceWeight; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: 'bg-slate-500' },
  { value: 'medium', label: 'Medium', color: 'bg-blue-500' },
  { value: 'high', label: 'High', color: 'bg-amber-500' },
  { value: 'required', label: 'Required', color: 'bg-red-500' },
];

// ============================================================================
// Subcomponents
// ============================================================================

interface PreferenceCardProps {
  preference: EditablePreference;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onChange: (updates: Partial<EditablePreference>) => void;
  onDelete: () => void;
}

function PreferenceCard({
  preference,
  isExpanded,
  onToggleExpand,
  onChange,
  onDelete,
}: PreferenceCardProps) {
  const typeDefinition = useMemo(
    () =>
      PREFERENCE_TYPE_DEFINITIONS.find(
        (d) => d.type === preference.preferenceType
      ),
    [preference.preferenceType]
  );

  const weightOption = useMemo(
    () => WEIGHT_OPTIONS.find((w) => w.value === preference.weight),
    [preference.weight]
  );

  return (
    <div
      className={`
        bg-slate-800/50 border rounded-lg overflow-hidden transition-all
        ${preference.isActive ? 'border-slate-700' : 'border-slate-700/50 opacity-60'}
        ${preference.isNew ? 'ring-2 ring-violet-500/50' : ''}
      `}
    >
      {/* Header */}
      <div
        className="flex items-center gap-3 p-4 cursor-pointer hover:bg-slate-700/30 transition-colors"
        onClick={onToggleExpand}
      >
        <button className="p-1 text-slate-400">
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-white font-medium">
              {typeDefinition?.label || preference.preferenceType}
            </span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium text-white ${weightOption?.color}`}
            >
              {preference.weight}
            </span>
            {!preference.isActive && (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-600 text-slate-300">
                Inactive
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-0.5 truncate">
            {typeDefinition?.description}
          </p>
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
          title="Delete preference"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-slate-700 p-4 space-y-4">
          {/* Weight selector */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Weight
            </label>
            <div className="flex gap-2">
              {WEIGHT_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onChange({ weight: option.value })}
                  className={`
                    flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-all
                    ${
                      preference.weight === option.value
                        ? `${option.color} text-white`
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }
                  `}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Active toggle */}
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-slate-300">Active</label>
            <button
              onClick={() => onChange({ is_active: !preference.isActive })}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${preference.isActive ? 'bg-violet-500' : 'bg-slate-600'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${preference.isActive ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Notes (optional)
            </label>
            <input
              type="text"
              value={preference.description || ''}
              onChange={(e) => onChange({ description: e.target.value || null })}
              placeholder="Add notes about this preference..."
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-500"
            />
          </div>

          {/* Config section (for preferences with config) */}
          {typeDefinition?.hasConfig && typeDefinition.configSchema && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Configuration
              </label>
              <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700">
                {typeDefinition.configSchema.fields.map((field) => (
                  <div key={field.name} className="mb-3 last:mb-0">
                    <label className="block text-xs font-medium text-slate-400 mb-1">
                      {field.label}
                    </label>
                    {field.type === 'multiselect' && field.options && (
                      <div className="flex flex-wrap gap-1">
                        {field.options.map((option) => {
                          const currentValues = (preference.configJson[field.name] as string[]) || [];
                          const isSelected = currentValues.includes(option.value);

                          return (
                            <button
                              key={option.value}
                              onClick={() => {
                                const newValues = isSelected
                                  ? currentValues.filter((v) => v !== option.value)
                                  : [...currentValues, option.value];
                                onChange({
                                  config_json: {
                                    ...preference.configJson,
                                    [field.name]: newValues,
                                  },
                                });
                              }}
                              className={`
                                px-2 py-1 rounded text-xs font-medium transition-colors
                                ${
                                  isSelected
                                    ? 'bg-violet-500 text-white'
                                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                                }
                              `}
                            >
                              {option.label}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PreferenceEditor({
  templateId: _templateId,
  templateName,
  preferences: initialPreferences,
  isLoading = false,
  onSave,
  isSaving = false,
  onClose,
}: PreferenceEditorProps) {
  // Convert to editable format
  const [editablePreferences, setEditablePreferences] = useState<EditablePreference[]>(
    () =>
      initialPreferences.map((p) => ({
        id: p.id,
        preference_type: p.preferenceType,
        weight: p.weight,
        config_json: p.configJson,
        is_active: p.isActive,
        description: p.description,
        isNew: false,
      }))
  );

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Get available preference types (not already added)
  const availableTypes = useMemo(() => {
    const usedTypes = editablePreferences.map((p) => p.preferenceType);
    return PREFERENCE_TYPE_DEFINITIONS.filter((d) => !usedTypes.includes(d.type));
  }, [editablePreferences]);

  const handleAddPreference = useCallback((type: PreferenceType) => {
    const newId = `new-${Date.now()}`;
    setEditablePreferences((prev) => [
      ...prev,
      {
        id: newId,
        preference_type: type,
        weight: 'medium',
        config_json: {},
        is_active: true,
        description: null,
        isNew: true,
      },
    ]);
    setExpandedId(newId);
    setHasChanges(true);
  }, []);

  const handleUpdatePreference = useCallback(
    (id: string, updates: Partial<EditablePreference>) => {
      setEditablePreferences((prev) =>
        prev.map((p) => (p.id === id ? { ...p, ...updates } : p))
      );
      setHasChanges(true);
    },
    []
  );

  const handleDeletePreference = useCallback((id: string) => {
    setEditablePreferences((prev) => prev.filter((p) => p.id !== id));
    setHasChanges(true);
  }, []);

  const handleSave = useCallback(() => {
    const preferencesToSave: RotationPreferenceCreate[] = editablePreferences.map(
      (p) => ({
        preference_type: p.preferenceType,
        weight: p.weight,
        config_json: p.configJson,
        is_active: p.isActive,
        description: p.description,
      })
    );
    onSave(preferencesToSave);
    setHasChanges(false);
  }, [editablePreferences, onSave]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-violet-500/20 rounded-lg">
            <Settings className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">
              Scheduling Preferences
            </h2>
            <p className="text-sm text-slate-400">{templateName}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {onClose && (
            <button
              onClick={onClose}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={isSaving || !hasChanges}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            Save Preferences
          </button>
        </div>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-300">
          <p className="font-medium mb-1">About Scheduling Preferences</p>
          <p className="text-blue-300/80">
            Preferences are soft constraints that guide the scheduling optimizer.
            Higher weights give more priority to satisfying the preference.
            &quot;Required&quot; preferences must be satisfied for a valid schedule.
          </p>
        </div>
      </div>

      {/* Unsaved changes warning */}
      {hasChanges && (
        <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-amber-300">
            You have unsaved changes
          </span>
        </div>
      )}

      {/* Preference list */}
      <div className="space-y-3">
        {editablePreferences.length === 0 ? (
          <div className="p-8 text-center bg-slate-800/30 border border-slate-700 border-dashed rounded-lg">
            <Settings className="w-10 h-10 text-slate-400 mx-auto mb-3" />
            <p className="text-slate-300 mb-4">
              No preferences configured yet
            </p>
            <p className="text-sm text-slate-300">
              Add preferences to customize how this rotation is scheduled
            </p>
          </div>
        ) : (
          editablePreferences.map((pref) => (
            <PreferenceCard
              key={pref.id}
              preference={pref}
              isExpanded={expandedId === pref.id}
              onToggleExpand={() =>
                setExpandedId(expandedId === pref.id ? null : pref.id)
              }
              onChange={(updates) => handleUpdatePreference(pref.id, updates)}
              onDelete={() => handleDeletePreference(pref.id)}
            />
          ))
        )}
      </div>

      {/* Add preference section */}
      {availableTypes.length > 0 && (
        <div className="border-t border-slate-700 pt-6">
          <h3 className="text-sm font-medium text-slate-400 mb-3">
            Add Preference
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {availableTypes.map((typeDef) => (
              <button
                key={typeDef.type}
                onClick={() => handleAddPreference(typeDef.type)}
                className="flex items-center gap-2 p-3 bg-slate-800/50 border border-slate-700 hover:border-violet-500/50 rounded-lg text-left transition-colors"
              >
                <Plus className="w-4 h-4 text-violet-400 flex-shrink-0" />
                <div className="min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {typeDef.label}
                  </div>
                  <div className="text-xs text-slate-300 truncate">
                    {typeDef.description}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default PreferenceEditor;
