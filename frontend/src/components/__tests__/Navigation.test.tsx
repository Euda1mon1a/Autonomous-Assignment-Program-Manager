/**
 * Tests for Navigation Component
 * Component: Navigation - Main navigation bar
 */

import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { Navigation } from '../Navigation';
import { useAuth } from '@/contexts/AuthContext';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/',
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    refresh: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock Next.js Link
jest.mock('next/link', () => {
  const MockLink = ({ children, href, ...props }: React.AnchorHTMLAttributes<HTMLAnchorElement> & { href: string; children: React.ReactNode }) => {
    return <a href={href} {...props}>{children}</a>;
  };
  MockLink.displayName = 'Link';
  return MockLink;
});

// Mock Auth context
const mockAuth = {
  user: { id: '1', username: 'Test User', email: 'test@example.com', role: 'faculty' },
  isAuthenticated: true,
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockedUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

describe('Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedUseAuth.mockReturnValue({
      ...mockAuth,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    } as ReturnType<typeof useAuth>);
  });

  it('renders without crashing', () => {
    render(<Navigation />);
    // Navigation may have responsive duplicates (desktop + mobile)
    expect(screen.getAllByText('Scheduler').length).toBeGreaterThan(0);
  });

  it('renders navigation links', () => {
    render(<Navigation />);
    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(screen.getAllByText('People').length).toBeGreaterThan(0);
  });

  it('renders UserMenu when authenticated', () => {
    render(<Navigation />);
    expect(screen.getAllByText('Test User').length).toBeGreaterThan(0);
  });

  it('hides admin links for non-admin users', () => {
    render(<Navigation />);
    expect(screen.queryAllByText('Settings')).toHaveLength(0);
  });

  it('shows admin links for admin users', () => {
    mockedUseAuth.mockReturnValue({
      user: { ...mockAuth.user, role: 'admin' },
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      logout: jest.fn(),
      refreshUser: jest.fn(),
    } as ReturnType<typeof useAuth>);

    render(<Navigation />);
    expect(screen.getAllByText('Settings').length).toBeGreaterThan(0);
  });
});
