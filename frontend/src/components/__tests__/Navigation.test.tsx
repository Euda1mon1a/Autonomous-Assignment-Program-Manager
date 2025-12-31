/**
 * Tests for Navigation Component
 * Component: Navigation - Main navigation bar
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Navigation } from '../Navigation';

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

describe('Navigation', () => {
  it('renders without crashing', () => {
    render(<Navigation />);
    expect(screen.getByText('Scheduler')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(<Navigation />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('People')).toBeInTheDocument();
  });

  it('renders UserMenu when authenticated', () => {
    render(<Navigation />);
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });

  it('hides admin links for non-admin users', () => {
    render(<Navigation />);
    expect(screen.queryByText('Settings')).not.toBeInTheDocument();
  });

  it('shows admin links for admin users', () => {
    jest.spyOn(require('@/contexts/AuthContext'), 'useAuth').mockReturnValue({
      user: { ...mockAuth.user, role: 'admin' },
      isAuthenticated: true,
    });

    render(<Navigation />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
