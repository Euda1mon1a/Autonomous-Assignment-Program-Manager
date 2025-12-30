'use client';

/**
 * Admin User Management Page
 *
 * Administrative interface for managing system users, roles, and permissions.
 * Provides CRUD operations for users and role assignment capabilities.
 */
import { useState, useCallback, useMemo, useEffect } from 'react';
import {
  Users,
  UserPlus,
  Search,
  Filter,
  MoreVertical,
  Edit2,
  Trash2,
  Lock,
  Unlock,
  Mail,
  Shield,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Download,
  Loader2,
} from 'lucide-react';
import type {
  User,
  UserRole,
  UserStatus,
  UserManagementTab,
  UserCreate,
  UserUpdate,
  BulkAction,
  RolePermissions,
} from '@/types/admin-users';
import {
  USER_ROLE_LABELS,
  USER_ROLE_COLORS,
} from '@/types/admin-users';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useToggleUserLock,
  useResendInvite,
  useBulkUserAction,
} from '@/hooks/useAdminUsers';

// ============================================================================
// Mock Role Permissions Data (for display purposes only)
// ============================================================================

const MOCK_ROLE_PERMISSIONS: RolePermissions[] = [
  {
    role: 'admin',
    description: 'Full system access including user management and settings',
    permissions: [
      'schedule:read', 'schedule:write', 'schedule:generate', 'schedule:approve',
      'people:read', 'people:write',
      'absences:read', 'absences:write', 'absences:approve',
      'swaps:read', 'swaps:write', 'swaps:approve',
      'templates:read', 'templates:write',
      'admin:users', 'admin:settings', 'admin:audit', 'admin:scheduling',
    ],
  },
  {
    role: 'coordinator',
    description: 'Schedule management and approval capabilities',
    permissions: [
      'schedule:read', 'schedule:write', 'schedule:generate', 'schedule:approve',
      'people:read', 'people:write',
      'absences:read', 'absences:write', 'absences:approve',
      'swaps:read', 'swaps:write', 'swaps:approve',
      'templates:read', 'templates:write',
    ],
  },
  {
    role: 'faculty',
    description: 'View schedules, request swaps and absences',
    permissions: [
      'schedule:read',
      'people:read',
      'absences:read', 'absences:write',
      'swaps:read', 'swaps:write',
      'templates:read',
    ],
  },
  {
    role: 'resident',
    description: 'View own schedule, request absences',
    permissions: [
      'schedule:read',
      'people:read',
      'absences:read', 'absences:write',
      'swaps:read',
    ],
  },
];

// ============================================================================
// Constants
// ============================================================================

const TABS: { id: UserManagementTab; label: string; icon: React.ElementType }[] = [
  { id: 'users', label: 'Users', icon: Users },
  { id: 'roles', label: 'Roles & Permissions', icon: Shield },
  { id: 'activity', label: 'Activity Log', icon: Clock },
];

const STATUS_CONFIG: Record<UserStatus, { label: string; color: string; icon: React.ElementType }> = {
  active: { label: 'Active', color: 'bg-green-100 text-green-800', icon: CheckCircle2 },
  inactive: { label: 'Inactive', color: 'bg-gray-100 text-gray-800', icon: XCircle },
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800', icon: Clock },
  locked: { label: 'Locked', color: 'bg-red-100 text-red-800', icon: Lock },
};

// ============================================================================
// Helper Components
// ============================================================================

function StatusBadge({ status }: { status: UserStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}>
      <Icon className="w-3.5 h-3.5" />
      {config.label}
    </span>
  );
}

function RoleBadge({ role }: { role: UserRole }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${USER_ROLE_COLORS[role]}`}>
      {USER_ROLE_LABELS[role]}
    </span>
  );
}

function EmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="text-center py-12 px-4">
      <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-slate-200 mb-2">{title}</h3>
      <p className="text-slate-400 mb-6 max-w-md mx-auto">{description}</p>
      {action}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="w-8 h-8 text-violet-500 animate-spin mb-4" />
      <p className="text-slate-400">Loading users...</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
      <h3 className="text-lg font-medium text-slate-200 mb-2">Failed to load users</h3>
      <p className="text-slate-400 mb-6 max-w-md mx-auto text-center">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      )}
    </div>
  );
}

// ============================================================================
// Confirmation Dialog Component
// ============================================================================

interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  confirmVariant?: 'danger' | 'primary';
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  confirmVariant = 'danger',
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold text-white mb-2">{title}</h2>
        <p className="text-slate-400 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors disabled:opacity-50 ${
              confirmVariant === 'danger'
                ? 'bg-red-600 hover:bg-red-500'
                : 'bg-violet-600 hover:bg-violet-500'
            }`}
          >
            {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// User Row Component
// ============================================================================

interface UserRowProps {
  user: User;
  isSelected: boolean;
  onSelect: (userId: string) => void;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onToggleLock: (user: User) => void;
  onResendInvite: (user: User) => void;
}

function UserRow({ user, isSelected, onSelect, onEdit, onDelete, onToggleLock, onResendInvite }: UserRowProps) {
  const [showMenu, setShowMenu] = useState(false);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <tr className="border-b border-slate-700/50 hover:bg-slate-800/50 transition-colors">
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(user.id)}
          className="rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500"
        />
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-medium">
            {user.firstName[0]}{user.lastName[0]}
          </div>
          <div>
            <div className="font-medium text-slate-200">
              {user.firstName} {user.lastName}
            </div>
            <div className="text-sm text-slate-400">{user.email}</div>
          </div>
        </div>
      </td>
      <td className="px-4 py-3">
        <RoleBadge role={user.role} />
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={user.status} />
      </td>
      <td className="px-4 py-3 text-sm text-slate-400">
        {formatDate(user.lastLogin)}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          {user.mfaEnabled ? (
            <span className="text-green-400" title="MFA Enabled">
              <Shield className="w-4 h-4" />
            </span>
          ) : (
            <span className="text-slate-500" title="MFA Disabled">
              <Shield className="w-4 h-4" />
            </span>
          )}
        </div>
      </td>
      <td className="px-4 py-3">
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-1.5 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <MoreVertical className="w-4 h-4 text-slate-400" />
          </button>
          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-full mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20">
                <button
                  onClick={() => { onEdit(user); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit User
                </button>
                {user.status === 'pending' && (
                  <button
                    onClick={() => { onResendInvite(user); setShowMenu(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    <Mail className="w-4 h-4" />
                    Resend Invite
                  </button>
                )}
                <button
                  onClick={() => { onToggleLock(user); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  {user.status === 'locked' ? (
                    <>
                      <Unlock className="w-4 h-4" />
                      Unlock Account
                    </>
                  ) : (
                    <>
                      <Lock className="w-4 h-4" />
                      Lock Account
                    </>
                  )}
                </button>
                <hr className="border-slate-700 my-1" />
                <button
                  onClick={() => { onDelete(user); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-slate-700 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete User
                </button>
              </div>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

// ============================================================================
// Create/Edit User Modal
// ============================================================================

interface UserModalProps {
  user?: User;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: UserCreate) => void;
}

function UserModal({ user, isOpen, onClose, onSave }: UserModalProps) {
  const [formData, setFormData] = useState<UserCreate>({
    email: user?.email || '',
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    role: user?.role || 'resident',
    sendInvite: true,
  });

  // Reset form state when user prop changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        email: user?.email || '',
        firstName: user?.firstName || '',
        lastName: user?.lastName || '',
        role: user?.role || 'resident',
        sendInvite: true,
      });
    }
  }, [user, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">
            {user ? 'Edit User' : 'Create New User'}
          </h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                First Name
              </label>
              <input
                type="text"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Last Name
              </label>
              <input
                type="text"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
                required
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">
              Role
            </label>
            <select
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              {Object.entries(USER_ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          {!user && (
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.sendInvite}
                onChange={(e) => setFormData({ ...formData, sendInvite: e.target.checked })}
                className="rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500"
              />
              <span className="text-sm text-slate-300">Send invitation email</span>
            </label>
          )}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
            >
              {user ? 'Save Changes' : 'Create User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ============================================================================
// Roles Panel
// ============================================================================

function RolesPanel() {
  const [expandedRole, setExpandedRole] = useState<UserRole | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">Roles & Permissions</h2>
          <p className="text-sm text-slate-400">View role definitions and their permissions</p>
        </div>
      </div>

      <div className="space-y-3">
        {MOCK_ROLE_PERMISSIONS.map((roleConfig) => (
          <div
            key={roleConfig.role}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden"
          >
            <button
              onClick={() => setExpandedRole(expandedRole === roleConfig.role ? null : roleConfig.role)}
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <RoleBadge role={roleConfig.role} />
                <span className="text-sm text-slate-400">{roleConfig.description}</span>
              </div>
              {expandedRole === roleConfig.role ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </button>
            {expandedRole === roleConfig.role && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-700/50">
                <h4 className="text-sm font-medium text-slate-300 mb-3">Permissions</h4>
                <div className="flex flex-wrap gap-2">
                  {roleConfig.permissions.map((permission) => (
                    <span
                      key={permission}
                      className="inline-flex items-center px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded-md"
                    >
                      {permission}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Activity Panel
// ============================================================================

function ActivityPanel() {
  // Mock activity data
  const activities = [
    { id: '1', action: 'User created', user: 'Admin', target: 'Jane Resident', timestamp: '2024-12-23T10:00:00Z' },
    { id: '2', action: 'Role changed', user: 'Admin', target: 'John Faculty', timestamp: '2024-12-23T09:30:00Z' },
    { id: '3', action: 'Password reset', user: 'System', target: 'Locked Account', timestamp: '2024-12-22T15:00:00Z' },
    { id: '4', action: 'Account locked', user: 'System', target: 'Locked Account', timestamp: '2024-12-22T14:55:00Z' },
    { id: '5', action: 'Login', user: 'Coordinator', target: null, timestamp: '2024-12-22T14:00:00Z' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
          <p className="text-sm text-slate-400">User management activity log</p>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-300 hover:text-white border border-slate-600 rounded-lg hover:bg-slate-700 transition-colors">
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Time</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Action</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">User</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Target</th>
            </tr>
          </thead>
          <tbody>
            {activities.map((activity) => (
              <tr key={activity.id} className="border-b border-slate-700/50 last:border-0">
                <td className="px-4 py-3 text-sm text-slate-400">
                  {new Date(activity.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-slate-200">{activity.action}</td>
                <td className="px-4 py-3 text-sm text-slate-300">{activity.user}</td>
                <td className="px-4 py-3 text-sm text-slate-400">{activity.target || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminUsersPage() {
  // UI State
  const [activeTab, setActiveTab] = useState<UserManagementTab>('users');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<UserStatus | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>();

  // Confirmation dialog state
  const [deleteConfirm, setDeleteConfirm] = useState<{ isOpen: boolean; user?: User }>({
    isOpen: false,
  });

  // API Hooks
  const {
    data: usersData,
    isLoading,
    error,
    refetch,
  } = useUsers({
    search: searchQuery || undefined,
    role: roleFilter,
    status: statusFilter,
  });

  const createUserMutation = useCreateUser();
  const updateUserMutation = useUpdateUser();
  const deleteUserMutation = useDeleteUser();
  const toggleLockMutation = useToggleUserLock();
  const resendInviteMutation = useResendInvite();
  const bulkActionMutation = useBulkUserAction();

  // Derived data - memoize to prevent unnecessary re-renders
  const users = useMemo(() => usersData?.users ?? [], [usersData?.users]);
  const totalUsers = usersData?.total ?? 0;

  // Client-side filtering for search (API handles role/status filters)
  const filteredUsers = useMemo(() => {
    // If search is handled server-side, just return users
    // For now we still filter client-side for instant feedback
    return users.filter((user) => {
      const matchesSearch =
        searchQuery === '' ||
        user.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.lastName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [users, searchQuery]);

  const handleSelectUser = useCallback((userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedUsers.length === filteredUsers.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(filteredUsers.map((u) => u.id));
    }
  }, [selectedUsers.length, filteredUsers]);

  const handleCreateUser = useCallback((data: UserCreate) => {
    createUserMutation.mutate(data, {
      onSuccess: () => {
        setIsModalOpen(false);
        setEditingUser(undefined);
      },
    });
  }, [createUserMutation]);

  const handleUpdateUser = useCallback((data: UserCreate) => {
    if (!editingUser) return;

    const updateData: UserUpdate = {
      email: data.email,
      firstName: data.firstName,
      lastName: data.lastName,
      role: data.role,
    };

    updateUserMutation.mutate(
      { id: editingUser.id, data: updateData },
      {
        onSuccess: () => {
          setIsModalOpen(false);
          setEditingUser(undefined);
        },
      }
    );
  }, [editingUser, updateUserMutation]);

  const handleSaveUser = useCallback((data: UserCreate) => {
    if (editingUser) {
      handleUpdateUser(data);
    } else {
      handleCreateUser(data);
    }
  }, [editingUser, handleCreateUser, handleUpdateUser]);

  const handleEditUser = useCallback((user: User) => {
    setEditingUser(user);
    setIsModalOpen(true);
  }, []);

  const handleDeleteUser = useCallback((user: User) => {
    setDeleteConfirm({ isOpen: true, user });
  }, []);

  const handleConfirmDelete = useCallback(() => {
    if (!deleteConfirm.user) return;

    deleteUserMutation.mutate(deleteConfirm.user.id, {
      onSuccess: () => {
        setDeleteConfirm({ isOpen: false });
        setSelectedUsers((prev) => prev.filter((id) => id !== deleteConfirm.user?.id));
      },
      onError: () => {
        // Keep dialog open on error so user can see the error
      },
    });
  }, [deleteConfirm.user, deleteUserMutation]);

  const handleToggleLock = useCallback((user: User) => {
    const shouldLock = user.status !== 'locked';
    toggleLockMutation.mutate({ id: user.id, lock: shouldLock });
  }, [toggleLockMutation]);

  const handleResendInvite = useCallback((user: User) => {
    resendInviteMutation.mutate(user.id);
  }, [resendInviteMutation]);

  const handleBulkAction = useCallback((action: BulkAction) => {
    if (selectedUsers.length === 0) return;

    bulkActionMutation.mutate(
      { userIds: selectedUsers, action },
      {
        onSuccess: () => {
          setSelectedUsers([]);
        },
      }
    );
  }, [selectedUsers, bulkActionMutation]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg">
                <Users className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">User Management</h1>
                <p className="text-sm text-slate-400">
                  Manage users, roles, and permissions
                </p>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg
                    transition-all duration-200
                    ${isActive
                      ? 'bg-slate-800 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeTab === 'users' && (
          <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <div className="flex flex-1 gap-3 w-full sm:w-auto">
                {/* Search */}
                <div className="relative flex-1 sm:max-w-xs">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search users..."
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
                  onClick={() => { setEditingUser(undefined); setIsModalOpen(true); }}
                  className="flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors"
                >
                  <UserPlus className="w-4 h-4" />
                  Add User
                </button>
              </div>
            </div>

            {/* Filters Panel */}
            {showFilters && (
              <div className="flex gap-4 p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Role</label>
                  <select
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value as UserRole | 'all')}
                    className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Roles</option>
                    {Object.entries(USER_ROLE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as UserStatus | 'all')}
                    className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Statuses</option>
                    {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                      <option key={value} value={value}>{config.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Bulk Actions */}
            {selectedUsers.length > 0 && (
              <div className="flex items-center gap-4 p-3 bg-violet-900/30 border border-violet-700/50 rounded-lg">
                <span className="text-sm text-violet-200">
                  {selectedUsers.length} user(s) selected
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleBulkAction('activate')}
                    disabled={bulkActionMutation.isPending}
                    className="px-3 py-1.5 text-xs font-medium bg-violet-600 hover:bg-violet-500 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    {bulkActionMutation.isPending ? 'Processing...' : 'Activate'}
                  </button>
                  <button
                    onClick={() => handleBulkAction('deactivate')}
                    disabled={bulkActionMutation.isPending}
                    className="px-3 py-1.5 text-xs font-medium bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    Deactivate
                  </button>
                  <button
                    onClick={() => handleBulkAction('delete')}
                    disabled={bulkActionMutation.isPending}
                    className="px-3 py-1.5 text-xs font-medium bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
                <button
                  onClick={() => setSelectedUsers([])}
                  className="ml-auto text-sm text-violet-300 hover:text-violet-100"
                >
                  Clear selection
                </button>
              </div>
            )}

            {/* Users Table */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
              {isLoading ? (
                <LoadingState />
              ) : error ? (
                <ErrorState
                  message={error.message || 'Failed to load users'}
                  onRetry={() => refetch()}
                />
              ) : filteredUsers.length === 0 ? (
                <EmptyState
                  title="No users found"
                  description="No users match your current filters. Try adjusting your search or filters."
                />
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700/50">
                      <th className="px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedUsers.length === filteredUsers.length && filteredUsers.length > 0}
                          onChange={handleSelectAll}
                          className="rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        User
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Role
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Last Login
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                        MFA
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((user) => (
                      <UserRow
                        key={user.id}
                        user={user}
                        isSelected={selectedUsers.includes(user.id)}
                        onSelect={handleSelectUser}
                        onEdit={handleEditUser}
                        onDelete={handleDeleteUser}
                        onToggleLock={handleToggleLock}
                        onResendInvite={handleResendInvite}
                      />
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between text-sm text-slate-400">
              <span>Showing {filteredUsers.length} of {totalUsers} users</span>
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

        {activeTab === 'roles' && <RolesPanel />}
        {activeTab === 'activity' && <ActivityPanel />}
      </main>

      {/* Create/Edit Modal */}
      <UserModal
        user={editingUser}
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingUser(undefined); }}
        onSave={handleSaveUser}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        title="Delete User"
        message={`Are you sure you want to delete ${deleteConfirm.user?.firstName} ${deleteConfirm.user?.lastName} (${deleteConfirm.user?.email})? This action cannot be undone.`}
        confirmLabel="Delete"
        confirmVariant="danger"
        isLoading={deleteUserMutation.isPending}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteConfirm({ isOpen: false })}
      />
    </div>
  );
}
