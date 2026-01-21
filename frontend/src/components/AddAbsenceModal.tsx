'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from './Modal';
import { Input, Select, TextArea, DatePicker } from './forms';
import { useCreateAbsence, usePeople } from '@/lib/hooks';
import { validateRequired, validateDateRange } from '@/lib/validation';
import { AbsenceType, type AbsenceCreate } from '@/types/api';

interface AddAbsenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedPersonId?: string;
  /** Pre-fill start date (YYYY-MM-DD format) */
  preselectedStartDate?: string;
  /** Pre-fill end date (YYYY-MM-DD format) */
  preselectedEndDate?: string;
}

interface FormErrors {
  personId?: string;
  startDate?: string;
  endDate?: string;
  absenceType?: string;
  general?: string;
}

const absenceTypeOptions = [
  // Planned leave
  { value: 'vacation', label: 'Vacation' },
  { value: 'conference', label: 'Conference' },
  // Medical
  { value: 'sick', label: 'Sick' },
  { value: 'medical', label: 'Medical Leave' },
  { value: 'convalescent', label: 'Convalescent' },
  { value: 'maternity_paternity', label: 'Parental Leave' },
  // Emergency (blocking - Hawaii reality: 7+ days travel)
  { value: 'family_emergency', label: 'Family Emergency' },
  { value: 'emergency_leave', label: 'Emergency Leave' },
  { value: 'bereavement', label: 'Bereavement' },
  // Military
  { value: 'deployment', label: 'Deployment' },
  { value: 'tdy', label: 'TDY' },
  { value: 'training', label: 'Training' },
  { value: 'military_duty', label: 'Military Duty' },
];

export function AddAbsenceModal({
  isOpen,
  onClose,
  preselectedPersonId,
  preselectedStartDate,
  preselectedEndDate,
}: AddAbsenceModalProps) {
  const [personId, setPersonId] = useState(preselectedPersonId || '');
  const [absenceType, setAbsenceType] = useState<AbsenceType>(AbsenceType.VACATION);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [deploymentOrders, setDeploymentOrders] = useState(false);
  const [tdyLocation, setTdyLocation] = useState('');
  const [notes, setNotes] = useState('');
  const [isAwayFromProgram, setIsAwayFromProgram] = useState(true);
  const [errors, setErrors] = useState<FormErrors>({});

  const { data: peopleData, isLoading: isPeopleLoading } = usePeople();
  const createAbsence = useCreateAbsence();

  // Update personId if preselected changes
  useEffect(() => {
    if (preselectedPersonId) {
      setPersonId(preselectedPersonId);
    }
  }, [preselectedPersonId]);

  // Update dates if preselected changes
  useEffect(() => {
    if (preselectedStartDate) {
      setStartDate(preselectedStartDate);
    }
    if (preselectedEndDate) {
      setEndDate(preselectedEndDate);
    }
  }, [preselectedStartDate, preselectedEndDate]);

  const personOptions = peopleData?.items?.map((p) => ({
    value: p.id,
    label: `${p.name} (${p.type === 'resident' ? `PGY-${p.pgyLevel}` : 'Faculty'})`,
  })) || [];

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validate person is selected
    const personError = validateRequired(personId, 'Person');
    if (personError) {
      newErrors.personId = 'Please select a person';
    }

    // Validate start date is selected
    const startDateError = validateRequired(startDate, 'Start date');
    if (startDateError) {
      newErrors.startDate = startDateError;
    }

    // Validate end date is selected
    const endDateError = validateRequired(endDate, 'End date');
    if (endDateError) {
      newErrors.endDate = endDateError;
    }

    // Validate date range (end date >= start date)
    if (startDate && endDate) {
      const dateRangeError = validateDateRange(startDate, endDate);
      if (dateRangeError) {
        newErrors.endDate = dateRangeError;
      }
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
      personId: personId,
      absenceType: absenceType,
      startDate: startDate,
      endDate: endDate,
      isAwayFromProgram: isAwayFromProgram,
      ...(absenceType === AbsenceType.DEPLOYMENT && { deploymentOrders: deploymentOrders }),
      ...(absenceType === AbsenceType.TDY && tdyLocation && { tdyLocation: tdyLocation }),
      ...(notes && { notes }),
    };

    try {
      await createAbsence.mutateAsync(absenceData);
      handleClose();
    } catch (_err) {
      setErrors({ general: 'Failed to create absence. Please try again.' });
    }
  };

  const handleClose = () => {
    setPersonId(preselectedPersonId || '');
    setAbsenceType(AbsenceType.VACATION);
    setStartDate(preselectedStartDate || '');
    setEndDate(preselectedEndDate || '');
    setDeploymentOrders(false);
    setTdyLocation('');
    setNotes('');
    setIsAwayFromProgram(true);
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
          error={errors.personId}
          disabled={isPeopleLoading || !!preselectedPersonId}
        />

        <Select
          label="Absence Type"
          value={absenceType}
          onChange={(e) => setAbsenceType(e.target.value as AbsenceType)}
          options={absenceTypeOptions}
          error={errors.absenceType}
        />

        <div className="grid grid-cols-2 gap-4">
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={setStartDate}
            error={errors.startDate}
          />
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={setEndDate}
            error={errors.endDate}
          />
        </div>

        {absenceType === AbsenceType.DEPLOYMENT && (
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

        {absenceType === AbsenceType.TDY && (
          <Input
            label="TDY Location"
            value={tdyLocation}
            onChange={(e) => setTdyLocation(e.target.value)}
            placeholder="Enter TDY location"
          />
        )}

        <div className="flex items-center gap-2 pt-2">
          <input
            type="checkbox"
            id="isAwayFromProgram"
            checked={isAwayFromProgram}
            onChange={(e) => setIsAwayFromProgram(e.target.checked)}
            className="rounded border-gray-300 text-violet-600 focus:ring-violet-500"
          />
          <label htmlFor="isAwayFromProgram" className="text-sm text-gray-700">
            Counts toward away-from-program (28 days/year for residents)
          </label>
        </div>

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
