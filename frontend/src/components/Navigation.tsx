'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Calendar,
  CalendarCheck,
  CalendarDays,
  Users,
  FileText,
  CalendarOff,
  AlertTriangle,
  Settings,
  LogIn,
  HelpCircle,
  ArrowLeftRight,
  Phone,
  BarChart3,
  FileUp,
  ClipboardList,
  Beaker,
  Activity,
  Shield,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { MobileNav } from './MobileNav'
import { UserMenu } from './UserMenu'

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { href: '/', label: 'Dashboard', icon: Calendar },
  { href: '/my-schedule', label: 'My Schedule', icon: CalendarCheck },
  { href: '/schedule', label: 'Schedule', icon: CalendarDays },
  { href: '/people', label: 'People', icon: Users },
  { href: '/swaps', label: 'Swaps', icon: ArrowLeftRight },
  { href: '/call-roster', label: 'Call Roster', icon: Phone },
  { href: '/daily-manifest', label: 'Manifest', icon: ClipboardList },
  { href: '/heatmap', label: 'Heatmap', icon: BarChart3 },
  { href: '/conflicts', label: 'Conflicts', icon: AlertTriangle },
  { href: '/templates', label: 'Templates', icon: FileText },
  { href: '/absences', label: 'Absences', icon: CalendarOff },
  { href: '/import-export', label: 'Import/Export', icon: FileUp },
  { href: '/help', label: 'Help', icon: HelpCircle },
  { href: '/admin/scheduling', label: 'Lab', icon: Beaker, adminOnly: true },
  { href: '/admin/users', label: 'Users', icon: Shield, adminOnly: true },
  { href: '/admin/audit', label: 'Audit', icon: FileText, adminOnly: true },
  { href: '/admin/health', label: 'Health', icon: Activity, adminOnly: true },
  { href: '/settings', label: 'Settings', icon: Settings, adminOnly: true },
]

export function Navigation() {
  const pathname = usePathname()
  const { user, isAuthenticated, isLoading } = useAuth()

  const isAdmin = user?.role === 'admin'

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || (item.adminOnly && isAdmin)
  )

  return (
    <>
      {/* Skip to main content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-blue-600 focus:text-white focus:px-4 focus:py-2 focus:rounded-md focus:shadow-lg"
      >
        Skip to main content
      </a>

      <nav className="bg-white shadow-sm" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Left Side: Mobile Menu + Logo */}
            <div className="flex items-center gap-2">
            {/* Mobile Hamburger */}
            <MobileNav />

            {/* Logo */}
            <Link href="/" className="flex items-center gap-2" aria-label="Residency Scheduler home">
              <Calendar className="w-8 h-8 text-blue-600" aria-hidden="true" />
              <span className="font-bold text-xl text-gray-900 hidden sm:block">
                Residency Scheduler
              </span>
              <span className="font-bold text-xl text-gray-900 sm:hidden">
                Scheduler
              </span>
            </Link>
          </div>

          {/* Desktop Navigation Links - hidden on mobile */}
          <div className="hidden md:flex items-center gap-1">
            {filteredNavItems.map((item) => {
              const isActive = pathname === item.href
              const Icon = item.icon

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  aria-label={item.label}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <Icon className="w-4 h-4" aria-hidden="true" />
                  {item.label}
                </Link>
              )
            })}
          </div>

          {/* Right Side: Auth Section */}
          <div className="flex items-center">
            <div className="md:ml-4 md:pl-4 md:border-l md:border-gray-200 flex items-center gap-3">
              {isLoading ? (
                <span className="text-sm text-gray-400">...</span>
              ) : isAuthenticated && user ? (
                <UserMenu />
              ) : (
                <Link
                  href="/login"
                  aria-current={pathname === '/login' ? 'page' : undefined}
                  aria-label="Login to your account"
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    pathname === '/login'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <LogIn className="w-4 h-4" aria-hidden="true" />
                  <span className="hidden sm:inline">Login</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
    </>
  )
}
