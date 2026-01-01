import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { BatchResolution } from '@/features/conflicts/BatchResolution';
import type { Conflict } from '@/features/conflicts/types';
import { createWrapper } from '../../utils/test-utils';
import { QueryClient } from '@tanstack/react-query';

// Mock the hooks
jest.mock('@/features/conflicts/hooks', () => ({
  useBatchResolve: jest.fn(),
  useBatchIgnore: jest.fn(),
}));

import { useBatchResolve, useBatchIgnore } from '@/features/conflicts/hooks';

describe('BatchResolution', () => {
  const mockOnComplete = jest.fn();
  const mockOnCancel = jest.fn();
  const mockBatchResolveMutate = jest.fn();
  const mockBatchIgnoreMutate = jest.fn();

  const mockConflicts: Conflict[] = [
    {
      id: 'conflict-1',
      title: 'Assignment during absence',
      description: 'Dr. Smith is assigned while on vacation',
      severity: 'critical',
      type: 'absence_conflict',
      status: 'unresolved',
      conflict_date: '2024-02-15',
      affected_person_ids: ['person-1'],
      affected_assignment_ids: ['assign-1'],
      detected_at: '2024-02-10T10:00:00Z',
    },
    {
      id: 'conflict-2',
      title: 'Double-booked time slot',
      description: 'Two assignments at the same time',
      severity: 'high',
      type: 'scheduling_overlap',
      status: 'unresolved',
      conflict_date: '2024-02-20',
      affected_person_ids: ['person-2'],
      affected_assignment_ids: ['assign-2', 'assign-3'],
      detected_at: '2024-02-18T10:00:00Z',
    },
    {
      id: 'conflict-3',
      title: 'ACGME duty hour violation',
      description: 'Exceeds 80-hour work week',
      severity: 'medium',
      type: 'acgme_violation',
      status: 'unresolved',
      conflict_date: '2024-02-25',
      affected_person_ids: ['person-3'],
      affected_assignment_ids: ['assign-4'],
      detected_at: '2024-02-22T10:00:00Z',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    (useBatchResolve as jest.Mock).mockReturnValue({
      mutateAsync: mockBatchResolveMutate,
      isPending: false,
      isError: false,
      error: null,
    });

    (useBatchIgnore as jest.Mock).mockReturnValue({
      mutateAsync: mockBatchIgnoreMutate,
      isPending: false,
      isError: false,
      error: null,
    });
  });

  describe('Initial Rendering', () => {
    it('should render batch resolution header', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Batch Resolution')).toBeInTheDocument();
    });

    it('should display selected count', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('3 of 3 conflicts selected')).toBeInTheDocument();
    });

    it('should render all conflicts by default', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
      expect(screen.getByText('Double-booked time slot')).toBeInTheDocument();
      expect(screen.getByText('ACGME duty hour violation')).toBeInTheDocument();
    });

    it('should select all conflicts by default', () => {
      const { container } = render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // All conflicts should have checked checkboxes
      const checkedBoxes = container.querySelectorAll('svg[data-lucide="check-square"]');
      expect(checkedBoxes.length).toBeGreaterThan(0);
    });

    it('should display resolution method options', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText('Auto-resolve')).toBeInTheDocument();
      expect(screen.getByText('Ignore All')).toBeInTheDocument();
    });
  });

  describe('Critical Conflict Warning', () => {
    it('should display warning when critical conflicts are selected', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByText(/1 critical conflict selected/)).toBeInTheDocument();
      expect(
        screen.getByText(/Critical conflicts may affect patient safety or regulatory compliance/)
      ).toBeInTheDocument();
    });

    it('should not display warning when no critical conflicts selected', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // Deselect the critical conflict
      const criticalConflictRow = screen.getByText('Assignment during absence').closest('div');
      await user.click(criticalConflictRow!);

      await waitFor(() => {
        expect(screen.queryByText(/critical conflict selected/)).not.toBeInTheDocument();
      });
    });
  });

  describe('Conflict Selection', () => {
    it('should toggle conflict selection when clicked', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // Initially 3 selected
      expect(screen.getByText('3 of 3 conflicts selected')).toBeInTheDocument();

      // Click to deselect
      const conflictRow = screen.getByText('Assignment during absence').closest('div');
      await user.click(conflictRow!);

      await waitFor(() => {
        expect(screen.getByText('2 of 3 conflicts selected')).toBeInTheDocument();
      });

      // Click again to reselect
      await user.click(conflictRow!);

      await waitFor(() => {
        expect(screen.getByText('3 of 3 conflicts selected')).toBeInTheDocument();
      });
    });

    it('should toggle all conflicts with Select All button', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const selectAllButton = screen.getByText('Select All');

      // Click to deselect all
      await user.click(selectAllButton);

      await waitFor(() => {
        expect(screen.getByText('0 of 3 conflicts selected')).toBeInTheDocument();
      });

      // Click again to select all
      await user.click(selectAllButton);

      await waitFor(() => {
        expect(screen.getByText('3 of 3 conflicts selected')).toBeInTheDocument();
      });
    });

    it('should select conflicts by severity', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // Deselect all first
      await user.click(screen.getByText('Select All'));

      // Select only critical
      const selectCriticalButton = screen.getByText(/Select critical \(1\)/);
      await user.click(selectCriticalButton);

      await waitFor(() => {
        expect(screen.getByText('1 of 3 conflicts selected')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering', () => {
    it('should filter by severity', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const severityFilter = screen.getByDisplayValue('All severities');
      await user.selectOptions(severityFilter, 'critical');

      await waitFor(() => {
        expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
        expect(screen.queryByText('Double-booked time slot')).not.toBeInTheDocument();
      });
    });

    it('should filter by type', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const typeFilter = screen.getByDisplayValue('All types');
      await user.selectOptions(typeFilter, 'absence_conflict');

      await waitFor(() => {
        expect(screen.getByText('Assignment during absence')).toBeInTheDocument();
        expect(screen.queryByText('Double-booked time slot')).not.toBeInTheDocument();
      });
    });
  });

  describe('Resolution Method Selection', () => {
    it('should default to auto-resolve method', () => {
      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const autoResolveRadio = screen.getByLabelText(/Auto-resolve/);
      expect(autoResolveRadio).toBeChecked();
    });

    it('should switch to ignore method when selected', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const ignoreRadio = screen.getByLabelText(/Ignore All/);
      await user.click(ignoreRadio);

      expect(ignoreRadio).toBeChecked();
    });

    it('should show reason textarea when ignore method is selected', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const ignoreRadio = screen.getByLabelText(/Ignore All/);
      await user.click(ignoreRadio);

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Provide a reason for ignoring/)).toBeInTheDocument();
      });
    });

    it('should require reason when ignore method is selected', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const ignoreRadio = screen.getByLabelText(/Ignore All/);
      await user.click(ignoreRadio);

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      expect(processButton).toBeDisabled();
    });
  });

  describe('Processing Conflicts', () => {
    it('should call batchResolve mutation with auto-resolve method', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockResolvedValue({
        total: 3,
        successful: 3,
        failed: 0,
        results: [],
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      expect(mockBatchResolveMutate).toHaveBeenCalledWith({
        conflict_ids: ['conflict-1', 'conflict-2', 'conflict-3'],
        resolution_method: 'auto_resolved',
      });
    });

    it('should call batchIgnore mutation with ignore method and reason', async () => {
      const user = userEvent.setup();

      mockBatchIgnoreMutate.mockResolvedValue({
        success: 3,
        failed: 0,
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // Switch to ignore method
      const ignoreRadio = screen.getByLabelText(/Ignore All/);
      await user.click(ignoreRadio);

      // Enter reason
      const reasonInput = screen.getByPlaceholderText(/Provide a reason for ignoring/);
      await user.type(reasonInput, 'Not applicable for current schedule');

      // Process
      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      expect(mockBatchIgnoreMutate).toHaveBeenCalledWith({
        conflictIds: ['conflict-1', 'conflict-2', 'conflict-3'],
        reason: 'Not applicable for current schedule',
      });
    });

    it('should disable process button when no conflicts selected', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      // Deselect all
      await user.click(screen.getByText('Select All'));

      const processButton = screen.getByRole('button', { name: /Process 0 Conflicts/ });
      expect(processButton).toBeDisabled();
    });

    it('should show loading state while processing', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ total: 3, successful: 3, failed: 0, results: [] }), 100))
      );

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      expect(screen.getByText('Processing...')).toBeInTheDocument();
    });
  });

  describe('Results Display', () => {
    it('should display success results', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockResolvedValue({
        total: 3,
        successful: 3,
        failed: 0,
        results: [],
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText('All Conflicts Resolved')).toBeInTheDocument();
        expect(screen.getByText('3 of 3 conflicts resolved (100%)')).toBeInTheDocument();
      });
    });

    it('should display partial success results', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockResolvedValue({
        total: 3,
        successful: 2,
        failed: 1,
        results: [],
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText('Partial Success')).toBeInTheDocument();
        expect(screen.getByText('2 of 3 conflicts resolved (67%)')).toBeInTheDocument();
      });
    });

    it('should display failure results', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockResolvedValue({
        total: 3,
        successful: 0,
        failed: 3,
        results: [],
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText('Resolution Failed')).toBeInTheDocument();
        expect(screen.getByText('0 of 3 conflicts resolved (0%)')).toBeInTheDocument();
      });
    });

    it('should call onComplete when Done button is clicked in results', async () => {
      const user = userEvent.setup();

      mockBatchResolveMutate.mockResolvedValue({
        total: 3,
        successful: 3,
        failed: 0,
        results: [],
      });

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const processButton = screen.getByRole('button', { name: /Process 3 Conflicts/ });
      await user.click(processButton);

      await waitFor(() => {
        expect(screen.getByText('All Conflicts Resolved')).toBeInTheDocument();
      });

      const doneButton = screen.getByRole('button', { name: 'Done' });
      await user.click(doneButton);

      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('Cancel Functionality', () => {
    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const cancelButtons = screen.getAllByRole('button', { name: 'Cancel' });
      await user.click(cancelButtons[0]);

      expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should call onCancel when X button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <BatchResolution
          conflicts={mockConflicts}
          onComplete={mockOnComplete}
          onCancel={mockOnCancel}
        />,
        { wrapper: createWrapper() }
      );

      const closeButton = screen.getByLabelText('Cancel');
      await user.click(closeButton);

      expect(mockOnCancel).toHaveBeenCalled();
    });
  });
});
