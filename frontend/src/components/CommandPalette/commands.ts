/**
 * Command Palette Commands
 *
 * Defines all available commands for the command palette.
 */

import {
  LayoutDashboard,
  Calendar,
  CalendarDays,
  Users,
  UserCog,
  ArrowLeftRight,
  Clock,
  Map,
  AlertTriangle,
  Shield,
  Activity,
  CalendarOff,
  Upload,
  HelpCircle,
  Settings,
  FlaskConical,
  Database,
  Blocks,
  FileText,
  RefreshCw,
  type LucideIcon,
} from 'lucide-react';

export type CommandCategory = 'navigation' | 'admin' | 'actions' | 'search';

export interface Command {
  id: string;
  label: string;
  description?: string;
  icon: LucideIcon;
  category: CommandCategory;
  keywords?: string[];
  action: () => void;
  shortcut?: string;
}

/**
 * Create navigation commands with router
 */
export function createNavigationCommands(
  navigate: (path: string) => void
): Command[] {
  return [
    // Main Navigation
    {
      id: 'nav-dashboard',
      label: 'Dashboard',
      description: 'Go to main dashboard',
      icon: LayoutDashboard,
      category: 'navigation',
      keywords: ['home', 'main', 'overview'],
      shortcut: 'g d',
      action: () => navigate('/'),
    },
    {
      id: 'nav-schedule',
      label: 'Schedule',
      description: 'View master schedule',
      icon: Calendar,
      category: 'navigation',
      keywords: ['calendar', 'assignments', 'blocks'],
      shortcut: 'g s',
      action: () => navigate('/schedule'),
    },
    {
      id: 'nav-my-schedule',
      label: 'My Schedule',
      description: 'View your personal schedule',
      icon: CalendarDays,
      category: 'navigation',
      keywords: ['personal', 'my', 'assignments'],
      shortcut: 'g m',
      action: () => navigate('/my-schedule'),
    },
    {
      id: 'nav-people',
      label: 'People',
      description: 'Residents and faculty directory',
      icon: Users,
      category: 'navigation',
      keywords: ['residents', 'faculty', 'staff', 'directory'],
      shortcut: 'g p',
      action: () => navigate('/people'),
    },
    {
      id: 'nav-swaps',
      label: 'Swap Marketplace',
      description: 'Request and manage shift swaps',
      icon: ArrowLeftRight,
      category: 'navigation',
      keywords: ['trade', 'exchange', 'shift'],
      shortcut: 'g w',
      action: () => navigate('/swaps'),
    },
    {
      id: 'nav-call-hub',
      label: 'Call Hub',
      description: 'View call assignments',
      icon: Clock,
      category: 'navigation',
      keywords: ['on-call', 'night', 'weekend'],
      action: () => navigate('/call-hub'),
    },
    {
      id: 'nav-heatmap',
      label: 'Heatmap',
      description: 'Schedule coverage visualization',
      icon: Map,
      category: 'navigation',
      keywords: ['coverage', 'visualization', 'gaps'],
      action: () => navigate('/heatmap'),
    },
    {
      id: 'nav-conflicts',
      label: 'Conflicts',
      description: 'View scheduling conflicts',
      icon: AlertTriangle,
      category: 'navigation',
      keywords: ['issues', 'problems', 'errors'],
      action: () => navigate('/conflicts'),
    },
    {
      id: 'nav-compliance',
      label: 'Compliance',
      description: 'ACGME compliance dashboard',
      icon: Shield,
      category: 'navigation',
      keywords: ['acgme', 'hours', 'violations', 'duty'],
      action: () => navigate('/compliance'),
    },
    {
      id: 'nav-activities',
      label: 'Activities',
      description: 'Activity templates and assignments',
      icon: Activity,
      category: 'navigation',
      keywords: ['rotations', 'templates'],
      action: () => navigate('/activities'),
    },
    {
      id: 'nav-absences',
      label: 'Absences',
      description: 'Leave and absence calendar',
      icon: CalendarOff,
      category: 'navigation',
      keywords: ['leave', 'vacation', 'pto', 'sick'],
      shortcut: 'g a',
      action: () => navigate('/absences'),
    },

    // Admin Navigation
    {
      id: 'admin-labs',
      label: 'Labs',
      description: 'Experimental visualizations',
      icon: FlaskConical,
      category: 'admin',
      keywords: ['experiments', 'visualization', '3d'],
      action: () => navigate('/admin/labs'),
    },
    {
      id: 'admin-users',
      label: 'User Management',
      description: 'Manage user accounts',
      icon: UserCog,
      category: 'admin',
      keywords: ['accounts', 'permissions', 'roles'],
      action: () => navigate('/admin/users'),
    },
    {
      id: 'admin-blocks',
      label: 'Block Explorer',
      description: 'View and edit schedule blocks',
      icon: Blocks,
      category: 'admin',
      keywords: ['schedule', 'blocks', 'periods'],
      action: () => navigate('/admin/block-explorer'),
    },
    {
      id: 'admin-schema',
      label: 'Schema',
      description: 'Database schema viewer',
      icon: Database,
      category: 'admin',
      keywords: ['database', 'tables', 'models'],
      action: () => navigate('/admin/schema'),
    },
    {
      id: 'admin-audit',
      label: 'Audit Log',
      description: 'View system audit trail',
      icon: FileText,
      category: 'admin',
      keywords: ['logs', 'history', 'changes'],
      action: () => navigate('/admin/audit'),
    },
    {
      id: 'admin-import',
      label: 'Import/Export',
      description: 'Data import and export tools',
      icon: Upload,
      category: 'admin',
      keywords: ['upload', 'download', 'data'],
      action: () => navigate('/hub/import-export'),
    },
    {
      id: 'nav-settings',
      label: 'Settings',
      description: 'Application settings',
      icon: Settings,
      category: 'admin',
      keywords: ['preferences', 'config'],
      action: () => navigate('/settings'),
    },
    {
      id: 'nav-help',
      label: 'Help',
      description: 'Documentation and support',
      icon: HelpCircle,
      category: 'admin',
      keywords: ['docs', 'documentation', 'support'],
      action: () => navigate('/help'),
    },
  ];
}

/**
 * Create action commands
 */
export function createActionCommands(
  callbacks: {
    onRefresh?: () => void;
    onGoToToday?: () => void;
  }
): Command[] {
  return [
    {
      id: 'action-refresh',
      label: 'Refresh Data',
      description: 'Reload current page data',
      icon: RefreshCw,
      category: 'actions',
      keywords: ['reload', 'update', 'sync'],
      shortcut: 'Alt+r',
      action: () => {
        callbacks.onRefresh?.();
        window.dispatchEvent(new CustomEvent('keyboard-shortcut', { detail: { action: 'refresh' } }));
      },
    },
    {
      id: 'action-today',
      label: 'Go to Today',
      description: 'Navigate to current date',
      icon: Calendar,
      category: 'actions',
      keywords: ['now', 'current', 'date'],
      shortcut: 't',
      action: () => {
        callbacks.onGoToToday?.();
        window.dispatchEvent(new CustomEvent('keyboard-shortcut', { detail: { action: 'go-to-today' } }));
      },
    },
  ];
}

/**
 * Category labels for display
 */
export const CATEGORY_LABELS: Record<CommandCategory, string> = {
  navigation: 'Navigation',
  admin: 'Admin',
  actions: 'Actions',
  search: 'Search Results',
};
