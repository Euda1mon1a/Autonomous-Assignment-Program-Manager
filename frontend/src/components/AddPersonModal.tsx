'use client';

import { useState, FormEvent } from 'react';
import { Modal } from './Modal';
import { Input, Select } from './forms';
import { useCreatePerson } from '@/lib/hooks';
import { validateRequired, validateEmail, validateMinLength, validatePgyLevel } from '@/lib/validation';
import { PersonType, FacultyRole, type PersonCreate } from '@/types/api';

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
  { value: '4', label: 'PGY-4' },
  { value: '5', label: 'PGY-5' },
  { value: '6', label: 'PGY-6' },
  { value: '7', label: 'PGY-7' },
  { value: '8', label: 'PGY-8' },
];

const facultyRoleOptions = [
  { value: FacultyRole.CORE, label: 'Core Faculty' },
  { value: FacultyRole.PD, label: 'Program Director' },
  { value: FacultyRole.APD, label: 'Associate Program Director' },
  { value: FacultyRole.OIC, label: 'Officer in Charge' },
  { value: FacultyRole.DEPT_CHIEF, label: 'Department Chief' },
  { value: FacultyRole.SPORTS_MED, label: 'Sports Medicine' },
  { value: FacultyRole.ADJUNCT, label: 'Adjunct Faculty' },
];

export function AddPersonModal({ isOpen, onClose }: AddPersonModalProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [type, setType] = useState<PersonType>(PersonType.RESIDENT);
  const [pgyLevel, setPgyLevel] = useState('1');
  const [facultyRole, setFacultyRole] = useState<FacultyRole>(FacultyRole.CORE);
  const [performsProcedures, setPerformsProcedures] = useState(false);
  const [specialties, setSpecialties] = useState('');
  const [errors, setErrors] = useState<FormErrors>({});

  const createPerson = useCreatePerson();

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Name is required and must be at least 2 characters
    const nameRequiredError = validateRequired(name, 'Name');
    if (nameRequiredError) {
      newErrors.name = nameRequiredError;
    } else {
      const nameMinLengthError = validateMinLength(name, 2, 'Name');
      if (nameMinLengthError) {
        newErrors.name = nameMinLengthError;
      }
    }

    // Email format validation (if provided)
    if (email) {
      const emailError = validateEmail(email);
      if (emailError) {
        newErrors.email = emailError;
      }
    }

    // PGY level validation for residents (1-8)
    if (type === PersonType.RESIDENT) {
      const pgyError = validatePgyLevel(pgyLevel);
      if (pgyError) {
        newErrors.pgy_level = pgyError;
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
      ...(type === PersonType.RESIDENT && { pgy_level: parseInt(pgyLevel) }),
      ...(type === PersonType.FACULTY && { faculty_role: facultyRole }),
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
    setType(PersonType.RESIDENT);
    setPgyLevel('1');
    setFacultyRole(FacultyRole.CORE);
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
          onChange={(e) => setType(e.target.value as PersonType)}
          options={typeOptions}
        />

        {type === PersonType.RESIDENT && (
          <Select
            label="PGY Level"
            value={pgyLevel}
            onChange={(e) => setPgyLevel(e.target.value)}
            options={pgyOptions}
            error={errors.pgy_level}
          />
        )}

        {type === PersonType.FACULTY && (
          <Select
            label="Faculty Role"
            value={facultyRole}
            onChange={(e) => setFacultyRole(e.target.value as FacultyRole)}
            options={facultyRoleOptions}
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
