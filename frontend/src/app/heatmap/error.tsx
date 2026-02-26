'use client';

import { BarChart3 } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function HeatmapError({
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
      pageTitle="Heatmap"
      icon={BarChart3}
      backPath="/"
    />
  );
}
