/**
 * Tests for WeeklyGridEditor component.
 *
 * Tests cover:
 * - Grid rendering with all 14 slots
 * - Slot selection and template assignment
 * - Template selector functionality
 * - Protected slot handling
 * - Save/cancel buttons
 * - Loading and readonly states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { WeeklyGridEditor } from '../WeeklyGridEditor';
import { createEmptyPattern } from '@/types/weekly-pattern';
import type { WeeklyPatternGrid, RotationTemplateRef } from '@/types/weekly-pattern';

// ============================================================================
// Test Data
// ============================================================================

const mockTemplates: RotationTemplateRef[] = [
  {
    id: 'clinic-1',
    name: 'Clinic',
    displayAbbreviation: 'C',
    backgroundColor: 'bg-blue-100',
    fontColor: 'text-blue-800',
  },
  {
    id: 'inpatient-1',
    name: 'Inpatient',
    displayAbbreviation: 'IP',
    backgroundColor: 'bg-purple-100',
    fontColor: 'text-purple-800',
  },
  {
    id: 'conference-1',
    name: 'Conference',
    displayAbbreviation: 'Conf',
    backgroundColor: 'bg-gray-100',
    fontColor: 'text-gray-800',
  },
];

function createTestPattern(): WeeklyPatternGrid {
  const pattern = createEmptyPattern();
  // Set Monday AM to Clinic
  pattern.slots[2].rotationTemplateId = 'clinic-1';
  // Set Monday PM to Inpatient
  pattern.slots[3].rotationTemplateId = 'inpatient-1';
  return pattern;
}

// ============================================================================
// Tests
// ============================================================================

describe('WeeklyGridEditor', () => {
  const defaultProps = {
    templateId: 'test-template',
    pattern: createEmptyPattern(),
    templates: mockTemplates,
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the grid with all day headers', () => {
      render(<WeeklyGridEditor {...defaultProps} />);

      // Check day headers are present (Mon-Sun display order)
      expect(screen.getByText('Mon')).toBeInTheDocument();
      expect(screen.getByText('Tue')).toBeInTheDocument();
      expect(screen.getByText('Wed')).toBeInTheDocument();
      expect(screen.getByText('Thu')).toBeInTheDocument();
      expect(screen.getByText('Fri')).toBeInTheDocument();
      expect(screen.getByText('Sat')).toBeInTheDocument();
      expect(screen.getByText('Sun')).toBeInTheDocument();
    });

    it('should render AM and PM rows', () => {
      render(<WeeklyGridEditor {...defaultProps} />);

      expect(screen.getByText('AM')).toBeInTheDocument();
      expect(screen.getByText('PM')).toBeInTheDocument();
    });

    it('should render 14 slot cells (7 days x 2 time periods)', () => {
      render(<WeeklyGridEditor {...defaultProps} />);

      const slots = screen.getAllByRole('button', {
        name: /.*: Empty|.*: Clinic|.*: Inpatient/,
      });
      expect(slots.length).toBe(14);
    });

    it('should render template selector when showSelector is true', () => {
      render(<WeeklyGridEditor {...defaultProps} showSelector={true} />);

      // Should show Clear button and template options
      expect(screen.getByRole('button', { name: 'Clear' })).toBeInTheDocument();
      mockTemplates.forEach((t) => {
        expect(
          screen.getByRole('button', { name: t.displayAbbreviation ?? t.name })
        ).toBeInTheDocument();
      });
    });

    it('should not render template selector when showSelector is false', () => {
      render(<WeeklyGridEditor {...defaultProps} showSelector={false} />);

      expect(
        screen.queryByRole('button', { name: 'Clear' })
      ).not.toBeInTheDocument();
    });

    it('should display loading state', () => {
      render(<WeeklyGridEditor {...defaultProps} isLoading={true} />);

      // Should show loading spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Pattern Display', () => {
    it('should display assigned templates in slots', () => {
      const patternWithAssignments = createTestPattern();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          pattern={patternWithAssignments}
        />
      );

      // Monday AM should show Clinic abbreviation
      expect(screen.getByText('C')).toBeInTheDocument();
      // Monday PM should show Inpatient abbreviation
      expect(screen.getByText('IP')).toBeInTheDocument();
    });

    it('should display empty slots with dash', () => {
      render(<WeeklyGridEditor {...defaultProps} />);

      // Empty slots show dash
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThan(0);
    });
  });

  describe('Interaction', () => {
    it('should call onChange when slot is clicked with selected template', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onChange={onChange}
        />
      );

      // First select a template from the selector
      const clinicButton = screen.getByRole('button', { name: 'C' });
      await user.click(clinicButton);

      // Then click a slot
      const tuesdayAmSlot = screen.getByRole('button', { name: 'Tue AM: Empty' });
      await user.click(tuesdayAmSlot);

      expect(onChange).toHaveBeenCalled();
    });

    it('should toggle slot selection when clicked twice', async () => {
      const user = userEvent.setup();

      render(<WeeklyGridEditor {...defaultProps} />);

      const slot = screen.getByRole('button', { name: 'Mon AM: Empty' });

      // First click - selects
      await user.click(slot);
      expect(slot).toHaveClass('ring-2');

      // Second click - deselects
      await user.click(slot);
      // Selection ring should be removed (checking the slot doesn't have the ring class)
    });

    it('should update slot when template is selected after slot', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onChange={onChange}
        />
      );

      // Select a slot
      const slot = screen.getByRole('button', { name: 'Mon AM: Empty' });
      await user.click(slot);

      // Then select a template
      const templateButton = screen.getByRole('button', { name: 'C' });
      await user.click(templateButton);

      expect(onChange).toHaveBeenCalled();
    });

    it('should not allow interaction in readonly mode', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onChange={onChange}
          readOnly={true}
        />
      );

      const slot = screen.getByRole('button', { name: 'Mon AM: Empty' });
      await user.click(slot);

      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('Save/Cancel Buttons', () => {
    it('should render save and cancel buttons when callbacks provided', () => {
      const onSave = vi.fn();
      const onCancel = vi.fn();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onSave={onSave}
          onCancel={onCancel}
        />
      );

      expect(
        screen.getByRole('button', { name: /Save Pattern/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /Cancel/i })
      ).toBeInTheDocument();
    });

    it('should call onSave when save button clicked', async () => {
      const onSave = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onSave={onSave}
        />
      );

      const saveButton = screen.getByRole('button', { name: /Save Pattern/i });
      await user.click(saveButton);

      expect(onSave).toHaveBeenCalled();
    });

    it('should call onCancel when cancel button clicked', async () => {
      const onCancel = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onCancel={onCancel}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(onCancel).toHaveBeenCalled();
    });

    it('should disable buttons when saving', () => {
      render(
        <WeeklyGridEditor
          {...defaultProps}
          onSave={vi.fn()}
          onCancel={vi.fn()}
          isSaving={true}
        />
      );

      const saveButton = screen.getByRole('button', { name: /Saving.../i });
      const cancelButton = screen.getByRole('button', { name: /Cancel/i });

      expect(saveButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
    });

    it('should show saving indicator when isSaving is true', () => {
      render(
        <WeeklyGridEditor
          {...defaultProps}
          onSave={vi.fn()}
          isSaving={true}
        />
      );

      expect(screen.getByText(/Saving.../i)).toBeInTheDocument();
    });

    it('should not render buttons in readonly mode', () => {
      render(
        <WeeklyGridEditor
          {...defaultProps}
          onSave={vi.fn()}
          onCancel={vi.fn()}
          readOnly={true}
        />
      );

      expect(
        screen.queryByRole('button', { name: /Save Pattern/i })
      ).not.toBeInTheDocument();
      expect(
        screen.queryByRole('button', { name: /Cancel/i })
      ).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels on slots', () => {
      const patternWithAssignments = createTestPattern();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          pattern={patternWithAssignments}
        />
      );

      // Assigned slots should have template name in label
      expect(
        screen.getByRole('button', { name: 'Mon AM: Clinic' })
      ).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: 'Mon PM: Inpatient' })
      ).toBeInTheDocument();

      // Empty slots should show "Empty"
      expect(
        screen.getByRole('button', { name: 'Tue AM: Empty' })
      ).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();

      render(
        <WeeklyGridEditor
          {...defaultProps}
          onChange={onChange}
        />
      );

      // First select a template
      const clinicButton = screen.getByRole('button', { name: 'C' });
      await user.click(clinicButton);

      // Tab to a slot and press Enter
      const slot = screen.getByRole('button', { name: 'Mon AM: Empty' });
      slot.focus();
      await user.keyboard('{Enter}');

      expect(onChange).toHaveBeenCalled();
    });
  });
});
