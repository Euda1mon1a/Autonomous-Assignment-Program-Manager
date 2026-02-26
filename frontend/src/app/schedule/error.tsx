'use client';

import { CalendarDays } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function ScheduleError({
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
      pageTitle="Schedule"
      icon={CalendarDays}
      backPath="/"
    />
  );
}
