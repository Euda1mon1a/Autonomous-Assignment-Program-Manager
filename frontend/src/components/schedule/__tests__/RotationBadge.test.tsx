import React from 'react';
import { render, screen } from '@testing-library/react';
import { RotationBadge } from '../RotationBadge';

describe('RotationBadge', () => {
  describe('rendering', () => {
    it('renders clinic rotation badge', () => {
      render(<RotationBadge rotationType="clinic" />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Rotation type: Clinic');
    });

    it('renders inpatient rotation badge', () => {
      render(<RotationBadge rotationType="inpatient" />);

      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      expect(screen.getByText('🛏️')).toBeInTheDocument();
    });

    it('renders procedures rotation badge', () => {
      render(<RotationBadge rotationType="procedures" />);

      expect(screen.getByText('Procedures')).toBeInTheDocument();
      expect(screen.getByText('💉')).toBeInTheDocument();
    });

    it('renders conference rotation badge', () => {
      render(<RotationBadge rotationType="conference" />);

      expect(screen.getByText('Conference')).toBeInTheDocument();
      expect(screen.getByText('📚')).toBeInTheDocument();
    });

    it('renders call rotation badge', () => {
      render(<RotationBadge rotationType="call" />);

      expect(screen.getByText('Call')).toBeInTheDocument();
      expect(screen.getByText('📞')).toBeInTheDocument();
    });

    it('renders FMIT rotation badge', () => {
      render(<RotationBadge rotationType="fmit" />);

      expect(screen.getByText('FMIT')).toBeInTheDocument();
      expect(screen.getByText('🎖️')).toBeInTheDocument();
    });

    it('renders TDY rotation badge', () => {
      render(<RotationBadge rotationType="tdy" />);

      expect(screen.getByText('TDY')).toBeInTheDocument();
      expect(screen.getByText('✈️')).toBeInTheDocument();
    });

    it('renders deployment rotation badge', () => {
      render(<RotationBadge rotationType="deployment" />);

      expect(screen.getByText('Deployment')).toBeInTheDocument();
      expect(screen.getByText('🌍')).toBeInTheDocument();
    });

    it('renders leave rotation badge', () => {
      render(<RotationBadge rotationType="leave" />);

      expect(screen.getByText('Leave')).toBeInTheDocument();
      expect(screen.getByText('🏖️')).toBeInTheDocument();
    });

    it('renders admin rotation badge', () => {
      render(<RotationBadge rotationType="admin" />);

      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('📋')).toBeInTheDocument();
    });

    it('renders unknown rotation with default styling', () => {
      render(<RotationBadge rotationType="unknown_rotation" />);

      expect(screen.getByText('unknown_rotation')).toBeInTheDocument();
      expect(screen.getByText('📌')).toBeInTheDocument();
    });
  });

  describe('size variants', () => {
    it('renders small badge', () => {
      render(<RotationBadge rotationType="clinic" size="sm" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs');
    });

    it('renders medium badge (default)', () => {
      render(<RotationBadge rotationType="clinic" size="md" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('px-3', 'py-1', 'text-sm');
    });

    it('renders large badge', () => {
      render(<RotationBadge rotationType="clinic" size="lg" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('px-4', 'py-1.5', 'text-base');
    });
  });

  describe('icon display', () => {
    it('shows icon by default', () => {
      render(<RotationBadge rotationType="clinic" />);

      expect(screen.getByText('🏥')).toBeInTheDocument();
    });

    it('hides icon when showIcon is false', () => {
      render(<RotationBadge rotationType="clinic" showIcon={false} />);

      expect(screen.queryByText('🏥')).not.toBeInTheDocument();
      expect(screen.getByText('Clinic')).toBeInTheDocument();
    });
  });

  describe('color coding', () => {
    it('applies clinic colors (blue)', () => {
      render(<RotationBadge rotationType="clinic" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('applies inpatient colors (purple)', () => {
      render(<RotationBadge rotationType="inpatient" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
    });

    it('applies procedures colors (green)', () => {
      render(<RotationBadge rotationType="procedures" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('applies call colors (red)', () => {
      render(<RotationBadge rotationType="call" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('applies default colors for unknown type', () => {
      render(<RotationBadge rotationType="unknown" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-slate-100', 'text-slate-800');
    });
  });

  describe('case insensitivity', () => {
    it('handles uppercase rotation types', () => {
      render(<RotationBadge rotationType="CLINIC" />);

      expect(screen.getByText('Clinic')).toBeInTheDocument();
      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('handles mixed case rotation types', () => {
      render(<RotationBadge rotationType="InPatient" />);

      expect(screen.getByText('Inpatient')).toBeInTheDocument();
      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('bg-purple-100', 'text-purple-800');
    });
  });

  describe('custom className', () => {
    it('applies custom className', () => {
      render(<RotationBadge rotationType="clinic" className="custom-class" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA role and label', () => {
      render(<RotationBadge rotationType="clinic" />);

      const badge = screen.getByRole('status');
      expect(badge).toHaveAttribute('aria-label', 'Rotation type: Clinic');
    });

    it('marks icon as decorative', () => {
      render(<RotationBadge rotationType="clinic" />);

      const icon = screen.getByText('🏥');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });
  });
});
