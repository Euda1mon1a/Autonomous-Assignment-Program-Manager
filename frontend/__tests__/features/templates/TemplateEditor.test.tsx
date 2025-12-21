/**
 * Tests for TemplateEditor Component
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TemplateEditor } from '@/features/templates/components/TemplateEditor';
import type { ScheduleTemplate } from '@/features/templates/types';

describe('TemplateEditor', () => {
  const mockOnSave = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render create template form', () => {
    render(
      <TemplateEditor
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Create Template')).toBeInTheDocument();
    expect(screen.getByLabelText(/Template Name/)).toBeInTheDocument();
  });

  it('should render edit template form with existing data', () => {
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
      tags: ['test'],
      createdBy: 'user-1',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
      usageCount: 0,
      isPublic: false,
      version: 1,
    };

    render(
      <TemplateEditor
        template={mockTemplate}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Edit Template')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Template')).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    const user = userEvent.setup();
    render(
      <TemplateEditor
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const saveButton = screen.getByText('Create Template');
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeInTheDocument();
    });

    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it('should call onSave with form data', async () => {
    const user = userEvent.setup();
    render(
      <TemplateEditor
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const nameInput = screen.getByLabelText(/Template Name/);
    await user.type(nameInput, 'New Template');

    const saveButton = screen.getByText('Create Template');
    await user.click(saveButton);

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'New Template',
        })
      );
    });
  });

  it('should call onCancel when cancel is clicked', async () => {
    const user = userEvent.setup();
    render(
      <TemplateEditor
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('should disable save button while loading', () => {
    render(
      <TemplateEditor
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        isLoading={true}
      />
    );

    const saveButton = screen.getByText('Saving...');
    expect(saveButton).toBeDisabled();
  });
});
