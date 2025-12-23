'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Menu,
  X,
  Calendar,
  CalendarCheck,
  Users,
  FileText,
  CalendarOff,
  AlertTriangle,
  Settings,
  LogIn,
  HelpCircle,
<<<<<<< HEAD
  ArrowLeftRight,
  Phone,
  BarChart3,
  FileUp,
  ClipboardList,
=======
>>>>>>> origin/docs/session-14-summary
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/my-schedule', label: 'My Schedule', icon: CalendarCheck },
  { href: '/people', label: 'People', icon: Users },
<<<<<<< HEAD
  { href: '/swaps', label: 'Swaps', icon: ArrowLeftRight },
  { href: '/call-roster', label: 'Call Roster', icon: Phone },
  { href: '/daily-manifest', label: 'Daily Manifest', icon: ClipboardList },
  { href: '/heatmap', label: 'Heatmap', icon: BarChart3 },
  { href: '/conflicts', label: 'Conflicts', icon: AlertTriangle },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/import-export', label: 'Import/Export', icon: FileUp },
=======
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/compliance', label: 'Compliance', icon: AlertTriangle },
>>>>>>> origin/docs/session-14-summary
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)
  const [touchStart, setTouchStart] = useState<number | null>(null)
  const [touchEnd, setTouchEnd] = useState<number | null>(null)
  const pathname = usePathname()
  const { user, isAuthenticated } = useAuth()
  const drawerRef = useRef<HTMLDivElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const hamburgerButtonRef = useRef<HTMLButtonElement>(null)

  const isAdmin = user?.role === 'admin'

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || (item.adminOnly && isAdmin)
  )

  // Minimum swipe distance (in px) to trigger close
  const minSwipeDistance = 50

  // Handle touch gestures for swipe to close
  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null)
    setTouchStart(e.targetTouches[0].clientX)
  }

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX)
  }

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return

    const distance = touchStart - touchEnd
    const isLeftSwipe = distance > minSwipeDistance

    // Close drawer on left swipe
    if (isLeftSwipe) {
      setIsOpen(false)
    }

    setTouchStart(null)
    setTouchEnd(null)
  }

  // Handle keyboard navigation
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
        // Return focus to hamburger button
        hamburgerButtonRef.current?.focus()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Focus the close button when drawer opens
      closeButtonRef.current?.focus()
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen])

  // Close drawer on route change
  useEffect(() => {
    setIsOpen(false)
  }, [pathname])

  const handleOpen = useCallback(() => {
    setIsOpen(true)
  }, [])

  const handleClose = useCallback(() => {
    setIsOpen(false)
    // Return focus to hamburger button
    setTimeout(() => {
      hamburgerButtonRef.current?.focus()
    }, 100)
  }, [])

  return (
    <>
      {/* Hamburger Button - visible on mobile only, min 44x44px touch target */}
      <button
        ref={hamburgerButtonRef}
        onClick={handleOpen}
        className="flex md:hidden items-center justify-center min-w-[44px] min-h-[44px] p-2.5 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 active:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label="Open navigation menu"
        aria-expanded={isOpen}
        aria-controls="mobile-nav-menu"
        type="button"
      >
        <Menu className="w-6 h-6" aria-hidden="true" />
      </button>

      {/* Backdrop Overlay - semi-transparent with smooth fade */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity duration-300 ease-in-out"
          onClick={handleClose}
          aria-hidden="true"
          role="presentation"
        />
      )}

      {/* Slide-out Drawer from left with swipe support */}
      <aside
        ref={drawerRef}
        id="mobile-nav-menu"
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
        aria-hidden={!isOpen}
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
        className={`fixed top-0 left-0 h-full w-64 sm:w-72 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Drawer Header with close button (44x44px touch target) */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-white">
          <div className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-blue-600" aria-hidden="true" />
            <span className="font-bold text-gray-900">Scheduler</span>
          </div>
          <button
            ref={closeButtonRef}
            onClick={handleClose}
            className="min-w-[44px] min-h-[44px] p-2.5 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 active:bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            aria-label="Close navigation menu"
            type="button"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation Links - scrollable if needed */}
        <nav className="flex-1 overflow-y-auto overscroll-contain p-4" aria-label="Primary navigation">
          <ul className="space-y-1" role="list">
            {filteredNavItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={handleClose}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-3 min-h-[44px] px-3 py-2.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      isActive
                        ? 'bg-blue-100 text-blue-700 font-semibold'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 active:bg-gray-200'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                </li>
              )
            })}
          </ul>

          {/* Login Link for non-authenticated users */}
          {!isAuthenticated && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <Link
                href="/login"
                onClick={handleClose}
                aria-current={pathname === '/login' ? 'page' : undefined}
                className={`flex items-center gap-3 min-h-[44px] px-3 py-2.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  pathname === '/login'
                    ? 'bg-blue-100 text-blue-700 font-semibold'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 active:bg-gray-200'
                }`}
              >
                <LogIn className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                <span>Login</span>
              </Link>
            </div>
          )}
        </nav>

        {/* User Info at Bottom (if authenticated) */}
        {isAuthenticated && user && (
          <div className="shrink-0 p-4 border-t border-gray-200 bg-gradient-to-r from-gray-50 to-white">
            <div className="flex items-center gap-3 min-h-[56px]">
              <div
                className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center text-white text-sm font-semibold shadow-sm flex-shrink-0"
                aria-hidden="true"
              >
                {user.username
                  .split(' ')
                  .map((n) => n[0])
                  .join('')
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {user.username}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user.role}</p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
