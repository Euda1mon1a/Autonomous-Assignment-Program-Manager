import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BlockCard } from '../BlockCard';

describe('BlockCard', () => {
  const defaultProps = {
    blockId: 'block-123',
    personName: 'Dr. Smith',
    rotationType: 'Clinic',
    date: '2024-01-15',
    shift: 'AM' as const,
  };

  it('renders block information correctly', () => {
    render(<BlockCard {...defaultProps} />);

    expect(screen.getByText('Dr. Smith')).toBeInTheDocument();
    expect(screen.getByText('Clinic')).toBeInTheDocument();
    expect(screen.getByText('AM')).toBeInTheDocument();
  });

  it('applies conflict styling when isConflict is true', () => {
    render(<BlockCard {...defaultProps} isConflict />);

    const card = screen.getByRole('button');
    expect(card).toHaveClass('ring-red-500');
  });

  it('applies warning styling when isWarning is true', () => {
    render(<BlockCard {...defaultProps} isWarning />);

    const card = screen.getByRole('button');
    expect(card).toHaveClass('ring-yellow-500');
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<BlockCard {...defaultProps} onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('handles keyboard navigation', () => {
    const handleClick = jest.fn();
    render(<BlockCard {...defaultProps} onClick={handleClick} />);

    const card = screen.getByRole('button');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(card, { key: ' ' });
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('displays duration when provided', () => {
    render(<BlockCard {...defaultProps} duration={8} />);

    expect(screen.getByText('8h')).toBeInTheDocument();
  });

  it('handles drag start event', () => {
    const handleDragStart = jest.fn();
    render(<BlockCard {...defaultProps} onDragStart={handleDragStart} />);

    const card = screen.getByRole('button');
    fireEvent.dragStart(card);

    expect(handleDragStart).toHaveBeenCalled();
  });

  it('prevents drag when isDraggable is false', () => {
    const handleDragStart = jest.fn();
    render(<BlockCard {...defaultProps} isDraggable={false} onDragStart={handleDragStart} />);

    const card = screen.getByRole('button');
    const event = new DragEvent('dragstart', { bubbles: true });
    Object.defineProperty(event, 'dataTransfer', {
      value: { effectAllowed: '', setData: jest.fn() },
    });

    card.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
});
