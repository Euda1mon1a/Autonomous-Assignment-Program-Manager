'use client';

import { AlertTriangle, AlertCircle, Info, Clock, Users, Calendar, UserX, Building2 } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export type WarningType = 'hours' | 'supervision' | 'conflict' | 'absence' | 'capacity';
export type WarningSeverity = 'info' | 'warning' | 'critical';

export interface AssignmentWarning {
  type: WarningType;
  severity: WarningSeverity;
  message: string;
}

interface AssignmentWarningsProps {
  warnings: AssignmentWarning[];
  onAcknowledgeCritical?: (acknowledged: boolean) => void;
  criticalAcknowledged?: boolean;
}

// ============================================================================
// Helper Functions
// ============================================================================

function getWarningIcon(type: WarningType) {
  switch (type) {
    case 'hours':
      return Clock;
    case 'supervision':
      return Users;
    case 'conflict':
      return Calendar;
    case 'absence':
      return UserX;
    case 'capacity':
      return Building2;
    default:
      return AlertCircle;
  }
}

function getSeverityStyles(severity: WarningSeverity) {
  switch (severity) {
    case 'critical':
      return {
        container: 'bg-red-50 border-red-200 text-red-800',
        icon: 'text-red-500',
      };
    case 'warning':
      return {
        container: 'bg-amber-50 border-amber-200 text-amber-800',
        icon: 'text-amber-500',
      };
    case 'info':
    default:
      return {
        container: 'bg-blue-50 border-blue-200 text-blue-800',
        icon: 'text-blue-500',
      };
  }
}

function getSeverityIcon(severity: WarningSeverity) {
  switch (severity) {
    case 'critical':
      return AlertTriangle;
    case 'warning':
      return AlertCircle;
    case 'info':
    default:
      return Info;
  }
}

// ============================================================================
// Component
// ============================================================================

export function AssignmentWarnings({
  warnings,
  onAcknowledgeCritical,
  criticalAcknowledged = false,
}: AssignmentWarningsProps) {
  if (warnings.length === 0) {
    return null;
  }

  const hasCritical = warnings.some((w) => w.severity === 'critical');
  const sortedWarnings = [...warnings].sort((a, b) => {
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    return severityOrder[a.severity] - severityOrder[b.severity];
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
        <AlertTriangle className="w-4 h-4" />
        <span>Warnings ({warnings.length})</span>
      </div>

      <div className="space-y-2 max-h-48 overflow-y-auto">
        {sortedWarnings.map((warning, index) => {
          const styles = getSeverityStyles(warning.severity);
          const TypeIcon = getWarningIcon(warning.type);
          const SeverityIcon = getSeverityIcon(warning.severity);

          return (
            <div
              key={`${warning.type}-${index}`}
              className={`flex items-start gap-3 p-3 rounded-md border ${styles.container}`}
            >
              <div className={`flex-shrink-0 mt-0.5 ${styles.icon}`}>
                <SeverityIcon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <TypeIcon className={`w-3.5 h-3.5 ${styles.icon}`} />
                  <span className="text-xs font-medium uppercase tracking-wide">
                    {warning.type}
                  </span>
                </div>
                <p className="text-sm">{warning.message}</p>
              </div>
            </div>
          );
        })}
      </div>

      {hasCritical && onAcknowledgeCritical && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={criticalAcknowledged}
              onChange={(e) => onAcknowledgeCritical(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-red-600 border-red-300 rounded focus:ring-red-500"
            />
            <span className="text-sm text-red-800">
              <strong>I understand this override</strong> - There are critical warnings that may
              cause scheduling conflicts or compliance issues. By checking this box, I acknowledge
              that I have reviewed these warnings and accept responsibility for this assignment.
            </span>
          </label>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Utility Functions for Generating Warnings
// ============================================================================

export interface WarningCheckContext {
  personId: string;
  personName?: string;
  date: string;
  session: 'AM' | 'PM';
  rotationTemplateId?: string;
  existingAssignments?: Array<{
    date: string;
    session: 'AM' | 'PM';
    rotationName?: string;
  }>;
  absences?: Array<{
    startDate: string;
    endDate: string;
    type: string;
  }>;
  weeklyHours?: number;
  maxWeeklyHours?: number;
  rotationCapacity?: number;
  currentRotationCount?: number;
  requiresSupervision?: boolean;
  hasSupervisor?: boolean;
}

export function generateWarnings(context: WarningCheckContext): AssignmentWarning[] {
  const warnings: AssignmentWarning[] = [];

  // Check for hours warning
  if (context.weeklyHours !== undefined && context.maxWeeklyHours !== undefined) {
    const hoursAfterAssignment = context.weeklyHours + 4; // Assuming 4-hour block
    if (hoursAfterAssignment > context.maxWeeklyHours) {
      const overBy = hoursAfterAssignment - context.maxWeeklyHours;
      warnings.push({
        type: 'hours',
        severity: overBy > 8 ? 'critical' : 'warning',
        message: `This assignment would put ${context.personName || 'this person'} at ${hoursAfterAssignment} hours this week (${overBy} hours over the ${context.maxWeeklyHours}-hour limit).`,
      });
    }
  }

  // Check for supervision warning
  if (context.requiresSupervision && !context.hasSupervisor) {
    warnings.push({
      type: 'supervision',
      severity: 'critical',
      message: 'This rotation requires faculty supervision, but no supervisor is assigned for this block.',
    });
  }

  // Check for scheduling conflict
  if (context.existingAssignments) {
    const conflictingAssignment = context.existingAssignments.find(
      (a) => a.date === context.date && a.session === context.session
    );
    if (conflictingAssignment) {
      warnings.push({
        type: 'conflict',
        severity: 'critical',
        message: `${context.personName || 'This person'} is already assigned to ${conflictingAssignment.rotationName || 'another rotation'} during this time slot.`,
      });
    }
  }

  // Check for absence conflict
  if (context.absences) {
    const targetDate = new Date(context.date);
    const conflictingAbsence = context.absences.find((a) => {
      const startDate = new Date(a.startDate);
      const endDate = new Date(a.endDate);
      return targetDate >= startDate && targetDate <= endDate;
    });
    if (conflictingAbsence) {
      warnings.push({
        type: 'absence',
        severity: 'critical',
        message: `${context.personName || 'This person'} has a recorded ${conflictingAbsence.type.replace('_', ' ')} absence on this date.`,
      });
    }
  }

  // Check for capacity warning
  if (
    context.rotationCapacity !== undefined &&
    context.currentRotationCount !== undefined
  ) {
    if (context.currentRotationCount >= context.rotationCapacity) {
      warnings.push({
        type: 'capacity',
        severity: 'warning',
        message: `This rotation is at capacity (${context.currentRotationCount}/${context.rotationCapacity}). Adding another person may affect quality of supervision.`,
      });
    }
  }

  return warnings;
}

// ============================================================================
// Warning Summary Component (for list views)
// ============================================================================

interface WarningBadgeProps {
  warnings: AssignmentWarning[];
  compact?: boolean;
}

export function WarningBadge({ warnings, compact = false }: WarningBadgeProps) {
  if (warnings.length === 0) {
    return null;
  }

  const hasCritical = warnings.some((w) => w.severity === 'critical');
  const hasWarning = warnings.some((w) => w.severity === 'warning');

  const bgColor = hasCritical ? 'bg-red-100' : hasWarning ? 'bg-amber-100' : 'bg-blue-100';
  const textColor = hasCritical ? 'text-red-700' : hasWarning ? 'text-amber-700' : 'text-blue-700';
  const Icon = hasCritical ? AlertTriangle : hasWarning ? AlertCircle : Info;

  if (compact) {
    return (
      <div className={`inline-flex items-center justify-center w-5 h-5 rounded-full ${bgColor}`}>
        <Icon className={`w-3 h-3 ${textColor}`} />
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${bgColor} ${textColor}`}>
      <Icon className="w-3 h-3" />
      <span>{warnings.length}</span>
    </div>
  );
}
