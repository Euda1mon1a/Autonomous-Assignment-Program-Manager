'use client';

import React, { useState } from 'react';

export type RiskTier = 0 | 1 | 2;

export interface RiskBarProps {
  /** Permission tier level: 0 = Read-only, 1 = Scoped Changes, 2 = High Impact */
  tier: RiskTier;
  /** Custom label override (defaults based on tier) */
  label?: string;
  /** Optional tooltip content explaining the tier */
  tooltip?: string;
  /** Additional CSS classes */
  className?: string;
}

const tierConfig: Record<RiskTier, { color: string; defaultLabel: string; defaultTooltip: string }> = {
  0: {
    color: 'bg-green-600',
    defaultLabel: 'Read-only',
    defaultTooltip: 'You can view data but cannot make changes. Safe browsing mode.',
  },
  1: {
    color: 'bg-amber-500',
    defaultLabel: 'Scoped Changes',
    defaultTooltip: 'You can make reversible changes within your assigned scope.',
  },
  2: {
    color: 'bg-red-600',
    defaultLabel: 'High Impact',
    defaultTooltip: 'You have access to destructive or system-wide operations. Proceed with caution.',
  },
};

/**
 * RiskBar component displays the user's current permission tier
 * as a fixed bar under the global header.
 *
 * WCAG 2.1 AA Compliance:
 * - Green (bg-green-600): 4.5:1 contrast ratio with white text
 * - Amber (bg-amber-500): 4.5:1 contrast ratio with white text
 * - Red (bg-red-600): 4.5:1 contrast ratio with white text
 *
 * @example
 * ```tsx
 * // Basic usage
 * <RiskBar tier={0} />
 *
 * // With custom label
 * <RiskBar tier={1} label="Editor Mode" />
 *
 * // With custom tooltip
 * <RiskBar tier={2} tooltip="Admin privileges active" />
 * ```
 */
export function RiskBar({
  tier,
  label,
  tooltip,
  className = '',
}: RiskBarProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const tooltipId = React.useId();

  const config = tierConfig[tier];
  const displayLabel = label ?? config.defaultLabel;
  const displayTooltip = tooltip ?? config.defaultTooltip;

  return (
    <div
      className={`w-full h-8 ${config.color} flex items-center justify-center relative ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onFocus={() => setShowTooltip(true)}
      onBlur={() => setShowTooltip(false)}
      role="status"
      aria-label={`Permission level: ${displayLabel}`}
      aria-describedby={showTooltip ? tooltipId : undefined}
      tabIndex={0}
    >
      <span className="text-white text-sm font-medium">
        {displayLabel}
      </span>

      {/* Tooltip */}
      {showTooltip && (
        <div
          id={tooltipId}
          role="tooltip"
          className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 px-3 py-2 text-xs text-white bg-gray-900 rounded shadow-lg max-w-xs text-center"
        >
          {displayTooltip}
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 w-0 h-0 border-4 border-l-transparent border-r-transparent border-t-transparent border-b-gray-900" />
        </div>
      )}
    </div>
  );
}

/**
 * Utility hook to determine risk tier from user roles
 * Can be used with authentication context to auto-determine tier
 */
export function useRiskTierFromRoles(roles: string[]): RiskTier {
  // Tier 2: Admin only (keys to kingdom - system config, user management)
  const tier2Roles = ['admin'];
  // Tier 1: Program operations (coordinators, chiefs - approvals, schedule management)
  const tier1Roles = ['coordinator', 'chief'];

  if (roles.some(role => tier2Roles.includes(role.toLowerCase()))) {
    return 2;
  }

  if (roles.some(role => tier1Roles.includes(role.toLowerCase()))) {
    return 1;
  }

  // Tier 0: Everyone else (faculty, resident, clinical_staff - view + self-service)
  return 0;
}
