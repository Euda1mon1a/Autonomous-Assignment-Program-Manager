'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from '@/components/Modal';
import { Input, Select } from '@/components/forms';
import { useUpdateTemplate } from '@/lib/hooks';
import type { RotationTemplate, RotationTemplateUpdate } from '@/types/api';

interface EditTemplateModalProps {
  isOpen: boolean;
  onClose: () => void;
  template: RotationTemplate | null;
}

interface FormErrors {
  name?: string;
  activity_type?: string;
  max_supervision_ratio?: string;
  general?: string;
}

const activityTypeOptions = [
  { value: 'clinic', label: 'Clinic' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'conference', label: 'Conference' },
  { value: 'elective', label: 'Elective' },
  { value: 'call', label: 'Call' },
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
  { value: 'green-500', label: 'Green (Outpatient)' },
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

// Map Tailwind color names to hex for preview
const tailwindToHex: Record<string, string> = {
  'black': '#000000',
  'white': '#ffffff',
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

export function EditTemplateModal({ isOpen, onClose, template }: EditTemplateModalProps) {
  const [name, setName] = useState('');
  const [activityType, setActivityType] = useState('clinic');
  const [abbreviation, setAbbreviation] = useState('');
  const [fontColor, setFontColor] = useState('');
  const [backgroundColor, setBackgroundColor] = useState('');
  const [clinicLocation, setClinicLocation] = useState('');
  const [maxResidents, setMaxResidents] = useState('');
  const [requiresSpecialty, setRequiresSpecialty] = useState('');
  const [requiresProcedureCredential, setRequiresProcedureCredential] = useState(false);
  const [supervisionRequired, setSupervisionRequired] = useState(true);
  const [maxSupervisionRatio, setMaxSupervisionRatio] = useState('4');
  const [errors, setErrors] = useState<FormErrors>({});

  const updateTemplate = useUpdateTemplate();

  // Pre-populate form when template changes
  useEffect(() => {
    if (template) {
      setName(template.name);
      setActivityType(template.activity_type);
      setAbbreviation(template.abbreviation || '');
      setFontColor(template.font_color || '');
      setBackgroundColor(template.background_color || '');
      setClinicLocation(template.clinic_location || '');
      setMaxResidents(template.max_residents?.toString() || '');
      setRequiresSpecialty(template.requires_specialty || '');
      setRequiresProcedureCredential(template.requires_procedure_credential);
      setSupervisionRequired(template.supervision_required);
      setMaxSupervisionRatio(template.max_supervision_ratio.toString());
    }
  }, [template]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!activityType) {
      newErrors.activity_type = 'Activity type is required';
    }

    const ratio = parseInt(maxSupervisionRatio);
    if (isNaN(ratio) || ratio < 1 || ratio > 10) {
      newErrors.max_supervision_ratio = 'Supervision ratio must be between 1 and 10';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm() || !template) {
      return;
    }

    const templateData: RotationTemplateUpdate = {
      name: name.trim(),
      activity_type: activityType,
      abbreviation: abbreviation.trim() || undefined,
      font_color: fontColor || undefined,
      background_color: backgroundColor || undefined,
      clinic_location: clinicLocation.trim() || undefined,
      max_residents: maxResidents ? parseInt(maxResidents) : undefined,
      requires_specialty: requiresSpecialty.trim() || undefined,
      requires_procedure_credential: requiresProcedureCredential,
      supervision_required: supervisionRequired,
      max_supervision_ratio: parseInt(maxSupervisionRatio),
    };

    try {
      await updateTemplate.mutateAsync({ id: template.id, data: templateData });
      handleClose();
    } catch (err) {
      setErrors({ general: 'Failed to update template. Please try again.' });
    }
  };

  const handleClose = () => {
    setErrors({});
    onClose();
  };

  if (!template) return null;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Edit Rotation Template">
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
          placeholder="e.g., Inpatient Medicine"
          required
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="Activity Type"
            value={activityType}
            onChange={(e) => setActivityType(e.target.value)}
            options={activityTypeOptions}
            error={errors.activity_type}
          />

          <Input
            label="Abbreviation"
            value={abbreviation}
            onChange={(e) => setAbbreviation(e.target.value)}
            placeholder="e.g., IM"
          />
        </div>

        {/* Color Selectors with Preview */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">Color Theme</label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Font Color</label>
              <div className="flex gap-2">
                <select
                  value={fontColor}
                  onChange={(e) => setFontColor(e.target.value)}
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                >
                  {fontColorOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {fontColor && (
                  <div
                    className="w-8 h-8 rounded border border-gray-300"
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
                  className="flex-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
                >
                  {backgroundColorOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {backgroundColor && (
                  <div
                    className="w-8 h-8 rounded border border-gray-300"
                    style={{ backgroundColor: tailwindToHex[backgroundColor] || backgroundColor }}
                  />
                )}
              </div>
            </div>
          </div>
          {/* Live Preview */}
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
                {abbreviation || 'ABC'}
              </div>
            </div>
          )}
        </div>

        <Input
          label="Clinic Location"
          value={clinicLocation}
          onChange={(e) => setClinicLocation(e.target.value)}
          placeholder="e.g., Building A, Room 201"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Max Residents"
            type="number"
            value={maxResidents}
            onChange={(e) => setMaxResidents(e.target.value)}
            placeholder="e.g., 4"
            min="1"
          />

          <Input
            label="Supervision Ratio (1:N)"
            type="number"
            value={maxSupervisionRatio}
            onChange={(e) => setMaxSupervisionRatio(e.target.value)}
            error={errors.max_supervision_ratio}
            min="1"
            max="10"
          />
        </div>

        <Input
          label="Requires Specialty"
          value={requiresSpecialty}
          onChange={(e) => setRequiresSpecialty(e.target.value)}
          placeholder="e.g., Cardiology (leave blank if none)"
        />

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="editSupervisionRequired"
              checked={supervisionRequired}
              onChange={(e) => setSupervisionRequired(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="editSupervisionRequired" className="text-sm text-gray-700">
              Supervision required
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="editRequiresProcedureCredential"
              checked={requiresProcedureCredential}
              onChange={(e) => setRequiresProcedureCredential(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="editRequiresProcedureCredential" className="text-sm text-gray-700">
              Requires procedure credential
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="btn-secondary"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={updateTemplate.isPending}
            className="btn-primary disabled:opacity-50"
          >
            {updateTemplate.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
