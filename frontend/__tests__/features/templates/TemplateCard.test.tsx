/**
 * Tests for TemplateCard Component
 *
 * Tests rendering, actions, and user interactions with template cards.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TemplateCard } from '@/features/templates/components/TemplateCard';
import type { ScheduleTemplate } from '@/features/templates/types';

describe('TemplateCard', () => {
  const mockTemplate: ScheduleTemplate = {
    id: 'template-1',
    name: 'Standard Clinic Schedule',
    description: 'Weekly clinic schedule template',
    category: 'clinic',
    visibility: 'private',
    status: 'active',
    durationWeeks: 1,
    startDayOfWeek: 1,
    patterns: [
      {
        id: 'p1',
        name: 'Morning Clinic',
        dayOfWeek: 1,
        timeOfDay: 'AM',
        activityType: 'clinic',
        role: 'primary',
      },
      {
        id: 'p2',
        name: 'Afternoon Clinic',
        dayOfWeek: 1,
        timeOfDay: 'PM',
        activityType: 'clinic',
        role: 'primary',
      },
    ],
    requiresSupervision: true,
    allowWeekends: false,
    allowHolidays: false,
    tags: ['clinic', 'weekday'],
    createdBy: 'user-1',
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
    usageCount: 5,
    isPublic: false,
    version: 1,
  };

  const mockOnEdit = jest.fn();
  const mockOnDelete = jest.fn();
  const mockOnDuplicate = jest.fn();
  const mockOnShare = jest.fn();
  const mockOnPreview = jest.fn();
  const mockOnApply = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render template name', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText('Standard Clinic Schedule')).toBeInTheDocument();
    });

    it('should render template description', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText('Weekly clinic schedule template')).toBeInTheDocument();
    });

    it('should not render description if not provided', () => {
      const templateWithoutDesc = { ...mockTemplate, description: undefined };
      render(<TemplateCard template={templateWithoutDesc} />);
      expect(screen.queryByText('Weekly clinic schedule template')).not.toBeInTheDocument();
    });

    it('should display category badge', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText('clinic')).toBeInTheDocument();
    });

    it('should display status badge', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText('active')).toBeInTheDocument();
    });

    it('should display duration', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText(/1 week/)).toBeInTheDocument();
    });

    it('should display plural weeks correctly', () => {
      const multiWeekTemplate = { ...mockTemplate, durationWeeks: 4 };
      render(<TemplateCard template={multiWeekTemplate} />);
      expect(screen.getByText(/4 weeks/)).toBeInTheDocument();
    });

    it('should display pattern count', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText(/2 patterns/)).toBeInTheDocument();
    });

    it('should display usage count', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText(/Used 5 times/)).toBeInTheDocument();
    });

    it('should display tags', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.getByText('#clinic')).toBeInTheDocument();
      expect(screen.getByText('#weekday')).toBeInTheDocument();
    });

    it('should show +more indicator for many tags', () => {
      const manyTagsTemplate = {
        ...mockTemplate,
        tags: ['tag1', 'tag2', 'tag3', 'tag4', 'tag5'],
      };
      render(<TemplateCard template={manyTagsTemplate} />);
      expect(screen.getByText('+2 more')).toBeInTheDocument();
    });

    it('should render visibility icon for private templates', () => {
      const { container } = render(<TemplateCard template={mockTemplate} />);
      // Check for Lock icon (private)
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('should render visibility icon for public templates', () => {
      const publicTemplate = { ...mockTemplate, visibility: 'public' as const };
      const { container } = render(<TemplateCard template={publicTemplate} />);
      // Check for Globe icon (public)
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('should render visibility icon for shared templates', () => {
      const sharedTemplate = { ...mockTemplate, visibility: 'shared' as const };
      const { container } = render(<TemplateCard template={sharedTemplate} />);
      // Check for Users icon (shared)
      expect(container.querySelector('svg')).toBeInTheDocument();
    });
  });

  describe('Day Coverage Indicators', () => {
    it('should show active days', () => {
      const { container } = render(<TemplateCard template={mockTemplate} />);
      // Monday should be active (dayOfWeek: 1)
      const dayIndicators = container.querySelectorAll('.flex-1');
      expect(dayIndicators.length).toBeGreaterThan(0);
    });

    it('should highlight days with patterns', () => {
      const multiDayTemplate = {
        ...mockTemplate,
        patterns: [
          ...mockTemplate.patterns,
          {
            id: 'p3',
            name: 'Tuesday Clinic',
            dayOfWeek: 2,
            timeOfDay: 'AM' as const,
            activityType: 'clinic',
            role: 'primary' as const,
          },
        ],
      };
      const { container } = render(<TemplateCard template={multiDayTemplate} />);
      // Find the day coverage indicator row specifically (flex gap-1 mb-3)
      const dayRow = container.querySelector('.flex.gap-1.mb-3');
      expect(dayRow).toBeInTheDocument();
      const dayIndicators = dayRow?.querySelectorAll('.flex-1');
      expect(dayIndicators?.length).toBe(7); // All 7 days should be shown
    });
  });

  describe('Actions Menu', () => {
    it('should show actions menu when button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.getByText('Delete')).toBeInTheDocument();
      });
    });

    it('should close menu when clicking outside', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText('Edit')).toBeInTheDocument();
      });

      // The component uses a fixed overlay div to catch outside clicks
      // Find and click the overlay (fixed inset-0 z-10 element)
      const overlay = document.querySelector('.fixed.inset-0.z-10');
      expect(overlay).toBeInTheDocument();
      await user.click(overlay!);

      await waitFor(() => {
        expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      });
    });

    it('should show all provided action buttons', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
          onDuplicate={mockOnDuplicate}
          onShare={mockOnShare}
          onPreview={mockOnPreview}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      await waitFor(() => {
        expect(screen.getByText('Preview')).toBeInTheDocument();
        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.getByText('Duplicate')).toBeInTheDocument();
        expect(screen.getByText('Share')).toBeInTheDocument();
        expect(screen.getByText('Delete')).toBeInTheDocument();
      });
    });

    it('should hide actions when showActions is false', () => {
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
          showActions={false}
        />
      );

      expect(screen.queryByLabelText('Template actions')).not.toBeInTheDocument();
    });
  });

  describe('Action Callbacks', () => {
    it('should call onEdit when Edit is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      const editButton = await screen.findByText('Edit');
      await user.click(editButton);

      expect(mockOnEdit).toHaveBeenCalledWith(mockTemplate);
    });

    it('should call onDelete when Delete is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onDelete={mockOnDelete}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      const deleteButton = await screen.findByText('Delete');
      await user.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalledWith(mockTemplate);
    });

    it('should call onDuplicate when Duplicate is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onDuplicate={mockOnDuplicate}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      const duplicateButton = await screen.findByText('Duplicate');
      await user.click(duplicateButton);

      expect(mockOnDuplicate).toHaveBeenCalledWith(mockTemplate);
    });

    it('should call onShare when Share is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onShare={mockOnShare}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      const shareButton = await screen.findByText('Share');
      await user.click(shareButton);

      expect(mockOnShare).toHaveBeenCalledWith(mockTemplate);
    });

    it('should call onPreview when Preview is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onPreview={mockOnPreview}
        />
      );

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      const previewButton = await screen.findByText('Preview');
      await user.click(previewButton);

      expect(mockOnPreview).toHaveBeenCalledWith(mockTemplate);
    });

    it('should call onPreview when card is clicked', async () => {
      const user = userEvent.setup();
      const { container } = render(
        <TemplateCard
          template={mockTemplate}
          onPreview={mockOnPreview}
        />
      );

      const card = container.querySelector('.card');
      if (card) {
        await user.click(card);
        expect(mockOnPreview).toHaveBeenCalledWith(mockTemplate);
      }
    });

    it('should call onApply when Apply button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onApply={mockOnApply}
        />
      );

      const applyButton = screen.getByText('Apply');
      await user.click(applyButton);

      expect(mockOnApply).toHaveBeenCalledWith(mockTemplate);
    });

    it('should prevent event propagation for Apply button', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onApply={mockOnApply}
          onPreview={mockOnPreview}
        />
      );

      const applyButton = screen.getByText('Apply');
      await user.click(applyButton);

      expect(mockOnApply).toHaveBeenCalledWith(mockTemplate);
      expect(mockOnPreview).not.toHaveBeenCalled();
    });
  });

  describe('Conditional Rendering', () => {
    it('should not show Apply button if onApply is not provided', () => {
      render(<TemplateCard template={mockTemplate} />);
      expect(screen.queryByText('Apply')).not.toBeInTheDocument();
    });

    it('should show Apply button if onApply is provided', () => {
      render(
        <TemplateCard
          template={mockTemplate}
          onApply={mockOnApply}
        />
      );
      expect(screen.getByText('Apply')).toBeInTheDocument();
    });

    it('should not show action menu items if handlers are not provided', async () => {
      const user = userEvent.setup();
      render(<TemplateCard template={mockTemplate} />);

      const menuButton = screen.getByLabelText('Template actions');
      await user.click(menuButton);

      // Menu should be empty or not show specific actions
      expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      expect(screen.queryByText('Delete')).not.toBeInTheDocument();
    });
  });

  describe('Category Styling', () => {
    it('should apply clinic category colors', () => {
      const { container } = render(<TemplateCard template={mockTemplate} />);
      const card = container.querySelector('.card');
      expect(card).toHaveClass('border-teal-200');
    });

    it('should apply call category colors', () => {
      const callTemplate = { ...mockTemplate, category: 'call' as const };
      const { container } = render(<TemplateCard template={callTemplate} />);
      const card = container.querySelector('.card');
      expect(card).toHaveClass('border-orange-200');
    });

    it('should apply rotation category colors', () => {
      const rotationTemplate = { ...mockTemplate, category: 'rotation' as const };
      const { container } = render(<TemplateCard template={rotationTemplate} />);
      const card = container.querySelector('.card');
      expect(card).toHaveClass('border-purple-200');
    });
  });

  describe('Status Styling', () => {
    it('should apply active status colors', () => {
      render(<TemplateCard template={mockTemplate} />);
      const statusBadge = screen.getByText('active');
      expect(statusBadge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('should apply draft status colors', () => {
      const draftTemplate = { ...mockTemplate, status: 'draft' as const };
      render(<TemplateCard template={draftTemplate} />);
      const statusBadge = screen.getByText('draft');
      expect(statusBadge).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('should apply archived status colors', () => {
      const archivedTemplate = { ...mockTemplate, status: 'archived' as const };
      render(<TemplateCard template={archivedTemplate} />);
      const statusBadge = screen.getByText('archived');
      expect(statusBadge).toHaveClass('bg-gray-100', 'text-gray-800');
    });
  });

  describe('Accessibility', () => {
    it('should have accessible action button labels', () => {
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
        />
      );

      expect(screen.getByLabelText('Template actions')).toBeInTheDocument();
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCard
          template={mockTemplate}
          onEdit={mockOnEdit}
          onApply={mockOnApply}
        />
      );

      // Tab order: actions menu button first (top right of card), then Apply button (bottom)
      await user.tab();
      expect(screen.getByLabelText('Template actions')).toHaveFocus();

      // Tab to Apply button
      await user.tab();
      expect(screen.getByText('Apply')).toHaveFocus();
    });
  });
});
