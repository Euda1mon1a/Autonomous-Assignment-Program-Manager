'use client';

import { ClipboardList } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function DailyManifestError({
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
      pageTitle="Daily Manifest"
      icon={ClipboardList}
      backPath="/"
    />
  );
}
