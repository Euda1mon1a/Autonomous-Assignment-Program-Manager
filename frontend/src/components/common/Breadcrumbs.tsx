'use client'

import { useMemo } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  href: string
  isCurrentPage?: boolean
}

// Map of path segments to readable labels
const PATH_LABELS: Record<string, string> = {
  schedule: 'Schedule',
  'my-schedule': 'My Schedule',
  people: 'People',
  absences: 'Absences',
  holidays: 'Holidays',
  rotations: 'Rotations',
  admin: 'Admin',
  scheduling: 'Scheduling Lab',
  settings: 'Settings',
  analytics: 'Analytics',
  resilience: 'Resilience',
  'swap-marketplace': 'Swap Marketplace',
  audit: 'Audit Log',
  conflicts: 'Conflicts',
  'game-theory': 'Game Theory',
  '3d-schedule': '3D Schedule',
}

interface BreadcrumbsProps {
  /** Custom breadcrumb items (overrides auto-generated) */
  items?: BreadcrumbItem[]
  /** Show home icon as first item */
  showHome?: boolean
  /** Additional CSS classes */
  className?: string
}

/**
 * Breadcrumbs Component
 *
 * Automatically generates breadcrumb navigation based on the current route.
 * Can also accept custom breadcrumb items for more control.
 */
export function Breadcrumbs({
  items,
  showHome = true,
  className = '',
}: BreadcrumbsProps) {
  const pathname = usePathname()

  // Auto-generate breadcrumbs from pathname
  const breadcrumbs = useMemo<BreadcrumbItem[]>(() => {
    if (items) return items

    const segments = pathname.split('/').filter(Boolean)
    const crumbs: BreadcrumbItem[] = []

    let currentPath = ''
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`

      // Skip dynamic segments (e.g., IDs)
      if (segment.match(/^[0-9a-f-]{36}$/i)) {
        // UUID pattern - skip or label as "Details"
        crumbs.push({
          label: 'Details',
          href: currentPath,
          isCurrentPage: index === segments.length - 1,
        })
        return
      }

      const label = PATH_LABELS[segment] || formatSegmentLabel(segment)

      crumbs.push({
        label,
        href: currentPath,
        isCurrentPage: index === segments.length - 1,
      })
    })

    return crumbs
  }, [pathname, items])

  // Don't render on home page
  if (pathname === '/' && !items) {
    return null
  }

  // Don't render if only one crumb (current page)
  if (breadcrumbs.length <= 1 && !showHome) {
    return null
  }

  return (
    <nav
      aria-label="Breadcrumb"
      className={`flex items-center text-sm ${className}`}
    >
      <ol className="flex items-center gap-1 flex-wrap">
        {/* Home link */}
        {showHome && (
          <li className="flex items-center">
            <Link
              href="/"
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors p-1 -ml-1 rounded hover:bg-gray-100"
              aria-label="Home"
            >
              <Home className="w-4 h-4" />
              <span className="sr-only sm:not-sr-only sm:ml-1">Dashboard</span>
            </Link>
            {breadcrumbs.length > 0 && (
              <ChevronRight className="w-4 h-4 text-gray-400 mx-1" aria-hidden="true" />
            )}
          </li>
        )}

        {/* Breadcrumb items */}
        {breadcrumbs.map((crumb, index) => (
          <li key={crumb.href} className="flex items-center">
            {crumb.isCurrentPage ? (
              <span
                className="text-gray-900 font-medium"
                aria-current="page"
              >
                {crumb.label}
              </span>
            ) : (
              <>
                <Link
                  href={crumb.href}
                  className="text-gray-500 hover:text-gray-700 transition-colors hover:underline"
                >
                  {crumb.label}
                </Link>
                <ChevronRight
                  className="w-4 h-4 text-gray-400 mx-1"
                  aria-hidden="true"
                />
              </>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

/**
 * Format a URL segment into a readable label
 */
function formatSegmentLabel(segment: string): string {
  return segment
    .replace(/-/g, ' ')
    .replace(/_/g, ' ')
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Breadcrumb wrapper with consistent styling for pages
 */
export function PageBreadcrumbs({ className = '' }: { className?: string }) {
  return (
    <div className={`mb-4 ${className}`}>
      <Breadcrumbs />
    </div>
  )
}

/**
 * Custom breadcrumb builder for complex navigation
 */
export function useBreadcrumbs(customItems?: BreadcrumbItem[]) {
  const pathname = usePathname()

  return useMemo(() => {
    if (customItems) return customItems

    const segments = pathname.split('/').filter(Boolean)
    const crumbs: BreadcrumbItem[] = []

    let currentPath = ''
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`

      if (segment.match(/^[0-9a-f-]{36}$/i)) {
        crumbs.push({
          label: 'Details',
          href: currentPath,
          isCurrentPage: index === segments.length - 1,
        })
        return
      }

      const label = PATH_LABELS[segment] || formatSegmentLabel(segment)

      crumbs.push({
        label,
        href: currentPath,
        isCurrentPage: index === segments.length - 1,
      })
    })

    return crumbs
  }, [pathname, customItems])
}
