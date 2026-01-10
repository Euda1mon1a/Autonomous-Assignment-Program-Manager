/**
 * Tests for EditTemplateModal Component
 * Component: EditTemplateModal - Modal for editing rotation templates
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EditTemplateModal } from '../EditTemplateModal';
import type { RotationTemplate } from '@/types/api';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('EditTemplateModal', () => {
  const mockTemplate: RotationTemplate = {
    id: '1',
    name: 'Test Template',
    activityType: 'clinic',
    abbreviation: 'TT',
    displayAbbreviation: 'TT',
    fontColor: null,
    backgroundColor: '#FF0000',
    clinicLocation: null,
    maxResidents: 4,
    requiresSpecialty: null,
    requiresProcedureCredential: false,
    supervisionRequired: true,
    maxSupervisionRatio: 4,
    createdAt: '2024-01-01T00:00:00Z',
  };
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<EditTemplateModal isOpen={true} template={mockTemplate} onClose={mockOnClose} />);
    expect(screen.getByText(/edit template/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<EditTemplateModal isOpen={false} template={mockTemplate} onClose={mockOnClose} />);
    expect(screen.queryByText(/edit template/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<EditTemplateModal isOpen={true} template={mockTemplate} onClose={mockOnClose} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
