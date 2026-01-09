'use client';

/**
 * CredentialCellModal Component
 *
 * Modal for granting, editing, or revoking credentials.
 */
import { useState, useCallback } from 'react';
import { X, Loader2, Trash2, Save, Plus } from 'lucide-react';
import {
  useCreateCredential,
  useUpdateCredential,
  useDeleteCredential,
  type Credential,
  type CredentialStatus,
  type CompetencyLevel,
  type CredentialCreate,
  type CredentialUpdate,
} from '@/hooks/useProcedures';
import { useToast } from '@/contexts/ToastContext';
import type { Person } from '@/types/api';
import type { Procedure } from '@/hooks/useProcedures';

// ============================================================================
// Types
// ============================================================================

export interface CredentialCellModalProps {
  faculty: Person;
  procedure: Procedure;
  credential: Credential | null;
  onClose: () => void;
}

// ============================================================================
// Constants
// ============================================================================

const STATUS_OPTIONS: { value: CredentialStatus; label: string }[] = [
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'suspended', label: 'Suspended' },
  { value: 'expired', label: 'Expired' },
];

const COMPETENCY_OPTIONS: { value: CompetencyLevel; label: string }[] = [
  { value: 'trainee', label: 'Trainee' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'expert', label: 'Expert' },
  { value: 'master', label: 'Master' },
];

// ============================================================================
// Main Component
// ============================================================================

export function CredentialCellModal({
  faculty,
  procedure,
  credential,
  onClose,
}: CredentialCellModalProps) {
  const { toast } = useToast();
  const createCredential = useCreateCredential();
  const updateCredential = useUpdateCredential();
  const deleteCredential = useDeleteCredential();

  const isEditing = credential !== null;

  // Form state
  const [status, setStatus] = useState<CredentialStatus>(credential?.status || 'active');
  const [competencyLevel, setCompetencyLevel] = useState<CompetencyLevel>(
    credential?.competencyLevel || 'qualified'
  );
  const [expirationDate, setExpirationDate] = useState(
    credential?.expirationDate?.split('T')[0] || ''
  );
  const [notes, setNotes] = useState(credential?.notes || '');

  const isPending =
    createCredential.isPending || updateCredential.isPending || deleteCredential.isPending;

  const handleSave = useCallback(async () => {
    if (isEditing && credential) {
      // Update existing credential
      const updates: CredentialUpdate = {
        status,
        competencyLevel: competencyLevel,
        expirationDate: expirationDate || null,
        notes: notes || null,
      };

      try {
        await updateCredential.mutateAsync({ id: credential.id, data: updates });
        toast.success('Credential updated');
        onClose();
      } catch (error) {
        toast.error(error);
      }
    } else {
      // Create new credential
      const data: CredentialCreate = {
        personId: faculty.id,
        procedureId: procedure.id,
        status,
        competencyLevel: competencyLevel,
        expirationDate: expirationDate || null,
        notes: notes || null,
      };

      try {
        await createCredential.mutateAsync(data);
        toast.success('Credential granted');
        onClose();
      } catch (error) {
        toast.error(error);
      }
    }
  }, [
    isEditing,
    credential,
    faculty.id,
    procedure.id,
    status,
    competencyLevel,
    expirationDate,
    notes,
    createCredential,
    updateCredential,
    toast,
    onClose,
  ]);

  const handleDelete = useCallback(async () => {
    if (!credential) return;

    if (!confirm('Revoke this credential? This cannot be undone.')) {
      return;
    }

    try {
      await deleteCredential.mutateAsync(credential.id);
      toast.success('Credential revoked');
      onClose();
    } catch (error) {
      toast.error(error);
    }
  }, [credential, deleteCredential, toast, onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-xl shadow-2xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-white">
              {isEditing ? 'Edit Credential' : 'Grant Credential'}
            </h2>
            <p className="text-sm text-slate-400">
              {faculty.name} - {procedure.name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-4">
          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as CredentialStatus)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Competency Level */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Competency Level
            </label>
            <select
              value={competencyLevel}
              onChange={(e) => setCompetencyLevel(e.target.value as CompetencyLevel)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              {COMPETENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Expiration Date */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Expiration Date (optional)
            </label>
            <input
              type="date"
              value={expirationDate}
              onChange={(e) => setExpirationDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
              placeholder="Add notes..."
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700">
          {isEditing ? (
            <button
              onClick={handleDelete}
              disabled={isPending}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {deleteCredential.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              Revoke
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              disabled={isPending}
              className="px-4 py-2 text-slate-300 hover:text-white transition-colors text-sm font-medium disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isPending}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {(createCredential.isPending || updateCredential.isPending) ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : isEditing ? (
                <Save className="w-4 h-4" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              {isEditing ? 'Save' : 'Grant'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
