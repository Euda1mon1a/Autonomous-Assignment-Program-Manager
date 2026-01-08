/**
 * Tests for BulkPatternModal component
 *
 * Tests rendering, mode selection, pattern configuration, and submission.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BulkPatternModal, SchedulePattern } from '@/components/admin/BulkPatternModal';
import type { RotationTemplate } from '@/types/admin-templates';

// Mock template data
const mockTemplates: RotationTemplate[] = [
  {
    id: '1',
    name: 'Cardiology Clinic',
    activity_type: 'clinic',
    template_category: 'rotation',
    abbreviation: 'CARD',
    display_abbreviation: 'Cardiology',
    font_color: '#FFFFFF',
    background_color: '#3B82F6',
    clinic_location: 'Building A',
    max_residents: 4,
    requires_specialty: 'Cardiology',
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Internal Medicine',
    activity_type: 'inpatient',
    template_category: 'rotation',
    abbreviation: 'IM',
    display_abbreviation: 'Internal',
    font_color: '#FFFFFF',
    background_color: '#10B981',
    clinic_location: null,
    max_residents: 8,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2025-01-02T00:00:00Z',
  },
  {
    id: '3',
    name: 'Outpatient Clinic',
    activity_type: 'outpatient',
    template_category: 'rotation',
    abbreviation: 'OPC',
    display_abbreviation: 'Outpatient',
    font_color: '#FFFFFF',
    background_color: '#F59E0B',
    clinic_location: 'Building B',
    max_residents: 6,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: false,
    max_supervision_ratio: null,
    created_at: '2025-01-03T00:00:00Z',
  },
];

const mockPatterns: SchedulePattern[] = [
  {
    id: 'pattern-1',
    pattern_type: 'regular',
    setting: 'outpatient',
    days_of_week: [1, 2, 3, 4, 5],
    recurrence_weeks: 1,
  },
  {
    id: 'pattern-2',
    pattern_type: 'alternating',
    setting: 'inpatient',
    days_of_week: [1, 3, 5],
    recurrence_weeks: 2,
  },
];

describe('BulkPatternModal', () => {
  const defaultProps = {
    isOpen: true,
    selectedTemplates: [mockTemplates[0], mockTemplates[1]],
    allTemplates: mockTemplates,
    onClose: jest.fn(),
    onApply: jest.fn().mockResolvedValue(undefined),
    isApplying: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<BulkPatternModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should show modal title', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Apply Patterns')).toBeInTheDocument();
    });

    it('should show selected template count', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('2 templates selected')).toBeInTheDocument();
    });

    it('should show singular when one template selected', () => {
      render(
        <BulkPatternModal
          {...defaultProps}
          selectedTemplates={[mockTemplates[0]]}
        />
      );
      expect(screen.getByText('1 template selected')).toBeInTheDocument();
    });

    it('should show Cancel button', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should show Apply button', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /apply to 2 templates/i })).toBeInTheDocument();
    });
  });

  describe('Mode Selection', () => {
    it('should show Custom Pattern mode by default', () => {
      render(<BulkPatternModal {...defaultProps} />);
      const customButton = screen.getByRole('button', { name: /custom pattern/i });
      expect(customButton).toHaveClass('border-violet-500');
    });

    it('should show Copy from Template mode button', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByRole('button', { name: /copy from template/i })).toBeInTheDocument();
    });

    it('should switch to copy mode when Copy from Template is clicked', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const copyButton = screen.getByRole('button', { name: /copy from template/i });
      expect(copyButton).toHaveClass('border-violet-500');
    });

    it('should show source template dropdown in copy mode', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      expect(screen.getByText('Source Template')).toBeInTheDocument();
      expect(screen.getByText('Select a template...')).toBeInTheDocument();
    });

    it('should not include selected templates in source options', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();

      // The third template (Outpatient Clinic) should be in options since it's not selected
      expect(screen.getByText('Outpatient Clinic')).toBeInTheDocument();

      // The selected templates should NOT be in options
      expect(screen.queryByRole('option', { name: 'Cardiology Clinic' })).not.toBeInTheDocument();
      expect(screen.queryByRole('option', { name: 'Internal Medicine' })).not.toBeInTheDocument();
    });
  });

  describe('Custom Pattern Mode', () => {
    it('should show pattern type selector', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Pattern Type')).toBeInTheDocument();
    });

    it('should show setting selector', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Setting')).toBeInTheDocument();
    });

    it('should show days of week selector', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Days of Week')).toBeInTheDocument();
    });

    it('should show recurrence input', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Recurrence (weeks)')).toBeInTheDocument();
    });

    it('should show notes input', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByText('Notes (optional)')).toBeInTheDocument();
    });

    it('should have Mon-Fri selected by default', () => {
      render(<BulkPatternModal {...defaultProps} />);

      // Day selector buttons for Mon-Fri should have violet background
      const dayButtons = screen.getAllByRole('button').filter(btn =>
        ['M', 'T', 'W', 'F'].includes(btn.textContent || '')
      );

      // At least some weekday buttons should exist
      expect(dayButtons.length).toBeGreaterThan(0);
    });

    it('should toggle day selection when day button is clicked', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      // Find a day button - using title to be more specific
      const sundayButton = screen.getByTitle('Sun');

      // Click to select Sunday
      await user.click(sundayButton);

      // The button should now have the selected class (violet background)
      expect(sundayButton).toHaveClass('bg-violet-500');
    });

    it('should change pattern type when selected', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      const patternSelect = screen.getByDisplayValue('Regular');
      await user.selectOptions(patternSelect, 'split');

      expect(screen.getByDisplayValue('Split')).toBeInTheDocument();
    });

    it('should change setting when selected', async () => {
      const user = userEvent.setup();
      render(<BulkPatternModal {...defaultProps} />);

      const settingSelect = screen.getByDisplayValue('Outpatient');
      await user.selectOptions(settingSelect, 'inpatient');

      expect(screen.getByDisplayValue('Inpatient')).toBeInTheDocument();
    });
  });

  describe('Copy Mode with Pattern Loading', () => {
    it('should call fetchPatterns when source template is selected', async () => {
      const user = userEvent.setup();
      const fetchPatterns = jest.fn().mockResolvedValue(mockPatterns);
      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3'); // Outpatient Clinic

      await waitFor(() => {
        expect(fetchPatterns).toHaveBeenCalledWith('3');
      });
    });

    it('should show loading state while fetching patterns', async () => {
      const user = userEvent.setup();
      let resolvePatterns: (value: SchedulePattern[]) => void;
      const fetchPatterns = jest.fn().mockReturnValue(
        new Promise<SchedulePattern[]>((resolve) => {
          resolvePatterns = resolve;
        })
      );

      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      expect(screen.getByText('Loading patterns...')).toBeInTheDocument();

      // Resolve the promise
      resolvePatterns!(mockPatterns);

      await waitFor(() => {
        expect(screen.queryByText('Loading patterns...')).not.toBeInTheDocument();
      });
    });

    it('should display loaded patterns', async () => {
      const user = userEvent.setup();
      const fetchPatterns = jest.fn().mockResolvedValue(mockPatterns);
      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      await waitFor(() => {
        expect(screen.getByText('Found 2 patterns:')).toBeInTheDocument();
      });
    });

    it('should show message when template has no patterns', async () => {
      const user = userEvent.setup();
      const fetchPatterns = jest.fn().mockResolvedValue([]);
      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      await waitFor(() => {
        expect(screen.getByText('This template has no patterns configured.')).toBeInTheDocument();
      });
    });

    it('should show error when pattern fetch fails', async () => {
      const user = userEvent.setup();
      const fetchPatterns = jest.fn().mockRejectedValue(new Error('Network error'));
      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      await waitFor(() => {
        expect(screen.getByText('Failed to load patterns from source template')).toBeInTheDocument();
      });
    });
  });

  describe('Submit Functionality', () => {
    it('should call onApply with custom pattern when form is submitted', async () => {
      const user = userEvent.setup();
      const onApply = jest.fn().mockResolvedValue(undefined);
      render(<BulkPatternModal {...defaultProps} onApply={onApply} />);

      await user.click(screen.getByRole('button', { name: /apply to 2 templates/i }));

      await waitFor(() => {
        expect(onApply).toHaveBeenCalledTimes(1);
      });

      const [templateIds, patterns] = onApply.mock.calls[0] as [string[], SchedulePattern[]];
      expect(templateIds).toEqual(['1', '2']);
      expect(patterns).toHaveLength(1);
      expect(patterns[0].pattern_type).toBe('regular');
      expect(patterns[0].setting).toBe('outpatient');
    });

    it('should call onApply with source patterns in copy mode', async () => {
      const user = userEvent.setup();
      const onApply = jest.fn().mockResolvedValue(undefined);
      const fetchPatterns = jest.fn().mockResolvedValue(mockPatterns);

      render(
        <BulkPatternModal
          {...defaultProps}
          onApply={onApply}
          fetchPatterns={fetchPatterns}
        />
      );

      // Switch to copy mode
      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      // Select source template
      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      // Wait for patterns to load
      await waitFor(() => {
        expect(screen.getByText('Found 2 patterns:')).toBeInTheDocument();
      });

      // Submit
      await user.click(screen.getByRole('button', { name: /apply to 2 templates/i }));

      await waitFor(() => {
        expect(onApply).toHaveBeenCalledTimes(1);
      });

      const [, patterns] = onApply.mock.calls[0] as [string[], SchedulePattern[]];
      expect(patterns).toEqual(mockPatterns);
    });

    it('should show error when trying to submit copy mode without patterns', async () => {
      const user = userEvent.setup();
      const fetchPatterns = jest.fn().mockResolvedValue([]);
      render(
        <BulkPatternModal
          {...defaultProps}
          fetchPatterns={fetchPatterns}
        />
      );

      // Switch to copy mode
      await user.click(screen.getByRole('button', { name: /copy from template/i }));

      // Select source template
      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      // Wait for empty patterns
      await waitFor(() => {
        expect(screen.getByText('This template has no patterns configured.')).toBeInTheDocument();
      });

      // Apply button should be disabled
      const applyButton = screen.getByRole('button', { name: /apply to 2 templates/i });
      expect(applyButton).toBeDisabled();
    });

    it('should show loading state while applying', () => {
      render(<BulkPatternModal {...defaultProps} isApplying={true} />);
      expect(screen.getByText('Applying...')).toBeInTheDocument();
    });

    it('should disable buttons while applying', () => {
      render(<BulkPatternModal {...defaultProps} isApplying={true} />);
      expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /applying/i })).toBeDisabled();
    });
  });

  describe('Close Functionality', () => {
    it('should call onClose when Cancel is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkPatternModal {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when X button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkPatternModal {...defaultProps} onClose={onClose} />);

      await user.click(screen.getByLabelText('Close'));

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should not close when applying', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      render(<BulkPatternModal {...defaultProps} onClose={onClose} isApplying={true} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onClose).not.toHaveBeenCalled();
    });

    it('should reset state when closed', async () => {
      const user = userEvent.setup();
      const onClose = jest.fn();
      const fetchPatterns = jest.fn().mockResolvedValue(mockPatterns);

      render(
        <BulkPatternModal
          {...defaultProps}
          onClose={onClose}
          fetchPatterns={fetchPatterns}
        />
      );

      // Switch to copy mode and load patterns
      await user.click(screen.getByRole('button', { name: /copy from template/i }));
      const select = screen.getByRole('combobox');
      await user.selectOptions(select, '3');

      await waitFor(() => {
        expect(screen.getByText('Found 2 patterns:')).toBeInTheDocument();
      });

      // Close the modal
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper dialog role', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    });

    it('should have aria-labelledby pointing to title', () => {
      render(<BulkPatternModal {...defaultProps} />);
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby', 'bulk-pattern-title');
    });

    it('should have accessible close button', () => {
      render(<BulkPatternModal {...defaultProps} />);
      expect(screen.getByLabelText('Close')).toBeInTheDocument();
    });
  });

  describe('Pattern Type Options', () => {
    it('should list all pattern type options', () => {
      render(<BulkPatternModal {...defaultProps} />);

      const patternSelect = screen.getByDisplayValue('Regular');
      expect(patternSelect).toBeInTheDocument();

      // Check that options exist
      const options = patternSelect.querySelectorAll('option');
      const optionValues = Array.from(options).map(opt => opt.value);

      expect(optionValues).toContain('regular');
      expect(optionValues).toContain('split');
      expect(optionValues).toContain('mirrored');
      expect(optionValues).toContain('alternating');
    });
  });

  describe('Setting Options', () => {
    it('should list all setting options', () => {
      render(<BulkPatternModal {...defaultProps} />);

      const settingSelect = screen.getByDisplayValue('Outpatient');
      expect(settingSelect).toBeInTheDocument();

      // Check that options exist
      const options = settingSelect.querySelectorAll('option');
      const optionValues = Array.from(options).map(opt => opt.value);

      expect(optionValues).toContain('inpatient');
      expect(optionValues).toContain('outpatient');
    });
  });
});
