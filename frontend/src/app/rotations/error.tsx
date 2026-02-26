'use client';

import { FileText } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function RotationsError({
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
      pageTitle="Rotations"
      icon={FileText}
      backPath="/"
    />
  );
}
