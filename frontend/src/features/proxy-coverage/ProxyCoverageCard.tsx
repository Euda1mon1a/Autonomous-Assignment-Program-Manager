'use client';

import { ArrowRight, Calendar, MapPin, Repeat, Shield, User, UserCheck } from 'lucide-react';
import type { CoverageRelationship, CoverageType, CoverageStatus } from './types';

interface ProxyCoverageCardProps {
  coverage: CoverageRelationship;
  compact?: boolean;
}

const COVERAGE_TYPE_CONFIG: Record<CoverageType, {
  label: string;
  icon: typeof Shield;
  bgColor: string;
  textColor: string;
  borderColor: string;
}> = {
  remote_surrogate: {
    label: 'Remote Surrogate',
    icon: MapPin,
    bgColor: 'bg-purple-50',
    textColor: 'text-purple-700',
    borderColor: 'border-purple-200',
  },
  swap_absorb: {
    label: 'Swap (Absorb)',
    icon: UserCheck,
    bgColor: 'bg-blue-50',
    textColor: 'text-blue-700',
    borderColor: 'border-blue-200',
  },
  swap_exchange: {
    label: 'Swap (Exchange)',
    icon: Repeat,
    bgColor: 'bg-cyan-50',
    textColor: 'text-cyan-700',
    borderColor: 'border-cyan-200',
  },
  backup_call: {
    label: 'Backup Call',
    icon: Shield,
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-700',
    borderColor: 'border-amber-200',
  },
  absence_coverage: {
    label: 'Absence Coverage',
    icon: User,
    bgColor: 'bg-red-50',
    textColor: 'text-red-700',
    borderColor: 'border-red-200',
  },
  temporary_proxy: {
    label: 'Temporary Proxy',
    icon: User,
    bgColor: 'bg-slate-50',
    textColor: 'text-slate-700',
    borderColor: 'border-slate-200',
  },
};

const STATUS_CONFIG: Record<CoverageStatus, {
  label: string;
  dotColor: string;
}> = {
  active: { label: 'Active', dotColor: 'bg-green-500' },
  scheduled: { label: 'Scheduled', dotColor: 'bg-blue-500' },
  completed: { label: 'Completed', dotColor: 'bg-slate-400' },
  cancelled: { label: 'Cancelled', dotColor: 'bg-red-500' },
};

/**
 * ProxyCoverageCard - Display a single coverage relationship
 *
 * Shows who is covering for whom with visual indicators for type and status.
 */
export function ProxyCoverageCard({ coverage, compact = false }: ProxyCoverageCardProps) {
  const typeConfig = COVERAGE_TYPE_CONFIG[coverage.coverageType];
  const statusConfig = STATUS_CONFIG[coverage.status];
  const TypeIcon = typeConfig.icon;

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Check if covering person is a placeholder
  const isPlaceholder = coverage.coveringPerson.name.startsWith('(');

  if (compact) {
    return (
      <div
        className={`flex items-center gap-3 p-3 rounded-lg border ${typeConfig.bgColor} ${typeConfig.borderColor}`}
      >
        <TypeIcon className={`w-4 h-4 ${typeConfig.textColor}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-sm">
            {isPlaceholder ? (
              <span className="text-slate-500 italic">{coverage.coveringPerson.name}</span>
            ) : (
              <span className="font-medium truncate">{coverage.coveringPerson.name}</span>
            )}
            <ArrowRight className="w-3 h-3 text-slate-400 flex-shrink-0" />
            <span className="truncate text-slate-600">{coverage.coveredPerson.name}</span>
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full ${statusConfig.dotColor}`} />
      </div>
    );
  }

  return (
    <div
      className={`p-4 rounded-xl border ${typeConfig.bgColor} ${typeConfig.borderColor} transition-all hover:shadow-md`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <TypeIcon className={`w-5 h-5 ${typeConfig.textColor}`} />
          <span className={`text-sm font-medium ${typeConfig.textColor}`}>
            {typeConfig.label}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${statusConfig.dotColor}`} />
          <span className="text-xs text-slate-500">{statusConfig.label}</span>
        </div>
      </div>

      {/* Coverage Relationship */}
      <div className="flex items-center gap-3 mb-3">
        {/* Covering Person */}
        <div className="flex-1 text-center">
          {isPlaceholder ? (
            <>
              <div className="w-10 h-10 mx-auto rounded-full bg-slate-200 flex items-center justify-center mb-1">
                <User className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-sm text-slate-500 italic">{coverage.coveringPerson.name}</p>
            </>
          ) : (
            <>
              <div className="w-10 h-10 mx-auto rounded-full bg-green-100 flex items-center justify-center mb-1">
                <UserCheck className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-sm font-medium">{coverage.coveringPerson.name}</p>
              {coverage.coveringPerson.pgyLevel && (
                <p className="text-xs text-slate-500">PGY-{coverage.coveringPerson.pgyLevel}</p>
              )}
            </>
          )}
        </div>

        {/* Arrow */}
        <div className="flex flex-col items-center">
          <ArrowRight className="w-5 h-5 text-slate-400" />
          <span className="text-[10px] text-slate-400 mt-0.5">covers for</span>
        </div>

        {/* Covered Person */}
        <div className="flex-1 text-center">
          <div className="w-10 h-10 mx-auto rounded-full bg-slate-100 flex items-center justify-center mb-1">
            <User className="w-5 h-5 text-slate-500" />
          </div>
          <p className="text-sm font-medium">{coverage.coveredPerson.name}</p>
          {coverage.coveredPerson.pgyLevel && (
            <p className="text-xs text-slate-500">PGY-{coverage.coveredPerson.pgyLevel}</p>
          )}
        </div>
      </div>

      {/* Details */}
      <div className="flex items-center gap-4 text-xs text-slate-500 border-t border-slate-200 pt-2 mt-2">
        <div className="flex items-center gap-1">
          <Calendar className="w-3.5 h-3.5" />
          <span>
            {formatDate(coverage.startDate)}
            {coverage.endDate && coverage.endDate !== coverage.startDate && (
              <> - {formatDate(coverage.endDate)}</>
            )}
          </span>
        </div>
        {coverage.location && (
          <div className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            <span>{coverage.location}</span>
          </div>
        )}
      </div>

      {/* Reason */}
      {coverage.reason && (
        <p className="text-xs text-slate-500 mt-2 italic">{coverage.reason}</p>
      )}
    </div>
  );
}
