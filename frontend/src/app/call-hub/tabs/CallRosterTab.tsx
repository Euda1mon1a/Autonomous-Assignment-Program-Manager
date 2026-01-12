'use client';

/**
 * CallRosterTab Component
 *
 * Read-only call roster view for Tier 0 users (and all higher tiers).
 * Wraps the existing CallRoster feature component with minimal styling
 * to fit the Call Hub layout.
 *
 * Features:
 * - Month view calendar with color-coded roles
 * - List view for detailed information
 * - Today's on-call highlight section
 * - Role filtering
 *
 * This tab is always green (read-only) regardless of user tier.
 */

import { CallRoster } from '@/features/call-roster';

export function CallRosterTab() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <CallRoster />
    </div>
  );
}
