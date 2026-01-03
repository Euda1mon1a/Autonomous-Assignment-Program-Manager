"use client";

/**
 * Admin User Management Page
 *
 * Administrative interface for managing system users, roles, and permissions.
 * Provides CRUD operations for users and role assignment capabilities.
 */
import {
  useActivityLog,
  useBulkUserAction,
  useCreateUser,
  useDeleteUser,
  useResendInvite,
  useToggleUserLock,
  useUpdateUser,
  useUsers,
} from "@/hooks/useAdminUsers";
import type {
  BulkAction,
  RolePermissions,
  User,
  UserCreate,
  UserManagementTab,
  UserRole,
  UserStatus,
  UserUpdate,
} from "@/types/admin-users";
import { USER_ROLE_COLORS, USER_ROLE_LABELS } from "@/types/admin-users";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Download,
  Edit2,
  Loader2,
  Lock,
  Mail,
  MoreVertical,
  RefreshCw,
  Search,
  Shield,
  Trash2,
  Unlock,
  UserPlus,
  Users,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

// ============================================================================
// Mock Role Permissions Data (for display purposes only)
// ============================================================================

const MOCK_ROLE_PERMISSIONS: RolePermissions[] = [
  {
    role: "admin",
    description: "Full system access including user management and settings",
    permissions: [
      "schedule:read",
      "schedule:write",
      "schedule:generate",
      "schedule:approve",
      "people:read",
      "people:write",
      "absences:read",
      "absences:write",
      "absences:approve",
      "swaps:read",
      "swaps:write",
      "swaps:approve",
      "templates:read",
      "templates:write",
      "admin:users",
      "admin:settings",
      "admin:audit",
      "admin:scheduling",
    ],
  },
  {
    role: "coordinator",
    description: "Schedule management and approval capabilities",
    permissions: [
      "schedule:read",
      "schedule:write",
      "schedule:generate",
      "schedule:approve",
      "people:read",
      "people:write",
      "absences:read",
      "absences:write",
      "absences:approve",
      "swaps:read",
      "swaps:write",
      "swaps:approve",
      "templates:read",
      "templates:write",
    ],
  },
  {
    role: "faculty",
    description: "View schedules, request swaps and absences",
    permissions: [
      "schedule:read",
      "people:read",
      "absences:read",
      "absences:write",
      "swaps:read",
      "swaps:write",
      "templates:read",
    ],
  },
  {
    role: "resident",
    description: "View own schedule, request absences",
    permissions: [
      "schedule:read",
      "people:read",
      "absences:read",
      "absences:write",
      "swaps:read",
    ],
  },
];

// ============================================================================
// Constants
// ============================================================================

const TABS: {
  id: UserManagementTab;
  label: string;
  icon: React.ElementType;
}[] = [
  { id: "users", label: "Users", icon: Users },
  { id: "roles", label: "Roles & Permissions", icon: Shield },
  { id: "activity", label: "Activity Log", icon: Clock },
];

const STATUS_CONFIG: Record<
  UserStatus,
  { label: string; color: string; icon: React.ElementType }
> = {
  active: {
    label: "Active",
    color: "bg-green-100 text-green-800",
    icon: CheckCircle2,
  },
  inactive: {
    label: "Inactive",
    color: "bg-gray-100 text-gray-800",
    icon: XCircle,
  },
  pending: {
    label: "Pending",
    color: "bg-yellow-100 text-yellow-800",
    icon: Clock,
  },
  locked: { label: "Locked", color: "bg-red-100 text-red-800", icon: Lock },
};

// ============================================================================
// Helper Components
// ============================================================================

function StatusBadge({ status }: { status: UserStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}
    >
      <Icon className="w-3.5 h-3.5" />
      {config.label}
    </span>
  );
}

function RoleBadge({ role }: { role: UserRole }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${USER_ROLE_COLORS[role]}`}
    >
      {USER_ROLE_LABELS[role]}
    </span>
  );
}

function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="text-center py-12 px-4 border border-dashed border-slate-700 rounded-lg">
      <Users className="w-12 h-12 text-slate-500 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-slate-200 mb-2">{title}</h3>
      <p className="text-slate-400 mb-6 max-w-md mx-auto">{description}</p>
      {action}
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
  confirmVariant?: "danger" | "primary";
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmLabel = "Confirm",
  confirmVariant = "danger",
  isLoading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />
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
              confirmVariant === "danger"
                ? "bg-red-600 hover:bg-red-500"
                : "bg-violet-600 hover:bg-violet-500"
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

function UserRow({
  user,
  isSelected,
  onSelect,
  onEdit,
  onDelete,
  onToggleLock,
  onResendInvite,
}: UserRowProps) {
  const [showMenu, setShowMenu] = useState(false);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
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
            {user.firstName[0]}
            {user.lastName[0]}
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
                  onClick={() => {
                    onEdit(user);
                    setShowMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit User
                </button>
                {user.status === "pending" && (
                  <button
                    onClick={() => {
                      onResendInvite(user);
                      setShowMenu(false);
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    <Mail className="w-4 h-4" />
                    Resend Invite
                  </button>
                )}
                <button
                  onClick={() => {
                    onToggleLock(user);
                    setShowMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  {user.status === "locked" ? (
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
                  onClick={() => {
                    onDelete(user);
                    setShowMenu(false);
                  }}
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
    email: user?.email || "",
    firstName: user?.firstName || "",
    lastName: user?.lastName || "",
    role: user?.role || "resident",
    sendInvite: true,
  });

  // Reset form state when user prop changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        email: user?.email || "",
        firstName: user?.firstName || "",
        lastName: user?.lastName || "",
        role: user?.role || "resident",
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
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-slate-800 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="px-6 py-4 border-b border-slate-700">
          <h2 className="text-lg font-semibold text-white">
            {user ? "Edit User" : "Create New User"}
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
                onChange={(e) =>
                  setFormData({ ...formData, firstName: e.target.value })
                }
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
                onChange={(e) =>
                  setFormData({ ...formData, lastName: e.target.value })
                }
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
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
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
              onChange={(e) =>
                setFormData({ ...formData, role: e.target.value as UserRole })
              }
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
            >
              {Object.entries(USER_ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          {!user && (
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.sendInvite}
                onChange={(e) =>
                  setFormData({ ...formData, sendInvite: e.target.checked })
                }
                className="rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500"
              />
              <span className="text-sm text-slate-300">
                Send invitation email
              </span>
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
              {user ? "Save Changes" : "Create User"}
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
          <h2 className="text-lg font-semibold text-white">
            Roles & Permissions
          </h2>
          <p className="text-sm text-slate-400">
            View role definitions and their permissions
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {MOCK_ROLE_PERMISSIONS.map((roleConfig) => (
          <div
            key={roleConfig.role}
            className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden"
          >
            <button
              onClick={() =>
                setExpandedRole(
                  expandedRole === roleConfig.role ? null : roleConfig.role
                )
              }
              className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <RoleBadge role={roleConfig.role} />
                <span className="text-sm text-slate-400">
                  {roleConfig.description}
                </span>
              </div>
              {expandedRole === roleConfig.role ? (
                <ChevronUp className="w-5 h-5 text-slate-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-slate-400" />
              )}
            </button>
            {expandedRole === roleConfig.role && (
              <div className="px-4 pb-4 pt-2 border-t border-slate-700/50">
                <h4 className="text-sm font-medium text-slate-300 mb-3">
                  Permissions
                </h4>
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
  const [page, setPage] = useState(1);
  const { data, isLoading } = useActivityLog({
    page,
    pageSize: 20,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="w-8 h-8 text-violet-500 animate-spin" />
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No Activity Found"
        description="No user account activity has been recorded yet."
      />
    );
  }

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
              <th className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                Time
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
            </tr>
          </thead>
          <tbody>
            {data.items.map((activity) => (
              <tr
                key={activity.id}
                className="border-b border-slate-700/50 last:border-0 hover:bg-slate-800/20"
              >
                <td className="px-4 py-3 text-sm text-slate-400">
                  {new Date(activity.timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-sm text-slate-200">
                  <span className="capitalize">
                    {activity.action.replace(/_/g, " ").toLowerCase()}
                  </span>
                </td>
                {/* Note: In a real app, you might want to fetch user details or resolve names */}
                <td className="px-4 py-3 text-sm text-slate-300">
                  {activity.userId}
                </td>
                <td className="px-4 py-3 text-sm text-slate-400">-</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {data.totalPages > 1 && (
        <div className="flex justify-between items-center px-4 py-2 border-t border-slate-700/50">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-white disabled:opacity-50"
          >
            <ArrowLeft className="w-4 h-4" /> Previous
          </button>
          <span className="text-xs text-slate-500">
            Page {page} of {data.totalPages}
          </span>
          <button
            disabled={page === data.totalPages}
            onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-white disabled:opacity-50"
          >
            Next <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminUsersPage() {
  // UI State
  const [activeTab, setActiveTab] = useState<UserManagementTab>("users");
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<UserRole | "all">("all");
  const [statusFilter, setStatusFilter] = useState<UserStatus | "all">("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>();

  // Confirmation dialog state
  const [deleteConfirm, setDeleteConfirm] = useState<{
    isOpen: boolean;
    user?: User;
  }>({
    isOpen: false,
  });

  // API Hooks
  const {
    data: usersData,
    isLoading,
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
  // Use server totals if available, otherwise array length
  const totalUsers = usersData?.total ?? users.length;

  // Client-side filtering for search (API handles role/status filters)
  const filteredUsers = useMemo(() => {
    // If search is handled server-side, just return users
    // For now we still filter client-side for instant feedback
    return users.filter((user) => {
      const matchesSearch =
        searchQuery === "" ||
        user.firstName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.lastName.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [users, searchQuery]);

  const handleSelectUser = useCallback((userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    if (selectedUsers.length === filteredUsers.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(filteredUsers.map((u) => u.id));
    }
  }, [selectedUsers.length, filteredUsers]);

  const handleCreateUser = useCallback(
    (data: UserCreate) => {
      createUserMutation.mutate(data, {
        onSuccess: () => {
          setIsModalOpen(false);
          setEditingUser(undefined);
        },
      });
    },
    [createUserMutation]
  );

  const handleUpdateUser = useCallback(
    (data: UserCreate) => {
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
    },
    [editingUser, updateUserMutation]
  );

  const handleSaveUser = useCallback(
    (data: UserCreate) => {
      if (editingUser) {
        handleUpdateUser(data);
      } else {
        handleCreateUser(data);
      }
    },
    [editingUser, handleCreateUser, handleUpdateUser]
  );

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
        setSelectedUsers((prev) =>
          prev.filter((id) => id !== deleteConfirm.user?.id)
        );
      },
      onError: () => {
        // Keep dialog open on error so user can see the error
      },
    });
  }, [deleteConfirm.user, deleteUserMutation]);

  const handleToggleLock = useCallback(
    (user: User) => {
      const shouldLock = user.status !== "locked";
      toggleLockMutation.mutate({ id: user.id, lock: shouldLock });
    },
    [toggleLockMutation]
  );

  const handleResendInvite = useCallback(
    (user: User) => {
      resendInviteMutation.mutate(user.id);
    },
    [resendInviteMutation]
  );

  const handleBulkAction = useCallback(
    (action: BulkAction) => {
      if (selectedUsers.length === 0) return;

      bulkActionMutation.mutate(
        { userIds: selectedUsers, action },
        {
          onSuccess: () => {
            setSelectedUsers([]);
          },
        }
      );
    },
    [selectedUsers, bulkActionMutation]
  );

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
                <h1 className="text-xl font-bold text-white">
                  User Management
                </h1>
                <p className="text-sm text-slate-400">
                  Manage users, roles, and permissions
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setEditingUser(undefined);
                setIsModalOpen(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-white text-slate-900 rounded-lg font-medium hover:bg-slate-50 transition-colors"
            >
              <UserPlus className="w-5 h-5" />
              Add User
            </button>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 mt-6 border-b border-slate-700/50">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? "border-violet-500 text-violet-400"
                      : "border-transparent text-slate-400 hover:text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === "users" && (
          <div className="space-y-4">
            {/* Filters & Actions */}
            <div className="flex items-center justify-between gap-4 p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl">
              <div className="flex items-center gap-4 flex-1">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search users..."
                    className="w-full pl-10 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={roleFilter}
                    onChange={(e) =>
                      setRoleFilter(e.target.value as UserRole | "all")
                    }
                    className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Roles</option>
                    {Object.entries(USER_ROLE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <select
                    value={statusFilter}
                    onChange={(e) =>
                      setStatusFilter(e.target.value as UserStatus | "all")
                    }
                    className="px-3 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    <option value="all">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="pending">Pending</option>
                    <option value="locked">Locked</option>
                  </select>
                </div>
              </div>
              <button
                onClick={() => refetch()}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                title="Refresh List"
              >
                <RefreshCw
                  className={`w-5 h-5 ${isLoading ? "animate-spin" : ""}`}
                />
              </button>
            </div>

            {/* Bulk Actions (only visible when users selected) */}
            {selectedUsers.length > 0 && (
              <div className="flex items-center gap-2 p-2 bg-violet-500/10 border border-violet-500/20 rounded-lg animate-in fade-in slide-in-from-top-2">
                <span className="text-sm text-violet-300 font-medium px-2">
                  {selectedUsers.length} selected
                </span>
                <div className="h-4 w-px bg-violet-500/20 mx-2" />
                <button
                  onClick={() => handleBulkAction("activate")}
                  className="px-3 py-1.5 text-xs font-medium text-violet-300 hover:bg-violet-500/20 rounded-md transition-colors"
                >
                  Activate
                </button>
                <button
                  onClick={() => handleBulkAction("deactivate")}
                  className="px-3 py-1.5 text-xs font-medium text-violet-300 hover:bg-violet-500/20 rounded-md transition-colors"
                >
                  Deactivate
                </button>
                <button
                  onClick={() => handleBulkAction("delete")}
                  className="px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-500/20 rounded-md transition-colors"
                >
                  Delete
                </button>
              </div>
            )}

            {/* Users Table */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden shadow-xl shadow-black/20">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-900/50 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-700/50">
                      <th className="px-4 py-3 w-10">
                        <input
                          type="checkbox"
                          checked={
                            selectedUsers.length === filteredUsers.length &&
                            filteredUsers.length > 0
                          }
                          onChange={handleSelectAll}
                          className="rounded border-slate-600 bg-slate-700 text-violet-500 focus:ring-violet-500"
                        />
                      </th>
                      <th className="px-4 py-3 font-medium">User</th>
                      <th className="px-4 py-3 font-medium">Role</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                      <th className="px-4 py-3 font-medium">Last Login</th>
                      <th className="px-4 py-3 font-medium">Security</th>
                      <th className="px-4 py-3 w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <tr>
                        <td colSpan={7}>
                          <div className="p-8 flex justify-center">
                            <Loader2 className="animate-spin text-slate-400" />
                          </div>
                        </td>
                      </tr>
                    ) : filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={7}>
                          <div className="p-8 text-center text-slate-500">
                            No users found
                          </div>
                        </td>
                      </tr>
                    ) : (
                      filteredUsers.map((user) => (
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
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            {/* Pagination Summary */}
            <div className="text-xs text-slate-500 text-right px-2">
              Showing {filteredUsers.length} of {totalUsers} users
            </div>
          </div>
        )}

        {activeTab === "roles" && <RolesPanel />}
        {activeTab === "activity" && <ActivityPanel />}
      </main>

      {/* Modals */}
      <UserModal
        user={editingUser}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingUser(undefined);
        }}
        onSave={handleSaveUser}
      />

      <ConfirmDialog
        isOpen={deleteConfirm.isOpen}
        title="Delete User"
        message={`Are you sure you want to delete ${deleteConfirm.user?.firstName} ${deleteConfirm.user?.lastName}? This action cannot be undone.`}
        confirmLabel="Delete User"
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteConfirm({ isOpen: false })}
        isLoading={deleteUserMutation.isPending}
      />
    </div>
  );
}
