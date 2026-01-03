/**
 * Tests for UserMenu Component
 * Component: UserMenu - User account dropdown menu
 */

import React from 'react';
import { render, screen, fireEvent } from '@/test-utils';
import '@testing-library/jest-dom';
import { UserMenu } from '../UserMenu';
import * as AuthContext from '@/contexts/AuthContext';

// Mock Auth context
const mockLogout = jest.fn();
const mockUser = {
  id: '1',
  username: 'John Doe',
  email: 'john@example.com',
  role: 'faculty',
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    logout: mockLogout,
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

describe('UserMenu', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders user initials in avatar', () => {
      render(<UserMenu />);
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('renders username', () => {
      render(<UserMenu />);
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    it('renders nothing when no user', () => {
      jest.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: null,
        logout: mockLogout,
        isAuthenticated: false,
        hasPermission: jest.fn(),
        hasRole: jest.fn(),
      } as any);

      const { container } = render(<UserMenu />);
      expect(container).toBeEmptyDOMElement();
    });

    it('has proper ARIA attributes', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-haspopup', 'true');
    });
  });

  describe('Dropdown interaction', () => {
    it('opens dropdown when clicked', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });

    it('closes dropdown when clicked outside', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);
      expect(screen.getByText('Settings')).toBeInTheDocument();

      fireEvent.mouseDown(document.body);
      expect(screen.queryByText('Settings')).not.toBeInTheDocument();
    });

    it('toggles aria-expanded', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'true');

      fireEvent.click(button);
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('rotates chevron icon when open', () => {
      const { container } = render(<UserMenu />);

      const button = screen.getByRole('button');
      const chevron = container.querySelector('.lucide-chevron-down');

      expect(chevron).not.toHaveClass('rotate-180');

      fireEvent.click(button);
      expect(chevron).toHaveClass('rotate-180');
    });
  });

  describe('User information display', () => {
    it('displays user email in dropdown', () => {
      render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });

    it('displays user role badge', () => {
      render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));
      expect(screen.getByText('faculty')).toBeInTheDocument();
    });

    it('applies correct role badge color', () => {
      const { container } = render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));

      const roleBadge = screen.getByText('faculty');
      expect(roleBadge).toHaveClass('bg-blue-100', 'text-blue-700');
    });

    it('handles admin role badge color', () => {
      jest.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { ...mockUser, role: 'admin' },
        logout: mockLogout,
        isAuthenticated: true,
        hasPermission: jest.fn(),
        hasRole: jest.fn(),
      } as any);

      render(<UserMenu />);
      fireEvent.click(screen.getByRole('button'));

      const roleBadge = screen.getByText('admin');
      expect(roleBadge).toHaveClass('bg-red-100', 'text-red-700');
    });
  });

  describe('Menu actions', () => {
    it('renders settings link', () => {
      render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));

      const settingsLink = screen.getByText('Settings').closest('a');
      expect(settingsLink).toHaveAttribute('href', '/settings');
    });

    it('calls logout when logout button clicked', () => {
      render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Logout'));

      expect(mockLogout).toHaveBeenCalledTimes(1);
    });

    it('closes dropdown when settings clicked', () => {
      render(<UserMenu />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      fireEvent.click(screen.getByText('Settings'));

      expect(screen.queryByText('john@example.com')).not.toBeInTheDocument();
    });

    it('closes dropdown when logout clicked', () => {
      render(<UserMenu />);

      fireEvent.click(screen.getByRole('button'));
      fireEvent.click(screen.getByText('Logout'));

      expect(screen.queryByText('john@example.com')).not.toBeInTheDocument();
    });
  });

  describe('Initials generation', () => {
    it('generates initials from multi-word name', () => {
      render(<UserMenu />);
      expect(screen.getByText('JD')).toBeInTheDocument();
    });

    it('limits initials to 2 characters', () => {
      jest.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { ...mockUser, username: 'John Paul Smith' },
        logout: mockLogout,
        isAuthenticated: true,
        hasPermission: jest.fn(),
        hasRole: jest.fn(),
      } as any);

      render(<UserMenu />);
      fireEvent.click(screen.getByRole('button'));

      expect(screen.getAllByText('JP')[0]).toBeInTheDocument();
    });

    it('uppercases initials', () => {
      jest.spyOn(AuthContext, 'useAuth').mockReturnValue({
        user: { ...mockUser, username: 'jane smith' },
        logout: mockLogout,
        isAuthenticated: true,
        hasPermission: jest.fn(),
        hasRole: jest.fn(),
      } as any);

      render(<UserMenu />);
      expect(screen.getByText('JS')).toBeInTheDocument();
    });
  });
});
