'use client';

import { useState, FormEvent, useEffect } from 'react';
import { Modal } from '@/components/Modal';
import { Input, Select } from '@/components/forms';
import { useUpdatePerson } from '@/lib/hooks';
import type { Person, PersonUpdate } from '@/types/api';

interface EditPersonModalProps {
  isOpen: boolean;
  onClose: () => void;
  person: Person | null;
}

interface FormErrors {
  name?: string;
  email?: string;
  pgy_level?: string;
  general?: string;
}

const typeOptions = [
  { value: 'resident', label: 'Resident' },
  { value: 'faculty', label: 'Faculty' },
];

const pgyOptions = [
  { value: '1', label: 'PGY-1' },
  { value: '2', label: 'PGY-2' },
  { value: '3', label: 'PGY-3' },
];

export function EditPersonModal({ isOpen, onClose, person }: EditPersonModalProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [type, setType] = useState<'resident' | 'faculty'>('resident');
  const [pgyLevel, setPgyLevel] = useState('1');
  const [performsProcedures, setPerformsProcedures] = useState(false);
  const [specialties, setSpecialties] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});

  const updatePerson = useUpdatePerson();

  // Pre-populate form when person changes
  useEffect(() => {
    if (person) {
      setName(person.name);
      setEmail(person.email || '');
      setType(person.type);
      setPgyLevel(person.pgy_level?.toString() || '1');
      setPerformsProcedures(person.performs_procedures);
      setSpecialties(person.specialties?.join(', ') || '');
    }
  }, [person]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (type === 'resident') {
      const pgyNum = parseInt(pgyLevel);
      if (isNaN(pgyNum) || pgyNum < 1 || pgyNum > 3) {
        newErrors.pgy_level = 'PGY level must be between 1 and 3';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm() || !person) {
      return;
    }

    const personData: PersonUpdate = {
      name: name.trim(),
      type,
      email: email.trim() || undefined,
      pgy_level: type === 'resident' ? parseInt(pgyLevel) : undefined,
      performs_procedures: performsProcedures,
      specialties: specialties ? specialties.split(',').map(s => s.trim()).filter(Boolean) : undefined,
    };

    try {
      await updatePerson.mutateAsync({ id: person.id, data: personData });
      handleClose();
    } catch (err) {
      setErrors({ general: 'Failed to update person. Please try again.' });
    }
  };

  const handleClose = () => {
    setErrors({});
    onClose();
  };

  if (!person) return null;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Edit Person">
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
          placeholder="Enter full name"
          required
        />

        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          placeholder="email@example.com"
        />

        <Select
          label="Type"
          value={type}
          onChange={(e) => setType(e.target.value as 'resident' | 'faculty')}
          options={typeOptions}
        />

        {type === 'resident' && (
          <Select
            label="PGY Level"
            value={pgyLevel}
            onChange={(e) => setPgyLevel(e.target.value)}
            options={pgyOptions}
            error={errors.pgy_level}
          />
        )}

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="editPerformsProcedures"
            checked={performsProcedures}
            onChange={(e) => setPerformsProcedures(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="editPerformsProcedures" className="text-sm text-gray-700">
            Performs procedures
          </label>
        </div>

        <Input
          label="Specialties"
          value={specialties}
          onChange={(e) => setSpecialties(e.target.value)}
          placeholder="Enter specialties, comma-separated"
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
            disabled={updatePerson.isPending}
            className="btn-primary disabled:opacity-50"
          >
            {updatePerson.isPending ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
