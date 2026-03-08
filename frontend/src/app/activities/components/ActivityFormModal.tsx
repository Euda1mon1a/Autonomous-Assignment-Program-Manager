'use client';

import { useState, useEffect, FormEvent } from 'react';
import { Modal } from '@/components/Modal';
import { Input, Select } from '@/components/forms';
import type {
  Activity,
  ActivityCategory,
  ActivityCreateRequest,
  ActivityUpdateRequest,
} from '@/types/activity';
import { ACTIVITY_CATEGORIES, ACTIVITY_CATEGORY_LABELS } from '@/types/activity';

interface ActivityFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: ActivityCreateRequest | ActivityUpdateRequest) => Promise<void>;
  activity: Activity | null; // null = creating new
  isSaving: boolean;
}

const categoryOptions = [
  { value: '', label: '-- Select Category --' },
  ...ACTIVITY_CATEGORIES.map((cat) => ({
    value: cat,
    label: ACTIVITY_CATEGORY_LABELS[cat],
  })),
];

const fontColorOptions = [
  { value: '', label: 'Default' },
  { value: 'black', label: 'Black' },
  { value: 'white', label: 'White' },
  { value: 'gray-200', label: 'Light Gray' },
  { value: 'gray-600', label: 'Medium Gray' },
  { value: 'gray-800', label: 'Dark Gray' },
];

const backgroundColorOptions = [
  { value: '', label: 'Default' },
  { value: 'green-500', label: 'Green (Clinical)' },
  { value: 'yellow-300', label: 'Yellow (Procedures)' },
  { value: 'sky-500', label: 'Sky Blue (Inpatient)' },
  { value: 'black', label: 'Black (Night Float)' },
  { value: 'purple-700', label: 'Purple (Education)' },
  { value: 'gray-100', label: 'Light Gray' },
  { value: 'gray-200', label: 'Gray (Off)' },
  { value: 'red-300', label: 'Red (Leave)' },
  { value: 'blue-300', label: 'Blue (Weekend)' },
  { value: 'amber-200', label: 'Amber (Post Call)' },
  { value: 'orange-400', label: 'Orange (Off-site)' },
  { value: 'teal-300', label: 'Teal (Supervision)' },
];

const tailwindToHex: Record<string, string> = {
  black: '#000000',
  white: '#ffffff',
  'gray-100': '#f3f4f6',
  'gray-200': '#e5e7eb',
  'gray-600': '#4b5563',
  'gray-800': '#1f2937',
  'green-500': '#22c55e',
  'yellow-300': '#fde047',
  'sky-500': '#0ea5e9',
  'purple-700': '#7e22ce',
  'red-300': '#fca5a5',
  'blue-300': '#93c5fd',
  'amber-200': '#fde68a',
  'orange-400': '#fb923c',
  'teal-300': '#5eead4',
};

interface FormErrors {
  name?: string;
  code?: string;
  activityCategory?: string;
  general?: string;
}

export function ActivityFormModal({
  isOpen,
  onClose,
  onSave,
  activity,
  isSaving,
}: ActivityFormModalProps) {
  const isEditing = !!activity;

  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [displayAbbreviation, setDisplayAbbreviation] = useState('');
  const [activityCategory, setActivityCategory] = useState<ActivityCategory | ''>('');
  const [fontColor, setFontColor] = useState('');
  const [backgroundColor, setBackgroundColor] = useState('');
  const [requiresSupervision, setRequiresSupervision] = useState(true);
  const [isProtected, setIsProtected] = useState(false);
  const [countsTowardClinicalHours, setClinicalHours] = useState(true);
  const [displayOrder, setDisplayOrder] = useState('0');
  const [errors, setErrors] = useState<FormErrors>({});

  // Populate form when activity changes
  useEffect(() => {
    if (isOpen) {
      if (activity) {
        setName(activity.name);
        setCode(activity.code);
        setDisplayAbbreviation(activity.displayAbbreviation || '');
        setActivityCategory(activity.activityCategory);
        setFontColor(activity.fontColor || '');
        setBackgroundColor(activity.backgroundColor || '');
        setRequiresSupervision(activity.requiresSupervision);
        setIsProtected(activity.isProtected);
        setClinicalHours(activity.countsTowardClinicalHours);
        setDisplayOrder(String(activity.displayOrder));
      } else {
        setName('');
        setCode('');
        setDisplayAbbreviation('');
        setActivityCategory('');
        setFontColor('');
        setBackgroundColor('');
        setRequiresSupervision(true);
        setIsProtected(false);
        setClinicalHours(true);
        setDisplayOrder('0');
      }
      setErrors({});
    }
  }, [isOpen, activity]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!name.trim()) newErrors.name = 'Name is required';
    if (!code.trim()) newErrors.code = 'Code is required';
    if (!activityCategory) newErrors.activityCategory = 'Category is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    const formData = {
      name: name.trim(),
      code: code.trim().toLowerCase(),
      displayAbbreviation: displayAbbreviation.trim() || (isEditing ? null : undefined),
      activityCategory: activityCategory as ActivityCategory,
      fontColor: fontColor || (isEditing ? null : undefined),
      backgroundColor: backgroundColor || (isEditing ? null : undefined),
      requiresSupervision,
      isProtected,
      countsTowardClinicalHours,
      displayOrder: parseInt(displayOrder) || 0,
    };

    try {
      await onSave(formData);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const message = (typeof detail === 'string' ? detail : null)
        || err?.message
        || `Failed to ${isEditing ? 'update' : 'create'} activity.`;
      setErrors({ general: message });
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? 'Edit Activity' : 'Create Activity'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.general && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {errors.general}
          </div>
        )}

        <Input
          label="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
          placeholder="e.g., FM Clinic"
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            error={errors.code}
            placeholder="e.g., fm_clinic"
            required
          />
          <Input
            label="Abbreviation"
            value={displayAbbreviation}
            onChange={(e) => setDisplayAbbreviation(e.target.value)}
            placeholder="e.g., C"
          />
        </div>

        <Select
          label="Category"
          value={activityCategory}
          onChange={(e) => setActivityCategory(e.target.value as ActivityCategory | '')}
          options={categoryOptions}
          error={errors.activityCategory}
        />

        {/* Color selectors with preview */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Color Theme</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Font Color</label>
              <div className="flex gap-2">
                <select
                  value={fontColor}
                  onChange={(e) => setFontColor(e.target.value)}
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 text-sm"
                >
                  {fontColorOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {fontColor && (
                  <div
                    className="w-8 h-8 rounded border border-gray-300 flex-shrink-0"
                    style={{ backgroundColor: tailwindToHex[fontColor] || fontColor }}
                  />
                )}
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Background Color</label>
              <div className="flex gap-2">
                <select
                  value={backgroundColor}
                  onChange={(e) => setBackgroundColor(e.target.value)}
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 text-sm"
                >
                  {backgroundColorOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {backgroundColor && (
                  <div
                    className="w-8 h-8 rounded border border-gray-300 flex-shrink-0"
                    style={{ backgroundColor: tailwindToHex[backgroundColor] || backgroundColor }}
                  />
                )}
              </div>
            </div>
          </div>
          {(fontColor || backgroundColor) && (
            <div className="mt-2">
              <label className="block text-xs text-gray-500 mb-1">Preview</label>
              <div
                className="inline-block px-3 py-1 rounded text-sm font-medium"
                style={{
                  color: tailwindToHex[fontColor] || fontColor || '#000000',
                  backgroundColor: tailwindToHex[backgroundColor] || backgroundColor || '#e5e7eb',
                }}
              >
                {displayAbbreviation || code.toUpperCase().slice(0, 3) || 'ABC'}
              </div>
            </div>
          )}
        </div>

        <Input
          label="Display Order"
          type="number"
          value={displayOrder}
          onChange={(e) => setDisplayOrder(e.target.value)}
          min="0"
        />

        {/* Flags */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="requiresSupervision"
              checked={requiresSupervision}
              onChange={(e) => setRequiresSupervision(e.target.checked)}
              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="requiresSupervision" className="text-sm text-gray-700">
              Requires supervision (ACGME)
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isProtected"
              checked={isProtected}
              onChange={(e) => setIsProtected(e.target.checked)}
              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="isProtected" className="text-sm text-gray-700">
              Protected (solver cannot modify)
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="clinicalHours"
              checked={countsTowardClinicalHours}
              onChange={(e) => setClinicalHours(e.target.checked)}
              className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
            />
            <label htmlFor="clinicalHours" className="text-sm text-gray-700">
              Counts toward clinical hours
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="btn-primary disabled:opacity-50"
          >
            {isSaving ? (isEditing ? 'Saving...' : 'Creating...') : isEditing ? 'Save Changes' : 'Create Activity'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
