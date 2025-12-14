'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from '@components/Modal';
import { Input, Select } from '@components/forms';
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

export function EditTemplateModal({ isOpen, onClose, template }: EditTemplateModalProps) {
  const [name, setName] = useState('');
  const [activityType, setActivityType] = useState('clinic');
  const [abbreviation, setAbbreviation] = useState('');
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
