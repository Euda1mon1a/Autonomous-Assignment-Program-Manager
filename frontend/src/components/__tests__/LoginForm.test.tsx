/**
 * Tests for LoginForm Component
 * Component: LoginForm - User authentication form
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import '@testing-library/jest-dom';
import { LoginForm } from '../LoginForm';

// Mock useRouter
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

// Mock useAuth
const mockLogin = jest.fn();
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    user: null,
    isAuthenticated: false,
    isLoading: false,
    logout: jest.fn(),
  }),
}));

describe('LoginForm', () => {
  beforeEach(() => {
    mockPush.mockClear();
    mockLogin.mockClear();
  });

  describe('Rendering', () => {
    it('renders username input', () => {
      render(<LoginForm />);
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    });

    it('renders password input', () => {
      render(<LoginForm />);
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('renders submit button', () => {
      render(<LoginForm />);
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    });

    it('password field is type password', () => {
      render(<LoginForm />);
      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('renders dev credentials info', () => {
      render(<LoginForm />);
      expect(screen.getByText(/local dev credentials/i)).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('disables submit when fields are empty', () => {
      render(<LoginForm />);
      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).toBeDisabled();
    });

    it('shows error when username is empty after blur', () => {
      render(<LoginForm />);
      const usernameInput = screen.getByLabelText(/username/i);
      fireEvent.focus(usernameInput);
      fireEvent.blur(usernameInput);

      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
    });

    it('shows error when password is empty after blur', () => {
      render(<LoginForm />);
      const passwordInput = screen.getByLabelText(/password/i);
      fireEvent.focus(passwordInput);
      fireEvent.blur(passwordInput);

      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });

    it('enables submit when both fields have values', () => {
      render(<LoginForm />);
      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Form Submission', () => {
    it('calls login on submit with valid credentials', async () => {
      mockLogin.mockResolvedValueOnce(undefined);

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith({ username: 'admin', password: 'admin123' });
      });
    });

    it('shows error message on failed login', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('shows loading state while submitting', async () => {
      mockLogin.mockImplementation(() => new Promise(() => {}));

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });

      // Verify button is enabled before clicking
      expect(submitButton).not.toBeDisabled();

      fireEvent.click(submitButton);

      // Verify mockLogin was called (form submission worked)
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled();
      });

      // After login is called, the button should show loading state
      expect(screen.getAllByText(/signing in/i).length).toBeGreaterThan(0);
    });

    it('calls onSuccess callback on successful login', async () => {
      const onSuccess = jest.fn();
      mockLogin.mockResolvedValueOnce(undefined);

      render(<LoginForm onSuccess={onSuccess} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form labels', () => {
      render(<LoginForm />);

      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it('has autocomplete attributes', () => {
      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(usernameInput).toHaveAttribute('autocomplete', 'username');
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password');
    });
  });

  describe('Security', () => {
    it('does not expose password in DOM', () => {
      render(<LoginForm />);

      const passwordInput = screen.getByLabelText(/password/i);
      fireEvent.change(passwordInput, { target: { value: 'secretpassword' } });

      expect(passwordInput).toHaveAttribute('type', 'password');
    });

    it('handles network errors', async () => {
      mockLogin.mockRejectedValueOnce(new Error('Network error: Cannot reach API'));

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('disables inputs while submitting', async () => {
      mockLogin.mockImplementation(() => new Promise(() => {}));

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      const submitButton = screen.getByRole('button', { name: /sign in/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(usernameInput).toBeDisabled();
        expect(passwordInput).toBeDisabled();
      });
    });

    it('renders help section', () => {
      render(<LoginForm />);
      expect(screen.getByText(/need help signing in/i)).toBeInTheDocument();
    });

    it('submits form when Enter key is pressed in password field', async () => {
      mockLogin.mockResolvedValueOnce(undefined);

      render(<LoginForm />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin123' } });

      fireEvent.keyDown(passwordInput, { key: 'Enter', code: 'Enter' });

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalled();
      });
    });
  });
});
