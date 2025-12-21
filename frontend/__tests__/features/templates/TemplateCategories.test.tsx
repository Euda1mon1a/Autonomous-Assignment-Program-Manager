/**
 * Tests for TemplateCategories Component
 *
 * Tests category filtering, different variants, and user interactions.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TemplateCategories, CategoryBadge } from '@/features/templates/components/TemplateCategories';
import type { TemplateCategory } from '@/features/templates/types';

describe('TemplateCategories', () => {
  const mockOnCategorySelect = jest.fn();
  const categoryCounts = {
    schedule: 5,
    assignment: 3,
    rotation: 2,
    call: 1,
    clinic: 4,
    custom: 0,
  } as Record<TemplateCategory, number>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Pills Variant', () => {
    it('should render category pills', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText(/Schedule/)).toBeInTheDocument();
      expect(screen.getByText(/Assignment/)).toBeInTheDocument();
      expect(screen.getByText(/Clinic/)).toBeInTheDocument();
    });

    it('should show category counts', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="pills"
        />
      );

      expect(screen.getByText('(5)')).toBeInTheDocument();
      expect(screen.getByText('(3)')).toBeInTheDocument();
      expect(screen.getByText('(4)')).toBeInTheDocument();
    });

    it('should highlight selected category', () => {
      render(
        <TemplateCategories
          selectedCategory="clinic"
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const clinicButton = screen.getByText(/Clinic/).closest('button');
      expect(clinicButton).toHaveClass('bg-teal-50', 'text-teal-700');
    });

    it('should highlight All when no category selected', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const allButton = screen.getByText('All');
      expect(allButton).toHaveClass('bg-blue-600', 'text-white');
    });

    it('should call onCategorySelect when category is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const clinicButton = screen.getByText(/Clinic/);
      await user.click(clinicButton);

      expect(mockOnCategorySelect).toHaveBeenCalledWith('clinic');
    });

    it('should deselect category when clicking selected category', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          selectedCategory="clinic"
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const clinicButton = screen.getByText(/Clinic/);
      await user.click(clinicButton);

      expect(mockOnCategorySelect).toHaveBeenCalledWith(undefined);
    });

    it('should deselect all categories when clicking All', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          selectedCategory="clinic"
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const allButton = screen.getByText('All');
      await user.click(allButton);

      expect(mockOnCategorySelect).toHaveBeenCalledWith(undefined);
    });
  });

  describe('Cards Variant', () => {
    it('should render category cards', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      expect(screen.getByText('Schedule Templates')).toBeInTheDocument();
      expect(screen.getByText('Assignment Patterns')).toBeInTheDocument();
      expect(screen.getByText('Clinic Templates')).toBeInTheDocument();
    });

    it('should show category icons in cards', () => {
      const { container } = render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });

    it('should show category counts in cards', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      expect(screen.getByText('5 templates')).toBeInTheDocument();
      expect(screen.getByText('3 templates')).toBeInTheDocument();
      expect(screen.getByText('0 templates')).toBeInTheDocument();
    });

    it('should use singular template when count is 1', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      expect(screen.getByText('1 template')).toBeInTheDocument();
    });

    it('should highlight selected category card', () => {
      const { container } = render(
        <TemplateCategories
          selectedCategory="clinic"
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      const cards = container.querySelectorAll('button');
      const clinicCard = Array.from(cards).find(card =>
        card.textContent?.includes('Clinic Templates')
      );

      expect(clinicCard).toHaveClass('bg-teal-50', 'border-teal-200', 'text-teal-700');
    });

    it('should call onCategorySelect when card is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      const clinicCard = screen.getByText('Clinic Templates');
      await user.click(clinicCard);

      expect(mockOnCategorySelect).toHaveBeenCalledWith('clinic');
    });
  });

  describe('List Variant', () => {
    it('should render category list', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      expect(screen.getByText('All Templates')).toBeInTheDocument();
      expect(screen.getByText('Schedule Templates')).toBeInTheDocument();
      expect(screen.getByText('Assignment Patterns')).toBeInTheDocument();
    });

    it('should show total count for All Templates', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      // Total: 5 + 3 + 2 + 1 + 4 + 0 = 15
      expect(screen.getByText('15')).toBeInTheDocument();
    });

    it('should show individual category counts', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      const counts = screen.getAllByText('5');
      expect(counts.length).toBeGreaterThan(0);
    });

    it('should highlight selected category in list', () => {
      render(
        <TemplateCategories
          selectedCategory="clinic"
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      const clinicButton = screen.getByText('Clinic Templates').closest('button');
      expect(clinicButton).toHaveClass('bg-teal-50', 'text-teal-700');
    });

    it('should highlight All Templates when no selection', () => {
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      const allButton = screen.getByText('All Templates').closest('button');
      expect(allButton).toHaveClass('bg-blue-50', 'text-blue-700');
    });

    it('should call onCategorySelect when list item is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      const scheduleButton = screen.getByText('Schedule Templates');
      await user.click(scheduleButton);

      expect(mockOnCategorySelect).toHaveBeenCalledWith('schedule');
    });
  });

  describe('Accessibility', () => {
    it('should be keyboard navigable in pills variant', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          variant="pills"
        />
      );

      const allButton = screen.getByText('All');
      allButton.focus();

      await user.keyboard('{Tab}');
      const scheduleButton = screen.getByText(/Schedule/);
      expect(scheduleButton).toHaveFocus();
    });

    it('should be keyboard navigable in cards variant', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="cards"
        />
      );

      await user.tab();
      const firstCard = screen.getByText('Schedule Templates').closest('button');
      expect(firstCard).toHaveFocus();
    });

    it('should be keyboard navigable in list variant', async () => {
      const user = userEvent.setup();
      render(
        <TemplateCategories
          onCategorySelect={mockOnCategorySelect}
          categoryCounts={categoryCounts}
          variant="list"
        />
      );

      await user.tab();
      const allButton = screen.getByText('All Templates').closest('button');
      expect(allButton).toHaveFocus();
    });
  });
});

describe('CategoryBadge', () => {
  it('should render category name', () => {
    render(<CategoryBadge category="clinic" />);
    expect(screen.getByText('Clinic Templates')).toBeInTheDocument();
  });

  it('should apply category colors', () => {
    const { container } = render(<CategoryBadge category="clinic" />);
    const badge = container.querySelector('.bg-teal-50');
    expect(badge).toBeInTheDocument();
  });

  it('should render with small size', () => {
    const { container } = render(<CategoryBadge category="clinic" size="sm" />);
    const badge = container.querySelector('.text-xs');
    expect(badge).toBeInTheDocument();
  });

  it('should render with medium size', () => {
    const { container } = render(<CategoryBadge category="clinic" size="md" />);
    const badge = container.querySelector('.text-sm');
    expect(badge).toBeInTheDocument();
  });

  it('should render with large size', () => {
    const { container } = render(<CategoryBadge category="clinic" size="lg" />);
    const badge = container.querySelector('.text-base');
    expect(badge).toBeInTheDocument();
  });

  it('should render category icon', () => {
    const { container } = render(<CategoryBadge category="clinic" />);
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it('should handle all category types', () => {
    const categories: TemplateCategory[] = ['schedule', 'assignment', 'rotation', 'call', 'clinic', 'custom'];

    categories.forEach(category => {
      const { unmount } = render(<CategoryBadge category={category} />);
      const badge = screen.getByText(/Templates|Patterns|Schedules/);
      expect(badge).toBeInTheDocument();
      unmount();
    });
  });
});
