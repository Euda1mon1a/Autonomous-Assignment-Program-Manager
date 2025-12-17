'use client';

import { Users, UserCheck, GraduationCap } from 'lucide-react';

// ============================================================================
// Props
// ============================================================================

interface StaffingSummaryProps {
  total: number;
  residents: number;
  faculty: number;
  fellows?: number;
  compact?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function StaffingSummary({
  total,
  residents,
  faculty,
  fellows = 0,
  compact = false,
}: StaffingSummaryProps) {
  if (compact) {
    return (
      <div className="flex items-center gap-2 text-xs">
        <span className="flex items-center gap-1 text-gray-600">
          <Users className="w-3.5 h-3.5" />
          {total}
        </span>
        <span className="text-gray-300">|</span>
        <span className="text-blue-600">{residents}R</span>
        <span className="text-purple-600">{faculty}F</span>
        {fellows > 0 && <span className="text-green-600">{fellows}Fe</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg">
        <Users className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">{total}</span>
        <span className="text-xs text-gray-500">Total</span>
      </div>

      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 rounded-lg">
        <GraduationCap className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-700">{residents}</span>
        <span className="text-xs text-blue-600">Residents</span>
      </div>

      <div className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 rounded-lg">
        <UserCheck className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-medium text-purple-700">{faculty}</span>
        <span className="text-xs text-purple-600">Faculty</span>
      </div>

      {fellows > 0 && (
        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 rounded-lg">
          <UserCheck className="w-4 h-4 text-green-600" />
          <span className="text-sm font-medium text-green-700">{fellows}</span>
          <span className="text-xs text-green-600">Fellows</span>
        </div>
      )}
    </div>
  );
}
