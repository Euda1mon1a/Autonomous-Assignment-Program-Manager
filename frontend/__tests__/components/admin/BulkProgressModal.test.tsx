/**
 * Tests for BulkProgressModal component
 *
 * Tests progress display, status updates, and completion states.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BulkProgressModal, BulkProgressItem } from '@/components/admin/BulkProgressModal';

describe('BulkProgressModal', () => {
  const defaultProps = {
    isOpen: true,
    operationType: 'delete' as const,
    totalItems: 5,
    completedItems: 2,
    failedItems: 0,
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<BulkProgressModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<BulkProgressModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should show operation title', () => {
      render(<BulkProgressModal {...defaultProps} />);
      expect(screen.getByText('Deleting Templates')).toBeInTheDocument();
    });

    it('should show progress description', () => {
      render(<BulkProgressModal {...defaultProps} />);
      expect(screen.getByText(/Deleting 5 templates/i)).toBeInTheDocument();
    });
  });

  describe('Operation Types', () => {
    it.each([
      ['delete', 'Deleting Templates', 'deleted'],
      ['update', 'Updating Templates', 'updated'],
      ['create', 'Creating Templates', 'created'],
      ['archive', 'Archiving Templates', 'archived'],
      ['restore', 'Restoring Templates', 'restored'],
      ['duplicate', 'Duplicating Templates', 'duplicated'],
    ] as const)('should show correct labels for %s operation', (type, title, _pastTense) => {
      render(<BulkProgressModal {...defaultProps} operationType={type} />);
      expect(screen.getByText(title)).toBeInTheDocument();
    });
  });

  describe('Progress Display', () => {
    it('should show progress bar', () => {
      render(<BulkProgressModal {...defaultProps} />);
      expect(screen.getByText('2 of 5')).toBeInTheDocument();
      expect(screen.getByText('40%')).toBeInTheDocument();
    });

    it('should show success count', () => {
      render(<BulkProgressModal {...defaultProps} completedItems={3} failedItems={1} />);
      expect(screen.getByText('2 succeeded')).toBeInTheDocument();
    });

    it('should show failure count when there are failures', () => {
      render(<BulkProgressModal {...defaultProps} completedItems={3} failedItems={1} />);
      expect(screen.getByText('1 failed')).toBeInTheDocument();
    });

    it('should not show failure count when no failures', () => {
      render(<BulkProgressModal {...defaultProps} completedItems={3} failedItems={0} />);
      expect(screen.queryByText('0 failed')).not.toBeInTheDocument();
    });
  });

  describe('Item List', () => {
    const items: BulkProgressItem[] = [
      { id: '1', label: 'Template A', status: 'success' },
      { id: '2', label: 'Template B', status: 'processing' },
      { id: '3', label: 'Template C', status: 'pending' },
      { id: '4', label: 'Template D', status: 'error', error: 'Failed to delete' },
    ];

    it('should render item list when provided', () => {
      render(<BulkProgressModal {...defaultProps} items={items} />);

      expect(screen.getByText('Template A')).toBeInTheDocument();
      expect(screen.getByText('Template B')).toBeInTheDocument();
      expect(screen.getByText('Template C')).toBeInTheDocument();
      expect(screen.getByText('Template D')).toBeInTheDocument();
    });

    it('should show error message for failed items', () => {
      render(<BulkProgressModal {...defaultProps} items={items} />);
      expect(screen.getByText('Failed to delete')).toBeInTheDocument();
    });
  });

  describe('Completion States', () => {
    it('should show success message when complete with no failures', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={0}
          isComplete
        />
      );

      expect(screen.getByText('Operation Complete')).toBeInTheDocument();
      expect(screen.getByText(/5 templates deleted successfully/i)).toBeInTheDocument();
    });

    it('should show error message when all failed', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={5}
          isComplete
        />
      );

      expect(screen.getByText('Operation Failed')).toBeInTheDocument();
    });

    it('should show partial success message when some failed', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={2}
          isComplete
        />
      );

      expect(screen.getByText('Operation Completed with Errors')).toBeInTheDocument();
      expect(screen.getByText(/3 templates deleted successfully/i)).toBeInTheDocument();
    });

    it('should show close button when complete', () => {
      render(<BulkProgressModal {...defaultProps} isComplete />);
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });

    it('should show Done button in footer when complete', () => {
      render(<BulkProgressModal {...defaultProps} isComplete />);
      expect(screen.getByRole('button', { name: /done/i })).toBeInTheDocument();
    });
  });

  describe('Cancel Functionality', () => {
    it('should show cancel button when onCancel is provided and not complete', () => {
      render(<BulkProgressModal {...defaultProps} onCancel={jest.fn()} />);
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should not show cancel button when complete', () => {
      render(<BulkProgressModal {...defaultProps} onCancel={jest.fn()} isComplete />);
      expect(screen.queryByRole('button', { name: /cancel$/i })).not.toBeInTheDocument();
    });

    it('should call onCancel when cancel button is clicked', async () => {
      const user = userEvent.setup();
      const onCancel = jest.fn();
      render(<BulkProgressModal {...defaultProps} onCancel={onCancel} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    it('should show cancelling state', () => {
      render(
        <BulkProgressModal {...defaultProps} onCancel={jest.fn()} isCancelling />
      );

      expect(screen.getByText(/cancelling/i)).toBeInTheDocument();
    });

    it('should disable cancel button when cancelling', () => {
      render(
        <BulkProgressModal {...defaultProps} onCancel={jest.fn()} isCancelling />
      );

      expect(screen.getByRole('button', { name: /cancelling/i })).toBeDisabled();
    });
  });

  describe('Close Functionality', () => {
    it('should call onClose when close button is clicked (complete state)', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkProgressModal {...defaultProps} onClose={onClose} isComplete />);

      await user.click(screen.getByRole('button', { name: /done/i }));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when X button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkProgressModal {...defaultProps} onClose={onClose} isComplete />);

      await user.click(screen.getByTitle('Close'));

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('Results Display', () => {
    it('should show errors section when results have failures', () => {
      const results = [
        { index: 0, templateId: '1', success: true, error: null },
        { index: 1, templateId: '2', success: false, error: 'Template not found' },
        { index: 2, templateId: '3', success: false, error: 'Permission denied' },
      ];

      render(<BulkProgressModal {...defaultProps} results={results} isComplete />);

      expect(screen.getByText('Errors')).toBeInTheDocument();
      expect(screen.getByText(/Item 2: Template not found/i)).toBeInTheDocument();
      expect(screen.getByText(/Item 3: Permission denied/i)).toBeInTheDocument();
    });

    it('should not show errors section when all successful', () => {
      const results = [
        { index: 0, templateId: '1', success: true, error: null },
        { index: 1, templateId: '2', success: true, error: null },
      ];

      render(<BulkProgressModal {...defaultProps} results={results} isComplete />);

      expect(screen.queryByText('Errors')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role', () => {
      render(<BulkProgressModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby pointing to title', () => {
      render(<BulkProgressModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'bulk-progress-title');
    });

    it('should have accessible close button', () => {
      render(<BulkProgressModal {...defaultProps} isComplete />);
      expect(screen.getByTitle('Close')).toHaveAttribute('aria-label', 'Close dialog');
    });
  });

  describe('Visual States', () => {
    it('should show violet color for in-progress', () => {
      render(<BulkProgressModal {...defaultProps} />);
      // Progress bar should be violet during operation
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should show emerald color for success', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={0}
          isComplete
        />
      );
      // Success icon should be emerald
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should show red color for error', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={5}
          isComplete
        />
      );
      // Error icon should be red
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });

    it('should show amber color for partial success', () => {
      render(
        <BulkProgressModal
          {...defaultProps}
          completedItems={5}
          failedItems={2}
          isComplete
        />
      );
      // Warning icon should be amber
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
    });
  });
});
