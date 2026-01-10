/**
 * Tests for Admin User Management Hooks
 *
 * Tests CRUD operations for user management including
 * filtering, pagination, bulk actions, and account locking.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useUsers,
  useUser,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useToggleUserLock,
  useResendInvite,
  useBulkUserAction,
} from '@/hooks/useAdminUsers';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data - raw API response format (snake_case)
const mockApiUser = {
  id: 'user-123',
  email: 'test@example.com',
  username: 'testuser',
  firstName: 'Test',
  lastName: 'User',
  role: 'faculty',
  isActive: true,
  isLocked: false,
  lockReason: null,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
  lastLogin: null,
  invite_sent_at: null,
  invite_accepted_at: null,
};

// Raw API response from backend
const mockApiUsersResponse = {
  items: [mockApiUser],
  total: 1,
  page: 1,
  pageSize: 20,
  totalPages: 1,
};

// Transformed frontend user format (camelCase)
const mockTransformedUser = {
  id: 'user-123',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: 'faculty',
  status: 'active',
  lastLogin: undefined,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
  mfaEnabled: false,
  failedLoginAttempts: 0,
  lockedUntil: undefined,
};

// Transformed response as returned by useUsers
const mockUsersResponse = {
  users: [mockTransformedUser],
  total: 1,
  page: 1,
  pageSize: 20,
  totalPages: 1,
};

// Create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useUsers', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches users list successfully and transforms response', async () => {
    // Mock returns raw API format (snake_case)
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse);

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Hook transforms to frontend format (camelCase)
    expect(result.current.data).toEqual(mockUsersResponse);
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users');
  });

  it('applies search filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse);

    const { result } = renderHook(
      () => useUsers({ search: 'test' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?search=test');
  });

  it('applies role filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse);

    const { result } = renderHook(
      () => useUsers({ role: 'faculty' }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?role=faculty');
  });

  it('applies pagination parameters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse);

    const { result } = renderHook(
      () => useUsers({ page: 2, pageSize: 50 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/admin/users?page=2&pageSize=50'
    );
  });

  it('handles errors', async () => {
    const error = { status: 500, message: 'Server error' };
    mockedApi.get.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe('useUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches single user successfully and transforms response', async () => {
    // Mock returns raw API format (snake_case)
    mockedApi.get.mockResolvedValueOnce(mockApiUser);

    const { result } = renderHook(() => useUser('user-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Hook transforms to frontend format (camelCase)
    expect(result.current.data).toEqual(mockTransformedUser);
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users/user-123');
  });

  it('does not fetch when id is empty', async () => {
    const { result } = renderHook(() => useUser(''), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).not.toHaveBeenCalled();
  });
});

describe('useCreateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('creates user successfully with snake_case payload', async () => {
    // API returns raw format
    const newApiUser = { ...mockApiUser, id: 'user-456' };
    mockedApi.post.mockResolvedValueOnce(newApiUser);

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createWrapper(),
    });

    // Frontend sends camelCase
    const createData = {
      email: 'new@example.com',
      firstName: 'New',
      lastName: 'User',
      role: 'resident' as const,
      sendInvite: true,
    };

    await act(async () => {
      result.current.mutate(createData);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Hook transforms to snake_case for API
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users', {
      email: 'new@example.com',
      firstName: 'New',
      lastName: 'User',
      role: 'resident',
      send_invite: true,
    });
  });

  it('handles duplicate email error', async () => {
    const error = { status: 409, message: 'Email already exists' };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        email: 'existing@example.com',
        firstName: 'Test',
        lastName: 'User',
        role: 'resident',
        sendInvite: false,
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe('useUpdateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('updates user successfully and transforms response', async () => {
    // API returns raw format
    const updatedApiUser = { ...mockApiUser, email: 'updated@example.com' };
    mockedApi.patch.mockResolvedValueOnce(updatedApiUser);

    const { result } = renderHook(() => useUpdateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'user-123',
        data: { email: 'updated@example.com' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Result is transformed to camelCase
    expect(result.current.data?.email).toBe('updated@example.com');
    expect(mockedApi.patch).toHaveBeenCalledWith('/admin/users/user-123', {
      email: 'updated@example.com',
    });
  });

  it('transforms firstName/lastName to snake_case', async () => {
    const updatedApiUser = { ...mockApiUser, firstName: 'Updated', lastName: 'Name' };
    mockedApi.patch.mockResolvedValueOnce(updatedApiUser);

    const { result } = renderHook(() => useUpdateUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        id: 'user-123',
        data: { firstName: 'Updated', lastName: 'Name' },
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Verify snake_case sent to API
    expect(mockedApi.patch).toHaveBeenCalledWith('/admin/users/user-123', {
      firstName: 'Updated',
      lastName: 'Name',
    });
  });
});

describe('useDeleteUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('deletes user successfully', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useDeleteUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-123');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedApi.del).toHaveBeenCalledWith('/admin/users/user-123');
  });

  it('handles deletion errors', async () => {
    const error = { status: 409, message: 'Cannot delete user with active assignments' };
    mockedApi.del.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useDeleteUser(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-123');
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useToggleUserLock', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('locks user successfully with locked field', async () => {
    // Backend returns this format
    const apiResponse = {
      userId: 'user-123',
      isLocked: true,
      lockReason: null,
      lockedAt: '2024-01-01T00:00:00Z',
      lockedBy: 'admin-1',
      message: 'User locked',
    };
    mockedApi.post.mockResolvedValueOnce(apiResponse);

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-123', lock: true });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Hook transforms response
    expect(result.current.data?.success).toBe(true);
    expect(result.current.data?.message).toBe('User locked');
    // Backend expects 'locked' field, not 'lock'
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-123/lock', {
      locked: true,
    });
  });

  it('unlocks user successfully', async () => {
    const apiResponse = {
      userId: 'user-123',
      isLocked: false,
      lockReason: null,
      lockedAt: null,
      lockedBy: null,
      message: 'User unlocked',
    };
    mockedApi.post.mockResolvedValueOnce(apiResponse);

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-123', lock: false });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data?.success).toBe(true);
    // Backend expects 'locked' field
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-123/lock', {
      locked: false,
    });
  });
});

describe('useResendInvite', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('resends invite successfully', async () => {
    const response = {
      success: true,
      message: 'Invitation sent',
    };
    mockedApi.post.mockResolvedValueOnce(response);

    const { result } = renderHook(() => useResendInvite(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-123');
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(response);
    expect(mockedApi.post).toHaveBeenCalledWith(
      '/admin/users/user-123/resend-invite'
    );
  });

  it('handles errors for non-pending users', async () => {
    const error = { status: 400, message: 'User is not pending' };
    mockedApi.post.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useResendInvite(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate('user-123');
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe('useBulkUserAction', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('performs bulk activate action with snake_case payload', async () => {
    // Backend returns this format
    const apiResponse = {
      action: 'activate',
      affectedCount: 5,
      successIds: ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'],
      failedIds: [],
      errors: [],
      message: '5 users activated',
    };
    mockedApi.post.mockResolvedValueOnce(apiResponse);

    const { result } = renderHook(() => useBulkUserAction(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        userIds: ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'],
        action: 'activate',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Hook transforms response
    expect(result.current.data?.success).toBe(true);
    expect(result.current.data?.affected).toBe(5);
    // Backend expects snake_case 'userIds'
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/bulk', {
      userIds: ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'],
      action: 'activate',
    });
  });

  it('reports partial success with failures', async () => {
    const apiResponse = {
      action: 'activate',
      affectedCount: 3,
      successIds: ['user-1', 'user-3', 'user-5'],
      failedIds: ['user-2', 'user-4'],
      errors: ['User user-2 not found', 'User user-4 has active assignments'],
      message: '3 users activated, 2 failures',
    };
    mockedApi.post.mockResolvedValueOnce(apiResponse);

    const { result } = renderHook(() => useBulkUserAction(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        userIds: ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'],
        action: 'activate',
      });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Hook transforms: success is false when there are failures
    expect(result.current.data?.success).toBe(false);
    expect(result.current.data?.failures).toHaveLength(2);
  });

  it('performs bulk delete action', async () => {
    const apiResponse = {
      action: 'delete',
      affectedCount: 2,
      successIds: ['user-1', 'user-2'],
      failedIds: [],
      errors: [],
      message: '2 users deleted',
    };
    mockedApi.post.mockResolvedValueOnce(apiResponse);

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

    expect(result.current.data?.affected).toBe(2);
  });
});
