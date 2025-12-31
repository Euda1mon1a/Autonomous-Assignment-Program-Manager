/**
 * Tests for ProtectedRoute Component
 * Component: ProtectedRoute - Route protection and authorization
 */

import React from 'react';
import { render, screen, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { ProtectedRoute } from '../ProtectedRoute';

// Mock Next.js navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock Auth context
const mockAuth = {
  isAuthenticated: true,
  isLoading: false,
  user: { id: '1', username: 'Test User', email: 'test@example.com', role: 'faculty' },
};

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockAuth,
}));

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAuth.isAuthenticated = true;
    mockAuth.isLoading = false;
    mockAuth.user = { id: '1', username: 'Test User', email: 'test@example.com', role: 'faculty' };
  });

  describe('Rendering', () => {
    it('renders children when authenticated', () => {
      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Protected content')).toBeInTheDocument();
    });

    it('shows loading spinner while checking auth', () => {
      mockAuth.isLoading = true;

      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('shows redirecting message when not authenticated', () => {
      mockAuth.isAuthenticated = false;
      mockAuth.isLoading = false;

      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Redirecting to login...')).toBeInTheDocument();
    });
  });

  describe('Authentication check', () => {
    it('redirects to login when not authenticated', async () => {
      mockAuth.isAuthenticated = false;
      mockAuth.isLoading = false;

      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('does not redirect when authenticated', async () => {
      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockPush).not.toHaveBeenCalled();
      });
    });

    it('does not redirect while loading', () => {
      mockAuth.isLoading = true;

      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  describe('Admin-only routes', () => {
    it('shows access denied for non-admin users', () => {
      mockAuth.user = { ...mockAuth.user, role: 'faculty' };

      render(
        <ProtectedRoute requireAdmin={true}>
          <div>Admin content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.queryByText('Admin content')).not.toBeInTheDocument();
    });

    it('renders children for admin users', () => {
      mockAuth.user = { ...mockAuth.user, role: 'admin' };

      render(
        <ProtectedRoute requireAdmin={true}>
          <div>Admin content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Admin content')).toBeInTheDocument();
      expect(screen.queryByText('Access Denied')).not.toBeInTheDocument();
    });

    it('shows return to dashboard button when access denied', () => {
      mockAuth.user = { ...mockAuth.user, role: 'faculty' };

      render(
        <ProtectedRoute requireAdmin={true}>
          <div>Admin content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('Return to Dashboard')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes for loading state', () => {
      mockAuth.isLoading = true;

      render(
        <ProtectedRoute>
          <div>Protected content</div>
        </ProtectedRoute>
      );

      const status = screen.getByRole('status');
      expect(status).toHaveAttribute('aria-live', 'polite');
      expect(status).toHaveAttribute('aria-busy', 'true');
    });

    it('has proper ARIA attributes for access denied', () => {
      mockAuth.user = { ...mockAuth.user, role: 'faculty' };

      render(
        <ProtectedRoute requireAdmin={true}>
          <div>Admin content</div>
        </ProtectedRoute>
      );

      const alert = screen.getByRole('alert');
      expect(alert).toHaveAttribute('aria-live', 'polite');
    });
  });
});
