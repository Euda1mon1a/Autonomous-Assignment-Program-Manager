/**
 * Tests for LoadingStates Component
 * Component: LoadingStates - Various loading state components
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import {
  Spinner,
  ButtonSpinner,
  PageSpinner,
  SkeletonText,
  SkeletonAvatar,
  SkeletonButton,
  SkeletonCard,
  ProgressBar,
  ProgressCircle,
  PageLoader,
  CardLoader,
  TableLoader,
  InlineLoader,
} from '../LoadingStates';

describe('LoadingStates', () => {
  describe('Spinner', () => {
    it('renders without crashing', () => {
      render(<Spinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<Spinner label="Loading data" />);
      const spinner = screen.getByRole('status');
      expect(spinner).toHaveAttribute('aria-busy', 'true');
      expect(spinner).toHaveAttribute('aria-label', 'Loading data');
    });

    it('renders different sizes', () => {
      const { container: smContainer } = render(<Spinner size="sm" />);
      expect(smContainer.querySelector('.w-4.h-4')).toBeInTheDocument();

      const { container: lgContainer } = render(<Spinner size="lg" />);
      expect(lgContainer.querySelector('.w-12.h-12')).toBeInTheDocument();
    });

    it('renders different variants', () => {
      const { container: primaryContainer } = render(<Spinner variant="primary" />);
      expect(primaryContainer.querySelector('.border-t-blue-600')).toBeInTheDocument();

      const { container: whiteContainer } = render(<Spinner variant="white" />);
      expect(whiteContainer.querySelector('.border-t-white')).toBeInTheDocument();
    });
  });

  describe('ButtonSpinner', () => {
    it('renders with small size', () => {
      const { container } = render(<ButtonSpinner />);
      expect(container.querySelector('.w-4.h-4')).toBeInTheDocument();
    });

    it('has processing label', () => {
      render(<ButtonSpinner />);
      expect(screen.getByLabelText('Processing')).toBeInTheDocument();
    });
  });

  describe('PageSpinner', () => {
    it('renders with message', () => {
      render(<PageSpinner message="Loading page..." />);
      expect(screen.getByText('Loading page...')).toBeInTheDocument();
    });

    it('renders without message', () => {
      render(<PageSpinner />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has minimum height', () => {
      const { container } = render(<PageSpinner />);
      expect(container.querySelector('.min-h-\\[400px\\]')).toBeInTheDocument();
    });
  });

  describe('SkeletonText', () => {
    it('renders default 3 lines', () => {
      const { container } = render(<SkeletonText />);
      const lines = container.querySelectorAll('.animate-pulse');
      expect(lines).toHaveLength(3);
    });

    it('renders custom number of lines', () => {
      const { container } = render(<SkeletonText lines={5} />);
      const lines = container.querySelectorAll('.animate-pulse');
      expect(lines).toHaveLength(5);
    });

    it('has proper ARIA attributes', () => {
      render(<SkeletonText />);
      const skeleton = screen.getByRole('status');
      expect(skeleton).toHaveAttribute('aria-busy', 'true');
      expect(skeleton).toHaveAttribute('aria-label', 'Loading content');
    });
  });

  describe('SkeletonAvatar', () => {
    it('renders circular shape', () => {
      const { container } = render(<SkeletonAvatar />);
      expect(container.querySelector('.rounded-full')).toBeInTheDocument();
    });

    it('renders different sizes', () => {
      const { container: smContainer } = render(<SkeletonAvatar size="sm" />);
      expect(smContainer.querySelector('.w-8.h-8')).toBeInTheDocument();

      const { container: lgContainer } = render(<SkeletonAvatar size="lg" />);
      expect(lgContainer.querySelector('.w-16.h-16')).toBeInTheDocument();
    });

    it('has loading label', () => {
      render(<SkeletonAvatar />);
      expect(screen.getByLabelText('Loading avatar')).toBeInTheDocument();
    });
  });

  describe('SkeletonButton', () => {
    it('renders different sizes', () => {
      const { container: smContainer } = render(<SkeletonButton size="sm" />);
      expect(smContainer.querySelector('.h-8')).toBeInTheDocument();

      const { container: lgContainer } = render(<SkeletonButton size="lg" />);
      expect(lgContainer.querySelector('.h-12')).toBeInTheDocument();
    });

    it('has loading label', () => {
      render(<SkeletonButton />);
      expect(screen.getByLabelText('Loading button')).toBeInTheDocument();
    });
  });

  describe('SkeletonCard', () => {
    it('renders card structure', () => {
      const { container } = render(<SkeletonCard />);
      expect(container.querySelector('.bg-white.rounded-lg.shadow')).toBeInTheDocument();
    });

    it('has loading label', () => {
      render(<SkeletonCard />);
      expect(screen.getByLabelText('Loading card')).toBeInTheDocument();
    });
  });

  describe('ProgressBar', () => {
    it('renders with percentage', () => {
      render(<ProgressBar percentage={50} />);
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<ProgressBar percentage={75} />);
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('clamps percentage between 0 and 100', () => {
      const { rerender } = render(<ProgressBar percentage={150} />);
      expect(screen.getByText('100%')).toBeInTheDocument();

      rerender(<ProgressBar percentage={-10} />);
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('hides label when showLabel is false', () => {
      render(<ProgressBar percentage={50} showLabel={false} />);
      expect(screen.queryByText('50%')).not.toBeInTheDocument();
    });
  });

  describe('ProgressCircle', () => {
    it('renders with percentage', () => {
      render(<ProgressCircle percentage={60} />);
      expect(screen.getByText('60%')).toBeInTheDocument();
    });

    it('has proper ARIA attributes', () => {
      render(<ProgressCircle percentage={80} />);
      const progressCircle = screen.getByRole('progressbar');
      expect(progressCircle).toHaveAttribute('aria-valuenow', '80');
    });

    it('hides label when showLabel is false', () => {
      render(<ProgressCircle percentage={50} showLabel={false} />);
      expect(screen.queryByText('50%')).not.toBeInTheDocument();
    });
  });

  describe('PageLoader', () => {
    it('renders full page loader', () => {
      const { container } = render(<PageLoader />);
      expect(container.querySelector('.min-h-screen')).toBeInTheDocument();
    });

    it('renders with message', () => {
      render(<PageLoader message="Loading data..." />);
      expect(screen.getByText('Loading data...')).toBeInTheDocument();
    });
  });

  describe('CardLoader', () => {
    it('renders single card by default', () => {
      render(<CardLoader />);
      expect(screen.getByLabelText('Loading card')).toBeInTheDocument();
    });

    it('renders multiple cards', () => {
      render(<CardLoader count={3} />);
      const cards = screen.getAllByLabelText('Loading card');
      expect(cards).toHaveLength(3);
    });
  });

  describe('TableLoader', () => {
    it('renders table structure', () => {
      render(<TableLoader />);
      expect(screen.getByLabelText('Loading table')).toBeInTheDocument();
    });

    it('renders custom rows and columns', () => {
      const { container } = render(<TableLoader rows={3} columns={4} />);
      const rows = container.querySelectorAll('.border-b');
      expect(rows).toHaveLength(3);
    });
  });

  describe('InlineLoader', () => {
    it('renders inline loader', () => {
      render(<InlineLoader />);
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('renders with text', () => {
      render(<InlineLoader text="Loading..." />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('uses inline-flex layout', () => {
      const { container } = render(<InlineLoader />);
      expect(container.querySelector('.inline-flex')).toBeInTheDocument();
    });
  });
});
