'use client';

import { Phone } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function CallHubError({
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
      pageTitle="Call Hub"
      icon={Phone}
      backPath="/"
    />
  );
}
