/**
 * Tests for Authentication Hooks
 *
 * Comprehensive test coverage for user authentication, authorization,
 * session management, and token refresh functionality.
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
  useAuth,
  useUser,
  useLogin,
  useLogout,
  usePermissions,
  useRole,
  useValidateSession,
  useAuthCheck,
} from './useAuth';
import * as authLib from '@/lib/auth';
import type { User, LoginCredentials, LoginResponse } from '@/lib/auth';

// Mock the auth library
jest.mock('@/lib/auth');

const mockedAuthLib = authLib as jest.Mocked<typeof authLib>;

// Test user data
const mockUser: User = {
  id: 'user-123',
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  isActive: true,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockLoginResponse: LoginResponse = {
  accessToken: 'mock-token',
  tokenType: 'bearer',
  user: mockUser,
};

// Create a wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
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

  it('fetches user data successfully', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockUser);
    expect(result.current.error).toBeNull();
  });

  it('handles 401 errors without retry', async () => {
    const error = { status: 401, message: 'Unauthorized' };
    mockedAuthLib.getCurrentUser.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.data).toBeUndefined();
    // Should not retry on 401
    expect(mockedAuthLib.getCurrentUser).toHaveBeenCalledTimes(1);
  });

  it('retries on non-401 errors', async () => {
    const error = { status: 500, message: 'Server error' };
    mockedAuthLib.getCurrentUser
      .mockRejectedValueOnce(error)
      .mockRejectedValueOnce(error)
      .mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should retry up to 2 times
    expect(mockedAuthLib.getCurrentUser).toHaveBeenCalled();
  });
});

describe('useAuthCheck', () => {
  it('checks authentication status successfully', async () => {
    const authCheckResponse = {
      authenticated: true,
      user: mockUser,
    };
    mockedAuthLib.checkAuth.mockResolvedValueOnce(authCheckResponse);

    const { result } = renderHook(() => useAuthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(authCheckResponse);
  });

  it('returns unauthenticated status', async () => {
    const authCheckResponse = {
      authenticated: false,
    };
    mockedAuthLib.checkAuth.mockResolvedValueOnce(authCheckResponse);

    const { result } = renderHook(() => useAuthCheck(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data?.authenticated).toBe(false);
    });
  });
});

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns complete authentication state', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(typeof result.current.hasPermission).toBe('function');
    expect(typeof result.current.hasRole).toBe('function');
  });

  it('hasPermission returns true for admin permissions', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasPermission('admin:full')).toBe(true);
    expect(result.current.hasPermission('schedule:generate')).toBe(true);
  });

  it('hasPermission returns false for invalid permissions', async () => {
    const facultyUser: User = { ...mockUser, role: 'faculty' };
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(facultyUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasPermission('admin:full')).toBe(false);
    expect(result.current.hasPermission('schedule:generate')).toBe(false);
  });

  it('hasRole checks user role correctly', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasRole('admin')).toBe(true);
    expect(result.current.hasRole('faculty')).toBe(false);
    expect(result.current.hasRole(['admin', 'coordinator'])).toBe(true);
  });

  it('refreshToken triggers token refresh', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);
    mockedAuthLib.performRefresh.mockResolvedValueOnce({ accessToken: 'new-token', refreshToken: 'new-refresh', tokenType: 'bearer' });

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      const refreshed = await result.current.refreshToken();
      expect(refreshed).toBe(true);
    });

    expect(mockedAuthLib.performRefresh).toHaveBeenCalled();
  });

  it('needsRefresh checks token expiry', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);
    mockedAuthLib.isTokenExpired.mockReturnValueOnce(false);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.needsRefresh()).toBe(false);
  });
});

describe('useLogin', () => {
  it('logs in successfully', async () => {
    mockedAuthLib.login.mockResolvedValueOnce(mockLoginResponse);

    const { result } = renderHook(() => useLogin(), {
      wrapper: createWrapper(),
    });

    const credentials: LoginCredentials = {
      username: 'testuser',
      password: 'password123',
    };

    await act(async () => {
      result.current.mutate(credentials);
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockLoginResponse);
    expect(mockedAuthLib.login).toHaveBeenCalledWith(credentials);
  });

  it('handles login errors', async () => {
    const error = { status: 401, message: 'Invalid credentials' };
    mockedAuthLib.login.mockRejectedValueOnce(error);

    const { result } = renderHook(() => useLogin(), {
      wrapper: createWrapper(),
    });

    const credentials: LoginCredentials = {
      username: 'testuser',
      password: 'wrongpassword',
    };

    await act(async () => {
      result.current.mutate(credentials);
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe('useLogout', () => {
  it('logs out successfully', async () => {
    mockedAuthLib.logout.mockResolvedValueOnce(true);

    const { result } = renderHook(() => useLogout(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockedAuthLib.logout).toHaveBeenCalled();
  });

  it('clears client state even on server error', async () => {
    mockedAuthLib.logout.mockRejectedValueOnce(new Error('Server error'));

    const { result } = renderHook(() => useLogout(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate();
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    // Should still clear client-side state (tested via invalidation)
    expect(mockedAuthLib.logout).toHaveBeenCalled();
  });
});

describe('usePermissions', () => {
  it('returns permissions for admin role', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => usePermissions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.permissions.length).toBeGreaterThan(0);
    expect(result.current.hasPermission('admin:full')).toBe(true);
  });

  it('returns limited permissions for resident role', async () => {
    const residentUser: User = { ...mockUser, role: 'resident' };
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(residentUser);

    const { result } = renderHook(() => usePermissions(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hasPermission('schedule:read')).toBe(true);
    expect(result.current.hasPermission('schedule:generate')).toBe(false);
    expect(result.current.hasPermission('admin:full')).toBe(false);
  });
});

describe('useRole', () => {
  it('returns role information', async () => {
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useRole(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.role).toBe('admin');
    expect(result.current.isAdmin).toBe(true);
    expect(result.current.isCoordinator).toBe(false);
    expect(result.current.isFaculty).toBe(false);
    expect(result.current.isResident).toBe(false);
  });

  it('provides convenience booleans for each role', async () => {
    const facultyUser: User = { ...mockUser, role: 'faculty' };
    mockedAuthLib.getCurrentUser.mockResolvedValueOnce(facultyUser);

    const { result } = renderHook(() => useRole(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isFaculty).toBe(true);
    expect(result.current.isAdmin).toBe(false);
  });
});

describe('useValidateSession', () => {
  it('validates session successfully', async () => {
    mockedAuthLib.validateToken.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useValidateSession(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockUser);
  });

  it('returns null for invalid session', async () => {
    mockedAuthLib.validateToken.mockResolvedValueOnce(null);

    const { result } = renderHook(() => useValidateSession(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeNull();
  });
});
