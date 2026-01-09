'use client';

/**
 * WeeklyRequirementsEditor Component
 *
 * Form for editing resident weekly scheduling requirements per rotation template.
 * Includes validation, protected slots configuration, and allowed clinic days.
 * Follows the dark theme pattern from admin scheduling page.
 */
import React, { useState, useCallback, useEffect } from 'react';
import {
  Save,
  AlertTriangle,
  Loader2,
  Clock,
  Calendar,
  Info,
  X,
  Plus,
  Trash2,
} from 'lucide-react';
import {
  useResidentWeeklyRequirement,
  useUpsertResidentWeeklyRequirement,
  useDeleteResidentWeeklyRequirement,
} from '@/hooks/useResidentWeeklyRequirements';
import type {
  WeeklyRequirementFormData,
  WeeklyRequirementFormErrors,
  DayOfWeek,
  TimeSlot,
  ProtectedSlotType,
  ProtectedSlots,
} from '@/types/resident-weekly-requirement';
import {
  DAY_OF_WEEK_LABELS,
  TIME_SLOT_LABELS,
  PROTECTED_SLOT_TYPE_CONFIG,
  PROTECTED_SLOT_TYPES,
  TIME_SLOTS,
  DEFAULT_WEEKLY_REQUIREMENT,
  validateWeeklyRequirement,
  hasValidationErrors,
} from '@/types/resident-weekly-requirement';

// ============================================================================
// Types
// ============================================================================

export interface WeeklyRequirementsEditorProps {
  /** Template ID to edit requirements for */
  templateId: string;
  /** Template name for display */
  templateName: string;
  /** Whether to show loading state */
  isLoading?: boolean;
  /** Callback when save completes */
  onSave?: () => void;
  /** Callback to close editor */
  onClose?: () => void;
}

// ============================================================================
// Subcomponents
// ============================================================================

interface MinMaxInputProps {
  label: string;
  minValue: number;
  maxValue: number;
  onMinChange: (value: number) => void;
  onMaxChange: (value: number) => void;
  error?: string;
  min?: number;
  max?: number;
}

function MinMaxInput({
  label,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  error,
  min = 0,
  max = 14,
}: MinMaxInputProps) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <label className="block text-xs text-slate-500 mb-1">Min</label>
          <input
            type="number"
            value={minValue}
            onChange={(e) => onMinChange(parseInt(e.target.value) || 0)}
            min={min}
            max={max}
            className={`
              w-full px-3 py-2 bg-slate-700 border rounded-lg text-white
              focus:outline-none focus:ring-2 focus:ring-violet-500
              ${error ? 'border-red-500' : 'border-slate-600'}
            `}
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs text-slate-500 mb-1">Max</label>
          <input
            type="number"
            value={maxValue}
            onChange={(e) => onMaxChange(parseInt(e.target.value) || 0)}
            min={min}
            max={max}
            className={`
              w-full px-3 py-2 bg-slate-700 border rounded-lg text-white
              focus:outline-none focus:ring-2 focus:ring-violet-500
              ${error ? 'border-red-500' : 'border-slate-600'}
            `}
          />
        </div>
      </div>
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}

interface DayCheckboxGroupProps {
  label: string;
  selectedDays: DayOfWeek[];
  onChange: (days: DayOfWeek[]) => void;
}

function DayCheckboxGroup({ label, selectedDays, onChange }: DayCheckboxGroupProps) {
  const allDays: DayOfWeek[] = [0, 1, 2, 3, 4, 5, 6];

  const handleToggle = useCallback(
    (day: DayOfWeek) => {
      if (selectedDays.includes(day)) {
        onChange(selectedDays.filter((d) => d !== day));
      } else {
        onChange([...selectedDays, day].sort((a, b) => a - b));
      }
    },
    [selectedDays, onChange]
  );

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      <div className="flex flex-wrap gap-2">
        {allDays.map((day) => {
          const isSelected = selectedDays.includes(day);
          return (
            <button
              key={day}
              type="button"
              onClick={() => handleToggle(day)}
              className={`
                px-3 py-2 rounded-lg text-sm font-medium transition-colors
                ${
                  isSelected
                    ? 'bg-violet-500 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }
              `}
            >
              {DAY_OF_WEEK_LABELS[day]}
            </button>
          );
        })}
      </div>
    </div>
  );
}

interface ProtectedSlotsEditorProps {
  slots: ProtectedSlots;
  onChange: (slots: ProtectedSlots) => void;
}

function ProtectedSlotsEditor({ slots, onChange }: ProtectedSlotsEditorProps) {
  const [showAddSlot, setShowAddSlot] = useState(false);
  const [newSlot, setNewSlot] = useState<TimeSlot | ''>('');
  const [newSlotType, setNewSlotType] = useState<ProtectedSlotType>('conference');

  const usedSlots = Object.keys(slots) as TimeSlot[];
  const availableSlots = TIME_SLOTS.filter((slot) => !usedSlots.includes(slot));

  const handleAddSlot = useCallback(() => {
    if (newSlot) {
      onChange({ ...slots, [newSlot]: newSlotType });
      setNewSlot('');
      setShowAddSlot(false);
    }
  }, [newSlot, newSlotType, slots, onChange]);

  const handleRemoveSlot = useCallback(
    (slot: TimeSlot) => {
      const newSlots = { ...slots };
      delete newSlots[slot];
      onChange(newSlots);
    },
    [slots, onChange]
  );

  const handleChangeSlotType = useCallback(
    (slot: TimeSlot, type: ProtectedSlotType) => {
      onChange({ ...slots, [slot]: type });
    },
    [slots, onChange]
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-slate-300">
          Protected Time Slots
        </label>
        {availableSlots.length > 0 && (
          <button
            type="button"
            onClick={() => setShowAddSlot(!showAddSlot)}
            className="flex items-center gap-1 text-sm text-violet-400 hover:text-violet-300 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Slot
          </button>
        )}
      </div>

      {/* Add slot form */}
      {showAddSlot && (
        <div className="flex items-end gap-2 p-3 bg-slate-900/50 rounded-lg border border-slate-700">
          <div className="flex-1">
            <label className="block text-xs text-slate-500 mb-1">Time Slot</label>
            <select
              value={newSlot}
              onChange={(e) => setNewSlot(e.target.value as TimeSlot | '')}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
            >
              <option value="">Select slot...</option>
              {availableSlots.map((slot) => (
                <option key={slot} value={slot}>
                  {TIME_SLOT_LABELS[slot]}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs text-slate-500 mb-1">Activity</label>
            <select
              value={newSlotType}
              onChange={(e) => setNewSlotType(e.target.value as ProtectedSlotType)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
            >
              {PROTECTED_SLOT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {PROTECTED_SLOT_TYPE_CONFIG[type].label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={handleAddSlot}
            disabled={!newSlot}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Add
          </button>
          <button
            type="button"
            onClick={() => setShowAddSlot(false)}
            className="p-2 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Existing slots list */}
      {usedSlots.length === 0 ? (
        <div className="p-4 text-center bg-slate-800/30 border border-slate-700 border-dashed rounded-lg">
          <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">No protected slots configured</p>
        </div>
      ) : (
        <div className="space-y-2">
          {usedSlots.map((slot) => {
            const slotType = slots[slot]!;
            const typeConfig = PROTECTED_SLOT_TYPE_CONFIG[slotType];

            return (
              <div
                key={slot}
                className="flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <span className="text-white font-medium">
                    {TIME_SLOT_LABELS[slot]}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium ${typeConfig.bgColor} ${typeConfig.color}`}
                  >
                    {typeConfig.label}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={slotType}
                    onChange={(e) =>
                      handleChangeSlotType(slot, e.target.value as ProtectedSlotType)
                    }
                    className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-sm text-white"
                  >
                    {PROTECTED_SLOT_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {PROTECTED_SLOT_TYPE_CONFIG[type].label}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => handleRemoveSlot(slot)}
                    className="p-1 text-slate-400 hover:text-red-400 transition-colors"
                    title="Remove slot"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function WeeklyRequirementsEditor({
  templateId,
  templateName,
  isLoading: externalLoading = false,
  onSave,
  onClose,
}: WeeklyRequirementsEditorProps) {
  // Fetch existing requirement
  const { data: existingRequirement, isLoading: fetchLoading } =
    useResidentWeeklyRequirement(templateId);

  // Mutations
  const upsertMutation = useUpsertResidentWeeklyRequirement();
  const deleteMutation = useDeleteResidentWeeklyRequirement();

  // Form state
  const [formData, setFormData] = useState<WeeklyRequirementFormData>(
    DEFAULT_WEEKLY_REQUIREMENT
  );
  const [errors, setErrors] = useState<WeeklyRequirementFormErrors>({});
  const [hasChanges, setHasChanges] = useState(false);

  // Initialize form data when existing requirement loads
  useEffect(() => {
    if (existingRequirement) {
      setFormData({
        fmClinicMinPerWeek: existingRequirement.fmClinicMinPerWeek,
        fmClinicMaxPerWeek: existingRequirement.fmClinicMaxPerWeek,
        specialtyMinPerWeek: existingRequirement.specialtyMinPerWeek,
        specialtyMaxPerWeek: existingRequirement.specialtyMaxPerWeek,
        academicsRequired: existingRequirement.academicsRequired,
        protectedSlots: existingRequirement.protectedSlots || {},
        allowedClinicDays: existingRequirement.allowedClinicDays || [1, 2, 3, 4, 5],
      });
      setHasChanges(false);
    }
  }, [existingRequirement]);

  // Update handlers
  const updateField = useCallback(
    <K extends keyof WeeklyRequirementFormData>(
      field: K,
      value: WeeklyRequirementFormData[K]
    ) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setHasChanges(true);
      // Clear errors when user makes changes
      setErrors({});
    },
    []
  );

  // Validate on change
  useEffect(() => {
    if (hasChanges) {
      const validationErrors = validateWeeklyRequirement(formData);
      setErrors(validationErrors);
    }
  }, [formData, hasChanges]);

  // Save handler
  const handleSave = useCallback(async () => {
    const validationErrors = validateWeeklyRequirement(formData);
    if (hasValidationErrors(validationErrors)) {
      setErrors(validationErrors);
      return;
    }

    try {
      await upsertMutation.mutateAsync({
        templateId,
        existingId: existingRequirement?.id,
        data: {
          fmClinicMinPerWeek: formData.fmClinicMinPerWeek,
          fmClinicMaxPerWeek: formData.fmClinicMaxPerWeek,
          specialtyMinPerWeek: formData.specialtyMinPerWeek,
          specialtyMaxPerWeek: formData.specialtyMaxPerWeek,
          academicsRequired: formData.academicsRequired,
          protectedSlots: formData.protectedSlots,
          allowedClinicDays: formData.allowedClinicDays,
        },
      });
      setHasChanges(false);
      onSave?.();
    } catch {
      // Error handled by mutation
    }
  }, [formData, templateId, existingRequirement?.id, upsertMutation, onSave]);

  // Delete handler
  const handleDelete = useCallback(async () => {
    if (!existingRequirement?.id) return;

    if (
      confirm(
        'Are you sure you want to delete the weekly requirements for this template? This cannot be undone.'
      )
    ) {
      try {
        await deleteMutation.mutateAsync({
          id: existingRequirement.id,
          templateId,
        });
        // Reset to defaults
        setFormData(DEFAULT_WEEKLY_REQUIREMENT);
        setHasChanges(false);
      } catch {
        // Error handled by mutation
      }
    }
  }, [existingRequirement?.id, templateId, deleteMutation]);

  const isLoading = externalLoading || fetchLoading;
  const isSaving = upsertMutation.isPending;
  const isDeleting = deleteMutation.isPending;

  // Check if this is a new requirement (not yet saved)
  const isNew = !existingRequirement;

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
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Calendar className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">
              Weekly Requirements
            </h2>
            <p className="text-sm text-slate-400">{templateName}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {existingRequirement && (
            <button
              onClick={handleDelete}
              disabled={isDeleting || isSaving}
              className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              Delete
            </button>
          )}
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
            disabled={isSaving || !hasChanges || hasValidationErrors(errors)}
            className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {isNew ? 'Create Requirements' : 'Save Changes'}
          </button>
        </div>
      </div>

      {/* Info banner for new requirements */}
      {isNew && (
        <div className="flex items-start gap-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-300">
            <p className="font-medium mb-1">No Weekly Requirements Configured</p>
            <p className="text-blue-300/80">
              Configure weekly scheduling constraints for this rotation template.
              These settings control how many clinic and specialty sessions
              residents can have per week while on this rotation.
            </p>
          </div>
        </div>
      )}

      {/* Unsaved changes warning */}
      {hasChanges && (
        <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span className="text-sm text-amber-300">You have unsaved changes</span>
        </div>
      )}

      {/* Form sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* FM Clinic Half-Days */}
        <MinMaxInput
          label="FM Clinic Half-Days Per Week"
          minValue={formData.fmClinicMinPerWeek}
          maxValue={formData.fmClinicMaxPerWeek}
          onMinChange={(value) => updateField('fmClinicMinPerWeek', value)}
          onMaxChange={(value) => updateField('fmClinicMaxPerWeek', value)}
          error={errors.fm_clinic}
        />

        {/* Specialty Half-Days */}
        <MinMaxInput
          label="Specialty Half-Days Per Week"
          minValue={formData.specialtyMinPerWeek}
          maxValue={formData.specialtyMaxPerWeek}
          onMinChange={(value) => updateField('specialtyMinPerWeek', value)}
          onMaxChange={(value) => updateField('specialtyMaxPerWeek', value)}
          error={errors.specialty}
        />
      </div>

      {/* Academics Required Toggle */}
      <div className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
        <div>
          <label className="text-sm font-medium text-white">
            Wednesday AM Academics Required
          </label>
          <p className="text-xs text-slate-500 mt-1">
            Residents must attend Wednesday morning academic sessions
          </p>
        </div>
        <button
          type="button"
          onClick={() => updateField('academicsRequired', !formData.academicsRequired)}
          className={`
            relative inline-flex h-6 w-11 items-center rounded-full transition-colors
            ${formData.academicsRequired ? 'bg-violet-500' : 'bg-slate-600'}
          `}
        >
          <span
            className={`
              inline-block h-4 w-4 transform rounded-full bg-white transition-transform
              ${formData.academicsRequired ? 'translate-x-6' : 'translate-x-1'}
            `}
          />
        </button>
      </div>

      {/* Allowed Clinic Days */}
      <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
        <DayCheckboxGroup
          label="Allowed Clinic Days"
          selectedDays={formData.allowedClinicDays}
          onChange={(days) => updateField('allowedClinicDays', days)}
        />
        <p className="text-xs text-slate-500 mt-2">
          Days when clinic sessions can be scheduled for residents on this rotation
        </p>
      </div>

      {/* Protected Slots */}
      <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
        <ProtectedSlotsEditor
          slots={formData.protectedSlots}
          onChange={(slots) => updateField('protectedSlots', slots)}
        />
        <p className="text-xs text-slate-500 mt-2">
          Time slots that are protected for specific activities and cannot be
          scheduled for clinical duties
        </p>
      </div>

      {/* Error display */}
      {errors.general && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span className="text-sm text-red-300">{errors.general}</span>
        </div>
      )}

      {/* Mutation error display */}
      {(upsertMutation.error || deleteMutation.error) && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span className="text-sm text-red-300">
            {(upsertMutation.error || deleteMutation.error)?.message ||
              'An error occurred'}
          </span>
        </div>
      )}
    </div>
  );
}

export default WeeklyRequirementsEditor;
