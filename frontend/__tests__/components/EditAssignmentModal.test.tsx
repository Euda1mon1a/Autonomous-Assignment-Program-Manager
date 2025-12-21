/**
 * Tests for EditAssignmentModal component
 *
 * Tests form rendering, validation, create/edit modes, permissions, and submission behavior
 */
import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EditAssignmentModal } from '@/components/schedule/EditAssignmentModal'
import { AssignmentRole, type Assignment } from '@/types/api'
import * as AuthContext from '@/contexts/AuthContext'

// Mock the hooks
jest.mock('@/lib/hooks', () => ({
  useUpdateAssignment: jest.fn(() => ({
    mutateAsync: jest.fn(),
    isPending: false,
  })),
  useCreateAssignment: jest.fn(() => ({
    mutateAsync: jest.fn(),
    isPending: false,
  })),
  useDeleteAssignment: jest.fn(() => ({
    mutateAsync: jest.fn(),
    isPending: false,
  })),
  useRotationTemplates: jest.fn(() => ({
    data: {
      items: [
        { id: 'template-1', name: 'Clinic', abbreviation: 'CLIN' },
        { id: 'template-2', name: 'Inpatient Medicine', abbreviation: 'IM' },
      ],
    },
    isLoading: false,
  })),
  usePerson: jest.fn(() => ({
    data: { id: 'person-1', name: 'Dr. John Smith' },
    isLoading: false,
  })),
  useAbsences: jest.fn(() => ({
    data: { items: [] },
  })),
  useAssignments: jest.fn(() => ({
    data: { items: [] },
  })),
}))

// Mock AuthContext
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

// Create a wrapper with QueryClient for testing
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
    logger: {
      log: () => {},
      warn: () => {},
      error: () => {},
    },
  })

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )
  }
}

describe('EditAssignmentModal', () => {
  const mockOnClose = jest.fn()
  const mockOnSave = jest.fn()
  const mockOnDelete = jest.fn()

  const mockAssignment: Assignment = {
    id: 'assignment-1',
    block_id: 'block-1',
    person_id: 'person-1',
    rotation_template_id: 'template-1',
    role: AssignmentRole.PRIMARY,
    notes: 'Test notes',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

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
  }

  beforeEach(() => {
    jest.clearAllMocks()
    // Default to admin user
    ;(AuthContext.useAuth as jest.Mock).mockReturnValue({
      user: { id: 'user-1', role: 'admin' },
    })
  })

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(
        <EditAssignmentModal {...defaultProps} isOpen={false} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    it('should render modal when isOpen is true', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('New Assignment')).toBeInTheDocument()
    })

    it('should show "Edit Assignment" title when editing', () => {
      render(
        <EditAssignmentModal {...defaultProps} assignment={mockAssignment} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('Edit Assignment')).toBeInTheDocument()
    })

    it('should render all form fields', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument()
      expect(screen.getByText('Notes')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/optional notes/i)).toBeInTheDocument()
    })

    it('should render read-only person, date, and session fields', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText('Dr. John Smith')).toBeInTheDocument()
      expect(screen.getByText(/Monday, January 15, 2024/i)).toBeInTheDocument()
      expect(screen.getByText('AM')).toBeInTheDocument()
    })

    it('should render Cancel and Save buttons', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create assignment/i })).toBeInTheDocument()
    })

    it('should render Delete button when editing', () => {
      render(
        <EditAssignmentModal {...defaultProps} assignment={mockAssignment} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    it('should not render Delete button when creating', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
    })
  })

  describe('Permission Handling', () => {
    it('should show permission message for non-admin users', () => {
      ;(AuthContext.useAuth as jest.Mock).mockReturnValue({
        user: { id: 'user-1', role: 'resident' },
      })

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByText(/you do not have permission to edit assignments/i)).toBeInTheDocument()
      expect(screen.queryByLabelText(/rotation/i)).not.toBeInTheDocument()
    })

    it('should allow coordinators to edit', () => {
      ;(AuthContext.useAuth as jest.Mock).mockReturnValue({
        user: { id: 'user-1', role: 'coordinator' },
      })

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument()
    })
  })

  describe('Form Pre-population', () => {
    it('should pre-populate form when editing assignment', () => {
      render(
        <EditAssignmentModal {...defaultProps} assignment={mockAssignment} />,
        { wrapper: createWrapper() }
      )

      const rotationSelect = screen.getByLabelText(/rotation/i) as HTMLSelectElement
      const roleSelect = screen.getByLabelText(/role/i) as HTMLSelectElement
      const notesTextarea = screen.getByPlaceholderText(/optional notes/i) as HTMLTextAreaElement

      expect(rotationSelect.value).toBe('template-1')
      expect(roleSelect.value).toBe('primary')
      expect(notesTextarea.value).toBe('Test notes')
    })

    it('should have empty fields when creating', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const rotationSelect = screen.getByLabelText(/rotation/i) as HTMLSelectElement
      const roleSelect = screen.getByLabelText(/role/i) as HTMLSelectElement
      const notesTextarea = screen.getByPlaceholderText(/optional notes/i) as HTMLTextAreaElement

      expect(rotationSelect.value).toBe('')
      expect(roleSelect.value).toBe('primary')
      expect(notesTextarea.value).toBe('')
    })
  })

  describe('Form Interactions', () => {
    it('should update rotation when selected', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const rotationSelect = screen.getByLabelText(/rotation/i)
      await user.selectOptions(rotationSelect, 'template-2')

      expect((rotationSelect as HTMLSelectElement).value).toBe('template-2')
    })

    it('should update role when selected', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const roleSelect = screen.getByLabelText(/role/i)
      await user.selectOptions(roleSelect, 'backup')

      expect((roleSelect as HTMLSelectElement).value).toBe('backup')
    })

    it('should update notes when typed', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const notesTextarea = screen.getByPlaceholderText(/optional notes/i)
      await user.type(notesTextarea, 'New notes')

      expect((notesTextarea as HTMLTextAreaElement).value).toBe('New notes')
    })
  })

  describe('Modal Interactions', () => {
    it('should call onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const cancelButton = screen.getByRole('button', { name: /cancel/i })
      await user.click(cancelButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when close button (X) is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const closeButton = screen.getByRole('button', { name: /close modal/i })
      await user.click(closeButton)

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })

    it('should call onClose when clicking on backdrop', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const backdrop = document.querySelector('.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop)
        expect(mockOnClose).toHaveBeenCalledTimes(1)
      }
    })

    it('should call onClose when Escape key is pressed', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      await user.keyboard('{Escape}')

      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  describe('Save Button State', () => {
    it('should disable save button when no rotation selected', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const saveButton = screen.getByRole('button', { name: /create assignment/i })
      expect(saveButton).toBeDisabled()
    })

    it('should enable save button when rotation is selected', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const rotationSelect = screen.getByLabelText(/rotation/i)
      await user.selectOptions(rotationSelect, 'template-1')

      const saveButton = screen.getByRole('button', { name: /create assignment/i })
      expect(saveButton).not.toBeDisabled()
    })
  })

  describe('Delete Functionality', () => {
    it('should show confirmation dialog when delete is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} assignment={mockAssignment} />,
        { wrapper: createWrapper() }
      )

      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument()
        expect(screen.getByText(/delete assignment/i)).toBeInTheDocument()
      })
    })

    it('should close delete confirmation when cancel is clicked', async () => {
      const user = userEvent.setup()

      render(
        <EditAssignmentModal {...defaultProps} assignment={mockAssignment} />,
        { wrapper: createWrapper() }
      )

      // Open delete confirmation
      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByRole('alertdialog')).toBeInTheDocument()
      })

      // Click cancel in confirmation dialog
      const cancelButton = screen.getAllByRole('button', { name: /cancel/i })[1] // Second cancel button
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria attributes on modal', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
    })

    it('should have proper labels for form controls', () => {
      render(
        <EditAssignmentModal {...defaultProps} />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/rotation/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/role/i)).toBeInTheDocument()
      expect(screen.getByText('Notes')).toBeInTheDocument()
    })
  })
})
