'use client';

/**
 * Create Call Assignment Modal
 *
 * Modal for creating new faculty call assignments with date picker,
 * faculty selection, and call type options.
 */

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from '@/components/Modal';
import { useFaculty } from '@/hooks/usePeople';
import { useCreateCallAssignment } from '@/hooks/useCallAssignments';

interface CreateCallAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface FormErrors {
  date?: string;
  person_id?: string;
  general?: string;
}

const callTypeOptions = [
  { value: 'weekday', label: 'Weekday (Mon-Thu)' },
  { value: 'sunday', label: 'Sunday' },
  { value: 'holiday', label: 'Holiday' },
  { value: 'backup', label: 'Backup' },
];

export function CreateCallAssignmentModal({
  isOpen,
  onClose,
}: CreateCallAssignmentModalProps) {
  const [date, setDate] = useState('');
  const [personId, setPersonId] = useState('');
  const [callType, setCallType] = useState('weekday');
  const [isWeekend, setIsWeekend] = useState(false);
  const [isHoliday, setIsHoliday] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  const { data: facultyData, isLoading: facultyLoading } = useFaculty();
  const createMutation = useCreateCallAssignment();

  // Auto-detect weekend when date changes
  useEffect(() => {
    if (date) {
      const d = new Date(date + 'T00:00:00');
      const dayOfWeek = d.getDay();
      const weekend = dayOfWeek === 0 || dayOfWeek === 6;
      setIsWeekend(weekend);

      // Auto-set call type for Sunday
      if (dayOfWeek === 0) {
        setCallType('sunday');
      } else if (dayOfWeek >= 1 && dayOfWeek <= 4) {
        setCallType('weekday');
      }
    }
  }, [date]);

  // Auto-set isHoliday when call type changes
  useEffect(() => {
    setIsHoliday(callType === 'holiday');
  }, [callType]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!date) {
      newErrors.date = 'Date is required';
    }

    if (!personId) {
      newErrors.personId = 'Faculty member is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await createMutation.mutateAsync({
        call_date: date,
        person_id: personId,
        call_type: callType,
        is_weekend: isWeekend,
        is_holiday: isHoliday,
      });
      handleClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setErrors({ general: `Failed to create call assignment: ${message}` });
    }
  };

  const handleClose = () => {
    setDate('');
    setPersonId('');
    setCallType('weekday');
    setIsWeekend(false);
    setIsHoliday(false);
    setErrors({});
    onClose();
  };

  const faculty = facultyData?.items || [];

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="New Call Assignment">
      <form onSubmit={handleSubmit} className="space-y-4">
        {errors.general && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {errors.general}
          </div>
        )}

        {/* Date */}
        {/* TODO: Native date input has typing quirk (year shows last digit only).
            Either make read-only with calendar-only input, or use a custom date picker component. */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
              errors.date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.date && (
            <p className="mt-1 text-sm text-red-600">{errors.date}</p>
          )}
        </div>

        {/* Faculty Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Faculty Member <span className="text-red-500">*</span>
          </label>
          <select
            value={personId}
            onChange={(e) => setPersonId(e.target.value)}
            disabled={facultyLoading}
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 ${
              errors.personId ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">
              {facultyLoading ? 'Loading faculty...' : 'Select faculty member'}
            </option>
            {faculty.map((person) => (
              <option key={person.id} value={person.id}>
                {person.name}
                {person.facultyRole ? ` (${person.facultyRole})` : ''}
              </option>
            ))}
          </select>
          {errors.personId && (
            <p className="mt-1 text-sm text-red-600">{errors.personId}</p>
          )}
        </div>

        {/* Call Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Call Type
          </label>
          <select
            value={callType}
            onChange={(e) => setCallType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          >
            {callTypeOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Checkboxes */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isWeekend"
              checked={isWeekend}
              onChange={(e) => setIsWeekend(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isWeekend" className="text-sm text-gray-700">
              Weekend call
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isHoliday"
              checked={isHoliday}
              onChange={(e) => setIsHoliday(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="isHoliday" className="text-sm text-gray-700">
              Holiday call
            </label>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
