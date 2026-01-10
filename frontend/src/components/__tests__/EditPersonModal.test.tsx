/**
 * Tests for EditPersonModal Component
 * Component: EditPersonModal - Modal for editing person details
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EditPersonModal } from '../EditPersonModal';
import { PersonType } from '@/types/api';
import type { Person } from '@/types/api';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('EditPersonModal', () => {
  const mockPerson: Person = {
    id: '1',
    name: 'Test User',
    email: 'test@example.com',
    type: PersonType.FACULTY,
    pgyLevel: null,
    performsProcedures: true,
    specialties: ['Internal Medicine'],
    primaryDuty: null,
    facultyRole: null,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };
  const mockOnClose = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<EditPersonModal isOpen={true} person={mockPerson} onClose={mockOnClose} />);
    expect(screen.getByText(/edit person/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<EditPersonModal isOpen={false} person={mockPerson} onClose={mockOnClose} />);
    expect(screen.queryByText(/edit person/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<EditPersonModal isOpen={true} person={mockPerson} onClose={mockOnClose} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
