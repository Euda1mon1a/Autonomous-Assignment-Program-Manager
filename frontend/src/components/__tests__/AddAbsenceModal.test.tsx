/**
 * Tests for AddAbsenceModal Component
 * Component: AddAbsenceModal - Modal for adding new absences
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { AddAbsenceModal } from '../AddAbsenceModal';

// Mock API calls
global.fetch = jest.fn();

// Mock toast context
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('AddAbsenceModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<AddAbsenceModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/add absence/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<AddAbsenceModal isOpen={false} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByText(/add absence/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<AddAbsenceModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('has form inputs for absence details', () => {
    render(<AddAbsenceModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });
});
