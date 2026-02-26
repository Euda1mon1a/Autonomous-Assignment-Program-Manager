'use client';

import { CalendarOff } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function AbsencesError({
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
      pageTitle="Absences"
      icon={CalendarOff}
      backPath="/"
    />
  );
}
