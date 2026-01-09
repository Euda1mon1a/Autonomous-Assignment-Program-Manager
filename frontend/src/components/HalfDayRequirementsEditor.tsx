'use client';

/**
 * HalfDayRequirementsEditor - Form for editing rotation half-day requirements.
 *
 * Features:
 * - Number inputs for FM clinic, specialty, academics, elective half-days
 * - Specialty name text input
 * - Total bar visualization (target: 10 half-days)
 * - Balance indicator (green when total = 10)
 * - Save/Cancel buttons
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import type {
  HalfDayRequirement,
  HalfDayRequirementCreate,
} from '@/types/admin-templates';

// ============================================================================
// Types
// ============================================================================

interface HalfDayRequirementsEditorProps {
  /** Current requirements data (null if not configured) */
  requirements: HalfDayRequirement | null;
  /** Whether the editor is in loading state */
  isLoading?: boolean;
  /** Whether changes are being saved */
  isSaving?: boolean;
  /** Callback when save is requested */
  onSave: (data: HalfDayRequirementCreate) => void;
  /** Callback when changes should be discarded */
  onCancel?: () => void;
  /** Read-only mode */
  readOnly?: boolean;
}

// ============================================================================
// Default Values
// ============================================================================

const DEFAULT_VALUES: HalfDayRequirementCreate = {
  fm_clinic_halfdays: 4,
  specialty_halfdays: 5,
  specialty_name: null,
  academics_halfdays: 1,
  elective_halfdays: 0,
  min_consecutive_specialty: 1,
  prefer_combined_clinic_days: true,
};

const TARGET_TOTAL = 10;

// ============================================================================
// Component
// ============================================================================

export function HalfDayRequirementsEditor({
  requirements,
  isLoading = false,
  isSaving = false,
  onSave,
  onCancel,
  readOnly = false,
}: HalfDayRequirementsEditorProps) {
  // Initialize form state from requirements or defaults
  const [formData, setFormData] = useState<HalfDayRequirementCreate>(() => ({
    fm_clinic_halfdays: requirements?.fm_clinic_halfdays ?? DEFAULT_VALUES.fm_clinic_halfdays,
    specialty_halfdays: requirements?.specialty_halfdays ?? DEFAULT_VALUES.specialty_halfdays,
    specialty_name: requirements?.specialty_name ?? DEFAULT_VALUES.specialty_name,
    academics_halfdays: requirements?.academics_halfdays ?? DEFAULT_VALUES.academics_halfdays,
    elective_halfdays: requirements?.elective_halfdays ?? DEFAULT_VALUES.elective_halfdays,
    min_consecutive_specialty: requirements?.min_consecutive_specialty ?? DEFAULT_VALUES.min_consecutive_specialty,
    prefer_combined_clinic_days: requirements?.prefer_combined_clinic_days ?? DEFAULT_VALUES.prefer_combined_clinic_days,
  }));

  // Update form when requirements change
  useEffect(() => {
    if (requirements) {
      setFormData({
        fm_clinic_halfdays: requirements.fm_clinic_halfdays,
        specialty_halfdays: requirements.specialty_halfdays,
        specialty_name: requirements.specialty_name,
        academics_halfdays: requirements.academics_halfdays,
        elective_halfdays: requirements.elective_halfdays,
        min_consecutive_specialty: requirements.min_consecutive_specialty,
        prefer_combined_clinic_days: requirements.prefer_combined_clinic_days,
      });
    }
  }, [requirements]);

  // Calculate total half-days
  const total = useMemo(() => {
    return (
      (formData.fm_clinic_halfdays ?? 0) +
      (formData.specialty_halfdays ?? 0) +
      (formData.academics_halfdays ?? 0) +
      (formData.elective_halfdays ?? 0)
    );
  }, [formData]);

  const isBalanced = total === TARGET_TOTAL;

  // Handlers
  const handleNumberChange = useCallback(
    (field: keyof HalfDayRequirementCreate) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value, 10);
        if (!isNaN(value) && value >= 0 && value <= 14) {
          setFormData((prev) => ({ ...prev, [field]: value }));
        }
      },
    []
  );

  const handleTextChange = useCallback(
    (field: keyof HalfDayRequirementCreate) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((prev) => ({ ...prev, [field]: e.target.value || null }));
      },
    []
  );

  const handleCheckboxChange = useCallback(
    (field: keyof HalfDayRequirementCreate) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData((prev) => ({ ...prev, [field]: e.target.checked }));
      },
    []
  );

  const handleSave = useCallback(() => {
    onSave(formData);
  }, [formData, onSave]);

  const handleReset = useCallback(() => {
    if (requirements) {
      setFormData({
        fm_clinic_halfdays: requirements.fm_clinic_halfdays,
        specialty_halfdays: requirements.specialty_halfdays,
        specialty_name: requirements.specialty_name,
        academics_halfdays: requirements.academics_halfdays,
        elective_halfdays: requirements.elective_halfdays,
        min_consecutive_specialty: requirements.min_consecutive_specialty,
        prefer_combined_clinic_days: requirements.prefer_combined_clinic_days,
      });
    } else {
      setFormData(DEFAULT_VALUES);
    }
    onCancel?.();
  }, [requirements, onCancel]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Total Bar */}
      <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Total Half-Days per Block
          </span>
          <span
            className={`text-lg font-bold ${
              isBalanced
                ? 'text-emerald-600 dark:text-emerald-400'
                : 'text-amber-600 dark:text-amber-400'
            }`}
          >
            {total} / {TARGET_TOTAL}
          </span>
        </div>
        <div className="w-full h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isBalanced
                ? 'bg-emerald-500'
                : total > TARGET_TOTAL
                ? 'bg-red-500'
                : 'bg-amber-500'
            }`}
            style={{ width: `${Math.min((total / TARGET_TOTAL) * 100, 100)}%` }}
          />
        </div>
        <div className="flex items-center gap-2 mt-2">
          {isBalanced ? (
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          ) : (
            <AlertCircle className="h-4 w-4 text-amber-500" />
          )}
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {isBalanced
              ? 'Balanced - matches standard block'
              : total > TARGET_TOTAL
              ? `${total - TARGET_TOTAL} half-days over standard`
              : `${TARGET_TOTAL - total} half-days under standard`}
          </span>
        </div>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* FM Clinic */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            FM Clinic Half-Days
          </label>
          <input
            type="number"
            min={0}
            max={14}
            value={formData.fm_clinic_halfdays ?? 0}
            onChange={handleNumberChange('fm_clinic_halfdays')}
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-slate-500">
            Family Medicine clinic sessions per block
          </p>
        </div>

        {/* Specialty */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Specialty Half-Days
          </label>
          <input
            type="number"
            min={0}
            max={14}
            value={formData.specialty_halfdays ?? 0}
            onChange={handleNumberChange('specialty_halfdays')}
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Specialty Name */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Specialty Name
          </label>
          <input
            type="text"
            value={formData.specialty_name ?? ''}
            onChange={handleTextChange('specialty_name')}
            placeholder="e.g., Neurology, Dermatology"
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Academics */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Academic Half-Days
          </label>
          <input
            type="number"
            min={0}
            max={14}
            value={formData.academics_halfdays ?? 0}
            onChange={handleNumberChange('academics_halfdays')}
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-slate-500">
            Protected lecture/education time (usually 1)
          </p>
        </div>

        {/* Elective */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Elective Half-Days
          </label>
          <input
            type="number"
            min={0}
            max={14}
            value={formData.elective_halfdays ?? 0}
            onChange={handleNumberChange('elective_halfdays')}
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-slate-500">
            Buffer/flexible time (optional)
          </p>
        </div>

        {/* Min Consecutive Specialty */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Min Consecutive Specialty Days
          </label>
          <input
            type="number"
            min={1}
            max={5}
            value={formData.min_consecutive_specialty ?? 1}
            onChange={handleNumberChange('min_consecutive_specialty')}
            disabled={readOnly || isSaving}
            className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-md
              bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100
              focus:ring-2 focus:ring-blue-500 focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-slate-500">
            Batch specialty days together
          </p>
        </div>
      </div>

      {/* Checkboxes */}
      <div className="space-y-3">
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.prefer_combined_clinic_days ?? true}
            onChange={handleCheckboxChange('prefer_combined_clinic_days')}
            disabled={readOnly || isSaving}
            className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-slate-700 dark:text-slate-300">
            Prefer combined clinic days (FM + specialty same day)
          </span>
        </label>
      </div>

      {/* Actions */}
      {!readOnly && (
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
          <button
            type="button"
            onClick={handleReset}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300
              bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-md
              hover:bg-slate-50 dark:hover:bg-slate-700
              disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="px-4 py-2 text-sm font-medium text-white
              bg-blue-600 rounded-md hover:bg-blue-700
              disabled:opacity-50 disabled:cursor-not-allowed
              flex items-center gap-2"
          >
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            Save Requirements
          </button>
        </div>
      )}
    </div>
  );
}

export default HalfDayRequirementsEditor;
