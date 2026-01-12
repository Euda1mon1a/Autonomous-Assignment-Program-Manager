'use client';

/**
 * Legacy Admin Page
 *
 * Provides access to old admin routes during the transition to unified hub architecture.
 * These routes are deprecated but maintained for backward compatibility.
 */

import Link from 'next/link';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import {
  ArrowLeftRight,
  Award,
  Building2,
  CalendarDays,
  CheckCircle,
  Database,
  FileText,
  FileUp,
  PhoneCall,
  Stethoscope,
  UserCog,
  ExternalLink,
} from 'lucide-react';

interface LegacyRoute {
  path: string;
  label: string;
  description: string;
  icon: React.ElementType;
  replacement?: string;
}

const LEGACY_ROUTES: LegacyRoute[] = [
  {
    path: '/admin/swaps',
    label: 'Swaps Admin',
    description: 'Legacy swap management interface',
    icon: ArrowLeftRight,
    replacement: '/swaps',
  },
  {
    path: '/admin/people',
    label: 'People Admin',
    description: 'Legacy user and personnel management',
    icon: UserCog,
    replacement: '/people',
  },
  {
    path: '/admin/faculty-call',
    label: 'Faculty Call',
    description: 'Legacy faculty call schedule management',
    icon: PhoneCall,
    replacement: '/call-hub',
  },
  {
    path: '/admin/import',
    label: 'Import',
    description: 'Legacy data import interface',
    icon: Database,
    replacement: '/hub/import-export',
  },
  {
    path: '/admin/block-import',
    label: 'Block Import',
    description: 'Import block schedules',
    icon: FileUp,
  },
  {
    path: '/admin/fmit/import',
    label: 'FMIT Import',
    description: 'FMIT-specific data import',
    icon: Building2,
  },
  {
    path: '/admin/faculty-activities',
    label: 'Faculty Activities',
    description: 'Faculty activity template management',
    icon: CalendarDays,
    replacement: '/activities',
  },
  {
    path: '/admin/compliance',
    label: 'Compliance Admin',
    description: 'Legacy compliance management',
    icon: CheckCircle,
    replacement: '/compliance',
  },
  {
    path: '/admin/procedures',
    label: 'Procedures',
    description: 'Procedure and credential management',
    icon: Stethoscope,
  },
  {
    path: '/admin/credentials',
    label: 'Credentials',
    description: 'Credential and certification management',
    icon: Award,
  },
  {
    path: '/admin/rotations',
    label: 'Rotations',
    description: 'Rotation template configuration',
    icon: CalendarDays,
  },
  {
    path: '/admin/audit',
    label: 'Audit Log',
    description: 'System audit trail',
    icon: FileText,
  },
];

export default function LegacyAdminPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Legacy Admin</h1>
            <p className="text-gray-600 mt-2">
              Access to deprecated admin routes. These pages are maintained for backward
              compatibility during the transition to the unified hub architecture.
            </p>
            <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-amber-800 text-sm">
                <strong>Note:</strong> Some routes have been consolidated into new unified hubs.
                Look for the &quot;New Location&quot; link to use the updated interface.
              </p>
            </div>
          </div>

          <div className="grid gap-4">
            {LEGACY_ROUTES.map((route) => {
              const Icon = route.icon;
              return (
                <div
                  key={route.path}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-gray-100 rounded-lg">
                        <Icon className="w-5 h-5 text-gray-600" />
                      </div>
                      <div>
                        <Link
                          href={route.path}
                          className="font-medium text-gray-900 hover:text-blue-600 flex items-center gap-1"
                        >
                          {route.label}
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                        <p className="text-sm text-gray-500 mt-1">{route.description}</p>
                        <p className="text-xs text-gray-400 mt-1 font-mono">{route.path}</p>
                      </div>
                    </div>
                    {route.replacement && (
                      <Link
                        href={route.replacement}
                        className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200 transition-colors"
                      >
                        New: {route.replacement}
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
