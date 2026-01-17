'use client';

import { ProtectedRoute } from '@/components/ProtectedRoute';
import ResilienceOverseerDashboard from '@/components/scheduling/ResilienceOverseerDashboard';

export default function ResilienceOverseerPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <ResilienceOverseerDashboard />
    </ProtectedRoute>
  );
}
