/**
 * Call Hub Page
 *
 * Unified call management hub consolidating:
 * - Call Roster (read-only view for all users)
 * - Faculty Call Admin (admin panel for Tier 1/2 users)
 *
 * Uses RiskBar to indicate permission level:
 * - Tier 0 (green): Read-only roster view
 * - Tier 1/2 (amber/red): Edit controls enabled
 *
 * @see docs/reviews/2026-01-11-frontend-consolidation-map.md
 */
import { Suspense } from 'react';
import { CallHubClient } from './CallHubClient';
import { LoadingSpinner } from '@/components/LoadingSpinner';

export const metadata = {
  title: 'Call Hub | Residency Scheduler',
  description: 'View and manage faculty call schedules and on-call roster',
};

/**
 * Server Component for Call Hub page.
 *
 * The server component handles initial data loading and renders
 * the client component which manages interactive state.
 */
export default function CallHubPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner />
        </div>
      }
    >
      <CallHubClient />
    </Suspense>
  );
}
