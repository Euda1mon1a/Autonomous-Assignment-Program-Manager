import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { EditAssignmentModal } from '@/components/schedule/EditAssignmentModal';
import {
  useUpdateAssignment,
  useCreateAssignment,
  useDeleteAssignment,
  useRotationTemplates,
  usePerson,
  useAbsences,
  useAssignments,
} from '@/lib/hooks';
import { useAuth } from '@/contexts/AuthContext';
import type { Assignment, RotationTemplate, Person } from '@/types/api';

// Mock all dependencies
jest.mock('@/lib/hooks', () => ({
  useUpdateAssignment: jest.fn(),
  useCreateAssignment: jest.fn(),
  useDeleteAssignment: jest.fn(),
  useRotationTemplates: jest.fn(),
  usePerson: jest.fn(),
  useAbsences: jest.fn(),
  useAssignments: jest.fn(),
}));

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/components/schedule/AssignmentWarnings', () => ({
  AssignmentWarnings: ({ warnings, criticalAcknowledged, onAcknowledgeCritical }: any) => (
    <div data-testid="assignment-warnings">
      {warnings.map((w: any, i: number) => (
        <div key={i} data-severity={w.severity}>
          {w.message}
        </div>
      ))}
      {warnings.some((w: any) => w.severity === 'critical') && (
        <button onClick={() => onAcknowledgeCritical(true)}>Acknowledge</button>
      )}
    </div>
  ),
  generateWarnings: jest.fn(() => []),
}));

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUseUpdateAssignment = useUpdateAssignment as jest.MockedFunction<typeof useUpdateAssignment>;
const mockUseCreateAssignment = useCreateAssignment as jest.MockedFunction<typeof useCreateAssignment>;
const mockUseDeleteAssignment = useDeleteAssignment as jest.MockedFunction<typeof useDeleteAssignment>;
const mockUseRotationTemplates = useRotationTemplates as jest.MockedFunction<typeof useRotationTemplates>;
const mockUsePerson = usePerson as jest.MockedFunction<typeof usePerson>;
const mockUseAbsences = useAbsences as jest.MockedFunction<typeof useAbsences>;
const mockUseAssignments = useAssignments as jest.MockedFunction<typeof useAssignments>;

describe('EditAssignmentModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSave = jest.fn();
  const mockOnDelete = jest.fn();
  const mockUpdateAsync = jest.fn();
  const mockCreateAsync = jest.fn();
  const mockDeleteAsync = jest.fn();

  const mockPerson: Person = {
    id: 'person-1',
    name: 'Dr. John Doe',
    type: 'resident',
    pgy_level: 3,
    performs_procedures: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const mockRotationTemplates: RotationTemplate[] = [
    {
      id: 'rotation-1',
      name: 'Cardiology',
      abbreviation: 'CARDS',
      supervision_required: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 'rotation-2',
      name: 'Surgery',
      abbreviation: 'SURG',
      supervision_required: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
  ];

  const mockAssignment: Assignment = {
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'rotation-1',
    role: 'primary',
    notes: 'Test notes',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    assignment: null,
    personId: 'person-1',
    date: '2024-01-15',
    session: 'AM' as const,
    blockId: 'block-1',
    onSave: mockOnSave,
    onDelete: mockOnDelete,
  };

  const setupMocks = (overrides = {}) => {
    mockUseAuth.mockReturnValue({
      user: { id: 'user-1', role: 'admin', name: 'Admin User', email: 'admin@test.com' },
      login: jest.fn(),
      logout: jest.fn(),
      isLoading: false,
      isAuthenticated: true,
      ...overrides,
    } as any);

    mockUseUpdateAssignment.mockReturnValue({
      mutateAsync: mockUpdateAsync,
      isPending: false,
    } as any);

    mockUseCreateAssignment.mockReturnValue({
      mutateAsync: mockCreateAsync,
      isPending: false,
    } as any);

    mockUseDeleteAssignment.mockReturnValue({
      mutateAsync: mockDeleteAsync,
      isPending: false,
    } as any);

    mockUseRotationTemplates.mockReturnValue({
      data: { items: mockRotationTemplates, total: 2 },
      isLoading: false,
    } as any);

    mockUsePerson.mockReturnValue({
      data: mockPerson,
      isLoading: false,
    } as any);

    mockUseAbsences.mockReturnValue({
      data: { items: [], total: 0 },
    } as any);

    mockUseAssignments.mockReturnValue({
      data: { items: [], total: 0 },
    } as any);
  };

  beforeEach(() => {
    jest.clearAllMocks();
    setupMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<EditAssignmentModal {...defaultProps} isOpen={false} />);

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render with "New Assignment" title when creating', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('New Assignment')).toBeInTheDocument();
    });

    it('should render with "Edit Assignment" title when editing', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Edit Assignment')).toBeInTheDocument();
    });

    it('should display person name', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText('Dr. John Doe')).toBeInTheDocument();
    });

    it('should display formatted date', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText(/monday.*january.*15.*2024/i)).toBeInTheDocument();
    });

    it('should display session', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText('AM')).toBeInTheDocument();
    });

    it('should show loading state for person', () => {
      mockUsePerson.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should render all form fields', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
    });

    it('should show delete button when editing', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    it('should not show delete button when creating', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    });

    it('should show permission denied message for non-admin users', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', role: 'viewer', name: 'Viewer', email: 'viewer@test.com' },
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText(/you do not have permission/i)).toBeInTheDocument();
      expect(screen.queryByLabelText(/rotation/i)).not.toBeInTheDocument();
    });
  });

  describe('Form Initialization', () => {
    it('should initialize form with empty values when creating new assignment', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      const rotationSelect = screen.getByLabelText(/rotation/i);
      const roleSelect = screen.getByLabelText(/role/i);
      const notesTextarea = screen.getByLabelText(/notes/i);

      expect(rotationSelect).toHaveValue('');
      expect(roleSelect).toHaveValue('primary');
      expect(notesTextarea).toHaveValue('');
    });

    it('should initialize form with assignment data when editing', () => {
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      const rotationSelect = screen.getByLabelText(/rotation/i);
      const roleSelect = screen.getByLabelText(/role/i);
      const notesTextarea = screen.getByLabelText(/notes/i);

      expect(rotationSelect).toHaveValue('rotation-1');
      expect(roleSelect).toHaveValue('primary');
      expect(notesTextarea).toHaveValue('Test notes');
    });

    it('should populate rotation dropdown with options', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      const rotationSelect = screen.getByLabelText(/rotation/i);
      const options = within(rotationSelect).getAllByRole('option');

      expect(options).toHaveLength(3); // Including "-- Select Rotation --"
      expect(options[0]).toHaveTextContent('-- Select Rotation --');
      expect(options[1]).toHaveTextContent('Cardiology (CARDS)');
      expect(options[2]).toHaveTextContent('Surgery (SURG)');
    });

    it('should populate role dropdown with options', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      const roleSelect = screen.getByLabelText(/role/i);
      const options = within(roleSelect).getAllByRole('option');

      expect(options).toHaveLength(3);
      expect(options[0]).toHaveTextContent('Primary');
      expect(options[1]).toHaveTextContent('Supervising');
      expect(options[2]).toHaveTextContent('Backup');
    });
  });

  describe('Form Interactions', () => {
    it('should allow changing rotation selection', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} />);

      const rotationSelect = screen.getByLabelText(/rotation/i);
      await user.selectOptions(rotationSelect, 'rotation-2');

      expect(rotationSelect).toHaveValue('rotation-2');
    });

    it('should allow changing role', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} />);

      const roleSelect = screen.getByLabelText(/role/i);
      await user.selectOptions(roleSelect, 'supervising');

      expect(roleSelect).toHaveValue('supervising');
    });

    it('should allow entering notes', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} />);

      const notesTextarea = screen.getByLabelText(/notes/i);
      await user.type(notesTextarea, 'Important assignment notes');

      expect(notesTextarea).toHaveValue('Important assignment notes');
    });

    it('should disable rotation select when templates are loading', () => {
      mockUseRotationTemplates.mockReturnValue({
        data: undefined,
        isLoading: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByLabelText(/rotation/i)).toBeDisabled();
    });
  });

  describe('Creating Assignment', () => {
    it('should create assignment with correct data', async () => {
      const user = userEvent.setup();
      mockCreateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.selectOptions(screen.getByLabelText(/role/i), 'primary');
      await user.type(screen.getByLabelText(/notes/i), 'Test notes');

      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(mockCreateAsync).toHaveBeenCalledWith({
          block_id: 'block-1',
          person_id: 'person-1',
          rotation_template_id: 'rotation-1',
          role: 'primary',
          notes: 'Test notes',
          created_by: 'user-1',
        });
      });
    });

    it('should call onSave callback after successful creation', async () => {
      const user = userEvent.setup();
      mockCreateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(mockAssignment);
      });
    });

    it('should close modal after successful creation', async () => {
      const user = userEvent.setup();
      mockCreateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should display error message when creation fails', async () => {
      const user = userEvent.setup();
      mockCreateAsync.mockRejectedValueOnce(new Error('Failed to create'));

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed to create/i)).toBeInTheDocument();
      });
      expect(mockOnClose).not.toHaveBeenCalled();
    });

    it('should require rotation template to be selected', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      const saveButton = screen.getByRole('button', { name: /create assignment/i });
      expect(saveButton).toBeDisabled();

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      expect(saveButton).not.toBeDisabled();
    });

    it('should require blockId to save', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} assignment={null} blockId={undefined} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(screen.getByText(/missing required information/i)).toBeInTheDocument();
      });
      expect(mockCreateAsync).not.toHaveBeenCalled();
    });
  });

  describe('Updating Assignment', () => {
    it('should update assignment with correct data', async () => {
      const user = userEvent.setup();
      mockUpdateAsync.mockResolvedValueOnce({ ...mockAssignment, role: 'supervising' });

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.selectOptions(screen.getByLabelText(/role/i), 'supervising');
      await user.clear(screen.getByLabelText(/notes/i));
      await user.type(screen.getByLabelText(/notes/i), 'Updated notes');

      await user.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(mockUpdateAsync).toHaveBeenCalledWith({
          id: 'assignment-1',
          data: {
            rotation_template_id: 'rotation-1',
            role: 'supervising',
            notes: 'Updated notes',
          },
        });
      });
    });

    it('should call onSave callback after successful update', async () => {
      const user = userEvent.setup();
      const updatedAssignment = { ...mockAssignment, role: 'supervising' as const };
      mockUpdateAsync.mockResolvedValueOnce(updatedAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.selectOptions(screen.getByLabelText(/role/i), 'supervising');
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(mockOnSave).toHaveBeenCalledWith(updatedAssignment);
      });
    });

    it('should close modal after successful update', async () => {
      const user = userEvent.setup();
      mockUpdateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should display error message when update fails', async () => {
      const user = userEvent.setup();
      mockUpdateAsync.mockRejectedValueOnce(new Error('Failed to update'));

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed to update/i)).toBeInTheDocument();
      });
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Deleting Assignment', () => {
    it('should show confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();
        expect(screen.getByText(/delete assignment/i)).toBeInTheDocument();
      });
    });

    it('should delete assignment when confirmed', async () => {
      const user = userEvent.setup();
      mockDeleteAsync.mockResolvedValueOnce(undefined);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /delete assignment/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockDeleteAsync).toHaveBeenCalledWith('assignment-1');
      });
    });

    it('should call onDelete callback after successful deletion', async () => {
      const user = userEvent.setup();
      mockDeleteAsync.mockResolvedValueOnce(undefined);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /delete assignment/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockOnDelete).toHaveBeenCalled();
      });
    });

    it('should close modal after successful deletion', async () => {
      const user = userEvent.setup();
      mockDeleteAsync.mockResolvedValueOnce(undefined);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /delete assignment/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it('should close confirmation dialog when cancel is clicked', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      const cancelButton = within(dialog).getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
      });
      expect(mockDeleteAsync).not.toHaveBeenCalled();
    });

    it('should display error message when deletion fails', async () => {
      const user = userEvent.setup();
      mockDeleteAsync.mockRejectedValueOnce(new Error('Failed to delete'));

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /delete assignment/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to delete/i)).toBeInTheDocument();
      });
      expect(mockOnClose).not.toHaveBeenCalled();
    });
  });

  describe('Cancel and Close', () => {
    it('should close modal when cancel button is clicked', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it('should not close modal when mutations are pending', () => {
      mockUseCreateAssignment.mockReturnValue({
        mutateAsync: mockCreateAsync,
        isPending: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      expect(cancelButton).toBeDisabled();
    });

    it('should reset form when modal is reopened', async () => {
      const user = userEvent.setup();
      const { rerender } = render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      await user.type(screen.getByLabelText(/notes/i), 'Test notes');

      // Close and reopen modal
      rerender(<EditAssignmentModal {...defaultProps} isOpen={false} assignment={null} />);
      rerender(<EditAssignmentModal {...defaultProps} isOpen={true} assignment={null} />);

      expect(screen.getByLabelText(/rotation/i)).toHaveValue('');
      expect(screen.getByLabelText(/notes/i)).toHaveValue('');
    });
  });

  describe('Loading States', () => {
    it('should disable buttons when creating assignment', () => {
      mockUseCreateAssignment.mockReturnValue({
        mutateAsync: mockCreateAsync,
        isPending: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /create assignment/i })).toBeDisabled();
    });

    it('should disable buttons when updating assignment', () => {
      mockUseUpdateAssignment.mockReturnValue({
        mutateAsync: mockUpdateAsync,
        isPending: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled();
    });

    it('should disable delete button when deleting', () => {
      mockUseDeleteAssignment.mockReturnValue({
        mutateAsync: mockDeleteAsync,
        isPending: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled();
    });

    it('should show loading spinner when creating', () => {
      mockUseCreateAssignment.mockReturnValue({
        mutateAsync: mockCreateAsync,
        isPending: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      // The Loader2 component is rendered
      expect(screen.getByRole('button', { name: /create assignment/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes on modal', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
    });

    it('should have accessible labels for all form controls', () => {
      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/notes/i)).toBeInTheDocument();
    });

    it('should have proper ARIA attributes on delete confirmation dialog', async () => {
      const user = userEvent.setup();
      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.click(screen.getByRole('button', { name: /delete/i }));

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby');
      expect(dialog).toHaveAttribute('aria-describedby');
    });
  });

  describe('Permissions', () => {
    it('should allow admin users to edit', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', role: 'admin', name: 'Admin', email: 'admin@test.com' },
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should allow coordinator users to edit', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', role: 'coordinator', name: 'Coordinator', email: 'coord@test.com' },
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should show read-only view for viewer users', () => {
      mockUseAuth.mockReturnValue({
        user: { id: 'user-1', role: 'viewer', name: 'Viewer', email: 'viewer@test.com' },
        login: jest.fn(),
        logout: jest.fn(),
        isLoading: false,
        isAuthenticated: true,
      } as any);

      render(<EditAssignmentModal {...defaultProps} />);

      expect(screen.getByText(/you do not have permission/i)).toBeInTheDocument();
      expect(screen.queryByLabelText(/rotation/i)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });
  });

  describe('Form Submission Edge Cases', () => {
    it('should handle empty notes correctly', async () => {
      const user = userEvent.setup();
      mockCreateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={null} />);

      await user.selectOptions(screen.getByLabelText(/rotation/i), 'rotation-1');
      // Don't type anything in notes
      await user.click(screen.getByRole('button', { name: /create assignment/i }));

      await waitFor(() => {
        expect(mockCreateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: undefined,
          })
        );
      });
    });

    it('should convert empty string notes to undefined', async () => {
      const user = userEvent.setup();
      mockUpdateAsync.mockResolvedValueOnce(mockAssignment);

      render(<EditAssignmentModal {...defaultProps} assignment={mockAssignment} />);

      await user.clear(screen.getByLabelText(/notes/i));
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      await waitFor(() => {
        expect(mockUpdateAsync).toHaveBeenCalledWith(
          expect.objectContaining({
            data: expect.objectContaining({
              notes: undefined,
            }),
          })
        );
      });
    });
  });
});
