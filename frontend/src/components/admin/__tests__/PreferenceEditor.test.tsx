/**
 * PreferenceEditor Component Tests
 *
 * Tests for the preference editor including:
 * - Rendering preferences
 * - Adding/removing preferences
 * - Weight changes
 * - Save handling
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PreferenceEditor } from '../PreferenceEditor';
import type { RotationPreference } from '@/types/admin-templates';

// ============================================================================
// Mock Data
// ============================================================================

const mockPreferences: RotationPreference[] = [
  {
    id: '1',
    rotation_template_id: 'template-1',
    preference_type: 'full_day_grouping',
    weight: 'medium',
    config_json: {},
    is_active: true,
    description: 'Group AM and PM together',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    rotation_template_id: 'template-1',
    preference_type: 'avoid_friday_pm',
    weight: 'high',
    config_json: {},
    is_active: true,
    description: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

// ============================================================================
// Tests
// ============================================================================

describe('PreferenceEditor', () => {
  const defaultProps = {
    templateId: 'template-1',
    templateName: 'FM Clinic',
    preferences: mockPreferences,
    onSave: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all preferences', () => {
      render(<PreferenceEditor {...defaultProps} />);

      expect(screen.getByText('Full Day Grouping')).toBeInTheDocument();
      expect(screen.getByText('Avoid Friday PM')).toBeInTheDocument();
    });

    it('displays template name', () => {
      render(<PreferenceEditor {...defaultProps} />);

      expect(screen.getByText('FM Clinic')).toBeInTheDocument();
    });

    it('shows empty state when no preferences', () => {
      render(<PreferenceEditor {...defaultProps} preferences={[]} />);

      expect(screen.getByText('No preferences configured yet')).toBeInTheDocument();
    });

    it('shows loading state', () => {
      render(<PreferenceEditor {...defaultProps} isLoading={true} />);

      // Check for spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Weight Display', () => {
    it('shows weight badges for each preference', () => {
      render(<PreferenceEditor {...defaultProps} />);

      expect(screen.getByText('medium')).toBeInTheDocument();
      expect(screen.getByText('high')).toBeInTheDocument();
    });
  });

  describe('Expand/Collapse', () => {
    it('expands preference card when clicked', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Find and click the first preference header
      const preferenceHeader = screen.getByText('Full Day Grouping').closest('div');
      fireEvent.click(preferenceHeader!);

      // Should show weight selector when expanded
      expect(screen.getByText('Weight')).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByText('Required')).toBeInTheDocument();
    });
  });

  describe('Adding Preferences', () => {
    it('shows available preference types to add', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Should show types not already added
      expect(screen.getByText('Consecutive Specialty')).toBeInTheDocument();
      expect(screen.getByText('Avoid Isolated Sessions')).toBeInTheDocument();
      expect(screen.getByText('Preferred Days')).toBeInTheDocument();
      expect(screen.getByText('Balance Weekly')).toBeInTheDocument();
    });

    it('adds new preference when type clicked', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Click to add a new preference
      const addButton = screen.getByText('Consecutive Specialty').closest('button');
      fireEvent.click(addButton!);

      // Should now show the unsaved changes warning since we added something
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  describe('Removing Preferences', () => {
    it('shows unsaved changes when delete clicked', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Find delete buttons and click the first one
      const deleteButtons = screen.getAllByTitle('Delete preference');
      fireEvent.click(deleteButtons[0]);

      // Should show unsaved changes warning (preference was removed)
      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });
  });

  describe('Saving', () => {
    it('disables save button when no changes', () => {
      render(<PreferenceEditor {...defaultProps} />);

      const saveButton = screen.getByText('Save Preferences').closest('button');
      expect(saveButton).toBeDisabled();
    });

    it('enables save button after changes', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Make a change - add a preference
      fireEvent.click(screen.getByText('Consecutive Specialty'));

      const saveButton = screen.getByText('Save Preferences').closest('button');
      expect(saveButton).not.toBeDisabled();
    });

    it('calls onSave with updated preferences', () => {
      const onSave = jest.fn();
      render(<PreferenceEditor {...defaultProps} onSave={onSave} />);

      // Add a preference to enable save
      fireEvent.click(screen.getByText('Consecutive Specialty'));

      // Click save
      fireEvent.click(screen.getByText('Save Preferences'));

      expect(onSave).toHaveBeenCalled();
      const savedPrefs = onSave.mock.calls[0][0];
      expect(savedPrefs.length).toBe(3); // 2 original + 1 new
    });

    it('shows unsaved changes warning', () => {
      render(<PreferenceEditor {...defaultProps} />);

      // Make a change
      fireEvent.click(screen.getByText('Consecutive Specialty'));

      expect(screen.getByText('You have unsaved changes')).toBeInTheDocument();
    });

    it('shows saving indicator when isSaving', () => {
      render(<PreferenceEditor {...defaultProps} isSaving={true} />);

      const saveButton = screen.getByText('Save Preferences').closest('button');
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Close Handler', () => {
    it('calls onClose when cancel clicked', () => {
      const onClose = jest.fn();
      render(<PreferenceEditor {...defaultProps} onClose={onClose} />);

      fireEvent.click(screen.getByText('Cancel'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Active Toggle', () => {
    it('shows inactive badge for inactive preferences', () => {
      const inactivePreference: RotationPreference = {
        ...mockPreferences[0],
        is_active: false,
      };
      render(
        <PreferenceEditor
          {...defaultProps}
          preferences={[inactivePreference]}
        />
      );

      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });
});
