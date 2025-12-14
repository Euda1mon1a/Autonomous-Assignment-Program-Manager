'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from './Modal';
import { Input, Select, TextArea, DatePicker } from './forms';
import { useCreateAbsence, usePeople } from '@/lib/hooks';
import type { AbsenceCreate } from '@/types/api';

interface AddAbsenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedPersonId?: string;
}

interface FormErrors {
  person_id?: string;
  start_date?: string;
  end_date?: string;
  absence_type?: string;
  general?: string;
}

const absenceTypeOptions = [
  { value: 'vacation', label: 'Vacation' },
  { value: 'deployment', label: 'Deployment' },
  { value: 'tdy', label: 'TDY' },
  { value: 'medical', label: 'Medical' },
  { value: 'family_emergency', label: 'Family Emergency' },
  { value: 'conference', label: 'Conference' },
];

type AbsenceType = 'vacation' | 'deployment' | 'tdy' | 'medical' | 'family_emergency' | 'conference';

export function AddAbsenceModal({ isOpen, onClose, preselectedPersonId }: AddAbsenceModalProps) {
  const [personId, setPersonId] = useState(preselectedPersonId || '');
  const [absenceType, setAbsenceType] = useState<AbsenceType>('vacation');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [deploymentOrders, setDeploymentOrders] = useState(false);
  const [tdyLocation, setTdyLocation] = useState('');
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});

  const { data: peopleData, isLoading: isPeopleLoading } = usePeople();
  const createAbsence = useCreateAbsence();

  // Update personId if preselected changes
  useEffect(() => {
    if (preselectedPersonId) {
      setPersonId(preselectedPersonId);
    }
  }, [preselectedPersonId]);

  const personOptions = peopleData?.items?.map((p) => ({
    value: p.id,
    label: `${p.name} (${p.type === 'resident' ? `PGY-${p.pgy_level}` : 'Faculty'})`,
  })) || [];

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!personId) {
      newErrors.person_id = 'Please select a person';
    }

    if (!startDate) {
      newErrors.start_date = 'Start date is required';
    }

    if (!endDate) {
      newErrors.end_date = 'End date is required';
    }

    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      newErrors.end_date = 'End date must be after start date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const absenceData: AbsenceCreate = {
      person_id: personId,
      absence_type: absenceType,
      start_date: startDate,
      end_date: endDate,
      ...(absenceType === 'deployment' && { deployment_orders: deploymentOrders }),
      ...(absenceType === 'tdy' && tdyLocation && { tdy_location: tdyLocation }),
      ...(notes && { notes }),
    };

    try {
      await createAbsence.mutateAsync(absenceData);
      handleClose();
    } catch (err) {
      setErrors({ general: 'Failed to create absence. Please try again.' });
    }
  };

  const handleClose = () => {
    setPersonId(preselectedPersonId || '');
    setAbsenceType('vacation');
    setStartDate('');
    setEndDate('');
    setDeploymentOrders(false);
    setTdyLocation('');
    setNotes('');
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Absence">
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.general && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {errors.general}
          </div>
        )}

        <Select
          label="Person"
          value={personId}
          onChange={(e) => setPersonId(e.target.value)}
          options={[{ value: '', label: isPeopleLoading ? 'Loading...' : 'Select a person' }, ...personOptions]}
          error={errors.person_id}
          disabled={isPeopleLoading || !!preselectedPersonId}
        />

        <Select
          label="Absence Type"
          value={absenceType}
          onChange={(e) => setAbsenceType(e.target.value as AbsenceType)}
          options={absenceTypeOptions}
          error={errors.absence_type}
        />

        <div className="grid grid-cols-2 gap-4">
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={setStartDate}
            error={errors.start_date}
          />
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={setEndDate}
            error={errors.end_date}
          />
        </div>

        {absenceType === 'deployment' && (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="deploymentOrders"
              checked={deploymentOrders}
              onChange={(e) => setDeploymentOrders(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="deploymentOrders" className="text-sm text-gray-700">
              Has deployment orders
            </label>
          </div>
        )}

        {absenceType === 'tdy' && (
          <Input
            label="TDY Location"
            value={tdyLocation}
            onChange={(e) => setTdyLocation(e.target.value)}
            placeholder="Enter TDY location"
          />
        )}

        <TextArea
          label="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional notes about this absence..."
          rows={3}
        />

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
            disabled={createAbsence.isPending}
            className="btn-primary disabled:opacity-50"
          >
            {createAbsence.isPending ? 'Creating...' : 'Add Absence'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
