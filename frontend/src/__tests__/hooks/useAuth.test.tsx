/**
 * useAuth Hooks Tests
 *
 * Tests for authentication hooks including login, logout, user queries,
 * permissions, roles, and token refresh functionality.
 */
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useUser,
  useAuth,
  useAuthCheck,
  useLogin,
  useLogout,
  useValidateSession,
  usePermissions,
  useRole,
} from '@/hooks/useAuth';
import * as authLib from '@/lib/auth';

// Mock the auth library
jest.mock('@/lib/auth');
const mockedAuth = authLib as jest.Mocked<typeof authLib>;

// Mock ApiError - the real ApiError is an interface, not a class
class MockApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// Test wrapper with QueryClient
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

describe('useUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch current user successfully', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'dr.smith',
      email: 'smith@example.com',
      role: 'coordinator',
      isActive: true,
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedAuth.getCurrentUser).toHaveBeenCalled();
    expect(result.current.data).toEqual(mockUser);
  });

  it('should handle unauthorized error (401)', async () => {
    const mockError = new MockApiError('Unauthorized', 401);
    mockedAuth.getCurrentUser.mockRejectedValue(mockError);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect((result.current.error as MockApiError)?.status).toBe(401);
    // Should not retry on 401
    expect(mockedAuth.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  it('should show loading state initially', () => {
    const mockUser = {
      id: 'user-123',
      username: 'dr.smith',
      email: 'smith@example.com',
      role: 'admin',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});

describe('useAuthCheck', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should check auth status for authenticated user', async () => {
    const mockAuthResponse = {
      authenticated: true,
      user: {
        id: 'user-123',
        username: 'dr.smith',
        email: 'smith@example.com',
        role: 'faculty',
      },
    };

    mockedAuth.checkAuth.mockResolvedValue(mockAuthResponse);

    const { result } = renderHook(() => useAuthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.authenticated).toBe(true);
    expect(result.current.data?.user?.username).toBe('dr.smith');
  });

  it('should check auth status for unauthenticated user', async () => {
    const mockAuthResponse = {
      authenticated: false,
    };

    mockedAuth.checkAuth.mockResolvedValue(mockAuthResponse);

    const { result } = renderHook(() => useAuthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.authenticated).toBe(false);
  });
});

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should provide complete auth state with permissions', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'coordinator',
      email: 'coord@example.com',
      role: 'coordinator',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.hasPermission).toBeDefined();
    expect(result.current.hasRole).toBeDefined();
  });

  it('should check permissions correctly for coordinator role', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'coordinator',
      role: 'coordinator',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    // Coordinator has schedule generation permission
    expect(result.current.hasPermission('schedule:generate')).toBe(true);
    // Coordinator does NOT have admin:full permission
    expect(result.current.hasPermission('admin:full')).toBe(false);
  });

  it('should check permissions correctly for resident role', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'resident',
      role: 'resident',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    // Resident has read permissions
    expect(result.current.hasPermission('schedule:read')).toBe(true);
    // Resident does NOT have schedule generation permission
    expect(result.current.hasPermission('schedule:generate')).toBe(false);
  });

  it('should check role correctly', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'admin',
      role: 'admin',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole(['admin', 'coordinator'])).toBe(true);
    expect(result.current.hasRole('resident')).toBe(false);
  });

  it('should provide token refresh methods', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'admin',
      role: 'admin',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isAuthenticated).toBe(true));

    expect(result.current.refreshToken).toBeDefined();
    expect(result.current.getTokenExpiry).toBeDefined();
    expect(result.current.needsRefresh).toBeDefined();
  });
});

describe('useLogin', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should login successfully with valid credentials', async () => {
    const mockResponse = {
      accessToken: 'token-123',
      user: {
        id: 'user-123',
        username: 'dr.smith',
        email: 'smith@example.com',
        role: 'admin',
      },
    };

    mockedAuth.login.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useLogin(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      username: 'dr.smith',
      password: 'password123',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // TanStack Query v5 passes mutation context as second argument
    expect(mockedAuth.login.mock.calls[0][0]).toEqual({
      username: 'dr.smith',
      password: 'password123',
    });
    expect(result.current.data?.user.username).toBe('dr.smith');
  });

  it('should handle invalid credentials error', async () => {
    const mockError = new MockApiError('Invalid credentials', 401);
    mockedAuth.login.mockRejectedValue(mockError);

    const { result } = renderHook(() => useLogin(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      username: 'wrong',
      password: 'wrong',
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect((result.current.error as MockApiError)?.status).toBe(401);
    expect(result.current.error?.message).toBe('Invalid credentials');
  });

  it('should show pending state during login', async () => {
    // Use a promise we control to keep the mutation pending
    let resolveLogin: (value: unknown) => void;
    const loginPromise = new Promise((resolve) => {
      resolveLogin = resolve;
    });
    mockedAuth.login.mockReturnValue(loginPromise as Promise<unknown>);

    const { result } = renderHook(() => useLogin(), {
      wrapper: createWrapper(),
    });

    result.current.mutate({
      username: 'dr.smith',
      password: 'password123',
    });

    await waitFor(() => expect(result.current.isPending).toBe(true));

    // Clean up
    resolveLogin!({
      accessToken: 'token-123',
      user: { id: 'user-123', username: 'dr.smith', role: 'admin' },
    });
  });
});

describe('useLogout', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should logout successfully', async () => {
    mockedAuth.logout.mockResolvedValue(true);

    const { result } = renderHook(() => useLogout(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockedAuth.logout).toHaveBeenCalled();
  });

  it('should clear local state even if server logout fails', async () => {
    mockedAuth.logout.mockResolvedValue(false);

    const { result } = renderHook(() => useLogout(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Should still complete successfully
    expect(result.current.isSuccess).toBe(true);
  });

  it('should clear local state on error', async () => {
    const mockError = new MockApiError('Network error', 500);
    mockedAuth.logout.mockRejectedValue(mockError);

    const { result } = renderHook(() => useLogout(), {
      wrapper: createWrapper(),
    });

    result.current.mutate();

    await waitFor(() => expect(result.current.isError).toBe(true));

    // Error thrown but local state should be cleared by onError
    expect(result.current.isError).toBe(true);
  });
});

describe('useValidateSession', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should validate session with valid token', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'dr.smith',
      role: 'faculty',
    };

    mockedAuth.validateToken.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useValidateSession(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockUser);
  });

  it('should return null for invalid token', async () => {
    mockedAuth.validateToken.mockResolvedValue(null);

    const { result } = renderHook(() => useValidateSession(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeNull();
  });
});

describe('usePermissions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return permissions for admin role', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'admin',
      role: 'admin',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => usePermissions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.hasPermission('admin:full')).toBe(true);
    expect(result.current.hasPermission('schedule:generate')).toBe(true);
    expect(result.current.permissions.length).toBeGreaterThan(0);
  });

  it('should return limited permissions for resident role', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'resident',
      role: 'resident',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => usePermissions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.hasPermission('schedule:read')).toBe(true);
    expect(result.current.hasPermission('admin:full')).toBe(false);
    expect(result.current.hasPermission('schedule:generate')).toBe(false);
  });
});

describe('useRole', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should return role and convenience booleans', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'coordinator',
      role: 'coordinator',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useRole(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.role).toBe('coordinator');
    expect(result.current.isCoordinator).toBe(true);
    expect(result.current.isAdmin).toBe(false);
    expect(result.current.isFaculty).toBe(false);
    expect(result.current.isResident).toBe(false);
  });

  it('should check role with array of roles', async () => {
    const mockUser = {
      id: 'user-123',
      username: 'faculty',
      role: 'faculty',
    };

    mockedAuth.getCurrentUser.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useRole(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.hasRole(['faculty', 'coordinator'])).toBe(true);
    expect(result.current.hasRole(['admin', 'coordinator'])).toBe(false);
  });
});
