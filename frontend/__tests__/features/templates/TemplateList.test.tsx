/**
 * Tests for TemplateList Component
 *
 * Tests rendering of template lists, loading/error states, and variants.
 */

import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { TemplateList, PredefinedTemplateCard } from '@/features/templates/components/TemplateList';
import type { ScheduleTemplate } from '@/features/templates/types';

// Mock TemplateCard component
jest.mock('@/features/templates/components/TemplateCard', () => ({
  TemplateCard: ({ template, onEdit, onDelete, onPreview }: {
    template: { id: string; name: string };
    onEdit?: () => void;
    onDelete?: () => void;
    onPreview?: () => void;
  }) => (
    <div data-testid={`template-card-${template.id}`}>
      <div>{template.name}</div>
      {onEdit && <button onClick={onEdit}>Edit</button>}
      {onDelete && <button onClick={onDelete}>Delete</button>}
      {onPreview && <button onClick={onPreview}>Preview</button>}
    </div>
  ),
}));

describe('TemplateList', () => {
  const mockTemplates: ScheduleTemplate[] = [
    {
      id: 'template-1',
      name: 'Clinic Template',
      description: 'Standard clinic schedule',
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
    },
    {
      id: 'template-2',
      name: 'Call Template',
      description: 'Call rotation template',
      category: 'call',
      visibility: 'shared',
      status: 'active',
      durationWeeks: 1,
      startDayOfWeek: 0,
      patterns: [],
      requiresSupervision: false,
      allowWeekends: true,
      allowHolidays: true,
      tags: [],
      createdBy: 'user-1',
      createdAt: '2025-01-01T00:00:00Z',
      updatedAt: '2025-01-01T00:00:00Z',
      usageCount: 3,
      isPublic: false,
      version: 1,
    },
  ];

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnDuplicate = jest.fn();
  const mockOnShare = jest.fn();
  const mockOnPreview = jest.fn();
  const mockOnApply = jest.fn();
  const mockOnRetry = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Grid Variant', () => {
    it('should render templates in grid layout', () => {
      const { container } = render(
        <TemplateList templates={mockTemplates} variant="grid" />
      );

      expect(screen.getByTestId('template-card-template-1')).toBeInTheDocument();
      expect(screen.getByTestId('template-card-template-2')).toBeInTheDocument();

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should pass props to TemplateCard components', () => {
      render(
        <TemplateList
          templates={mockTemplates}
          variant="grid"
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onPreview={mockOnPreview}
        />
      );

      expect(screen.getAllByText('Edit')).toHaveLength(2);
      expect(screen.getAllByText('Delete')).toHaveLength(2);
      expect(screen.getAllByText('Preview')).toHaveLength(2);
    });
  });

  describe('List Variant', () => {
    it('should render templates in list layout', () => {
      const { container } = render(
        <TemplateList templates={mockTemplates} variant="list" />
      );

      expect(screen.getByText('Clinic Template')).toBeInTheDocument();
      expect(screen.getByText('Call Template')).toBeInTheDocument();

      const listContainer = container.querySelector('.space-y-3');
      expect(listContainer).toBeInTheDocument();
    });

    it('should show template metadata in list view', () => {
      render(
        <TemplateList templates={mockTemplates} variant="list" />
      );

      // Should show duration and pattern count
      expect(screen.getAllByText(/1w/)).toHaveLength(2);
      expect(screen.getAllByText(/0 patterns/)).toHaveLength(2);
    });

    it('should show action buttons in list view', () => {
      render(
        <TemplateList
          templates={mockTemplates}
          variant="list"
          onEdit={mockOnEdit}
          onApply={mockOnApply}
        />
      );

      expect(screen.getAllByText('Edit')).toHaveLength(2);
      expect(screen.getAllByText('Apply')).toHaveLength(2);
    });

    it('should call onApply when Apply is clicked in list view', async () => {
      const user = userEvent.setup();
      render(
        <TemplateList
          templates={mockTemplates}
          variant="list"
          onApply={mockOnApply}
        />
      );

      const applyButtons = screen.getAllByText('Apply');
      await user.click(applyButtons[0]);

      expect(mockOnApply).toHaveBeenCalledWith(mockTemplates[0]);
    });

    it('should call onPreview when clicking list item', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <TemplateList
          templates={mockTemplates}
          variant="list"
          onPreview={mockOnPreview}
        />
      );

      const listItems = container.querySelectorAll('.flex.items-center.justify-between');
      if (listItems[0]) {
        await user.click(listItems[0]);
        expect(mockOnPreview).toHaveBeenCalledWith(mockTemplates[0]);
      }
    });
  });

  describe('Loading State', () => {
    it('should render skeleton loaders when loading', () => {
      const { container } = render(
        <TemplateList templates={[]} isLoading={true} variant="grid" />
      );

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should render 6 skeleton items in grid view', () => {
      const { container } = render(
        <TemplateList templates={[]} isLoading={true} variant="grid" />
      );

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(6);
    });

    it('should render skeleton items in list view', () => {
      const { container } = render(
        <TemplateList templates={[]} isLoading={true} variant="list" />
      );

      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('should not show templates while loading', () => {
      render(
        <TemplateList templates={mockTemplates} isLoading={true} />
      );

      expect(screen.queryByText('Clinic Template')).not.toBeInTheDocument();
      expect(screen.queryByText('Call Template')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should render error message', () => {
      render(
        <TemplateList
          templates={[]}
          isError={true}
          error={new Error('Failed to load templates')}
        />
      );

      expect(screen.getByText('Failed to load templates')).toBeInTheDocument();
    });

    it('should show generic error message if no error provided', () => {
      render(
        <TemplateList
          templates={[]}
          isError={true}
        />
      );

      expect(screen.getByText('Failed to load templates')).toBeInTheDocument();
    });

    it('should show retry button on error', () => {
      render(
        <TemplateList
          templates={[]}
          isError={true}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateList
          templates={[]}
          isError={true}
          onRetry={mockOnRetry}
        />
      );

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalled();
    });

    it('should not show retry button if onRetry is not provided', () => {
      render(
        <TemplateList
          templates={[]}
          isError={true}
        />
      );

      expect(screen.queryByText('Retry')).not.toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('should render empty state when no templates', () => {
      render(<TemplateList templates={[]} />);

      expect(screen.getByText('No templates found')).toBeInTheDocument();
    });

    it('should use custom empty message', () => {
      render(
        <TemplateList
          templates={[]}
          emptyMessage="No clinic templates available"
        />
      );

      expect(screen.getByText('No clinic templates available')).toBeInTheDocument();
    });

    it('should show empty action button', () => {
      const mockEmptyAction = jest.fn();
      render(
        <TemplateList
          templates={[]}
          emptyAction={{
            label: 'Create First Template',
            onClick: mockEmptyAction,
          }}
        />
      );

      expect(screen.getByText('Create First Template')).toBeInTheDocument();
    });

    it('should call empty action onClick', async () => {
      const user = userEvent.setup();
      const mockEmptyAction = jest.fn();
      render(
        <TemplateList
          templates={[]}
          emptyAction={{
            label: 'Create First Template',
            onClick: mockEmptyAction,
          }}
        />
      );

      const button = screen.getByText('Create First Template');
      await user.click(button);

      expect(mockEmptyAction).toHaveBeenCalled();
    });

    it('should show suggestion text in empty state', () => {
      render(<TemplateList templates={[]} />);

      expect(screen.getByText('Get started by creating your first template')).toBeInTheDocument();
    });
  });

  describe('Action Callbacks', () => {
    it('should call onEdit with correct template', async () => {
      const user = userEvent.setup();
      render(
        <TemplateList
          templates={mockTemplates}
          variant="grid"
          onEdit={mockOnEdit}
        />
      );

      const editButtons = screen.getAllByText('Edit');
      await user.click(editButtons[0]);

      expect(mockOnEdit).toHaveBeenCalledWith(mockTemplates[0]);
    });

    it('should call onDelete with correct template', async () => {
      const user = userEvent.setup();
      render(
        <TemplateList
          templates={mockTemplates}
          variant="grid"
          onDelete={mockOnDelete}
        />
      );

      const deleteButtons = screen.getAllByText('Delete');
      await user.click(deleteButtons[1]);

      expect(mockOnDelete).toHaveBeenCalledWith(mockTemplates[1]);
    });

    it('should call onPreview with correct template', async () => {
      const user = userEvent.setup();
      render(
        <TemplateList
          templates={mockTemplates}
          variant="grid"
          onPreview={mockOnPreview}
        />
      );

      const previewButtons = screen.getAllByText('Preview');
      await user.click(previewButtons[0]);

      expect(mockOnPreview).toHaveBeenCalledWith(mockTemplates[0]);
    });
  });
});

describe('PredefinedTemplateCard', () => {
  const mockPredefinedTemplate = {
    templateKey: 'standard-clinic',
    name: 'Standard Clinic Template',
    description: 'Pre-built clinic schedule',
    category: 'clinic',
    patterns: [{ id: 'p1' }, { id: 'p2' }],
    durationWeeks: 1,
    tags: ['clinic', 'weekday'],
  };

  const mockOnImport = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render template name', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('Standard Clinic Template')).toBeInTheDocument();
    });

    it('should render description', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('Pre-built clinic schedule')).toBeInTheDocument();
    });

    it('should render category', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('clinic')).toBeInTheDocument();
    });

    it('should render System badge', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('System')).toBeInTheDocument();
    });

    it('should display duration', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText(/1 week/)).toBeInTheDocument();
    });

    it('should display pattern count', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('2 patterns')).toBeInTheDocument();
    });

    it('should display tags', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('#clinic')).toBeInTheDocument();
      expect(screen.getByText('#weekday')).toBeInTheDocument();
    });
  });

  describe('Import Button', () => {
    it('should render import button', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      expect(screen.getByText('Import to Library')).toBeInTheDocument();
    });

    it('should call onImport when clicked', async () => {
      const user = userEvent.setup();
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      const importButton = screen.getByText('Import to Library');
      await user.click(importButton);

      expect(mockOnImport).toHaveBeenCalledWith('standard-clinic');
    });

    it('should show loading state when importing', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
          isImporting={true}
        />
      );

      expect(screen.getByText('Importing...')).toBeInTheDocument();
    });

    it('should disable button when importing', () => {
      render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
          isImporting={true}
        />
      );

      const button = screen.getByText('Importing...');
      expect(button).toBeDisabled();
    });
  });

  describe('Category Styling', () => {
    it('should apply clinic category colors', () => {
      const { container } = render(
        <PredefinedTemplateCard
          template={mockPredefinedTemplate}
          onImport={mockOnImport}
        />
      );

      const card = container.querySelector('.bg-teal-50');
      expect(card).toBeInTheDocument();
    });

    it('should apply call category colors', () => {
      const callTemplate = { ...mockPredefinedTemplate, category: 'call' };
      const { container } = render(
        <PredefinedTemplateCard
          template={callTemplate}
          onImport={mockOnImport}
        />
      );

      const card = container.querySelector('.bg-orange-50');
      expect(card).toBeInTheDocument();
    });
  });
});
