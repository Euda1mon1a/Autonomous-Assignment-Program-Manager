'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Menu,
  X,
  Calendar,
  Users,
  FileText,
  CalendarOff,
  AlertTriangle,
  Settings,
  LogIn,
  HelpCircle,
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
  { href: '/people', label: 'People', icon: Users },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/compliance', label: 'Compliance', icon: AlertTriangle },
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()
  const { user, isAuthenticated } = useAuth()

  const isAdmin = user?.role === 'admin'

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || (item.adminOnly && isAdmin)
  )

  return (
    <>
      {/* Hamburger Button - visible on mobile only */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex md:hidden items-center justify-center p-2 rounded-md text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        aria-label="Open menu"
        aria-expanded={isOpen}
        aria-controls="mobile-nav-menu"
      >
        <Menu className="w-6 h-6" />
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Slide-out Drawer */}
      <div
        id="mobile-nav-menu"
        aria-hidden={!isOpen}
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-xl z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-blue-600" />
            <span className="font-bold text-gray-900">Scheduler</span>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 rounded-md text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
            aria-label="Close menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="p-4">
          <ul className="space-y-1">
            {filteredNavItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    aria-current={isActive ? 'page' : undefined}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.label}
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
                onClick={() => setIsOpen(false)}
                aria-current={pathname === '/login' ? 'page' : undefined}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  pathname === '/login'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <LogIn className="w-5 h-5" />
                Login
              </Link>
            </div>
          )}
        </nav>

        {/* User Info at Bottom (if authenticated) */}
        {isAuthenticated && user && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
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
      </div>
    </>
  )
}
