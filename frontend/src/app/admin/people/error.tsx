'use client';

import { UserCog } from 'lucide-react';
import { PageErrorBoundary } from '@/components/PageErrorBoundary';

export default function PeopleError({
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
      pageTitle="People Management"
      icon={UserCog}
    />
  );
}
