'use client';

/**
 * Admin Audit Log Page
 *
 * Administrative interface for viewing system audit logs.
 * Provides filtering, searching, and export capabilities.
 */
import { useState, useMemo } from 'react';
import {
  FileText,
  Search,
  Filter,
  Download,
  Calendar,
  Clock,
  User,
  AlertTriangle,
  Info,
  XCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  BarChart3,
  List,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import type {
  AuditEntry,
  AuditCategory,
  AuditSeverity,
  AuditAction,
  AuditViewMode,
  AuditFilters,
  AuditStats,
} from '@/types/admin-audit';
import {
  AUDIT_CATEGORY_LABELS,
  AUDIT_CATEGORY_COLORS,
  AUDIT_SEVERITY_COLORS,
} from '@/types/admin-audit';

// ============================================================================
// Mock Data
// ============================================================================

const MOCK_ENTRIES: AuditEntry[] = [
  {
    id: '1',
    timestamp: '2024-12-23T10:30:00Z',
    category: 'authentication',
    action: 'login',
    severity: 'info',
    userId: 'user-1',
    userName: 'Admin User',
    ipAddress: '192.168.1.100',
    success: true,
    details: { method: 'password', mfa: true },
  },
  {
    id: '2',
    timestamp: '2024-12-23T10:25:00Z',
    category: 'schedule',
    action: 'schedule_generated',
    severity: 'info',
    userId: 'user-1',
    userName: 'Admin User',
    targetType: 'Schedule',
    targetName: 'December 2024',
    success: true,
    details: { algorithm: 'hybrid', duration_ms: 12500 },
  },
  {
    id: '3',
    timestamp: '2024-12-23T10:20:00Z',
    category: 'user',
    action: 'user_created',
    severity: 'info',
    userId: 'user-1',
    userName: 'Admin User',
    targetId: 'user-5',
    targetType: 'User',
    targetName: 'New User',
    success: true,
  },
  {
    id: '4',
    timestamp: '2024-12-23T10:15:00Z',
    category: 'authentication',
    action: 'login_failed',
    severity: 'warning',
    userName: 'unknown@example.mil',
    ipAddress: '10.0.0.55',
    success: false,
    errorMessage: 'Invalid credentials',
    details: { attempts: 3 },
  },
  {
    id: '5',
    timestamp: '2024-12-23T10:10:00Z',
    category: 'swap',
    action: 'swap_approved',
    severity: 'info',
    userId: 'user-2',
    userName: 'Coordinator',
    targetId: 'swap-123',
    targetType: 'Swap',
    success: true,
  },
  {
    id: '6',
    timestamp: '2024-12-23T10:05:00Z',
    category: 'system',
    action: 'settings_updated',
    severity: 'warning',
    userId: 'user-1',
    userName: 'Admin User',
    targetType: 'Settings',
    targetName: 'Schedule Configuration',
    success: true,
    oldValue: { maxHoursPerWeek: 80 },
    newValue: { maxHoursPerWeek: 70 },
  },
  {
    id: '7',
    timestamp: '2024-12-23T09:55:00Z',
    category: 'authorization',
    action: 'login_failed',
    severity: 'error',
    userId: 'user-6',
    userName: 'Locked Account',
    ipAddress: '192.168.1.200',
    success: false,
    errorMessage: 'Account is locked',
  },
  {
    id: '8',
    timestamp: '2024-12-23T09:50:00Z',
    category: 'absence',
    action: 'absence_approved',
    severity: 'info',
    userId: 'user-2',
    userName: 'Coordinator',
    targetId: 'absence-456',
    targetType: 'Absence',
    targetName: 'Annual Leave - John Faculty',
    success: true,
  },
  {
    id: '9',
    timestamp: '2024-12-23T09:45:00Z',
    category: 'data',
    action: 'data_exported',
    severity: 'info',
    userId: 'user-1',
    userName: 'Admin User',
    targetType: 'Export',
    success: true,
    details: { format: 'csv', records: 1250 },
  },
  {
    id: '10',
    timestamp: '2024-12-23T09:40:00Z',
    category: 'system',
    action: 'backup_created',
    severity: 'info',
    userId: 'system',
    userName: 'System',
    targetType: 'Backup',
    success: true,
    details: { size_mb: 45.2, tables: 15 },
  },
];

const MOCK_STATS: AuditStats = {
  totalEntries: 1250,
  entriesByCategory: {
    authentication: 450,
    authorization: 35,
    schedule: 180,
    user: 95,
    swap: 120,
    absence: 200,
    system: 100,
    data: 70,
  },
  entriesBySeverity: {
    info: 1100,
    warning: 120,
    error: 25,
    critical: 5,
  },
  recentFailures: 15,
  activeUsers24h: 42,
  topActions: [
    { action: 'login', count: 380 },
    { action: 'schedule_generated', count: 45 },
    { action: 'swap_requested', count: 38 },
    { action: 'absence_requested', count: 32 },
    { action: 'assignment_updated', count: 28 },
  ],
};

// ============================================================================
// Constants
// ============================================================================

const SEVERITY_ICONS: Record<AuditSeverity, React.ElementType> = {
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
  critical: AlertCircle,
};

// ============================================================================
// Helper Components
// ============================================================================

function CategoryBadge({ category }: { category: AuditCategory }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${AUDIT_CATEGORY_COLORS[category]}`}>
      {AUDIT_CATEGORY_LABELS[category]}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: AuditSeverity }) {
  const Icon = SEVERITY_ICONS[severity];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${AUDIT_SEVERITY_COLORS[severity]}`}>
      <Icon className="w-3.5 h-3.5" />
      {severity.charAt(0).toUpperCase() + severity.slice(1)}
    </span>
  );
}

function StatCard({ label, value, icon: Icon, trend }: { label: string; value: number | string; icon: React.ElementType; trend?: 'up' | 'down' }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="p-2 bg-slate-700/50 rounded-lg">
          <Icon className="w-5 h-5 text-slate-400" />
        </div>
        {trend && (
          <span className={trend === 'up' ? 'text-red-400' : 'text-green-400'}>
            {trend === 'up' ? '↑' : '↓'}
          </span>
        )}
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold text-white">{value}</div>
        <div className="text-sm text-slate-400">{label}</div>
      </div>
    </div>
  );
}

// ============================================================================
// Entry Detail Panel
// ============================================================================

interface EntryDetailProps {
  entry: AuditEntry;
  onClose: () => void;
}

function EntryDetail({ entry, onClose }: EntryDetailProps) {
  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-md bg-slate-800 border-l border-slate-700 shadow-2xl z-50 overflow-y-auto">
      <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Audit Entry Details</h2>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors"
        >
          <XCircle className="w-5 h-5 text-slate-400" />
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Status & Severity */}
        <div className="flex items-center gap-3">
          <SeverityBadge severity={entry.severity} />
          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
            entry.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {entry.success ? 'Success' : 'Failed'}
          </span>
        </div>

        {/* Timestamp */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Timestamp</label>
          <div className="text-sm text-white">
            {new Date(entry.timestamp).toLocaleString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </div>
        </div>

        {/* Category & Action */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Category</label>
            <CategoryBadge category={entry.category} />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Action</label>
            <div className="text-sm text-white">{entry.action.replace(/_/g, ' ')}</div>
          </div>
        </div>

        {/* User Info */}
        {entry.userName ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">User</label>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs font-medium">
                {entry.userName.split(' ').map((n: string) => n[0]).join('')}
              </div>
              <div>
                <div className="text-sm text-white">{entry.userName}</div>
                {entry.userId ? (
                  <div className="text-xs text-slate-400">{entry.userId}</div>
                ) : null}
              </div>
            </div>
          </div>
        ) : null}

        {/* Target */}
        {entry.targetType ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Target</label>
            <div className="text-sm text-white">
              {entry.targetType}
              {entry.targetName ? `: ${entry.targetName}` : null}
            </div>
            {entry.targetId ? (
              <div className="text-xs text-slate-400 mt-0.5">{entry.targetId}</div>
            ) : null}
          </div>
        ) : null}

        {/* IP Address */}
        {entry.ipAddress ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">IP Address</label>
            <div className="text-sm text-white font-mono">{entry.ipAddress}</div>
          </div>
        ) : null}

        {/* Error Message */}
        {entry.errorMessage ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Error Message</label>
            <div className="p-3 bg-red-900/30 border border-red-800/50 rounded-lg text-sm text-red-200">
              {entry.errorMessage}
            </div>
          </div>
        ) : null}

        {/* Old/New Values */}
        {(entry.oldValue !== undefined || entry.newValue !== undefined) ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Changes</label>
            <div className="grid grid-cols-2 gap-3">
              {entry.oldValue !== undefined ? (
                <div>
                  <div className="text-xs text-slate-500 mb-1">Before</div>
                  <pre className="p-2 bg-slate-900 rounded-lg text-xs text-slate-300 overflow-x-auto">
                    {JSON.stringify(entry.oldValue, null, 2)}
                  </pre>
                </div>
              ) : null}
              {entry.newValue !== undefined ? (
                <div>
                  <div className="text-xs text-slate-500 mb-1">After</div>
                  <pre className="p-2 bg-slate-900 rounded-lg text-xs text-slate-300 overflow-x-auto">
                    {JSON.stringify(entry.newValue, null, 2)}
                  </pre>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {/* Additional Details */}
        {entry.details && Object.keys(entry.details).length > 0 ? (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-2">Additional Details</label>
            <pre className="p-3 bg-slate-900 rounded-lg text-xs text-slate-300 overflow-x-auto">
              {JSON.stringify(entry.details, null, 2)}
            </pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}

// ============================================================================
// Stats Overview Panel
// ============================================================================

function StatsOverview({ stats }: { stats: AuditStats }) {
  const categoryData = Object.entries(stats.entriesByCategory)
    .sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Entries (24h)"
          value={stats.totalEntries.toLocaleString()}
          icon={FileText}
        />
        <StatCard
          label="Active Users"
          value={stats.activeUsers24h}
          icon={User}
        />
        <StatCard
          label="Failed Operations"
          value={stats.recentFailures}
          icon={XCircle}
          trend="up"
        />
        <StatCard
          label="Critical Events"
          value={stats.entriesBySeverity.critical}
          icon={AlertCircle}
        />
      </div>

      {/* Category Distribution */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Events by Category</h3>
        <div className="space-y-3">
          {categoryData.map(([category, count]) => {
            const percentage = (count / stats.totalEntries) * 100;
            return (
              <div key={category}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-slate-300">{AUDIT_CATEGORY_LABELS[category as AuditCategory]}</span>
                  <span className="text-slate-400">{count} ({percentage.toFixed(1)}%)</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-violet-500 to-purple-500 rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Top Actions */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Top Actions</h3>
        <div className="space-y-2">
          {stats.topActions.map((item, index) => (
            <div key={item.action} className="flex items-center justify-between py-2 border-b border-slate-700/50 last:border-0">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 flex items-center justify-center bg-slate-700 rounded-full text-xs text-slate-300">
                  {index + 1}
                </span>
                <span className="text-sm text-slate-200">{item.action.replace(/_/g, ' ')}</span>
              </div>
              <span className="text-sm text-slate-400">{item.count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminAuditPage() {
  const [viewMode, setViewMode] = useState<AuditViewMode>('list');
  const [entries] = useState<AuditEntry[]>(MOCK_ENTRIES);
  const [stats] = useState<AuditStats>(MOCK_STATS);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<AuditCategory | 'all'>('all');
  const [severityFilter, setSeverityFilter] = useState<AuditSeverity | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const matchesSearch =
        searchQuery === '' ||
        entry.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.userName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        entry.targetName?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || entry.category === categoryFilter;
      const matchesSeverity = severityFilter === 'all' || entry.severity === severityFilter;
      return matchesSearch && matchesCategory && matchesSeverity;
    });
  }, [entries, searchQuery, categoryFilter, severityFilter]);

  const handleExport = async () => {
    setIsExporting(true);
    // Simulate export
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsExporting(false);
    // Export complete
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Audit Logs</h1>
                <p className="text-sm text-slate-400">
                  System activity and security events
                </p>
              </div>
            </div>

            {/* View Toggle */}
            <div className="flex items-center gap-2 bg-slate-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'list'
                    ? 'bg-violet-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <List className="w-4 h-4" />
                List
              </button>
              <button
                onClick={() => setViewMode('stats')}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'stats'
                    ? 'bg-violet-600 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Stats
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {viewMode === 'stats' ? (
          <StatsOverview stats={stats} />
        ) : (
          <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex flex-1 gap-3 w-full sm:w-auto">
                {/* Search */}
                <div className="relative flex-1 sm:max-w-xs">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search logs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                {/* Filter Toggle */}
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`flex items-center gap-2 px-3 py-2 border rounded-lg transition-colors ${
                    showFilters
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <Filter className="w-4 h-4" />
                  Filters
                </button>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  className="flex items-center gap-2 px-3 py-2 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </button>
                <button
                  onClick={handleExport}
                  disabled={isExporting}
                  className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  <Download className={`w-4 h-4 ${isExporting ? 'animate-bounce' : ''}`} />
                  {isExporting ? 'Exporting...' : 'Export'}
                </button>
              </div>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="flex gap-4 p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Category</label>
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value as AuditCategory | 'all')}
                    className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Categories</option>
                    {Object.entries(AUDIT_CATEGORY_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Severity</label>
                  <select
                    value={severityFilter}
                    onChange={(e) => setSeverityFilter(e.target.value as AuditSeverity | 'all')}
                    className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Severities</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Date Range</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="date"
                      className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                    />
                    <span className="text-slate-400">to</span>
                    <input
                      type="date"
                      className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Logs Table */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Time
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Severity
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEntries.map((entry) => (
                    <tr
                      key={entry.id}
                      onClick={() => setSelectedEntry(entry)}
                      className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 text-sm text-slate-400">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          {new Date(entry.timestamp).toLocaleTimeString('en-US', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </div>
                        <div className="text-xs text-slate-500">
                          {new Date(entry.timestamp).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <SeverityBadge severity={entry.severity} />
                      </td>
                      <td className="px-4 py-3">
                        <CategoryBadge category={entry.category} />
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-200">
                        {entry.action.replace(/_/g, ' ')}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {entry.userName || '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-400">
                        {entry.targetName || entry.targetType || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          entry.success
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {entry.success ? 'OK' : 'Failed'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between text-sm text-slate-400">
              <span>Showing {filteredEntries.length} entries</span>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 border border-slate-700 rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50" disabled>
                  Previous
                </button>
                <button className="px-3 py-1.5 border border-slate-700 rounded-lg hover:bg-slate-800 transition-colors disabled:opacity-50" disabled>
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Entry Detail Sidebar */}
      {selectedEntry && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40"
            onClick={() => setSelectedEntry(null)}
          />
          <EntryDetail
            entry={selectedEntry}
            onClose={() => setSelectedEntry(null)}
          />
        </>
      )}
    </div>
  );
}
