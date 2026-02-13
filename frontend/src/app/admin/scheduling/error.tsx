'use client';

import { Beaker } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function SchedulingError({
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
      pageTitle="Scheduling Laboratory"
      icon={Beaker}
    />
  );
}
