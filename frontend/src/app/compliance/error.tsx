'use client';

import { CheckCircle } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function ComplianceError({
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
      pageTitle="Compliance"
      icon={CheckCircle}
      backPath="/"
    />
  );
}
