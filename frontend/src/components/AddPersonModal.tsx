'use client';

import { useState, FormEvent } from 'react';
import { Modal } from './Modal';
import { Input, Select } from './forms';
import { useCreatePerson } from '@/lib/hooks';
import type { PersonCreate } from '@/types/api';

interface AddPersonModalProps {
  isOpen: boolean;
  onClose: () => void;
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

export function AddPersonModal({ isOpen, onClose }: AddPersonModalProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [type, setType] = useState<'resident' | 'faculty'>('resident');
  const [pgyLevel, setPgyLevel] = useState('1');
  const [performsProcedures, setPerformsProcedures] = useState(false);
  const [specialties, setSpecialties] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});

  const createPerson = useCreatePerson();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Name is required
    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }

    // Email format validation (if provided)
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // PGY level validation for residents
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

    if (!validateForm()) {
      return;
    }

    const personData: PersonCreate = {
      name: name.trim(),
      type,
      ...(email && { email: email.trim() }),
      ...(type === 'resident' && { pgy_level: parseInt(pgyLevel) }),
      performs_procedures: performsProcedures,
      ...(specialties && { specialties: specialties.split(',').map(s => s.trim()).filter(Boolean) }),
    };

    try {
      await createPerson.mutateAsync(personData);
      handleClose();
    } catch (err) {
      setErrors({ general: 'Failed to create person. Please try again.' });
    }
  };

  const handleClose = () => {
    // Reset form
    setName('');
    setEmail('');
    setType('resident');
    setPgyLevel('1');
    setPerformsProcedures(false);
    setSpecialties('');
    setErrors({});
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Person">
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
            id="performsProcedures"
            checked={performsProcedures}
            onChange={(e) => setPerformsProcedures(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="performsProcedures" className="text-sm text-gray-700">
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
            disabled={createPerson.isPending}
            className="btn-primary disabled:opacity-50"
          >
            {createPerson.isPending ? 'Creating...' : 'Add Person'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
