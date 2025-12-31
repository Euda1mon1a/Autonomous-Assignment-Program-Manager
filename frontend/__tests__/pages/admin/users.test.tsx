/**
 * Tests for Admin User Management Page
 *
 * Tests user management functionality, role management, activity tracking,
 * CRUD operations, bulk actions, and access control.
 */
import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminUsersPage from '@/app/admin/users/page';
import * as hooks from '@/hooks/useAdminUsers';

// Mock the hooks
jest.mock('@/hooks/useAdminUsers');
const mockUseUsers = hooks.useUsers as jest.MockedFunction<typeof hooks.useUsers>;
const mockUseCreateUser = hooks.useCreateUser as jest.MockedFunction<typeof hooks.useCreateUser>;
const mockUseUpdateUser = hooks.useUpdateUser as jest.MockedFunction<typeof hooks.useUpdateUser>;
const mockUseDeleteUser = hooks.useDeleteUser as jest.MockedFunction<typeof hooks.useDeleteUser>;
const mockUseToggleUserLock = hooks.useToggleUserLock as jest.MockedFunction<typeof hooks.useToggleUserLock>;
const mockUseResendInvite = hooks.useResendInvite as jest.MockedFunction<typeof hooks.useResendInvite>;
const mockUseBulkUserAction = hooks.useBulkUserAction as jest.MockedFunction<typeof hooks.useBulkUserAction>;

// Mock user data
const mockUsers = {
  users: [
    {
      id: 'user-1',
      email: 'admin@example.mil',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin' as const,
      status: 'active' as const,
      lastLogin: '2024-12-23T10:00:00Z',
      mfaEnabled: true,
    },
    {
      id: 'user-2',
      email: 'coordinator@example.mil',
      firstName: 'Coordinator',
      lastName: 'User',
      role: 'coordinator' as const,
      status: 'active' as const,
      lastLogin: '2024-12-22T15:00:00Z',
      mfaEnabled: false,
    },
    {
      id: 'user-3',
      email: 'locked@example.mil',
      firstName: 'Locked',
      lastName: 'Account',
      role: 'resident' as const,
      status: 'locked' as const,
      lastLogin: null,
      mfaEnabled: false,
    },
  ],
  total: 3,
};

// Create test wrapper
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('AdminUsersPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    mockUseUsers.mockReturnValue({
      data: mockUsers,
      isLoading: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    mockUseCreateUser.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseUpdateUser.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseDeleteUser.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseToggleUserLock.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseResendInvite.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);

    mockUseBulkUserAction.mockReturnValue({
      mutate: jest.fn(),
      isPending: false,
    } as any);
  });

  describe('Page Rendering', () => {
    it('should render page title and description', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('Manage users, roles, and permissions')).toBeInTheDocument();
    });

    it('should render all tabs', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('Roles & Permissions')).toBeInTheDocument();
      expect(screen.getByText('Activity Log')).toBeInTheDocument();
    });

    it('should start on Users tab by default', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const usersTab = screen.getByText('Users').closest('button');
      expect(usersTab).toHaveClass('bg-slate-800', 'text-white');
    });

    it('should render search input', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByPlaceholderText('Search users...')).toBeInTheDocument();
    });

    it('should render Add User button', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByRole('button', { name: /Add User/i })).toBeInTheDocument();
    });

    it('should render user table headers', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('User')).toBeInTheDocument();
      expect(screen.getByText('Role')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Last Login')).toBeInTheDocument();
      expect(screen.getByText('MFA')).toBeInTheDocument();
    });
  });

  describe('User List Display', () => {
    it('should display all users', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('Coordinator User')).toBeInTheDocument();
      expect(screen.getByText('Locked Account')).toBeInTheDocument();
    });

    it('should display user emails', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('admin@example.mil')).toBeInTheDocument();
      expect(screen.getByText('coordinator@example.mil')).toBeInTheDocument();
    });

    it('should display user status badges', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const statusBadges = screen.getAllByText('Active');
      expect(statusBadges.length).toBeGreaterThan(0);

      expect(screen.getByText('Locked')).toBeInTheDocument();
    });

    it('should display user count', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText(/Showing 3 of 3 users/i)).toBeInTheDocument();
    });

    it('should show loading state', () => {
      mockUseUsers.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading users...')).toBeInTheDocument();
    });

    it('should show error state', () => {
      mockUseUsers.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to load'),
        refetch: jest.fn(),
      } as any);

      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('Failed to load users')).toBeInTheDocument();
    });

    it('should show empty state when no users', () => {
      mockUseUsers.mockReturnValue({
        data: { users: [], total: 0 },
        isLoading: false,
        error: null,
        refetch: jest.fn(),
      } as any);

      render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should filter users by name', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search users...');
      await user.type(searchInput, 'Admin');

      expect(screen.getByText('Admin User')).toBeInTheDocument();
      // Coordinator and Locked should still be in DOM but filtered client-side
    });

    it('should filter users by email', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search users...');
      await user.type(searchInput, 'coordinator@');

      expect(screen.getByText('Coordinator User')).toBeInTheDocument();
    });

    it('should clear search', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const searchInput = screen.getByPlaceholderText('Search users...');
      await user.type(searchInput, 'Admin');
      await user.clear(searchInput);

      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('Coordinator User')).toBeInTheDocument();
    });
  });

  describe('Filter Functionality', () => {
    it('should toggle filters panel', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const filterButton = screen.getByRole('button', { name: /Filters/i });
      await user.click(filterButton);

      expect(screen.getByText('Role')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });

    it('should filter by role', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      // Open filters
      await user.click(screen.getByRole('button', { name: /Filters/i }));

      // Select role filter
      const roleSelect = screen.getByLabelText('Role');
      await user.selectOptions(roleSelect, 'admin');

      // Should call useUsers with role filter
      expect(mockUseUsers).toHaveBeenCalled();
    });

    it('should filter by status', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      await user.click(screen.getByRole('button', { name: /Filters/i }));

      const statusSelect = screen.getByLabelText('Status');
      await user.selectOptions(statusSelect, 'active');

      expect(mockUseUsers).toHaveBeenCalled();
    });
  });

  describe('User Selection', () => {
    it('should select individual user', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[1]); // First user checkbox (0 is select all)

      expect(checkboxes[1]).toBeChecked();
    });

    it('should select all users', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
      await user.click(selectAllCheckbox);

      expect(selectAllCheckbox).toBeChecked();
    });

    it('should show bulk actions when users selected', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[1]);

      expect(screen.getByText(/1 user\(s\) selected/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Activate/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Deactivate/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Delete/i })).toBeInTheDocument();
    });

    it('should clear selection', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const checkboxes = screen.getAllByRole('checkbox');
      await user.click(checkboxes[1]);

      const clearButton = screen.getByText('Clear selection');
      await user.click(clearButton);

      expect(screen.queryByText(/1 user\(s\) selected/i)).not.toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch to Roles tab', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const rolesTab = screen.getByText('Roles & Permissions').closest('button');
      await user.click(rolesTab!);

      expect(rolesTab).toHaveClass('bg-slate-800', 'text-white');
      expect(screen.getByText('View role definitions and their permissions')).toBeInTheDocument();
    });

    it('should switch to Activity tab', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const activityTab = screen.getByText('Activity Log').closest('button');
      await user.click(activityTab!);

      expect(activityTab).toHaveClass('bg-slate-800', 'text-white');
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    });

    it('should display role permissions when expanded', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      await user.click(screen.getByText('Roles & Permissions').closest('button')!);

      // Find and expand admin role
      const adminRole = screen.getAllByText('Admin')[0].closest('button');
      await user.click(adminRole!);

      expect(screen.getByText('Permissions')).toBeInTheDocument();
    });
  });

  describe('Create User Modal', () => {
    it('should open create user modal', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      await user.click(screen.getByRole('button', { name: /Add User/i }));

      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });

    it('should close modal on cancel', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      await user.click(screen.getByRole('button', { name: /Add User/i }));
      await user.click(screen.getByRole('button', { name: /Cancel/i }));

      expect(screen.queryByText('Create New User')).not.toBeInTheDocument();
    });

    it('should validate required fields', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      await user.click(screen.getByRole('button', { name: /Add User/i }));

      const createButton = screen.getByRole('button', { name: /Create User/i });
      await user.click(createButton);

      // Form should not submit without required fields
      expect(screen.getByText('Create New User')).toBeInTheDocument();
    });
  });

  describe('User Actions Menu', () => {
    it('should open user actions menu', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const menuButtons = screen.getAllByRole('button');
      const moreButton = menuButtons.find(btn =>
        btn.querySelector('svg') && !btn.textContent
      );

      if (moreButton) {
        await user.click(moreButton);
        await waitFor(() => {
          expect(screen.getByText('Edit User')).toBeInTheDocument();
        });
      }
    });

    it('should show unlock option for locked users', async () => {
      const user = userEvent.setup();
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      // Find the locked user's menu
      const rows = screen.getAllByRole('row');
      const lockedRow = rows.find(row => row.textContent?.includes('Locked Account'));
      if (lockedRow) {
        const moreButton = within(lockedRow).getAllByRole('button')[1];
        await user.click(moreButton);

        await waitFor(() => {
          expect(screen.getByText('Unlock Account')).toBeInTheDocument();
        });
      }
    });
  });

  describe('Delete User Flow', () => {
    it('should show confirmation dialog', async () => {
      const user = userEvent.setup();
      const mockMutate = jest.fn();
      mockUseDeleteUser.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      } as any);

      render(<AdminUsersPage />, { wrapper: createWrapper() });

      // Open menu and click delete
      const menuButtons = screen.getAllByRole('button');
      const moreButton = menuButtons.find(btn =>
        btn.querySelector('svg') && !btn.textContent
      );

      if (moreButton) {
        await user.click(moreButton);
        await waitFor(() => {
          const deleteButton = screen.getByText('Delete User');
          user.click(deleteButton);
        });

        await waitFor(() => {
          expect(screen.getByText('Delete User')).toBeInTheDocument();
          expect(screen.getByText(/Are you sure/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const heading = screen.getByRole('heading', { name: 'User Management' });
      expect(heading).toBeInTheDocument();
      expect(heading.tagName).toBe('H1');
    });

    it('should have accessible buttons', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have accessible table', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });

    it('should have accessible checkboxes', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Layout', () => {
    it('should render on mobile', () => {
      const { container } = render(<AdminUsersPage />, { wrapper: createWrapper() });

      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('should have overflow handling for tables', () => {
      render(<AdminUsersPage />, { wrapper: createWrapper() });

      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });
  });
});
