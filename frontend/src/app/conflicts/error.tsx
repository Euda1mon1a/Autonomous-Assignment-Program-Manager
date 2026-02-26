'use client';

import { AlertTriangle } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function ConflictsError({
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
      pageTitle="Conflicts"
      icon={AlertTriangle}
      backPath="/"
    />
  );
}
