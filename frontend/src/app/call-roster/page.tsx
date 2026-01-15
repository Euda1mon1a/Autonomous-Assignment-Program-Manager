/**
 * Call Roster Page (Legacy Route)
 *
 * This route has been consolidated into the unified Call Hub.
 * Redirects to /call-hub with the roster tab active.
 *
 * @deprecated Use /call-hub instead
 * @see /app/call-hub/page.tsx
 */
import { redirect } from 'next/navigation';

export default function CallRosterPage() {
  redirect('/call-hub');
}
