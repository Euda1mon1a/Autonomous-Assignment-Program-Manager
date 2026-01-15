'use client';

/**
 * Admin Faculty Activities Page - Redirect
 *
 * This page has been consolidated into the Activities Hub.
 * Redirects to /activities with the faculty-templates tab selected.
 *
 * @deprecated Use /activities?tab=faculty-templates instead
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function AdminFacultyActivitiesPage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the Activities Hub with the faculty-templates tab
    router.replace('/activities?tab=faculty-templates');
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
        <p className="text-gray-600">Redirecting to Activities Hub...</p>
      </div>
    </div>
  );
}
