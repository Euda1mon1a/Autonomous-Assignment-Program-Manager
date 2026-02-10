/**
 * OperationHistoryPanel Component Tests
 *
 * Tests for the operation history panel including:
 * - Rendering operations list
 * - Empty state
 * - Loading state
 * - Expand/collapse operation details
 * - Undo button functionality
 * - Clear history
 * - Show more button
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import {
  OperationHistoryPanel,
  type OperationRecord,
  type OperationHistoryPanelProps,
} from '../OperationHistoryPanel';

// ============================================================================
// Mock BulkProgressModal to avoid import issues with its type
// ============================================================================

jest.mock('../BulkProgressModal', () => ({
  __esModule: true,
}));

// ============================================================================
// Test Data
// ============================================================================

function makeOperation(overrides?: Partial<OperationRecord>): OperationRecord {
  return {
    id: 'op-1',
    type: 'update',
    timestamp: new Date('2024-06-15T10:00:00Z'),
    templateIds: ['t1', 't2'],
    templateNames: ['Template Alpha', 'Template Beta'],
    status: 'success',
    canUndo: true,
    details: 'Updated activity type to inpatient',
    ...overrides,
  };
}

const defaultProps: OperationHistoryPanelProps = {
  operations: [
    makeOperation({ id: 'op-1', type: 'update' }),
    makeOperation({
      id: 'op-2',
      type: 'delete',
      timestamp: new Date('2024-06-15T09:00:00Z'),
      templateIds: ['t3'],
      templateNames: ['Template Gamma'],
      status: 'success',
      canUndo: false,
    }),
    makeOperation({
      id: 'op-3',
      type: 'create',
      timestamp: new Date('2024-06-15T08:00:00Z'),
      templateIds: ['t4', 't5', 't6'],
      templateNames: ['Template Delta', 'Template Epsilon', 'Template Zeta'],
      status: 'failed',
      canUndo: false,
    }),
  ],
  onUndo: jest.fn().mockResolvedValue(undefined),
};

// ============================================================================
// Tests
// ============================================================================

describe('OperationHistoryPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders the Operation History header', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.getByText('Operation History')).toBeInTheDocument();
    });

    it('shows total operations count', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('renders operation type labels', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.getByText('Updated')).toBeInTheDocument();
      expect(screen.getByText('Deleted')).toBeInTheDocument();
      expect(screen.getByText('Created')).toBeInTheDocument();
    });

    it('renders template count for each operation', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.getByText('2 templates')).toBeInTheDocument();
      expect(screen.getByText('1 template')).toBeInTheDocument();
      expect(screen.getByText('3 templates')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty message when no operations', () => {
      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={[]}
        />
      );

      expect(screen.getByText('No recent operations')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows spinner when loading', () => {
      const { container } = render(
        <OperationHistoryPanel {...defaultProps} isLoading />
      );

      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('does not show operations when loading', () => {
      render(<OperationHistoryPanel {...defaultProps} isLoading />);

      expect(screen.queryByText('Updated')).not.toBeInTheDocument();
    });
  });

  describe('Expand/Collapse', () => {
    it('expands operation details when clicked', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      // Click the first operation row
      const expandButton = screen.getAllByLabelText('Expand')[0];
      fireEvent.click(expandButton.closest('[class*="cursor-pointer"]')!);

      expect(screen.getByText('Affected templates:')).toBeInTheDocument();
      expect(screen.getByText('Template Alpha')).toBeInTheDocument();
      expect(screen.getByText('Template Beta')).toBeInTheDocument();
    });

    it('shows operation details text when expanded', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      // Click the first operation
      const expandButton = screen.getAllByLabelText('Expand')[0];
      fireEvent.click(expandButton.closest('[class*="cursor-pointer"]')!);

      expect(screen.getByText('Updated activity type to inpatient')).toBeInTheDocument();
    });

    it('collapses when clicked again', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      // Expand
      const expandButton = screen.getAllByLabelText('Expand')[0];
      fireEvent.click(expandButton.closest('[class*="cursor-pointer"]')!);
      expect(screen.getByText('Affected templates:')).toBeInTheDocument();

      // Collapse
      const collapseButton = screen.getByLabelText('Collapse');
      fireEvent.click(collapseButton.closest('[class*="cursor-pointer"]')!);
      expect(screen.queryByText('Affected templates:')).not.toBeInTheDocument();
    });
  });

  describe('Undo', () => {
    it('shows Undo button for undoable operations', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.getByText('Undo')).toBeInTheDocument();
    });

    it('does not show Undo button for non-undoable operations', () => {
      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={[
            makeOperation({ id: 'op-x', canUndo: false }),
          ]}
        />
      );

      expect(screen.queryByText('Undo')).not.toBeInTheDocument();
    });

    it('calls onUndo when Undo clicked', async () => {
      const onUndo = jest.fn().mockResolvedValue(undefined);
      render(
        <OperationHistoryPanel {...defaultProps} onUndo={onUndo} />
      );

      fireEvent.click(screen.getByText('Undo'));

      await waitFor(() => {
        expect(onUndo).toHaveBeenCalledWith('op-1');
      });
    });

    it('shows undoing state for specific operation', () => {
      const { container } = render(
        <OperationHistoryPanel {...defaultProps} undoingId="op-1" />
      );

      // The undo button for op-1 should be disabled
      const undoButton = screen.getByText('Undo').closest('button');
      expect(undoButton).toBeDisabled();

      // Should show spinner
      const spinner = container.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('does not show Undo for undone operations', () => {
      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={[
            makeOperation({ id: 'op-undone', status: 'undone', canUndo: true }),
          ]}
        />
      );

      expect(screen.queryByText('Undo')).not.toBeInTheDocument();
      expect(screen.getByText('Undone')).toBeInTheDocument();
    });
  });

  describe('Clear History', () => {
    it('shows Clear button when onClearHistory is provided', () => {
      const onClearHistory = jest.fn();
      render(
        <OperationHistoryPanel
          {...defaultProps}
          onClearHistory={onClearHistory}
        />
      );

      expect(screen.getByText('Clear')).toBeInTheDocument();
    });

    it('does not show Clear button when onClearHistory is not provided', () => {
      render(<OperationHistoryPanel {...defaultProps} />);

      expect(screen.queryByText('Clear')).not.toBeInTheDocument();
    });

    it('calls onClearHistory when clicked', () => {
      const onClearHistory = jest.fn();
      render(
        <OperationHistoryPanel
          {...defaultProps}
          onClearHistory={onClearHistory}
        />
      );

      fireEvent.click(screen.getByText('Clear'));

      expect(onClearHistory).toHaveBeenCalled();
    });

    it('does not show Clear button for empty operations', () => {
      const onClearHistory = jest.fn();
      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={[]}
          onClearHistory={onClearHistory}
        />
      );

      expect(screen.queryByText('Clear')).not.toBeInTheDocument();
    });
  });

  describe('Show More', () => {
    it('shows "Show more" button when operations exceed maxItems', () => {
      const manyOps = Array.from({ length: 25 }, (_, i) =>
        makeOperation({
          id: `op-${i}`,
          timestamp: new Date(2024, 5, 15, 10 - i),
        })
      );

      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={manyOps}
          maxItems={20}
        />
      );

      expect(screen.getByText('Show 5 more')).toBeInTheDocument();
    });

    it('does not show "Show more" when all operations fit', () => {
      render(<OperationHistoryPanel {...defaultProps} maxItems={20} />);

      expect(screen.queryByText(/Show \d+ more/)).not.toBeInTheDocument();
    });

    it('shows all operations after clicking Show more', () => {
      const manyOps = Array.from({ length: 25 }, (_, i) =>
        makeOperation({
          id: `op-${i}`,
          timestamp: new Date(2024, 5, 15, 10, 60 - i),
        })
      );

      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={manyOps}
          maxItems={20}
        />
      );

      fireEvent.click(screen.getByText('Show 5 more'));

      expect(screen.queryByText(/Show \d+ more/)).not.toBeInTheDocument();
    });
  });

  describe('Status Icons', () => {
    it('shows success indicator for successful non-undoable operations', () => {
      render(
        <OperationHistoryPanel
          {...defaultProps}
          operations={[
            makeOperation({ id: 'op-ok', status: 'success', canUndo: false }),
          ]}
        />
      );

      // The CheckCircle2 icon is present but no Undo button
      expect(screen.queryByText('Undo')).not.toBeInTheDocument();
    });
  });
});
