'use client';

import { Activity } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function WellnessError({
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
      pageTitle="Wellness"
      icon={Activity}
      backPath="/"
    />
  );
}
