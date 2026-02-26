'use client';

import { CalendarCheck } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function MyScheduleError({
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
      pageTitle="My Schedule"
      icon={CalendarCheck}
      backPath="/"
    />
  );
}
