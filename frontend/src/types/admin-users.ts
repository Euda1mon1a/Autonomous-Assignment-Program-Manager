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
  | 'admin'
  | 'coordinator'
  | 'faculty'
  | 'resident'
  | 'clinical_staff'
  | 'rn'
  | 'lpn'
  | 'msa';

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Administrator',
  coordinator: 'Coordinator',
  faculty: 'Faculty',
  resident: 'Resident',
  clinical_staff: 'Clinical Staff',
  rn: 'Registered Nurse',
  lpn: 'Licensed Practical Nurse',
  msa: 'Medical Support Assistant',
};

export const USER_ROLE_COLORS: Record<UserRole, string> = {
  admin: 'bg-red-100 text-red-800',
  coordinator: 'bg-purple-100 text-purple-800',
  faculty: 'bg-blue-100 text-blue-800',
  resident: 'bg-green-100 text-green-800',
  clinical_staff: 'bg-yellow-100 text-yellow-800',
  rn: 'bg-teal-100 text-teal-800',
  lpn: 'bg-cyan-100 text-cyan-800',
  msa: 'bg-gray-100 text-gray-800',
};

// ============================================================================
// User Types
// ============================================================================

export type UserStatus = 'active' | 'inactive' | 'pending' | 'locked';

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
  | 'schedule:read'
  | 'schedule:write'
  | 'schedule:generate'
  | 'schedule:approve'
  | 'people:read'
  | 'people:write'
  | 'absences:read'
  | 'absences:write'
  | 'absences:approve'
  | 'swaps:read'
  | 'swaps:write'
  | 'swaps:approve'
  | 'templates:read'
  | 'templates:write'
  | 'admin:users'
  | 'admin:settings'
  | 'admin:audit'
  | 'admin:scheduling';

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
  field: 'name' | 'email' | 'role' | 'status' | 'lastLogin' | 'createdAt';
  direction: 'asc' | 'desc';
}

// ============================================================================
// Bulk Actions
// ============================================================================

export type BulkAction =
  | 'activate'
  | 'deactivate'
  | 'resetPassword'
  | 'resendInvite'
  | 'delete';

export interface BulkActionRequest {
  userIds: string[];
  action: BulkAction;
  reason?: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface UsersResponse {
  users: User[];
  total: number;
  page: number;
  pageSize: number;
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

// ============================================================================
// State Types
// ============================================================================

export type UserManagementTab = 'users' | 'roles' | 'activity';

export interface UserManagementState {
  activeTab: UserManagementTab;
  filters: UserFilters;
  sort: UserSortOptions;
  selectedUsers: string[];
  isCreating: boolean;
  editingUser?: User;
}
