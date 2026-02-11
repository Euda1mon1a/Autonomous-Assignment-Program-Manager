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
  const MockLink = ({ children, href, ...props }: any) => {
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
    mockedUseAuth.mockReturnValue(mockAuth as any);
  });

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
    mockedUseAuth.mockReturnValue({
      user: { ...mockAuth.user, role: 'admin' },
      isAuthenticated: true,
      logout: jest.fn(),
      hasPermission: jest.fn(),
      hasRole: jest.fn(),
    } as any);

    render(<Navigation />);
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });
});
