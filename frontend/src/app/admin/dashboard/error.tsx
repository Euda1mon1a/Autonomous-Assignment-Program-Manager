'use client';

import { LayoutDashboard } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <PageErrorBoundary
      error={error}
      reset={reset}
      pageTitle="Dashboard"
      icon={LayoutDashboard}
    />
  );
}
