/**
 * useAdminUsers Hook Tests
 *
 * Tests for admin user management hooks including CRUD operations,
 * user locking, invitations, and bulk actions.
 */
import { renderHook, waitFor } from '@/test-utils'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import * as api from '@/lib/api'
import {
  useUsers,
  useUser,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
  useToggleUserLock,
  useResendInvite,
  useBulkUserAction,
  type AdminUserFilters,
  type User,
  type UserCreate,
  type UserUpdate,
  type UsersResponse,
  type LockUserResponse,
  type ResendInviteResponse,
  type BulkActionResponse,
} from '@/hooks/useAdminUsers'
import type {
  AdminUserApiResponse,
  AdminUserListApiResponse,
  BulkActionRequest,
} from '@/types/admin-users'

// Mock the api module
jest.mock('@/lib/api')

const mockedApi = api as jest.Mocked<typeof api>

// Mock data
const mockUser: User = {
  id: 'user-1',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'resident',
  status: 'active',
  lastLogin: '2026-02-05T12:00:00Z',
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-02-01T00:00:00Z',
  mfaEnabled: false,
  failedLoginAttempts: 0,
}

const mockApiUser: AdminUserApiResponse = {
  id: 'user-1',
  username: 'test@example.com',
  email: 'test@example.com',
  firstName: 'John',
  lastName: 'Doe',
  role: 'resident',
  isActive: true,
  isLocked: false,
  lockReason: null,
  createdAt: '2026-01-01T00:00:00Z',
  updatedAt: '2026-02-01T00:00:00Z',
  lastLogin: '2026-02-05T12:00:00Z',
  inviteSentAt: null,
  inviteAcceptedAt: null,
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for reference/future tests
const mockUsersResponse: UsersResponse = {
  users: [mockUser],
  total: 1,
  page: 1,
  pageSize: 20,
  totalPages: 1,
}

const mockApiUsersResponse: AdminUserListApiResponse = {
  items: [mockApiUser],
  total: 1,
  page: 1,
  pageSize: 20,
  totalPages: 1,
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for reference/future tests
const mockLockResponse: LockUserResponse = {
  success: true,
  user: mockUser,
  message: 'User locked successfully',
}

const mockResendInviteResponse: ResendInviteResponse = {
  success: true,
  message: 'Invitation resent successfully',
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars -- kept for reference/future tests
const mockBulkActionResponse: BulkActionResponse = {
  success: true,
  affected: 2,
  failures: [],
  message: 'Bulk action completed successfully',
}

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Wrapper component with QueryClientProvider
function createWrapper() {
  const queryClient = createTestQueryClient()
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('useUsers', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch users without filters', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const { result } = renderHook(
      () => useUsers(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.users).toHaveLength(1)
    expect(result.current.data?.total).toBe(1)
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users')
  })

  it('should fetch users with search filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { search: 'john' }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?search=john')
  })

  it('should fetch users with role filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { role: 'resident' }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?role=resident')
  })

  it('should fetch users with status filter', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { status: 'active' }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?status=active')
  })

  it('should fetch users with pagination', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { page: 2, pageSize: 10 }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users?page=2&page_size=10')
  })

  it('should handle error when fetching users', async () => {
    const mockError = Object.assign(new Error('Failed to fetch'), {
      status: 500,
      message: 'Server error',
    })
    mockedApi.get.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useUsers(),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })

  it('should skip role filter when set to "all"', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { role: 'all' }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users')
  })

  it('should skip status filter when set to "all"', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUsersResponse)

    const filters: AdminUserFilters = { status: 'all' }
    const { result } = renderHook(
      () => useUsers(filters),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users')
  })
})

describe('useUser', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch single user by ID', async () => {
    mockedApi.get.mockResolvedValueOnce(mockApiUser)

    const { result } = renderHook(
      () => useUser('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.id).toBe('user-1')
    expect(result.current.data?.email).toBe('test@example.com')
    expect(mockedApi.get).toHaveBeenCalledWith('/admin/users/user-1')
  })

  it('should not fetch when ID is empty', async () => {
    const { result } = renderHook(
      () => useUser(''),
      { wrapper: createWrapper() }
    )

    expect(result.current.isFetching).toBe(false)
    expect(mockedApi.get).not.toHaveBeenCalled()
  })

  it('should handle error when fetching single user', async () => {
    const mockError = Object.assign(new Error('Not found'), {
      status: 404,
      message: 'User not found',
    })
    mockedApi.get.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useUser('user-999'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })

  it('should derive status as "locked" when isLocked is true', async () => {
    const lockedUser = { ...mockApiUser, isLocked: true }
    mockedApi.get.mockResolvedValueOnce(lockedUser)

    const { result } = renderHook(
      () => useUser('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('locked')
  })

  it('should derive status as "inactive" when isActive is false', async () => {
    const inactiveUser = { ...mockApiUser, isActive: false }
    mockedApi.get.mockResolvedValueOnce(inactiveUser)

    const { result } = renderHook(
      () => useUser('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('inactive')
  })

  it('should derive status as "pending" when invite sent but not accepted', async () => {
    const pendingUser = {
      ...mockApiUser,
      inviteSentAt: '2026-02-01T00:00:00Z',
      inviteAcceptedAt: null,
    }
    mockedApi.get.mockResolvedValueOnce(pendingUser)

    const { result } = renderHook(
      () => useUser('user-1'),
      { wrapper: createWrapper() }
    )

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.status).toBe('pending')
  })
})

describe('useCreateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create a new user', async () => {
    mockedApi.post.mockResolvedValueOnce(mockApiUser)

    const { result } = renderHook(
      () => useCreateUser(),
      { wrapper: createWrapper() }
    )

    const newUser: UserCreate = {
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'resident',
      sendInvite: true,
    }

    result.current.mutate(newUser)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users', {
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'resident',
      sendInvite: true,
    })
  })

  it('should handle error when creating user', async () => {
    const mockError = Object.assign(new Error('Conflict'), {
      status: 409,
      message: 'User already exists',
    })
    mockedApi.post.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useCreateUser(),
      { wrapper: createWrapper() }
    )

    const newUser: UserCreate = {
      email: 'existing@example.com',
      firstName: 'Jane',
      lastName: 'Smith',
      role: 'faculty',
      sendInvite: false,
    }

    result.current.mutate(newUser)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useUpdateUser', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should update an existing user', async () => {
    const updatedApiUser = { ...mockApiUser, firstName: 'Jane' }
    mockedApi.patch.mockResolvedValueOnce(updatedApiUser)

    const { result } = renderHook(
      () => useUpdateUser(),
      { wrapper: createWrapper() }
    )

    const update: UserUpdate = {
      firstName: 'Jane',
    }

    result.current.mutate({ id: 'user-1', data: update })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.patch).toHaveBeenCalledWith('/admin/users/user-1', {
      firstName: 'Jane',
    })
  })

  it('should map status to isActive when updating', async () => {
    mockedApi.patch.mockResolvedValueOnce(mockApiUser)

    const { result } = renderHook(
      () => useUpdateUser(),
      { wrapper: createWrapper() }
    )

    const update: UserUpdate = {
      status: 'active',
    }

    result.current.mutate({ id: 'user-1', data: update })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.patch).toHaveBeenCalledWith('/admin/users/user-1', {
      isActive: true,
    })
  })

  it('should handle error when updating user', async () => {
    const mockError = Object.assign(new Error('Forbidden'), {
      status: 403,
      message: 'Insufficient permissions',
    })
    mockedApi.patch.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useUpdateUser(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({ id: 'user-1', data: { role: 'admin' } })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useDeleteUser', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should delete a user', async () => {
    mockedApi.del.mockResolvedValueOnce(undefined)

    const { result } = renderHook(
      () => useDeleteUser(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('user-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.del).toHaveBeenCalledWith('/admin/users/user-1')
  })

  it('should handle error when deleting user', async () => {
    const mockError = Object.assign(new Error('Not found'), {
      status: 404,
      message: 'User not found',
    })
    mockedApi.del.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useDeleteUser(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('user-999')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useToggleUserLock', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should lock a user', async () => {
    const lockApiResponse = {
      userId: 'user-1',
      isLocked: true,
      lockReason: 'Security violation',
      lockedAt: '2026-02-05T12:00:00Z',
      lockedBy: 'admin-1',
      message: 'User locked successfully',
    }
    mockedApi.post.mockResolvedValueOnce(lockApiResponse)

    const { result } = renderHook(
      () => useToggleUserLock(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({ id: 'user-1', lock: true })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-1/lock', {
      locked: true,
    })
  })

  it('should unlock a user', async () => {
    const unlockApiResponse = {
      userId: 'user-1',
      isLocked: false,
      lockReason: null,
      lockedAt: null,
      lockedBy: null,
      message: 'User unlocked successfully',
    }
    mockedApi.post.mockResolvedValueOnce(unlockApiResponse)

    const { result } = renderHook(
      () => useToggleUserLock(),
      { wrapper: createWrapper() }
    )

    result.current.mutate({ id: 'user-1', lock: false })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-1/lock', {
      locked: false,
    })
  })
})

describe('useResendInvite', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should resend invitation', async () => {
    mockedApi.post.mockResolvedValueOnce(mockResendInviteResponse)

    const { result } = renderHook(
      () => useResendInvite(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('user-1')

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/user-1/resend-invite')
  })

  it('should handle error when resending invite', async () => {
    const mockError = Object.assign(new Error('Bad request'), {
      status: 400,
      message: 'User has already accepted invitation',
    })
    mockedApi.post.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useResendInvite(),
      { wrapper: createWrapper() }
    )

    result.current.mutate('user-1')

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})

describe('useBulkUserAction', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should perform bulk activation', async () => {
    const bulkApiResponse = {
      action: 'activate',
      affectedCount: 2,
      successIds: ['user-1', 'user-2'],
      failedIds: [],
      errors: [],
      message: 'Bulk activation completed successfully',
    }
    mockedApi.post.mockResolvedValueOnce(bulkApiResponse)

    const { result } = renderHook(
      () => useBulkUserAction(),
      { wrapper: createWrapper() }
    )

    const request: BulkActionRequest = {
      userIds: ['user-1', 'user-2'],
      action: 'activate',
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(mockedApi.post).toHaveBeenCalledWith('/admin/users/bulk', {
      userIds: ['user-1', 'user-2'],
      action: 'activate',
    })
    expect(result.current.data?.success).toBe(true)
    expect(result.current.data?.affected).toBe(2)
  })

  it('should handle partial failures in bulk action', async () => {
    const bulkApiResponse = {
      action: 'delete',
      affectedCount: 1,
      successIds: ['user-1'],
      failedIds: ['user-2'],
      errors: ['User user-2 not found'],
      message: 'Bulk delete partially completed',
    }
    mockedApi.post.mockResolvedValueOnce(bulkApiResponse)

    const { result } = renderHook(
      () => useBulkUserAction(),
      { wrapper: createWrapper() }
    )

    const request: BulkActionRequest = {
      userIds: ['user-1', 'user-2'],
      action: 'delete',
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data?.success).toBe(false)
    expect(result.current.data?.affected).toBe(1)
    expect(result.current.data?.failures).toHaveLength(1)
  })

  it('should handle error in bulk action', async () => {
    const mockError = Object.assign(new Error('Server error'), {
      status: 500,
      message: 'Failed to process bulk action',
    })
    mockedApi.post.mockRejectedValueOnce(mockError)

    const { result } = renderHook(
      () => useBulkUserAction(),
      { wrapper: createWrapper() }
    )

    const request: BulkActionRequest = {
      userIds: ['user-1'],
      action: 'resetPassword',
    }

    result.current.mutate(request)

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })

    expect(result.current.error).toEqual(mockError)
  })
})
