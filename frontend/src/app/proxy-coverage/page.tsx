'use client';

import { ProxyCoverageDashboard } from '@/features/proxy-coverage';
import { ProtectedRoute } from '@/components/ProtectedRoute';

export default function ProxyCoveragePage() {
  return (
    <ProtectedRoute>
      <ProxyCoverageDashboard />
    </ProtectedRoute>
  );
}
