'use client';

import { ArrowLeftRight } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function SwapsError({
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
      pageTitle="Force Swap"
      icon={ArrowLeftRight}
    />
  );
}
