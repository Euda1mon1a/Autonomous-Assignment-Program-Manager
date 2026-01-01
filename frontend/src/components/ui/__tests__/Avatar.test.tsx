/**
 * Tests for Avatar Component
 * Component: Avatar - User avatars with status indicators
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { Avatar, AvatarGroup } from '../Avatar';

describe('Avatar', () => {
  // Test: Rendering
  describe('Rendering', () => {
    it('renders with default fallback icon', () => {
      render(<Avatar />);

      const avatar = screen.getByRole('img', { hidden: true }).parentElement;
      expect(avatar).toBeInTheDocument();
    });

    it('renders with image', () => {
      render(<Avatar src="/avatar.jpg" alt="User avatar" />);

      const img = screen.getByAltText('User avatar');
      expect(img).toHaveAttribute('src', '/avatar.jpg');
    });

    it('renders with initials from name', () => {
      render(<Avatar name="John Doe" />);

      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('extracts initials correctly from full name', () => {
      render(<Avatar name="Jane Marie Smith" />);

      expect(screen.getByText('JM')).toBeInTheDocument();
    });

    it('extracts initials correctly from single name', () => {
      render(<Avatar name="Madonna" />);

      expect(screen.getByText('M')).toBeInTheDocument();
    });

    it('uppercases initials', () => {
      render(<Avatar name="john doe" />);

      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('renders status indicator when provided', () => {
      render(<Avatar name="John Doe" status="online" />);

      const statusIndicator = screen.getByLabelText('Status: online');
      expect(statusIndicator).toBeInTheDocument();
    });
  });

  // Test: Sizes
  describe('Sizes', () => {
    it('renders xs size', () => {
      const { container } = render(<Avatar size="xs" name="JD" />);

      expect(container.querySelector('.w-6.h-6')).toBeInTheDocument();
    });

    it('renders sm size', () => {
      const { container } = render(<Avatar size="sm" name="JD" />);

      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });

    it('renders md size (default)', () => {
      const { container } = render(<Avatar size="md" name="JD" />);

      expect(container.querySelector('.w-10.h-10')).toBeInTheDocument();
    });

    it('renders lg size', () => {
      const { container } = render(<Avatar size="lg" name="JD" />);

      expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
    });

    it('renders xl size', () => {
      const { container } = render(<Avatar size="xl" name="JD" />);

      expect(container.querySelector('.w-16.h-16')).toBeInTheDocument();
    });
  });

  // Test: Status indicators
  describe('Status Indicators', () => {
    it('renders online status with green color', () => {
      const { container } = render(<Avatar name="JD" status="online" />);

      expect(container.querySelector('.bg-green-500')).toBeInTheDocument();
    });

    it('renders offline status with gray color', () => {
      const { container } = render(<Avatar name="JD" status="offline" />);

      expect(container.querySelector('.bg-gray-400')).toBeInTheDocument();
    });

    it('renders away status with amber color', () => {
      const { container } = render(<Avatar name="JD" status="away" />);

      expect(container.querySelector('.bg-amber-500')).toBeInTheDocument();
    });

    it('renders busy status with red color', () => {
      const { container } = render(<Avatar name="JD" status="busy" />);

      expect(container.querySelector('.bg-red-500')).toBeInTheDocument();
    });

    it('does not render status indicator when not provided', () => {
      render(<Avatar name="JD" />);

      expect(screen.queryByLabelText(/Status:/)).not.toBeInTheDocument();
    });
  });

  // Test: Image fallback
  describe('Image Fallback', () => {
    it('falls back to initials when image fails to load', () => {
      render(<Avatar src="/broken.jpg" name="John Doe" />);

      const img = screen.getByAltText('User avatar');
      fireEvent.error(img);

      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('falls back to icon when image fails and no name', () => {
      const { container } = render(<Avatar src="/broken.jpg" />);

      const img = screen.getByAltText('User avatar');
      fireEvent.error(img);

      // Icon should be rendered
      const avatar = container.querySelector('.rounded-full');
      expect(avatar).toBeInTheDocument();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('applies custom className', () => {
      const { container } = render(<Avatar className="custom-class" name="JD" />);

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('renders with both image and name (prefers image)', () => {
      render(<Avatar src="/avatar.jpg" name="John Doe" alt="User" />);

      const img = screen.getByAltText('User');
      expect(img).toHaveAttribute('src', '/avatar.jpg');
      expect(screen.queryByText('JD')).not.toBeInTheDocument();
    });

    it('renders with status indicator sized appropriately for avatar size', () => {
      const { container: containerXs } = render(<Avatar name="JD" status="online" size="xs" />);
      expect(containerXs.querySelector('.w-1\\.5.h-1\\.5')).toBeInTheDocument();

      const { container: containerXl } = render(<Avatar name="JD" status="online" size="xl" />);
      expect(containerXl.querySelector('.w-4.h-4')).toBeInTheDocument();
    });

    it('uses default alt text when not provided', () => {
      render(<Avatar src="/avatar.jpg" />);

      expect(screen.getByAltText('User avatar')).toBeInTheDocument();
    });
  });
});

describe('AvatarGroup', () => {
  const mockAvatars = [
    { name: 'John Doe', src: '/john.jpg' },
    { name: 'Jane Smith', src: '/jane.jpg' },
    { name: 'Bob Wilson', src: '/bob.jpg' },
    { name: 'Alice Johnson', src: '/alice.jpg' },
  ];

  // Test: Rendering
  describe('Rendering', () => {
    it('renders multiple avatars', () => {
      render(<AvatarGroup avatars={mockAvatars.slice(0, 3)} />);

      expect(screen.getByAltText(/John Doe|User avatar/)).toBeInTheDocument();
      expect(screen.getByAltText(/Jane Smith|User avatar/)).toBeInTheDocument();
      expect(screen.getByAltText(/Bob Wilson|User avatar/)).toBeInTheDocument();
    });

    it('limits avatars to max prop', () => {
      render(<AvatarGroup avatars={mockAvatars} max={2} />);

      const images = screen.getAllByRole('img', { hidden: true });
      expect(images).toHaveLength(2);
    });

    it('shows remaining count when exceeds max', () => {
      render(<AvatarGroup avatars={mockAvatars} max={2} />);

      expect(screen.getByText('+2')).toBeInTheDocument();
    });

    it('does not show remaining count when within max', () => {
      render(<AvatarGroup avatars={mockAvatars.slice(0, 2)} max={3} />);

      expect(screen.queryByText(/^\+/)).not.toBeInTheDocument();
    });

    it('uses default max of 3', () => {
      render(<AvatarGroup avatars={mockAvatars} />);

      const images = screen.getAllByRole('img', { hidden: true });
      expect(images).toHaveLength(3);
      expect(screen.getByText('+1')).toBeInTheDocument();
    });
  });

  // Test: Sizes
  describe('Sizes', () => {
    it('renders avatars with specified size', () => {
      const { container } = render(<AvatarGroup avatars={mockAvatars.slice(0, 2)} size="lg" />);

      expect(container.querySelector('.w-12.h-12')).toBeInTheDocument();
    });

    it('applies size to remaining count indicator', () => {
      const { container } = render(<AvatarGroup avatars={mockAvatars} max={2} size="sm" />);

      expect(container.querySelector('.w-8.h-8')).toBeInTheDocument();
    });
  });

  // Test: Edge cases
  describe('Edge Cases', () => {
    it('applies custom className', () => {
      const { container } = render(
        <AvatarGroup avatars={mockAvatars.slice(0, 2)} className="custom-class" />
      );

      expect(container.querySelector('.custom-class')).toBeInTheDocument();
    });

    it('handles empty avatars array', () => {
      const { container } = render(<AvatarGroup avatars={[]} />);

      expect(container.querySelector('.flex')).toBeInTheDocument();
      expect(screen.queryByRole('img', { hidden: true })).not.toBeInTheDocument();
    });

    it('handles max greater than avatars length', () => {
      render(<AvatarGroup avatars={mockAvatars.slice(0, 2)} max={5} />);

      const images = screen.getAllByRole('img', { hidden: true });
      expect(images).toHaveLength(2);
      expect(screen.queryByText(/^\+/)).not.toBeInTheDocument();
    });

    it('applies ring styling to avatars', () => {
      const { container } = render(<AvatarGroup avatars={mockAvatars.slice(0, 2)} />);

      expect(container.querySelector('.ring-2.ring-white')).toBeInTheDocument();
    });

    it('overlaps avatars with negative space', () => {
      const { container } = render(<AvatarGroup avatars={mockAvatars.slice(0, 2)} />);

      expect(container.querySelector('.-space-x-2')).toBeInTheDocument();
    });
  });
});
