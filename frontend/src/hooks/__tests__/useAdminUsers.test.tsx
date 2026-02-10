/**
 * Tests for useAdminUsers hooks.
 *
 * Tests cover:
 * - Query key structure
 * - useUsers: list fetching with filters and transform
 * - useUser: single user fetch with transform
 * - useActivityLog: activity log fetching with filters
 * - useCreateUser: user creation mutation
 * - useUpdateUser: user update mutation
 * - useDeleteUser: user deletion mutation
 * - useToggleUserLock: lock/unlock mutation
 * - useResendInvite: resend invite mutation
 * - useBulkUserAction: bulk action mutation
 * - Error handling across all hooks
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

import {
  useUsers,
  useUser,
  useActivityLog,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useToggleUserLock,
  useResendInvite,
  useBulkUserAction,
  adminUsersQueryKeys,
} from '../useAdminUsers';

// ============================================================================
// Mocks
// ============================================================================

jest.mock('@/lib/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  patch: jest.fn(),
  del: jest.fn(),
}));

import { get, post, patch, del } from '@/lib/api';

const mockGet = get as jest.Mock;
const mockPost = post as jest.Mock;
const mockPatch = patch as jest.Mock;
const mockDel = del as jest.Mock;

// ============================================================================
// Test Setup
// ============================================================================

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

// ============================================================================
// Test Data
// ============================================================================

const mockApiUser = {
  id: 'user-1',
  username: 'jdoe',
  email: 'jdoe@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'resident',
  isActive: true,
  isLocked: false,
  lockReason: null,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-06-01T00:00:00Z',
  lastLogin: '2025-06-15T10:00:00Z',
  inviteSentAt: null,
  inviteAcceptedAt: null,
};

const mockApiUserLocked = {
  ...mockApiUser,
  id: 'user-2',
  isLocked: true,
};

const mockApiUserPending = {
  ...mockApiUser,
  id: 'user-3',
  inviteSentAt: '2025-01-01T00:00:00Z',
  inviteAcceptedAt: null,
};

const mockApiUserInactive = {
  ...mockApiUser,
  id: 'user-4',
  isActive: false,
};

const mockListResponse = {
  items: [mockApiUser, mockApiUserLocked],
  total: 2,
  page: 1,
  pageSize: 10,
  totalPages: 1,
};

const mockActivityLogResponse = {
  items: [
    {
      id: 'log-1',
      userId: 'user-1',
      action: 'login',
      timestamp: '2025-06-15T10:00:00Z',
    },
  ],
  total: 1,
  page: 1,
  pageSize: 10,
  totalPages: 1,
};

// ============================================================================
// Query Keys Tests
// ============================================================================

describe('adminUsersQueryKeys', () => {
  it('should have correct base key', () => {
    expect(adminUsersQueryKeys.all).toEqual(['admin', 'users']);
  });

  it('should generate correct list key without filters', () => {
    expect(adminUsersQueryKeys.list()).toEqual([
      'admin', 'users', 'list', undefined,
    ]);
  });

  it('should generate correct list key with filters', () => {
    const filters = { search: 'john', role: 'resident' as const };
    expect(adminUsersQueryKeys.list(filters)).toEqual([
      'admin', 'users', 'list', filters,
    ]);
  });

  it('should generate correct detail key', () => {
    expect(adminUsersQueryKeys.detail('user-1')).toEqual([
      'admin', 'users', 'detail', 'user-1',
    ]);
  });

  it('should generate correct activity key', () => {
    const filters = { userId: 'user-1' };
    expect(adminUsersQueryKeys.activity(filters)).toEqual([
      'admin', 'activity', filters,
    ]);
  });
});

// ============================================================================
// useUsers Tests
// ============================================================================

describe('useUsers', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch users and transform API response', async () => {
    mockGet.mockResolvedValueOnce(mockListResponse);

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/admin/users');
    expect(result.current.data?.users).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);

    // Check first user transformed correctly (active)
    const user1 = result.current.data?.users[0];
    expect(user1?.id).toBe('user-1');
    expect(user1?.status).toBe('active');
    expect(user1?.firstName).toBe('John');
    expect(user1?.lastName).toBe('Doe');

    // Check second user transformed correctly (locked)
    const user2 = result.current.data?.users[1];
    expect(user2?.id).toBe('user-2');
    expect(user2?.status).toBe('locked');
  });

  it('should pass search filter as query param', async () => {
    mockGet.mockResolvedValueOnce({ ...mockListResponse, items: [] });

    const { result } = renderHook(
      () => useUsers({ search: 'john' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('search=john')
    );
  });

  it('should pass role filter excluding "all"', async () => {
    mockGet.mockResolvedValueOnce({ ...mockListResponse, items: [] });

    const { result } = renderHook(
      () => useUsers({ role: 'resident' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith(
      expect.stringContaining('role=resident')
    );
  });

  it('should not pass role filter when "all"', async () => {
    mockGet.mockResolvedValueOnce({ ...mockListResponse, items: [] });

    const { result } = renderHook(
      () => useUsers({ role: 'all' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/admin/users');
  });

  it('should pass pagination params', async () => {
    mockGet.mockResolvedValueOnce({ ...mockListResponse, items: [] });

    const { result } = renderHook(
      () => useUsers({ page: 2, pageSize: 25 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('page=2');
    expect(url).toContain('page_size=25');
  });

  it('should derive status correctly for each user state', async () => {
    mockGet.mockResolvedValueOnce({
      items: [mockApiUser, mockApiUserLocked, mockApiUserPending, mockApiUserInactive],
      total: 4,
      page: 1,
      pageSize: 10,
      totalPages: 1,
    });

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const users = result.current.data?.users;
    expect(users?.[0].status).toBe('active');
    expect(users?.[1].status).toBe('locked');
    expect(users?.[2].status).toBe('pending');
    expect(users?.[3].status).toBe('inactive');
  });

  it('should handle API error', async () => {
    const apiError = { message: 'Unauthorized', status: 401 };
    mockGet.mockRejectedValueOnce(apiError);

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

// ============================================================================
// useUser Tests
// ============================================================================

describe('useUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch a single user and transform', async () => {
    mockGet.mockResolvedValueOnce(mockApiUser);

    const { result } = renderHook(() => useUser('user-1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/admin/users/user-1');
    expect(result.current.data?.id).toBe('user-1');
    expect(result.current.data?.email).toBe('jdoe@example.com');
    expect(result.current.data?.status).toBe('active');
  });

  it('should not fetch when id is empty', () => {
    const { result } = renderHook(() => useUser(''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
    expect(mockGet).not.toHaveBeenCalled();
  });
});

// ============================================================================
// useActivityLog Tests
// ============================================================================

describe('useActivityLog', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch activity logs', async () => {
    mockGet.mockResolvedValueOnce(mockActivityLogResponse);

    const { result } = renderHook(() => useActivityLog(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockGet).toHaveBeenCalledWith('/admin/users/activity-log');
    expect(result.current.data?.items).toHaveLength(1);
  });

  it('should pass filters as query params', async () => {
    mockGet.mockResolvedValueOnce(mockActivityLogResponse);

    const { result } = renderHook(
      () =>
        useActivityLog({
          userId: 'user-1',
          dateFrom: '2025-01-01',
          dateTo: '2025-06-30',
          page: 1,
          pageSize: 20,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('user_id=user-1');
    expect(url).toContain('date_from=2025-01-01');
    expect(url).toContain('date_to=2025-06-30');
    expect(url).toContain('page=1');
    expect(url).toContain('page_size=20');
  });
});

// ============================================================================
// useCreateUser Tests
// ============================================================================

describe('useCreateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should create a user and return transformed result', async () => {
    mockPost.mockResolvedValueOnce(mockApiUser);

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        email: 'jdoe@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'resident',
        sendInvite: true,
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/admin/users', {
      email: 'jdoe@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'resident',
      send_invite: true,
    });

    expect(result.current.data?.id).toBe('user-1');
    expect(result.current.data?.status).toBe('active');
  });

  it('should handle creation error', async () => {
    mockPost.mockRejectedValueOnce({ message: 'Conflict', status: 409 });

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        email: 'jdoe@example.com',
        firstName: 'John',
        lastName: 'Doe',
        role: 'resident',
        sendInvite: false,
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useUpdateUser Tests
// ============================================================================

describe('useUpdateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should update a user with partial data', async () => {
    mockPatch.mockResolvedValueOnce({
      ...mockApiUser,
      firstName: 'Jane',
    });

    const { result } = renderHook(() => useUpdateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'user-1',
        data: { firstName: 'Jane' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith('/admin/users/user-1', {
      firstName: 'Jane',
    });
    expect(result.current.data?.firstName).toBe('Jane');
  });

  it('should map status to isActive when updating status', async () => {
    mockPatch.mockResolvedValueOnce(mockApiUserInactive);

    const { result } = renderHook(() => useUpdateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'user-4',
        data: { status: 'active' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPatch).toHaveBeenCalledWith('/admin/users/user-4', {
      isActive: true,
    });
  });
});

// ============================================================================
// useDeleteUser Tests
// ============================================================================

describe('useDeleteUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should delete a user', async () => {
    mockDel.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-1');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockDel).toHaveBeenCalledWith('/admin/users/user-1');
  });

  it('should handle deletion error', async () => {
    mockDel.mockRejectedValueOnce({ message: 'Not found', status: 404 });

    const { result } = renderHook(() => useDeleteUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('nonexistent');
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

// ============================================================================
// useToggleUserLock Tests
// ============================================================================

describe('useToggleUserLock', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should lock a user', async () => {
    mockPost.mockResolvedValueOnce({
      userId: 'user-1',
      isLocked: true,
      lockReason: null,
      lockedAt: '2025-06-15T10:00:00Z',
      lockedBy: 'admin-1',
      message: 'User locked successfully',
    });

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-1', lock: true });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/admin/users/user-1/lock', {
      locked: true,
    });
    expect(result.current.data?.success).toBe(true);
    expect(result.current.data?.message).toBe('User locked successfully');
  });

  it('should unlock a user', async () => {
    mockPost.mockResolvedValueOnce({
      userId: 'user-1',
      isLocked: false,
      lockReason: null,
      lockedAt: null,
      lockedBy: null,
      message: 'User unlocked successfully',
    });

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-1', lock: false });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/admin/users/user-1/lock', {
      locked: false,
    });
  });
});

// ============================================================================
// useResendInvite Tests
// ============================================================================

describe('useResendInvite', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should resend invite', async () => {
    const mockResponse = { success: true, message: 'Invite resent' };
    mockPost.mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useResendInvite(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-3');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith(
      '/admin/users/user-3/resend-invite'
    );
    expect(result.current.data?.success).toBe(true);
  });
});

// ============================================================================
// useBulkUserAction Tests
// ============================================================================

describe('useBulkUserAction', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should perform bulk action and transform response', async () => {
    mockPost.mockResolvedValueOnce({
      action: 'deactivate',
      affectedCount: 2,
      successIds: ['user-1', 'user-2'],
      failedIds: [],
      errors: [],
      message: '2 users deactivated',
    });

    const { result } = renderHook(() => useBulkUserAction(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        userIds: ['user-1', 'user-2'],
        action: 'deactivate',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockPost).toHaveBeenCalledWith('/admin/users/bulk', {
      userIds: ['user-1', 'user-2'],
      action: 'deactivate',
    });
    expect(result.current.data?.success).toBe(true);
    expect(result.current.data?.affected).toBe(2);
    expect(result.current.data?.failures).toEqual([]);
  });

  it('should report partial failures', async () => {
    mockPost.mockResolvedValueOnce({
      action: 'delete',
      affectedCount: 1,
      successIds: ['user-1'],
      failedIds: ['user-2'],
      errors: ['user-2: Cannot delete admin user'],
      message: 'Partially completed',
    });

    const { result } = renderHook(() => useBulkUserAction(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        userIds: ['user-1', 'user-2'],
        action: 'delete',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.success).toBe(false);
    expect(result.current.data?.affected).toBe(1);
    expect(result.current.data?.failures).toEqual([
      'user-2: Cannot delete admin user',
    ]);
  });
});
