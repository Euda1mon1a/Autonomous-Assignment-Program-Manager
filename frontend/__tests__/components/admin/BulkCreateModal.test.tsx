/**
 * Tests for BulkCreateModal component
 *
 * Tests rendering, template management, validation, and submission.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BulkCreateModal } from '@/components/admin/BulkCreateModal';
import type { TemplateCreateRequest } from '@/types/admin-templates';

describe('BulkCreateModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onSubmit: jest.fn().mockResolvedValue(undefined),
    isSubmitting: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<BulkCreateModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should show modal title', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Create Multiple Templates')).toBeInTheDocument();
    });

    it('should show template count description', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText(/Add 1 template at once/i)).toBeInTheDocument();
    });

    it('should render with one default template row', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('#1')).toBeInTheDocument();
    });

    it('should show Add Template button', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Add Template')).toBeInTheDocument();
    });

    it('should show Cancel button', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should show Create button', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /create 1 template/i })).toBeInTheDocument();
    });
  });

  describe('Template Management', () => {
    it('should add a new template row when Add Template is clicked', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      await user.click(screen.getByText('Add Template'));

      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText(/Add 2 templates at once/i)).toBeInTheDocument();
    });

    it('should update template name when typing in input', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      const nameInput = screen.getByPlaceholderText('Template name *');
      await user.type(nameInput, 'Test Template');

      expect(nameInput).toHaveValue('Test Template');
    });

    it('should show duplicate button on template row', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByTitle('Duplicate')).toBeInTheDocument();
    });

    it('should duplicate template when duplicate button is clicked', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Fill in a name first
      const nameInput = screen.getByPlaceholderText('Template name *');
      await user.type(nameInput, 'Original Template');

      // Click duplicate
      await user.click(screen.getByTitle('Duplicate'));

      // Should now have 2 templates
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument();
    });

    it('should not show remove button when only one template exists', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.queryByTitle('Remove')).not.toBeInTheDocument();
    });

    it('should show remove button when multiple templates exist', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      await user.click(screen.getByText('Add Template'));

      expect(screen.getAllByTitle('Remove')).toHaveLength(2);
    });

    it('should remove template when remove button is clicked', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Add second template
      await user.click(screen.getByText('Add Template'));
      expect(screen.getByText('#2')).toBeInTheDocument();

      // Remove the second template
      const removeButtons = screen.getAllByTitle('Remove');
      await user.click(removeButtons[1]);

      // Should only have one template now
      expect(screen.queryByText('#2')).not.toBeInTheDocument();
      expect(screen.getByText(/Add 1 template at once/i)).toBeInTheDocument();
    });
  });

  describe('Template Expansion', () => {
    it('should toggle template expansion when clicking header', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // First template should be expanded by default (Activity Type label visible)
      expect(screen.getByText('Activity Type *')).toBeInTheDocument();

      // Click to collapse (using the expand/collapse button label)
      const collapseButton = screen.getByLabelText('Collapse');
      await user.click(collapseButton);

      // Expanded content should be hidden
      expect(screen.queryByText('Activity Type *')).not.toBeInTheDocument();
    });

    it('should expand collapsed template when clicking header', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Collapse first
      const collapseButton = screen.getByLabelText('Collapse');
      await user.click(collapseButton);

      // Should show expand button now
      const expandButton = screen.getByLabelText('Expand');
      await user.click(expandButton);

      // Should show expanded content again
      expect(screen.getByText('Activity Type *')).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    it('should show validation error when template name is empty', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Try to submit without entering a name
      const createButton = screen.getByRole('button', { name: /create 1 template/i });
      expect(createButton).toBeDisabled();

      // The error should appear in the validation section
      expect(screen.getByText(/Template #1 requires a name/i)).toBeInTheDocument();
    });

    it('should remove validation error when name is entered', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Initially disabled
      const createButton = screen.getByRole('button', { name: /create 1 template/i });
      expect(createButton).toBeDisabled();

      // Enter a name
      const nameInput = screen.getByPlaceholderText('Template name *');
      await user.type(nameInput, 'Test Template');

      // Should be enabled now
      expect(createButton).toBeEnabled();
    });

    it('should show duplicate name error', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Add two templates
      await user.click(screen.getByText('Add Template'));

      // Give same name to both
      const nameInputs = screen.getAllByPlaceholderText('Template name *');
      await user.type(nameInputs[0], 'Same Name');
      await user.type(nameInputs[1], 'Same Name');

      expect(screen.getByText(/Duplicate name: "Same Name"/i)).toBeInTheDocument();
    });

    it('should disable create button when validation fails', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Add duplicate names
      await user.click(screen.getByText('Add Template'));
      const nameInputs = screen.getAllByPlaceholderText('Template name *');
      await user.type(nameInputs[0], 'Duplicate');
      await user.type(nameInputs[1], 'Duplicate');

      const createButton = screen.getByRole('button', { name: /create 2 templates/i });
      expect(createButton).toBeDisabled();
    });
  });

  describe('Form Fields', () => {
    it('should show activity type selector in expanded view', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Activity Type *')).toBeInTheDocument();
    });

    it('should show abbreviation input', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('e.g., CLIN')).toBeInTheDocument();
    });

    it('should show max residents input', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByPlaceholderText('No limit')).toBeInTheDocument();
    });

    it('should show supervision required checkbox', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Supervision Required')).toBeInTheDocument();
    });

    it('should show procedure credential checkbox', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Requires Procedure Credential')).toBeInTheDocument();
    });

    it('should show color pickers', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByText('Background Color')).toBeInTheDocument();
      expect(screen.getByText('Font Color')).toBeInTheDocument();
    });
  });

  describe('Submit Functionality', () => {
    it('should call onSubmit with template data when form is valid', async () => {
      const user = userEvent.setup();
      const onSubmit = jest.fn().mockResolvedValue(undefined);
      render(<BulkCreateModal {...defaultProps} onSubmit={onSubmit} />);

      // Fill in the template name
      const nameInput = screen.getByPlaceholderText('Template name *');
      await user.type(nameInput, 'Test Template');

      // Click create
      const createButton = screen.getByRole('button', { name: /create 1 template/i });
      await user.click(createButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
      });

      // Check the data passed
      const submittedData = onSubmit.mock.calls[0][0] as TemplateCreateRequest[];
      expect(submittedData).toHaveLength(1);
      expect(submittedData[0].name).toBe('Test Template');
      expect(submittedData[0].activityType).toBe('clinic');
    });

    it('should show loading state while submitting', async () => {
      render(<BulkCreateModal {...defaultProps} isSubmitting={true} />);
      expect(screen.getByText('Creating...')).toBeInTheDocument();
    });

    it('should disable buttons while submitting', () => {
      render(<BulkCreateModal {...defaultProps} isSubmitting={true} />);
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
    });
  });

  describe('Close Functionality', () => {
    it('should call onClose when Cancel is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkCreateModal {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when X button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkCreateModal {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByLabelText('Close'));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should not close when submitting', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkCreateModal {...defaultProps} onClose={onClose} isSubmitting={true} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe('CSV Import', () => {
    it('should show Import CSV button when onOpenCSVImport is provided', () => {
      render(
        <BulkCreateModal {...defaultProps} onOpenCSVImport={jest.fn()} />
      );
      expect(screen.getByText('Import CSV')).toBeInTheDocument();
    });

    it('should not show Import CSV button when onOpenCSVImport is not provided', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.queryByText('Import CSV')).not.toBeInTheDocument();
    });

    it('should call onOpenCSVImport when Import CSV is clicked', async () => {
      const user = userEvent.setup();
      const onOpenCSVImport = jest.fn();
      render(
        <BulkCreateModal {...defaultProps} onOpenCSVImport={onOpenCSVImport} />
      );

      await user.click(screen.getByText('Import CSV'));

      expect(onOpenCSVImport).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby pointing to title', () => {
      render(<BulkCreateModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'bulk-create-title');
    });

    it('should have accessible close button', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });

    it('should have accessible duplicate button', () => {
      render(<BulkCreateModal {...defaultProps} />);
      expect(screen.getByLabelText('Duplicate template')).toBeInTheDocument();
    });
  });

  describe('Activity Type Badges', () => {
    it('should show default activity type in dropdown', () => {
      render(<BulkCreateModal {...defaultProps} />);
      // Check that the select shows Clinic as the selected value
      expect(screen.getByDisplayValue('Clinic')).toBeInTheDocument();
    });

    it('should update dropdown when activity type changes', async () => {
      const user = userEvent.setup();
      render(<BulkCreateModal {...defaultProps} />);

      // Change activity type to inpatient
      const select = screen.getByDisplayValue('Clinic');
      await user.selectOptions(select, 'inpatient');

      // Verify the dropdown changed
      expect(screen.getByDisplayValue('Inpatient')).toBeInTheDocument();
    });
  });
});
