'use client';

import { useState, useEffect, useMemo } from 'react';
import { Modal } from '@/components/Modal';
import { Select } from '@/components/forms/Select';
import { TextArea } from '@/components/forms/TextArea';
import {
  useUpdateAssignment,
  useCreateAssignment,
  useDeleteAssignment,
  useRotationTemplates,
  usePerson,
} from '@/lib/hooks';
import { useAuth } from '@/contexts/AuthContext';
import type { Assignment, AssignmentCreate, AssignmentUpdate } from '@/types/api';
import {
  AssignmentWarnings,
  AssignmentWarning,
  generateWarnings,
  WarningCheckContext,
} from './AssignmentWarnings';
import { Trash2, Save, X, Loader2 } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface EditAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment | null; // null = creating new
  personId: string;
  date: string;
  session: 'AM' | 'PM';
  blockId?: string;
  onSave?: (assignment: Assignment) => void;
  onDelete?: () => void;
  warningContext?: Partial<WarningCheckContext>;
}

// ============================================================================
// Component
// ============================================================================

export function EditAssignmentModal({
  isOpen,
  onClose,
  assignment,
  personId,
  date,
  session,
  blockId,
  onSave,
  onDelete,
  warningContext,
}: EditAssignmentModalProps) {
  const { user } = useAuth();
  const canEdit = user?.role === 'admin' || user?.role === 'coordinator';

  // State
  const [rotationTemplateId, setRotationTemplateId] = useState<string>('');
  const [role, setRole] = useState<'primary' | 'supervising' | 'backup'>('primary');
  const [notes, setNotes] = useState<string>('');
  const [criticalAcknowledged, setCriticalAcknowledged] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Queries
  const { data: rotationTemplatesData, isLoading: templatesLoading } = useRotationTemplates();
  const { data: person, isLoading: personLoading } = usePerson(personId);

  // Mutations
  const createAssignment = useCreateAssignment();
  const updateAssignment = useUpdateAssignment();
  const deleteAssignment = useDeleteAssignment();

  const isLoading =
    templatesLoading ||
    personLoading ||
    createAssignment.isPending ||
    updateAssignment.isPending ||
    deleteAssignment.isPending;

  const isEditing = !!assignment;

  // Reset form when modal opens/closes or assignment changes
  useEffect(() => {
    if (isOpen) {
      if (assignment) {
        setRotationTemplateId(assignment.rotation_template_id || '');
        setRole(assignment.role);
        setNotes(assignment.notes || '');
      } else {
        setRotationTemplateId('');
        setRole('primary');
        setNotes('');
      }
      setCriticalAcknowledged(false);
      setError(null);
    }
  }, [isOpen, assignment]);

  // Rotation template options
  const rotationOptions = useMemo(() => {
    const templates = rotationTemplatesData?.items || [];
    return [
      { value: '', label: '-- Select Rotation --' },
      ...templates.map((t) => ({
        value: t.id,
        label: t.abbreviation ? `${t.name} (${t.abbreviation})` : t.name,
      })),
    ];
  }, [rotationTemplatesData]);

  // Role options
  const roleOptions = [
    { value: 'primary', label: 'Primary' },
    { value: 'supervising', label: 'Supervising' },
    { value: 'backup', label: 'Backup' },
  ];

  // Generate warnings based on current state
  const warnings = useMemo<AssignmentWarning[]>(() => {
    if (!person || !rotationTemplateId) {
      return [];
    }

    const selectedRotation = rotationTemplatesData?.items?.find(
      (t) => t.id === rotationTemplateId
    );

    const context: WarningCheckContext = {
      personId,
      personName: person.name,
      date,
      session,
      rotationTemplateId,
      requiresSupervision: selectedRotation?.supervision_required,
      ...warningContext,
    };

    return generateWarnings(context);
  }, [person, rotationTemplateId, rotationTemplatesData, personId, date, session, warningContext]);

  const hasCriticalWarnings = warnings.some((w) => w.severity === 'critical');
  const canSave = canEdit && rotationTemplateId && (!hasCriticalWarnings || criticalAcknowledged);

  // Format date for display
  const formattedDate = useMemo(() => {
    try {
      const dateObj = new Date(date);
      return dateObj.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return date;
    }
  }, [date]);

  // Handlers
  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  const handleSave = async () => {
    if (!canSave || !blockId) {
      setError('Missing required information. Please ensure all fields are filled.');
      return;
    }

    setError(null);

    try {
      if (isEditing && assignment) {
        // Update existing assignment
        const updateData: AssignmentUpdate = {
          rotation_template_id: rotationTemplateId || undefined,
          role,
          notes: notes || undefined,
        };

        const result = await updateAssignment.mutateAsync({
          id: assignment.id,
          data: updateData,
        });

        onSave?.(result);
      } else {
        // Create new assignment
        const createData: AssignmentCreate = {
          block_id: blockId,
          person_id: personId,
          rotation_template_id: rotationTemplateId || undefined,
          role,
          notes: notes || undefined,
          created_by: user?.id,
        };

        const result = await createAssignment.mutateAsync(createData);
        onSave?.(result);
      }

      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save assignment');
    }
  };

  const handleDelete = async () => {
    if (!assignment || !canEdit) return;

    setError(null);

    try {
      await deleteAssignment.mutateAsync(assignment.id);
      onDelete?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete assignment');
    }
  };

  // Permission check
  if (!canEdit) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="View Assignment">
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            You do not have permission to edit assignments. Contact an administrator if you need to
            make changes.
          </p>
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={isEditing ? 'Edit Assignment' : 'New Assignment'}
    >
      <div className="space-y-5">
        {/* Read-only fields */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
              Person
            </label>
            <p className="mt-1 text-sm font-medium text-gray-900">
              {personLoading ? (
                <span className="text-gray-400">Loading...</span>
              ) : (
                person?.name || 'Unknown'
              )}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                Date
              </label>
              <p className="mt-1 text-sm font-medium text-gray-900">{formattedDate}</p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                Session
              </label>
              <p className="mt-1 text-sm font-medium text-gray-900">{session}</p>
            </div>
          </div>
        </div>

        {/* Editable fields */}
        <Select
          label="Rotation"
          options={rotationOptions}
          value={rotationTemplateId}
          onChange={(e) => setRotationTemplateId(e.target.value)}
          disabled={templatesLoading}
        />

        <Select
          label="Role"
          options={roleOptions}
          value={role}
          onChange={(e) => setRole(e.target.value as 'primary' | 'supervising' | 'backup')}
        />

        <TextArea
          label="Notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Optional notes about this assignment..."
          rows={3}
        />

        {/* Warnings */}
        {warnings.length > 0 && (
          <AssignmentWarnings
            warnings={warnings}
            criticalAcknowledged={criticalAcknowledged}
            onAcknowledgeCritical={setCriticalAcknowledged}
          />
        )}

        {/* Error display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center justify-between pt-2">
          <div>
            {isEditing && (
              <button
                onClick={handleDelete}
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-md hover:bg-red-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleteAssignment.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4" />
                )}
                Delete
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClose}
              disabled={isLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <X className="w-4 h-4" />
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!canSave || isLoading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {createAssignment.isPending || updateAssignment.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isEditing ? 'Save Changes' : 'Create Assignment'}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
