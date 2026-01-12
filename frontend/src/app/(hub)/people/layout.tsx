import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

/**
 * People Hub Layout (Server Component)
 *
 * Provides server-side authentication gating for the People Hub.
 * This layout runs on the server and checks for authentication
 * before rendering the client-side page components.
 *
 * Security: Uses httpOnly cookies for authentication verification.
 * The actual permission checks happen client-side with useAuth.
 */
export default async function PeopleHubLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Server-side auth check using httpOnly cookies
  const cookieStore = await cookies();
  const authToken = cookieStore.get('access_token');

  // Redirect to login if no auth token exists
  if (!authToken?.value) {
    redirect('/login?redirect=/people');
  }

  return <>{children}</>;
}
