/**
 * TemplateTable Component Tests
 *
 * Tests for the rotation template table including:
 * - Rendering templates
 * - Row selection
 * - Sorting
 * - Action handlers
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { TemplateTable } from '../TemplateTable';
import type { RotationTemplate, SortField, SortDirection } from '@/types/admin-templates';

// ============================================================================
// Mock Data
// ============================================================================

const mockTemplates: RotationTemplate[] = [
  {
    id: '1',
    name: 'FM Clinic',
    activity_type: 'clinic',
    abbreviation: 'FMC',
    display_abbreviation: 'FM',
    font_color: '#ffffff',
    background_color: '#10b981',
    clinic_location: 'Main Building',
    max_residents: 4,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Inpatient Ward',
    activity_type: 'inpatient',
    abbreviation: 'IP',
    display_abbreviation: 'IP',
    font_color: '#ffffff',
    background_color: '#3b82f6',
    clinic_location: null,
    max_residents: 6,
    requires_specialty: null,
    requires_procedure_credential: false,
    supervision_required: true,
    max_supervision_ratio: 4,
    created_at: '2024-01-15T00:00:00Z',
  },
  {
    id: '3',
    name: 'Procedure Lab',
    activity_type: 'procedure',
    abbreviation: 'PL',
    display_abbreviation: 'PL',
    font_color: '#ffffff',
    background_color: '#a855f7',
    clinic_location: 'Procedure Wing',
    max_residents: 2,
    requires_specialty: 'procedural',
    requires_procedure_credential: true,
    supervision_required: true,
    max_supervision_ratio: 2,
    created_at: '2024-02-01T00:00:00Z',
  },
];

const defaultSort: { field: SortField; direction: SortDirection } = {
  field: 'name',
  direction: 'asc',
};

// ============================================================================
// Tests
// ============================================================================

describe('TemplateTable', () => {
  const defaultProps = {
    templates: mockTemplates,
    selectedIds: [] as string[],
    onSelectionChange: jest.fn(),
    sort: defaultSort,
    onSortChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders all templates', () => {
      render(<TemplateTable {...defaultProps} />);

      expect(screen.getByText('FM Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient Ward')).toBeInTheDocument();
      expect(screen.getByText('Procedure Lab')).toBeInTheDocument();
    });

    it('displays activity type badges', () => {
      render(<TemplateTable {...defaultProps} />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('Procedure')).toBeInTheDocument();
    });

    it('shows empty state when no templates', () => {
      render(<TemplateTable {...defaultProps} templates={[]} />);

      expect(screen.getByText('No templates found')).toBeInTheDocument();
    });

    it('shows loading skeleton when isLoading is true', () => {
      const { container } = render(<TemplateTable {...defaultProps} isLoading={true} />);

      // Check for animate-pulse class which indicates loading state
      const skeleton = container.querySelector('.animate-pulse');
      expect(skeleton).toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('selects all rows when header checkbox clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onSelectionChange={onSelectionChange}
        />
      );

      const selectAllCheckbox = screen.getByLabelText('Select all');
      fireEvent.click(selectAllCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['1', '2', '3']);
    });

    it('deselects all when all are selected and header clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          selectedIds={['1', '2', '3']}
          onSelectionChange={onSelectionChange}
        />
      );

      const selectAllCheckbox = screen.getByLabelText('Deselect all');
      fireEvent.click(selectAllCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith([]);
    });

    it('selects individual row when row checkbox clicked', () => {
      const onSelectionChange = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onSelectionChange={onSelectionChange}
        />
      );

      const rowCheckbox = screen.getByLabelText('Select FM Clinic');
      fireEvent.click(rowCheckbox);

      expect(onSelectionChange).toHaveBeenCalledWith(['1']);
    });

    it('shows selection count when rows selected', () => {
      render(
        <TemplateTable
          {...defaultProps}
          selectedIds={['1', '2']}
        />
      );

      expect(screen.getByText('2 templates selected')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('calls onSortChange when name header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onSortChange={onSortChange}
        />
      );

      const nameHeader = screen.getByRole('button', { name: /Name/i });
      fireEvent.click(nameHeader);

      expect(onSortChange).toHaveBeenCalledWith('name');
    });

    it('calls onSortChange when activity type header clicked', () => {
      const onSortChange = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onSortChange={onSortChange}
        />
      );

      const activityHeader = screen.getByRole('button', { name: /Activity Type/i });
      fireEvent.click(activityHeader);

      expect(onSortChange).toHaveBeenCalledWith('activity_type');
    });
  });

  describe('Actions', () => {
    it('calls onEditPatterns when pattern button clicked', () => {
      const onEditPatterns = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onEditPatterns={onEditPatterns}
        />
      );

      const patternButtons = screen.getAllByTitle('Edit patterns');
      fireEvent.click(patternButtons[0]);

      expect(onEditPatterns).toHaveBeenCalledWith(mockTemplates[0]);
    });

    it('calls onEditPreferences when preferences button clicked', () => {
      const onEditPreferences = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onEditPreferences={onEditPreferences}
        />
      );

      const prefButtons = screen.getAllByTitle('Edit preferences');
      fireEvent.click(prefButtons[0]);

      expect(onEditPreferences).toHaveBeenCalledWith(mockTemplates[0]);
    });

    it('calls onDelete when delete button clicked', () => {
      const onDelete = jest.fn();
      render(
        <TemplateTable
          {...defaultProps}
          onDelete={onDelete}
        />
      );

      const deleteButtons = screen.getAllByTitle('Delete template');
      fireEvent.click(deleteButtons[0]);

      expect(onDelete).toHaveBeenCalledWith(mockTemplates[0]);
    });
  });

  describe('Display', () => {
    it('displays abbreviations correctly', () => {
      render(<TemplateTable {...defaultProps} />);

      expect(screen.getByText('FM')).toBeInTheDocument();
      expect(screen.getByText('IP')).toBeInTheDocument();
      expect(screen.getByText('PL')).toBeInTheDocument();
    });

    it('shows supervision status correctly', () => {
      render(<TemplateTable {...defaultProps} />);

      const requiredElements = screen.getAllByText('Required');
      expect(requiredElements.length).toBe(3);
    });

    it('displays max residents', () => {
      render(<TemplateTable {...defaultProps} />);

      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('6')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });
});
