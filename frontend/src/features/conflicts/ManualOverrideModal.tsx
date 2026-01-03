'use client';

import { useState, useEffect, useRef, useId } from 'react';
import { format } from 'date-fns';
import {
  X,
  Shield,
  AlertTriangle,
  AlertOctagon,
  Clock,
  Calendar,
  User,
  FileText,
  Check,
  Loader2,
  Info,
} from 'lucide-react';
import { useCreateOverride } from './hooks';
import type { Conflict, ManualOverride } from './types';

// ============================================================================
// Props
// ============================================================================

interface ManualOverrideModalProps {
  isOpen: boolean;
  onClose: () => void;
  conflict: Conflict | null;
  onOverrideCreated?: (conflict: Conflict) => void;
}

// ============================================================================
// Override Type Options
// ============================================================================

const OVERRIDE_TYPES = [
  {
    value: 'acknowledge' as const,
    label: 'Acknowledge',
    description: 'Acknowledge this conflict but proceed without changes',
    icon: Check,
  },
  {
    value: 'temporary' as const,
    label: 'Temporary Override',
    description: 'Override this conflict for a specific period of time',
    icon: Clock,
  },
  {
    value: 'permanent' as const,
    label: 'Permanent Override',
    description: 'Permanently override this conflict (requires justification)',
    icon: Shield,
  },
];

const ACGME_EXCEPTION_TYPES = [
  { value: 'educational_need', label: 'Educational Need' },
  { value: 'patient_care_continuity', label: 'Patient Care Continuity' },
  { value: 'emergency_coverage', label: 'Emergency Coverage' },
  { value: 'clinical_necessity', label: 'Clinical Necessity' },
  { value: 'other', label: 'Other (specify in justification)' },
];

// ============================================================================
// Component
// ============================================================================

export function ManualOverrideModal({
  isOpen,
  onClose,
  conflict,
  onOverrideCreated,
}: ManualOverrideModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const titleId = useId();

  // Form state
  const [overrideType, setOverrideType] = useState<'acknowledge' | 'temporary' | 'permanent'>('acknowledge');
  const [reason, setReason] = useState('');
  const [justification, setJustification] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [isAcgmeRelated, setIsAcgmeRelated] = useState(false);
  const [acgmeExceptionType, setAcgmeExceptionType] = useState('');
  const [supervisorRequired, setSupervisorRequired] = useState(false);
  const [supervisorApproved, setSupervisorApproved] = useState(false);
  const [supervisorId, setSupervisorId] = useState('');
  const [acknowledgeRisks, setAcknowledgeRisks] = useState(false);

  // Mutation
  const createOverride = useCreateOverride();

  // Reset form when modal opens/closes or conflict changes
  useEffect(() => {
    if (isOpen && conflict) {
      setOverrideType('acknowledge');
      setReason('');
      setJustification('');
      setExpiresAt('');
      setIsAcgmeRelated(conflict.type === 'acgme_violation');
      setAcgmeExceptionType('');
      setSupervisorRequired(conflict.severity === 'critical');
      setSupervisorApproved(false);
      setSupervisorId('');
      setAcknowledgeRisks(false);
    }
  }, [isOpen, conflict]);

  // Focus management
  useEffect(() => {
    if (isOpen && modalRef.current) {
      const focusable = modalRef.current.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      focusable?.focus();
    }
  }, [isOpen]);

  // Escape key handler
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Form validation
  const isValid = () => {
    if (!reason.trim()) return false;
    if (!justification.trim()) return false;
    if (overrideType === 'temporary' && !expiresAt) return false;
    if (isAcgmeRelated && !acgmeExceptionType) return false;
    if (supervisorRequired && !supervisorApproved) return false;
    if (!acknowledgeRisks) return false;
    return true;
  };

  // Submit handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!conflict || !isValid()) return;

    const override: ManualOverride = {
      conflict_id: conflict.id,
      override_type: overrideType,
      reason,
      justification,
      expires_at: overrideType === 'temporary' ? expiresAt : undefined,
      is_acgme_related: isAcgmeRelated,
      acgme_exception_type: isAcgmeRelated ? acgmeExceptionType : undefined,
      supervisor_approval_required: supervisorRequired,
      supervisor_approved: supervisorApproved,
      supervisor_id: supervisorApproved ? supervisorId || undefined : undefined,
    };

    try {
      const result = await createOverride.mutateAsync(override);
      if (onOverrideCreated) {
        onOverrideCreated(result);
      }
      onClose();
      } catch {
        // Assuming setError is defined elsewhere or needs to be added
        // For now, just keeping the comment as per original instruction
        // setError('Failed to apply override');
    }
  };

  if (!isOpen || !conflict) return null;

  const isCritical = conflict.severity === 'critical';
  const isAcgmeViolation = conflict.type === 'acgme_violation';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fadeIn">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col animate-scaleIn"
      >
        {/* Header */}
        <div className={`
          flex items-center justify-between p-4 border-b
          ${isCritical ? 'bg-red-50' : 'bg-amber-50'}
        `}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${isCritical ? 'bg-red-100' : 'bg-amber-100'}`}>
              <Shield className={`w-6 h-6 ${isCritical ? 'text-red-600' : 'text-amber-600'}`} />
            </div>
            <div>
              <h2 id={titleId} className="text-lg font-semibold text-gray-900">
                Create Manual Override
              </h2>
              <p className="text-sm text-gray-600">{conflict.title}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/50 rounded"
            aria-label="Close modal"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Warning banner */}
        {(isCritical || isAcgmeViolation) && (
          <div className={`
            px-4 py-3 flex items-start gap-3
            ${isCritical ? 'bg-red-100 border-b border-red-200' : 'bg-amber-100 border-b border-amber-200'}
          `}>
            <AlertOctagon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${isCritical ? 'text-red-600' : 'text-amber-600'}`} />
            <div className="text-sm">
              {isCritical && (
                <p className="font-medium text-red-800">
                  This is a critical conflict that may affect patient safety or regulatory compliance.
                </p>
              )}
              {isAcgmeViolation && (
                <p className={isCritical ? 'text-red-700 mt-1' : 'font-medium text-amber-800'}>
                  This conflict involves ACGME duty hour regulations. Overrides must be documented
                  and may be subject to audit review.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto">
          <div className="p-4 space-y-6">
            {/* Conflict summary */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Conflict Details</h3>
              <p className="text-sm text-gray-600 mb-3">{conflict.description}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  {format(new Date(conflict.conflict_date), 'MMMM d, yyyy')}
                  {conflict.conflict_session && ` (${conflict.conflict_session})`}
                </span>
                <span className="flex items-center gap-1">
                  <User className="w-3.5 h-3.5" />
                  {conflict.affected_person_ids.length} affected
                </span>
              </div>
            </div>

            {/* Override type selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Override Type
              </label>
              <div className="space-y-2">
                {OVERRIDE_TYPES.map((type) => {
                  const Icon = type.icon;
                  return (
                    <label
                      key={type.value}
                      className={`
                        flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors
                        ${overrideType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="overrideType"
                        value={type.value}
                        checked={overrideType === type.value}
                        onChange={(e) => setOverrideType(e.target.value as typeof overrideType)}
                        className="mt-1"
                      />
                      <Icon className={`w-5 h-5 flex-shrink-0 ${
                        overrideType === type.value ? 'text-blue-500' : 'text-gray-400'
                      }`} />
                      <div>
                        <span className="font-medium text-gray-900">{type.label}</span>
                        <p className="text-sm text-gray-500">{type.description}</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Expiration date for temporary overrides */}
            {overrideType === 'temporary' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Override Expires On <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={expiresAt}
                  onChange={(e) => setExpiresAt(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required={overrideType === 'temporary'}
                />
              </div>
            )}

            {/* Reason */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason for Override <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Brief reason for the override..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Justification */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <FileText className="w-4 h-4 inline mr-1" />
                Detailed Justification <span className="text-red-500">*</span>
              </label>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                placeholder="Provide a detailed justification for this override. This will be recorded for audit purposes..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={4}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                This justification will be recorded in the audit trail.
              </p>
            </div>

            {/* ACGME-specific fields */}
            {isAcgmeRelated && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-4" role="region" aria-label="ACGME compliance requirements">
                <div className="flex items-center gap-2 text-blue-800">
                  <Info className="w-5 h-5" aria-hidden="true" />
                  <span className="font-medium">ACGME Compliance Information</span>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Exception Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={acgmeExceptionType}
                    onChange={(e) => setAcgmeExceptionType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required={isAcgmeRelated}
                  >
                    <option value="">Select exception type...</option>
                    {ACGME_EXCEPTION_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <p className="text-xs text-blue-700">
                  ACGME allows for occasional exceptions to duty hour requirements when necessary
                  for patient care or educational purposes. All exceptions must be documented.
                </p>
              </div>
            )}

            {/* Supervisor approval */}
            {supervisorRequired && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-4" role="alert" aria-live="polite">
                <div className="flex items-center gap-2 text-amber-800">
                  <AlertTriangle className="w-5 h-5" aria-hidden="true" />
                  <span className="font-medium">Supervisor Approval Required</span>
                </div>

                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={supervisorApproved}
                    onChange={(e) => setSupervisorApproved(e.target.checked)}
                    className="mt-1 w-4 h-4 text-amber-600 border-amber-300 rounded focus:ring-amber-500"
                  />
                  <span className="text-sm text-amber-800">
                    I confirm that a supervising faculty member has reviewed and approved this override.
                  </span>
                </label>

                {supervisorApproved && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Approving Supervisor (optional)
                    </label>
                    <input
                      type="text"
                      value={supervisorId}
                      onChange={(e) => setSupervisorId(e.target.value)}
                      placeholder="Name or ID of approving supervisor..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Risk acknowledgment */}
            <div className={`
              p-4 rounded-lg border
              ${isCritical ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}
            `}>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={acknowledgeRisks}
                  onChange={(e) => setAcknowledgeRisks(e.target.checked)}
                  className={`
                    mt-1 w-4 h-4 rounded focus:ring-2
                    ${isCritical
                      ? 'text-red-600 border-red-300 focus:ring-red-500'
                      : 'text-blue-600 border-gray-300 focus:ring-blue-500'
                    }
                  `}
                  required
                />
                <span className={`text-sm ${isCritical ? 'text-red-800' : 'text-gray-700'}`}>
                  <strong>I understand and acknowledge</strong> that by creating this override, I am
                  accepting responsibility for any scheduling conflicts, compliance issues, or other
                  consequences that may result. This action will be recorded in the audit log.
                </span>
              </label>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 border-t bg-gray-50">
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-500">
                <Clock className="w-3.5 h-3.5 inline mr-1" />
                This override will be recorded with timestamp and user information.
              </p>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!isValid() || createOverride.isPending}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200
                    disabled:opacity-50 disabled:cursor-not-allowed
                    hover:shadow-lg active:scale-95
                    ${isCritical
                      ? 'bg-red-500 text-white hover:bg-red-600'
                      : 'bg-amber-500 text-white hover:bg-amber-600'
                    }
                  `}
                >
                  {createOverride.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4" />
                      Create Override
                    </>
                  )}
                </button>
              </div>
            </div>

            {createOverride.isError && (
              <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded-lg text-sm text-red-700" role="alert" aria-live="assertive">
                <strong>Error:</strong> {createOverride.error?.message || 'Failed to create override'}
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
