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
} from './useAdminUsers';
import * as api from '@/lib/api';

// Mock the API module
jest.mock('@/lib/api');

const mockedApi = api as jest.Mocked<typeof api>;

// Test data
const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  username: 'testuser',
  role: 'faculty' as const,
  status: 'active' as const,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockUsersResponse = {
  users: [mockUser],
  total: 1,
  page: 1,
  pageSize: 20,
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

  it('fetches users list successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockUsersResponse);

    const { result } = renderHook(() => useUsers(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockUsersResponse);
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users');
  });

  it('applies search filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockUsersResponse);

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
    mockedApi.get.mockResolvedValueOnce(mockUsersResponse);

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
    mockedApi.get.mockResolvedValueOnce(mockUsersResponse);

    const { result } = renderHook(
      () => useUsers({ page: 2, pageSize: 50 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockedApi.get).toHaveBeenCalledWith(
      '/admin/users?page=2&page_size=50'
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
  it('fetches single user successfully', async () => {
    mockedApi.get.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useUser('user-123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockUser);
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
  it('creates user successfully', async () => {
    const newUser = { ...mockUser, id: 'user-456' };
    mockedApi.post.mockResolvedValueOnce(newUser);

    const { result } = renderHook(() => useCreateUser(), {
      wrapper: createWrapper(),
    });

    const createData = {
      email: 'new@example.com',
      username: 'newuser',
      role: 'resident' as const,
      password: 'password123',
    };

    await act(async () => {
      result.current.mutate(createData);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(newUser);
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users', createData);
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
        username: 'test',
        role: 'resident',
        password: 'pass',
      });
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe('useUpdateUser', () => {
  it('updates user successfully', async () => {
    const updatedUser = { ...mockUser, email: 'updated@example.com' };
    mockedApi.patch.mockResolvedValueOnce(updatedUser);

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

    expect(result.current.data).toEqual(updatedUser);
    expect(mockedApi.patch).toHaveBeenCalledWith('/admin/users/user-123', {
      email: 'updated@example.com',
    });
  });
});

describe('useDeleteUser', () => {
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
  it('locks user successfully', async () => {
    const lockedUser = { ...mockUser, status: 'locked' as const };
    const response = {
      success: true,
      user: lockedUser,
      message: 'User locked',
    };
    mockedApi.post.mockResolvedValueOnce(response);

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-123', lock: true });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(response);
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-123/lock', {
      lock: true,
    });
  });

  it('unlocks user successfully', async () => {
    const unlockedUser = { ...mockUser, status: 'active' as const };
    const response = {
      success: true,
      user: unlockedUser,
      message: 'User unlocked',
    };
    mockedApi.post.mockResolvedValueOnce(response);

    const { result } = renderHook(() => useToggleUserLock(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ id: 'user-123', lock: false });
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(response);
  });
});

describe('useResendInvite', () => {
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
  it('performs bulk activate action', async () => {
    const response = {
      success: true,
      affected: 5,
      failures: [],
      message: '5 users activated',
    };
    mockedApi.post.mockResolvedValueOnce(response);

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

    expect(result.current.data).toEqual(response);
    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/bulk', {
      userIds: ['user-1', 'user-2', 'user-3', 'user-4', 'user-5'],
      action: 'activate',
    });
  });

  it('reports partial success with failures', async () => {
    const response = {
      success: true,
      affected: 3,
      failures: ['user-2', 'user-4'],
      message: '3 users activated, 2 failures',
    };
    mockedApi.post.mockResolvedValueOnce(response);

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

    expect(result.current.data?.failures).toHaveLength(2);
  });

  it('performs bulk delete action', async () => {
    const response = {
      success: true,
      affected: 2,
      failures: [],
      message: '2 users deleted',
    };
    mockedApi.post.mockResolvedValueOnce(response);

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
