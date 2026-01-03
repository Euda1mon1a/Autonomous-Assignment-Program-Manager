/**
 * Admin User Management Types
 *
 * Types for the admin user management interface including
 * user CRUD operations, role management, and audit tracking.
 */

// ============================================================================
// User Role Types
// ============================================================================

export type UserRole =
  | "admin"
  | "coordinator"
  | "faculty"
  | "resident"
  | "clinical_staff"
  | "rn"
  | "lpn"
  | "msa";

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrator",
  coordinator: "Coordinator",
  faculty: "Faculty",
  resident: "Resident",
  clinical_staff: "Clinical Staff",
  rn: "Registered Nurse",
  lpn: "Licensed Practical Nurse",
  msa: "Medical Support Assistant",
};

export const USER_ROLE_COLORS: Record<UserRole, string> = {
  admin: "bg-red-100 text-red-800",
  coordinator: "bg-purple-100 text-purple-800",
  faculty: "bg-blue-100 text-blue-800",
  resident: "bg-green-100 text-green-800",
  clinical_staff: "bg-yellow-100 text-yellow-800",
  rn: "bg-teal-100 text-teal-800",
  lpn: "bg-cyan-100 text-cyan-800",
  msa: "bg-gray-100 text-gray-800",
};

// ============================================================================
// User Types
// ============================================================================

export type UserStatus = "active" | "inactive" | "pending" | "locked";

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: UserStatus;
  personId?: string; // Link to Person entity if applicable
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  mfaEnabled: boolean;
  failedLoginAttempts: number;
  lockedUntil?: string;
}

export interface UserCreate {
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  personId?: string;
  sendInvite: boolean;
  temporaryPassword?: string;
}

export interface UserUpdate {
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: UserRole;
  status?: UserStatus;
  personId?: string;
}

// ============================================================================
// Permission Types
// ============================================================================

export type Permission =
  | "schedule:read"
  | "schedule:write"
  | "schedule:generate"
  | "schedule:approve"
  | "people:read"
  | "people:write"
  | "absences:read"
  | "absences:write"
  | "absences:approve"
  | "swaps:read"
  | "swaps:write"
  | "swaps:approve"
  | "templates:read"
  | "templates:write"
  | "admin:users"
  | "admin:settings"
  | "admin:audit"
  | "admin:scheduling";

export interface RolePermissions {
  role: UserRole;
  permissions: Permission[];
  description: string;
}

// ============================================================================
// Filter & Search Types
// ============================================================================

export interface UserFilters {
  search?: string;
  roles?: UserRole[];
  status?: UserStatus[];
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface UserSortOptions {
  field: "name" | "email" | "role" | "status" | "lastLogin" | "createdAt";
  direction: "asc" | "desc";
}

// ============================================================================
// Bulk Actions
// ============================================================================

export type BulkAction =
  | "activate"
  | "deactivate"
  | "resetPassword"
  | "resendInvite"
  | "delete";

export interface BulkActionRequest {
  userIds: string[];
  action: BulkAction;
  reason?: string;
}

// ============================================================================
// API Response Types
// ============================================================================

/**
 * API response for listing users.
 * Note: The API returns snake_case fields, but axios with proper config
 * transforms them. We also need to handle both `items` (API) and `users` (legacy).
 */
export interface UsersResponse {
  /** List of users (mapped from 'items' in API response) */
  users: User[];
  total: number;
  page: number;
  pageSize: number;
  totalPages?: number;
}

/**
 * Raw API response from backend (before transformation).
 * Used internally by the hooks for data mapping.
 */
export interface AdminUserListApiResponse {
  items: AdminUserApiResponse[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Raw user data from API (snake_case).
 */
export interface AdminUserApiResponse {
  id: string;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
  is_locked: boolean;
  lock_reason: string | null;
  created_at: string | null;
  updated_at: string | null;
  last_login: string | null;
  invite_sent_at: string | null;
  invite_accepted_at: string | null;
}

export interface UserActivityLog {
  id: string;
  userId: string;
  action: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
  details?: Record<string, unknown>;
}

export interface ActivityLogResponse {
  items: UserActivityLog[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export enum ActivityAction {
  USER_CREATED = "user_created",
  USER_UPDATED = "user_updated",
  USER_DELETED = "user_deleted",
  USER_LOCKED = "user_locked",
  USER_UNLOCKED = "user_unlocked",
  INVITE_SENT = "invite_sent",
  INVITE_RESENT = "invite_resent",
  INVITE_ACCEPTED = "invite_accepted",
  PASSWORD_RESET = "password_reset",
  LOGIN = "login",
  LOGOUT = "logout",
  BULK_ACTION = "bulk_action",
}

// ============================================================================
// State Types
// ============================================================================

export type UserManagementTab = "users" | "roles" | "activity";

export interface UserManagementState {
  activeTab: UserManagementTab;
  filters: UserFilters;
  sort: UserSortOptions;
  selectedUsers: string[];
  isCreating: boolean;
  editingUser?: User;
}
