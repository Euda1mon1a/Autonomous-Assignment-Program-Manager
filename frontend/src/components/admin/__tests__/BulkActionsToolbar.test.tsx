/**
 * BulkActionsToolbar Component Tests
 *
 * Tests for the bulk actions toolbar including:
 * - Visibility based on selection
 * - Action buttons
 * - Confirmation modals
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BulkActionsToolbar } from '../BulkActionsToolbar';

// ============================================================================
// Tests
// ============================================================================

describe('BulkActionsToolbar', () => {
  const defaultProps = {
    selectedCount: 3,
    onClearSelection: jest.fn(),
    onBulkDelete: jest.fn(),
    onBulkUpdateActivityType: jest.fn(),
    onBulkUpdateSupervision: jest.fn(),
    onBulkUpdateMaxResidents: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Visibility', () => {
    it('renders when items are selected', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('selected')).toBeInTheDocument();
    });

    it('does not render when nothing selected', () => {
      const { container } = render(
        <BulkActionsToolbar {...defaultProps} selectedCount={0} />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Clear Selection', () => {
    it('calls onClearSelection when X button clicked', () => {
      const onClearSelection = jest.fn();
      render(
        <BulkActionsToolbar
          {...defaultProps}
          onClearSelection={onClearSelection}
        />
      );

      const clearButton = screen.getByTitle('Clear selection');
      fireEvent.click(clearButton);

      expect(onClearSelection).toHaveBeenCalled();
    });
  });

  describe('Delete Action', () => {
    it('shows confirmation modal when delete clicked', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);

      expect(screen.getByText('Delete Templates')).toBeInTheDocument();
      expect(
        screen.getByText(/Are you sure you want to delete 3 templates/)
      ).toBeInTheDocument();
    });

    it('calls onBulkDelete when confirmed', () => {
      const onBulkDelete = jest.fn();
      render(
        <BulkActionsToolbar {...defaultProps} onBulkDelete={onBulkDelete} />
      );

      // Open modal - find the delete button in the toolbar
      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]); // First one is toolbar button

      // Confirm - modal has a second Delete button
      const confirmButtons = screen.getAllByRole('button', { name: 'Delete' });
      fireEvent.click(confirmButtons[confirmButtons.length - 1]); // Last one is confirm

      expect(onBulkDelete).toHaveBeenCalled();
    });

    it('closes modal when cancelled', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      // Open modal
      fireEvent.click(screen.getByText('Delete'));
      expect(screen.getByText('Delete Templates')).toBeInTheDocument();

      // Cancel
      fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(screen.queryByText('Delete Templates')).not.toBeInTheDocument();
    });
  });

  describe('Activity Type Dropdown', () => {
    it('opens dropdown when clicked', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      fireEvent.click(screen.getByText('Activity Type'));

      // Check that options appear
      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
    });

    it('calls onBulkUpdateActivityType when option selected', () => {
      const onBulkUpdateActivityType = jest.fn();
      render(
        <BulkActionsToolbar
          {...defaultProps}
          onBulkUpdateActivityType={onBulkUpdateActivityType}
        />
      );

      fireEvent.click(screen.getByText('Activity Type'));
      fireEvent.click(screen.getByText('Inpatient'));

      expect(onBulkUpdateActivityType).toHaveBeenCalledWith('inpatient');
    });
  });

  describe('Supervision Dropdown', () => {
    it('opens dropdown when clicked', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      fireEvent.click(screen.getByText('Supervision'));

      expect(screen.getByText('Required')).toBeInTheDocument();
      expect(screen.getByText('Not Required')).toBeInTheDocument();
    });

    it('calls onBulkUpdateSupervision with true for Required', () => {
      const onBulkUpdateSupervision = jest.fn();
      render(
        <BulkActionsToolbar
          {...defaultProps}
          onBulkUpdateSupervision={onBulkUpdateSupervision}
        />
      );

      fireEvent.click(screen.getByText('Supervision'));
      fireEvent.click(screen.getByText('Required'));

      expect(onBulkUpdateSupervision).toHaveBeenCalledWith(true);
    });

    it('calls onBulkUpdateSupervision with false for Not Required', () => {
      const onBulkUpdateSupervision = jest.fn();
      render(
        <BulkActionsToolbar
          {...defaultProps}
          onBulkUpdateSupervision={onBulkUpdateSupervision}
        />
      );

      fireEvent.click(screen.getByText('Supervision'));
      fireEvent.click(screen.getByText('Not Required'));

      expect(onBulkUpdateSupervision).toHaveBeenCalledWith(false);
    });
  });

  describe('Max Residents Action', () => {
    it('opens modal when clicked', () => {
      render(<BulkActionsToolbar {...defaultProps} />);

      fireEvent.click(screen.getByText('Max Residents'));

      expect(screen.getByText('Set Max Residents')).toBeInTheDocument();
    });

    it('calls onBulkUpdateMaxResidents with value when confirmed', async () => {
      const onBulkUpdateMaxResidents = jest.fn();
      render(
        <BulkActionsToolbar
          {...defaultProps}
          onBulkUpdateMaxResidents={onBulkUpdateMaxResidents}
        />
      );

      // Open modal
      fireEvent.click(screen.getByText('Max Residents'));

      // Change value
      const input = screen.getByRole('spinbutton');
      fireEvent.change(input, { target: { value: '8' } });

      // Confirm
      fireEvent.click(screen.getByRole('button', { name: 'Apply' }));

      expect(onBulkUpdateMaxResidents).toHaveBeenCalledWith(8);
    });
  });

  describe('Loading State', () => {
    it('disables delete button when pending', () => {
      render(
        <BulkActionsToolbar
          {...defaultProps}
          isPending={true}
          pendingAction="delete"
        />
      );

      const deleteButton = screen.getByText('Delete').closest('button');
      expect(deleteButton).toBeDisabled();
    });

    it('shows spinner when action pending', () => {
      render(
        <BulkActionsToolbar
          {...defaultProps}
          isPending={true}
          pendingAction="delete"
        />
      );

      // Check for spinner (Loader2 has animate-spin class)
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });
});
