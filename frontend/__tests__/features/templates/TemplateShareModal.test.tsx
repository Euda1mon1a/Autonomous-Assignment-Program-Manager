/**
 * Tests for TemplateShareModal Component
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplateShareModal } from '@/features/templates/components/TemplateShareModal';
import type { ScheduleTemplate } from '@/features/templates/types';

describe('TemplateShareModal', () => {
  const mockTemplate: ScheduleTemplate = {
    id: 't1',
    name: 'Test Template',
    description: 'Test description',
    category: 'clinic',
    visibility: 'private',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 1,
    patterns: [],
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: [],
    createdBy: 'user-1',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    usageCount: 0,
    isPublic: false,
    version: 1,
  };

  const mockOnShare = jest.fn();
  const mockOnDuplicate = jest.fn();
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Share Mode', () => {
    it('should render share modal', () => {
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="share"
          onShare={mockOnShare}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Share Template')).toBeInTheDocument();
    });

    it('should show visibility options', () => {
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="share"
          onShare={mockOnShare}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Private')).toBeInTheDocument();
      expect(screen.getByText('Shared')).toBeInTheDocument();
      expect(screen.getByText('Public')).toBeInTheDocument();
    });

    it('should call onShare when save is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="share"
          onShare={mockOnShare}
          onClose={mockOnClose}
        />
      );

      const saveButton = screen.getByText('Save Changes');
      await user.click(saveButton);

      expect(mockOnShare).toHaveBeenCalled();
    });

    it('should show share link when not private', async () => {
      const user = userEvent.setup();
      render(
        <TemplateShareModal
          template={{ ...mockTemplate, visibility: 'public' }}
          mode="share"
          onShare={mockOnShare}
          onClose={mockOnClose}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Share Link')).toBeInTheDocument();
      });
    });
  });

  describe('Duplicate Mode', () => {
    it('should render duplicate modal', () => {
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="duplicate"
          onDuplicate={mockOnDuplicate}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText('Duplicate Template')).toBeInTheDocument();
    });

    it('should show new name input', () => {
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="duplicate"
          onDuplicate={mockOnDuplicate}
          onClose={mockOnClose}
        />
      );

      // The label and input aren't properly associated, so use placeholder or display value
      expect(screen.getByDisplayValue('Test Template (Copy)')).toBeInTheDocument();
    });

    it('should show include patterns option', () => {
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="duplicate"
          onDuplicate={mockOnDuplicate}
          onClose={mockOnClose}
        />
      );

      expect(screen.getByText(/Include assignment patterns/)).toBeInTheDocument();
    });

    it('should call onDuplicate when create is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="duplicate"
          onDuplicate={mockOnDuplicate}
          onClose={mockOnClose}
        />
      );

      const createButton = screen.getByText('Create Duplicate');
      await user.click(createButton);

      expect(mockOnDuplicate).toHaveBeenCalled();
    });

    it('should allow changing duplicate name', async () => {
      const user = userEvent.setup();
      render(
        <TemplateShareModal
          template={mockTemplate}
          mode="duplicate"
          onDuplicate={mockOnDuplicate}
          onClose={mockOnClose}
        />
      );

      // Find the input by its default value
      const nameInput = screen.getByDisplayValue('Test Template (Copy)');
      await user.clear(nameInput);
      await user.type(nameInput, 'New Name');

      expect(nameInput).toHaveValue('New Name');
    });
  });

  it('should call onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TemplateShareModal
        template={mockTemplate}
        mode="share"
        onShare={mockOnShare}
        onClose={mockOnClose}
      />
    );

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should call onClose when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TemplateShareModal
        template={mockTemplate}
        mode="share"
        onShare={mockOnShare}
        onClose={mockOnClose}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });
});
