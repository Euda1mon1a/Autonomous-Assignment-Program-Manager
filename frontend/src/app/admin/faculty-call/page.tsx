/**
 * Faculty Call Administration Page (Legacy Route)
 *
 * This route has been consolidated into the unified Call Hub.
 * Redirects to /call-hub with the admin tab active.
 *
 * Note: URL query params could be added in future to preserve tab state:
 *   redirect('/call-hub?tab=admin')
 *
 * @deprecated Use /call-hub instead
 * @see /app/call-hub/page.tsx
 */
import { redirect } from 'next/navigation';

export default function FacultyCallAdminPage() {
  redirect('/call-hub');
}
