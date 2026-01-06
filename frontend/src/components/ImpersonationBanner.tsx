"use client";

/**
 * Impersonation Banner Component
 *
 * Displays a sticky warning banner when an admin is viewing the application
 * as another user. Provides clear visual indication and an easy way to
 * end the impersonation session.
 *
 * Features:
 * - Fixed position at top of viewport
 * - Cannot be dismissed or hidden
 * - Shows target user name and role
 * - Prominent "End Impersonation" button
 * - Amber/warning color scheme for visibility
 *
 * @module components/ImpersonationBanner
 */
import { useImpersonation } from "@/hooks/useImpersonation";
import { useRouter } from "next/navigation";
import { AlertTriangle, Eye, LogOut, Loader2 } from "lucide-react";
import { USER_ROLE_LABELS } from "@/types/admin-users";
import type { UserRole } from "@/types/admin-users";

/**
 * Format user's display name
 */
function formatUserName(user: {
  firstName: string;
  lastName: string;
  username: string;
}): string {
  if (user.firstName && user.lastName) {
    return `${user.firstName} ${user.lastName}`;
  }
  return user.username;
}

/**
 * Get role display label
 */
function getRoleLabel(role: string): string {
  return USER_ROLE_LABELS[role as UserRole] || role;
}

/**
 * Impersonation Banner Component
 *
 * Only renders when admin is actively impersonating another user.
 * Provides a persistent visual warning and controls to end the session.
 */
export function ImpersonationBanner() {
  const router = useRouter();
  const { isImpersonating, targetUser, originalUser, endImpersonation, isEnding } =
    useImpersonation();

  // Don't render if not impersonating
  if (!isImpersonating || !targetUser) {
    return null;
  }

  const handleEndImpersonation = () => {
    endImpersonation.mutate(undefined, {
      onSuccess: () => {
        // Redirect to admin users page after ending impersonation
        router.push("/admin/users");
      },
      onError: (error) => {
        console.error("Failed to end impersonation:", error);
        // Still try to redirect even on error
        router.push("/admin/users");
      },
    });
  };

  return (
    <div
      role="alert"
      aria-live="polite"
      className="fixed top-0 left-0 right-0 z-[100] bg-amber-500 shadow-lg"
    >
      <div className="max-w-7xl mx-auto px-4 py-2.5">
        <div className="flex items-center justify-between gap-4">
          {/* Left: Warning icon and message */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0 flex items-center gap-2">
              <AlertTriangle
                className="w-5 h-5 text-amber-950"
                aria-hidden="true"
              />
              <Eye className="w-5 h-5 text-amber-950" aria-hidden="true" />
            </div>

            <div className="flex items-center gap-2 min-w-0">
              <span className="text-sm font-semibold text-amber-950 whitespace-nowrap">
                Viewing as:
              </span>
              <span className="text-sm font-bold text-amber-950 truncate">
                {formatUserName(targetUser)}
              </span>
              <span className="px-2 py-0.5 text-xs font-medium bg-amber-600/30 text-amber-950 rounded-full whitespace-nowrap">
                {getRoleLabel(targetUser.role)}
              </span>
            </div>
          </div>

          {/* Center: Original user info (visible on larger screens) */}
          {originalUser && (
            <div className="hidden md:flex items-center gap-2 text-xs text-amber-900">
              <span>Logged in as:</span>
              <span className="font-medium">{formatUserName(originalUser)}</span>
            </div>
          )}

          {/* Right: End impersonation button */}
          <button
            onClick={handleEndImpersonation}
            disabled={isEnding}
            className="flex-shrink-0 flex items-center gap-2 px-4 py-1.5 text-sm font-semibold bg-amber-950 text-amber-50 rounded-lg hover:bg-amber-900 focus:outline-none focus:ring-2 focus:ring-amber-950 focus:ring-offset-2 focus:ring-offset-amber-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="End impersonation and return to your account"
          >
            {isEnding ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span className="hidden sm:inline">Ending...</span>
              </>
            ) : (
              <>
                <LogOut className="w-4 h-4" aria-hidden="true" />
                <span className="hidden sm:inline">End Impersonation</span>
                <span className="sm:hidden">End</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Spacer component to offset content when impersonation banner is visible
 *
 * Use this in layouts to prevent content from being hidden behind the
 * fixed-position banner.
 */
export function ImpersonationBannerSpacer() {
  const { isImpersonating, targetUser } = useImpersonation();

  if (!isImpersonating || !targetUser) {
    return null;
  }

  // Height matches the banner height (py-2.5 = ~44px)
  return <div className="h-[44px]" aria-hidden="true" />;
}
