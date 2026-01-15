'use client';

/**
 * Admin Compliance Page - Redirect to Unified Compliance Hub
 *
 * This page has been consolidated into the unified Compliance Hub at /compliance.
 * This redirect ensures any bookmarks or links to the old admin route continue to work.
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function AdminComplianceRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the unified compliance hub, defaulting to away-from-program tab
    // since that was the original admin compliance page content
    router.replace('/compliance?tab=away-from-program');
  }, [router]);

  return (
    <div
      className="flex flex-col items-center justify-center min-h-[60vh]"
      role="status"
      aria-live="polite"
    >
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" aria-hidden="true" />
      <p className="mt-3 text-gray-600">
        Redirecting to Compliance Hub...
      </p>
    </div>
  );
}
