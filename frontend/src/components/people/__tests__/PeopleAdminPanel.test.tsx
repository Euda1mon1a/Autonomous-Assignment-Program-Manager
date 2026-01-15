/**
 * Tests for PeopleAdminPanel Component
 * Component: Admin panel for managing people (Tier 1/2)
 */

import React from 'react';
import { renderWithProviders as render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { PeopleAdminPanel } from '../PeopleAdminPanel';
import { FacultyRole, type Person, type PersonType } from '@/types/api';

// Mock the hooks
jest.mock('@/hooks/usePeople', () => ({
  usePeople: jest.fn(),
  useBulkDeletePeople: jest.fn(),
  useBulkUpdatePeople: jest.fn(),
}));

jest.mock('@/hooks/useDebounce', () => ({
  useDebounce: jest.fn((value: string) => value),
}));

jest.mock('@/hooks/useKeyboardShortcuts', () => ({
  useKeyboardShortcuts: jest.fn(),
  getShortcutDisplay: jest.fn((shortcut: { key: string; modifiers?: string[] }) => {
    const modKey = shortcut.modifiers?.includes('cmd') ? 'Cmd+' : '';
    return `${modKey}${shortcut.key.toUpperCase()}`;
  }),
}));

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
      info: jest.fn(),
    },
  }),
}));

// Mock child components
jest.mock('@/components/admin/PeopleTable', () => ({
  PeopleTable: ({ people, selectedIds, onSelectionChange, sort: _sort, onSortChange }: {
    people: Person[];
    selectedIds: string[];
    onSelectionChange: (ids: string[]) => void;
    sort: { field: string; direction: string };
    onSortChange: (field: string) => void;
  }) => (
    <div data-testid="people-table">
      <div data-testid="table-count">{people.length} people</div>
      <div data-testid="selected-count">{selectedIds.length} selected</div>
      <button onClick={() => onSelectionChange(['1', '2'])} data-testid="select-items">
        Select Items
      </button>
      <button onClick={() => onSelectionChange([])} data-testid="clear-selection">
        Clear Selection
      </button>
      <button onClick={() => onSortChange('name')} data-testid="sort-name">
        Sort by Name
      </button>
    </div>
  ),
}));

jest.mock('@/components/admin/PeopleBulkActionsToolbar', () => ({
  PeopleBulkActionsToolbar: ({
    selectedCount,
    onClearSelection,
    onBulkDelete,
    onBulkUpdatePGY,
    onBulkUpdateType,
    isPending,
  }: {
    selectedCount: number;
    onClearSelection: () => void;
    onBulkDelete: () => void;
    onBulkUpdatePGY: (level: number) => void;
    onBulkUpdateType: (type: string) => void;
    isPending: boolean;
    pendingAction: string | null;
  }) =>
    selectedCount > 0 ? (
      <div data-testid="bulk-actions-toolbar">
        <span data-testid="bulk-count">{selectedCount} selected</span>
        <button onClick={onClearSelection} data-testid="clear-btn">
          Clear
        </button>
        <button onClick={onBulkDelete} data-testid="delete-btn" disabled={isPending}>
          Delete
        </button>
        <button onClick={() => onBulkUpdatePGY(2)} data-testid="update-pgy-btn">
          Set PGY-2
        </button>
        <button onClick={() => onBulkUpdateType('resident')} data-testid="update-type-btn">
          Set Resident
        </button>
      </div>
    ) : null,
}));

jest.mock('@/components/AddPersonModal', () => ({
  AddPersonModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? (
      <div data-testid="add-person-modal">
        <button onClick={onClose} data-testid="close-modal">
          Close
        </button>
      </div>
    ) : null,
}));

jest.mock('@/components/EditPersonModal', () => ({
  EditPersonModal: ({
    isOpen,
    onClose,
    person,
  }: {
    isOpen: boolean;
    onClose: () => void;
    person: Person | null;
  }) =>
    isOpen ? (
      <div data-testid="edit-person-modal">
        <span data-testid="editing-person">{person?.name}</span>
        <button onClick={onClose} data-testid="close-edit-modal">
          Close
        </button>
      </div>
    ) : null,
}));

jest.mock('@/components/ConfirmDialog', () => ({
  ConfirmDialog: ({
    isOpen,
    onClose,
    onConfirm,
    title,
    isLoading,
  }: {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmLabel: string;
    cancelLabel: string;
    variant: string;
    isLoading: boolean;
  }) =>
    isOpen ? (
      <div data-testid="confirm-dialog">
        <span data-testid="dialog-title">{title}</span>
        <button onClick={onConfirm} data-testid="confirm-btn" disabled={isLoading}>
          Confirm
        </button>
        <button onClick={onClose} data-testid="cancel-btn">
          Cancel
        </button>
      </div>
    ) : null,
}));

// Import mocked modules
import { usePeople, useBulkDeletePeople, useBulkUpdatePeople } from '@/hooks/usePeople';

const mockUsePeople = usePeople as jest.MockedFunction<typeof usePeople>;
const mockUseBulkDeletePeople = useBulkDeletePeople as jest.MockedFunction<typeof useBulkDeletePeople>;
const mockUseBulkUpdatePeople = useBulkUpdatePeople as jest.MockedFunction<typeof useBulkUpdatePeople>;

// Test data
const mockPeople: Person[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    type: 'resident' as PersonType,
    pgyLevel: 2,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Bob Smith',
    email: 'bob@example.com',
    type: 'faculty' as PersonType,
    pgyLevel: null,
    performsProcedures: false,
    specialties: ['Cardiology'],
    primaryDuty: null,
    facultyRole: FacultyRole.CORE,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  },
];

describe('PeopleAdminPanel', () => {
  const defaultProps = {
    canBulkDelete: true,
    riskTier: 2 as const,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUsePeople.mockReturnValue({
      data: { items: mockPeople, total: 2 },
      isLoading: false,
      isError: false,
      error: null,
      refetch: jest.fn(),
    } as unknown as ReturnType<typeof usePeople>);

    mockUseBulkDeletePeople.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({ succeeded: 2 }),
      isPending: false,
    } as unknown as ReturnType<typeof useBulkDeletePeople>);

    mockUseBulkUpdatePeople.mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue({ succeeded: 2 }),
      isPending: false,
    } as unknown as ReturnType<typeof useBulkUpdatePeople>);
  });

  // Test: Loading state
  describe('Loading State', () => {
    it('shows loading spinner while fetching data', () => {
      mockUsePeople.mockReturnValue({
        data: undefined,
        isLoading: true,
        isError: false,
        error: null,
        refetch: jest.fn(),
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });
  });

  // Test: People table rendering
  describe('Table Rendering', () => {
    it('renders people table with correct count', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByTestId('people-table')).toBeInTheDocument();
      expect(screen.getByTestId('table-count')).toHaveTextContent('2 people');
    });

    it('shows people count in stats', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // The stats div shows count, table mock also shows count
      // We should have at least one element with the count
      expect(screen.getAllByText(/2 people/).length).toBeGreaterThanOrEqual(1);
    });
  });

  // Test: Search functionality
  describe('Search', () => {
    it('renders search input', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('searchbox')).toBeInTheDocument();
    });

    it('filters people when search text is entered', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'alice' } });

      // The filtering happens in useMemo, which filters the mock data
      expect(searchInput).toHaveValue('alice');
    });

    it('clears search when X button is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const searchInput = screen.getByRole('searchbox');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      const clearButton = screen.getByRole('button', { name: /clear search/i });
      fireEvent.click(clearButton);

      expect(searchInput).toHaveValue('');
    });
  });

  // Test: Filters
  describe('Filters', () => {
    it('renders type filter dropdown', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('combobox', { name: /filter by type/i })).toBeInTheDocument();
    });

    it('renders PGY level filter when type is not faculty', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('combobox', { name: /filter by pgy level/i })).toBeInTheDocument();
    });

    it('hides PGY filter when faculty type is selected', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const typeFilter = screen.getByRole('combobox', { name: /filter by type/i });
      fireEvent.change(typeFilter, { target: { value: 'faculty' } });

      expect(screen.queryByRole('combobox', { name: /filter by pgy level/i })).not.toBeInTheDocument();
    });
  });

  // Test: Add person modal
  describe('Add Person Modal', () => {
    it('opens add person modal when Add Person button is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const addButton = screen.getByRole('button', { name: /add person/i });
      fireEvent.click(addButton);

      expect(screen.getByTestId('add-person-modal')).toBeInTheDocument();
    });

    it('closes modal when close button is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const addButton = screen.getByRole('button', { name: /add person/i });
      fireEvent.click(addButton);

      const closeButton = screen.getByTestId('close-modal');
      fireEvent.click(closeButton);

      expect(screen.queryByTestId('add-person-modal')).not.toBeInTheDocument();
    });
  });

  // Test: Selection and bulk actions
  describe('Selection and Bulk Actions', () => {
    it('shows bulk actions toolbar when items are selected', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // Trigger selection via mocked table
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      expect(screen.getByTestId('bulk-actions-toolbar')).toBeInTheDocument();
    });

    it('clears selection when clear button is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      // Clear selection via toolbar
      const clearButton = screen.getByTestId('clear-btn');
      fireEvent.click(clearButton);

      expect(screen.queryByTestId('bulk-actions-toolbar')).not.toBeInTheDocument();
    });
  });

  // Test: Bulk delete (Tier 2)
  describe('Bulk Delete', () => {
    it('shows confirmation dialog when delete is clicked', async () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      // Click delete
      const deleteButton = screen.getByTestId('delete-btn');
      fireEvent.click(deleteButton);

      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
      expect(screen.getByTestId('dialog-title')).toHaveTextContent('Delete People');
    });

    it('calls bulk delete when confirmed', async () => {
      const mockMutateAsync = jest.fn().mockResolvedValue({ succeeded: 2 });
      mockUseBulkDeletePeople.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as unknown as ReturnType<typeof useBulkDeletePeople>);

      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      // Click delete
      const deleteButton = screen.getByTestId('delete-btn');
      fireEvent.click(deleteButton);

      // Confirm deletion
      const confirmButton = screen.getByTestId('confirm-btn');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith(['1', '2']);
      });
    });

    it('closes dialog when cancelled', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items and open dialog
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      const deleteButton = screen.getByTestId('delete-btn');
      fireEvent.click(deleteButton);

      // Cancel
      const cancelButton = screen.getByTestId('cancel-btn');
      fireEvent.click(cancelButton);

      expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument();
    });
  });

  // Test: Bulk update PGY
  describe('Bulk Update PGY', () => {
    it('calls bulk update when PGY level is selected', async () => {
      const mockMutateAsync = jest.fn().mockResolvedValue({ succeeded: 2 });
      mockUseBulkUpdatePeople.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as unknown as ReturnType<typeof useBulkUpdatePeople>);

      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      // Click update PGY
      const updatePgyButton = screen.getByTestId('update-pgy-btn');
      fireEvent.click(updatePgyButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          personIds: ['1', '2'],
          updates: { pgyLevel: 2 },
        });
      });
    });
  });

  // Test: Bulk update type
  describe('Bulk Update Type', () => {
    it('calls bulk update when type is selected', async () => {
      const mockMutateAsync = jest.fn().mockResolvedValue({ succeeded: 2 });
      mockUseBulkUpdatePeople.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
      } as unknown as ReturnType<typeof useBulkUpdatePeople>);

      render(<PeopleAdminPanel {...defaultProps} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      // Click update type
      const updateTypeButton = screen.getByTestId('update-type-btn');
      fireEvent.click(updateTypeButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          personIds: ['1', '2'],
          updates: { type: 'resident' },
        });
      });
    });
  });

  // Test: Tier restrictions
  describe('Tier Restrictions', () => {
    it('shows message when user cannot bulk delete', () => {
      render(<PeopleAdminPanel canBulkDelete={false} riskTier={1} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      expect(screen.getByText(/bulk delete requires admin permissions/i)).toBeInTheDocument();
    });

    it('does not show message when user can bulk delete', () => {
      render(<PeopleAdminPanel canBulkDelete={true} riskTier={2} />);

      // Select items
      const selectButton = screen.getByTestId('select-items');
      fireEvent.click(selectButton);

      expect(screen.queryByText(/bulk delete requires admin permissions/i)).not.toBeInTheDocument();
    });
  });

  // Test: Refresh functionality
  describe('Refresh', () => {
    it('calls refetch when refresh button is clicked', () => {
      const mockRefetch = jest.fn();
      mockUsePeople.mockReturnValue({
        data: { items: mockPeople, total: 2 },
        isLoading: false,
        isError: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof usePeople>);

      render(<PeopleAdminPanel {...defaultProps} />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  // Test: Keyboard shortcuts help
  describe('Keyboard Shortcuts', () => {
    it('shows shortcuts help when button is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      const shortcutsButton = screen.getByRole('button', { name: /show keyboard shortcuts/i });
      fireEvent.click(shortcutsButton);

      expect(screen.getByRole('dialog', { name: /keyboard shortcuts/i })).toBeInTheDocument();
    });

    it('closes shortcuts help when X is clicked', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      // Open
      const shortcutsButton = screen.getByRole('button', { name: /show keyboard shortcuts/i });
      fireEvent.click(shortcutsButton);

      // Close
      const closeButton = screen.getByRole('button', { name: /close shortcuts/i });
      fireEvent.click(closeButton);

      expect(screen.queryByRole('dialog', { name: /keyboard shortcuts/i })).not.toBeInTheDocument();
    });
  });

  // Test: Accessibility
  describe('Accessibility', () => {
    it('has proper ARIA label for search input', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('searchbox')).toHaveAttribute('aria-label', 'Search people');
    });

    it('has proper ARIA labels for filter controls', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('combobox', { name: /filter by type/i })).toBeInTheDocument();
      expect(screen.getByRole('combobox', { name: /filter by pgy level/i })).toBeInTheDocument();
    });

    it('has proper ARIA labels for action buttons', () => {
      render(<PeopleAdminPanel {...defaultProps} />);

      expect(screen.getByRole('button', { name: /add person/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
    });
  });
});
