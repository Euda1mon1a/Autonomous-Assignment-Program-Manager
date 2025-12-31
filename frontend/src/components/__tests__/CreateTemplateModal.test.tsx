/**
 * Tests for CreateTemplateModal Component
 * Component: CreateTemplateModal - Modal for creating rotation templates
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { CreateTemplateModal } from '../CreateTemplateModal';

global.fetch = jest.fn();

jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
    },
  }),
}));

describe('CreateTemplateModal', () => {
  const mockOnClose = jest.fn();
  const mockOnSuccess = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<CreateTemplateModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.getByText(/create template/i)).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<CreateTemplateModal isOpen={false} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    expect(screen.queryByText(/create template/i)).not.toBeInTheDocument();
  });

  it('calls onClose when cancel button clicked', () => {
    render(<CreateTemplateModal isOpen={true} onClose={mockOnClose} onSuccess={mockOnSuccess} />);
    const cancelButton = screen.getByText(/cancel/i);
    fireEvent.click(cancelButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});
