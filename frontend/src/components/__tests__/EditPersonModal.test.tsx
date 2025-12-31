/**
 * Tests for EditPersonModal Component
 * Component: EditPersonModal - Modal for editing person details
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { EditPersonModal } from '../EditPersonModal';

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
  const mockPerson = {
    id: '1',
    username: 'Test User',
    email: 'test@example.com',
    role: 'faculty',
  };
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<EditPersonModal isOpen={true} person={mockPerson} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/edit person/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<EditPersonModal isOpen={false} person={mockPerson} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByText(/edit person/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<EditPersonModal isOpen={true} person={mockPerson} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
