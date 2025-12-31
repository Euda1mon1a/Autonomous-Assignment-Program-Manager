/**
 * Tests for MobileNav Component
 * Component: MobileNav - Mobile navigation drawer
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { MobileNav } from '../MobileNav';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  return ({ children, href, ...props }: any) => {
    return <a href={href} {...props}>{children}</a>;
  };
});

// Mock Auth context
const mockAuth = {
  user: { id: '1', username: 'Test User', email: 'test@example.com', role: 'faculty' },
  isAuthenticated: true,
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}));

describe('MobileNav', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('renders hamburger button', () => {
      render(<MobileNav />);
      expect(screen.getByLabelText('Open navigation menu')).toBeInTheDocument();
    });

    it('drawer is hidden by default', () => {
      const { container } = render(<MobileNav />);
      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveClass('-translate-x-full');
    });

    it('shows nav items when opened', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('My Schedule')).toBeInTheDocument();
      expect(screen.getByText('People')).toBeInTheDocument();
    });
  });

  describe('Drawer interaction', () => {
    it('opens drawer when hamburger clicked', () => {
      const { container } = render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveClass('translate-x-0');
    });

    it('closes drawer when close button clicked', () => {
      const { container } = render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));
      fireEvent.click(screen.getByLabelText('Close navigation menu'));

      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveClass('-translate-x-full');
    });

    it('closes drawer when backdrop clicked', () => {
      const { container } = render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      const backdrop = container.querySelector('.bg-black\\/50');
      fireEvent.click(backdrop!);

      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveClass('-translate-x-full');
    });

    it('closes drawer on Escape key', () => {
      const { container } = render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));
      fireEvent.keyDown(document, { key: 'Escape' });

      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveClass('-translate-x-full');
    });

    it('prevents body scroll when open', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('restores body scroll when closed', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));
      fireEvent.click(screen.getByLabelText('Close navigation menu'));

      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('User display', () => {
    it('shows user info when authenticated', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('faculty')).toBeInTheDocument();
    });

    it('shows user initials in avatar', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.getByText('TU')).toBeInTheDocument();
    });

    it('shows login link when not authenticated', () => {
      jest.spyOn(require('@/contexts/AuthContext'), 'useAuth').mockReturnValue({
        user: null,
        isAuthenticated: false,
      });

      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.getByText('Login')).toBeInTheDocument();
    });
  });

  describe('Admin-only items', () => {
    it('hides admin items for non-admin users', () => {
      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.queryByText('Settings')).not.toBeInTheDocument();
      expect(screen.queryByText('Lab')).not.toBeInTheDocument();
    });

    it('shows admin items for admin users', () => {
      jest.spyOn(require('@/contexts/AuthContext'), 'useAuth').mockReturnValue({
        user: { ...mockAuth.user, role: 'admin' },
        isAuthenticated: true,
      });

      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Lab')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes on hamburger button', () => {
      render(<MobileNav />);

      const button = screen.getByLabelText('Open navigation menu');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-controls', 'mobile-nav-menu');
    });

    it('updates aria-expanded when opened', () => {
      render(<MobileNav />);

      const button = screen.getByLabelText('Open navigation menu');
      fireEvent.click(button);

      expect(button).toHaveAttribute('aria-expanded', 'true');
    });

    it('drawer has proper dialog role', () => {
      const { container } = render(<MobileNav />);

      const drawer = container.querySelector('#mobile-nav-menu');
      expect(drawer).toHaveAttribute('role', 'dialog');
      expect(drawer).toHaveAttribute('aria-modal', 'true');
    });

    it('highlights active page', () => {
      jest.spyOn(require('next/navigation'), 'usePathname').mockReturnValue('/people');

      render(<MobileNav />);

      fireEvent.click(screen.getByLabelText('Open navigation menu'));

      const peopleLink = screen.getByText('People').closest('a');
      expect(peopleLink).toHaveAttribute('aria-current', 'page');
    });
  });
});
