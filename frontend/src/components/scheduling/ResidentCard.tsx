'use client';

import React from 'react';
import { User, Clock, AlertCircle } from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { Badge } from '../ui/Badge';

export interface ResidentCardProps {
  id: string;
  name: string;
  role: string;
  pgyLevel?: number;
  avatar?: string;
  currentRotation?: string;
  hoursThisWeek?: number;
  maxHours?: number;
  complianceStatus?: 'compliant' | 'warning' | 'violation';
  onClick?: () => void;
  className?: string;
}

/**
 * ResidentCard component for displaying resident information
 *
 * @example
 * ```tsx
 * <ResidentCard
 *   id="123"
 *   name="Dr. Jane Smith"
 *   role="RESIDENT"
 *   pgyLevel={2}
 *   currentRotation="Inpatient"
 *   hoursThisWeek={65}
 *   maxHours={80}
 *   complianceStatus="compliant"
 * />
 * ```
 */
export function ResidentCard({
  id,
  name,
  role,
  pgyLevel,
  avatar,
  currentRotation,
  hoursThisWeek,
  maxHours = 80,
  complianceStatus = 'compliant',
  onClick,
  className = '',
}: ResidentCardProps) {
  const complianceColors = {
    compliant: 'success',
    warning: 'warning',
    violation: 'danger',
  } as const;

  const hoursPercentage = hoursThisWeek ? (hoursThisWeek / maxHours) * 100 : 0;

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <Avatar
          src={avatar}
          name={name}
          size="md"
        />

        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate">
            {name}
          </h3>
          <p className="text-xs text-gray-600">
            {role}
            {pgyLevel && ` • PGY-${pgyLevel}`}
          </p>
        </div>

        {complianceStatus !== 'compliant' && (
          <AlertCircle className={`w-5 h-5 flex-shrink-0 ${
            complianceStatus === 'warning' ? 'text-amber-500' : 'text-red-500'
          }`} />
        )}
      </div>

      {/* Current Rotation */}
      {currentRotation && (
        <div className="mb-3">
          <Badge variant="primary" size="sm">
            {currentRotation}
          </Badge>
        </div>
      )}

      {/* Hours Tracking */}
      {hoursThisWeek !== undefined && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-600 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Hours this week
            </span>
            <span className={`font-medium ${
              complianceStatus === 'violation' ? 'text-red-600' :
              complianceStatus === 'warning' ? 'text-amber-600' :
              'text-gray-900'
            }`}>
              {hoursThisWeek} / {maxHours}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all ${
                hoursPercentage >= 100 ? 'bg-red-500' :
                hoursPercentage >= 80 ? 'bg-amber-500' :
                'bg-green-500'
              }`}
              style={{ width: `${Math.min(hoursPercentage, 100)}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact resident list item
 */
export function ResidentListItem({
  name,
  role,
  pgyLevel,
  avatar,
  onClick,
  className = '',
}: Pick<ResidentCardProps, 'name' | 'role' | 'pgyLevel' | 'avatar' | 'onClick' | 'className'>) {
  return (
    <div
      className={`flex items-center gap-3 p-2 rounded hover:bg-gray-50 ${
        onClick ? 'cursor-pointer' : ''
      } ${className}`}
      onClick={onClick}
    >
      <Avatar src={avatar} name={name} size="sm" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{name}</p>
        <p className="text-xs text-gray-600">
          {role}
          {pgyLevel && ` • PGY-${pgyLevel}`}
        </p>
      </div>
    </div>
  );
}
