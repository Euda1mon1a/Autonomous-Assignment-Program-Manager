'use client';

/**
 * SummaryCard Component
 *
 * Displays a metric card with an icon, title, and value.
 * Used in the dashboard to show key statistics like next assignment,
 * workload, and pending swap counts.
 */

import { ReactNode } from 'react';
import { LucideIcon } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface SummaryCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
  description?: string;
  isLoading?: boolean;
}

// ============================================================================
// Component
// ============================================================================

export function SummaryCard({
  title,
  value,
  icon: Icon,
  iconColor = 'text-blue-600',
  bgColor = 'bg-blue-50',
  description,
  isLoading = false,
}: SummaryCardProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4 md:p-6 animate-pulse">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="h-8 bg-gray-200 rounded w-32"></div>
          </div>
          <div className={`${bgColor} rounded-lg p-3`}>
            <div className="w-6 h-6 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 md:p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-600 mb-1 truncate">{title}</p>
          <p className="text-2xl md:text-3xl font-bold text-gray-900 mb-1 truncate">
            {value === null || value === undefined ? '-' : value}
          </p>
          {description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{description}</p>
          )}
        </div>
        <div className={`${bgColor} rounded-lg p-3 flex-shrink-0 ml-4`}>
          <Icon className={`w-6 h-6 ${iconColor}`} />
        </div>
      </div>
    </div>
  );
}
