/**
 * ExpiringCredentialsAlert Component Tests
 *
 * Tests for the credentials expiration alert including:
 * - Rendering with credentials at various expiration levels
 * - Severity grouping (critical, warning, info)
 * - Empty/loading states returning null
 * - Credential display and truncation
 */
import React from 'react';
import { render, screen } from '@/test-utils';
import '@testing-library/jest-dom';
import { ExpiringCredentialsAlert } from '../ExpiringCredentialsAlert';
import type { Credential } from '@/hooks/useProcedures';

// ============================================================================
// Helpers
// ============================================================================

function futureDate(daysFromNow: number): string {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  return date.toISOString();
}

function makeCredential(
  id: string,
  daysUntilExpiration: number
): Credential {
  return {
    id,
    personId: 'person-1',
    procedureId: 'proc-1',
    status: 'active',
    competencyLevel: 'qualified',
    issued_date: '2024-01-01T00:00:00Z',
    expirationDate: futureDate(daysUntilExpiration),
    last_verified_date: null,
    max_concurrent_residents: null,
    max_per_week: null,
    max_per_academicYear: null,
    notes: null,
    is_valid: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };
}

// ============================================================================
// Tests
// ============================================================================

describe('ExpiringCredentialsAlert', () => {
  describe('Rendering', () => {
    it('renders header with Expiring Credentials title', () => {
      const credentials = [makeCredential('cred-001', 5)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('Expiring Credentials')).toBeInTheDocument();
    });

    it('renders credential entries with truncated IDs', () => {
      const credentials = [makeCredential('abcdefgh-1234-5678', 5)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('Credential #abcdefgh')).toBeInTheDocument();
    });

    it('renders expiration days for a credential', () => {
      const credentials = [makeCredential('cred-001a', 3)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText(/Expires in 3 days/)).toBeInTheDocument();
    });

    it('renders singular "day" for 1 day', () => {
      const credentials = [makeCredential('cred-001b', 1)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText(/Expires in 1 day$/)).toBeInTheDocument();
    });
  });

  describe('Severity Grouping', () => {
    it('shows critical badge for credentials expiring within 7 days', () => {
      const credentials = [makeCredential('cred-crit', 3)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('1 critical')).toBeInTheDocument();
    });

    it('shows warning badge for credentials expiring within 14 days', () => {
      const credentials = [makeCredential('cred-warn', 10)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('1 warning')).toBeInTheDocument();
    });

    it('shows info/soon badge for credentials expiring after 14 days', () => {
      const credentials = [makeCredential('cred-info', 20)];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('1 soon')).toBeInTheDocument();
    });

    it('shows multiple severity badges simultaneously', () => {
      const credentials = [
        makeCredential('cred-c001', 3),  // critical
        makeCredential('cred-c002', 5),  // critical
        makeCredential('cred-w001', 10), // warning
        makeCredential('cred-i001', 20), // info
      ];
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.getByText('2 critical')).toBeInTheDocument();
      expect(screen.getByText('1 warning')).toBeInTheDocument();
      expect(screen.getByText('1 soon')).toBeInTheDocument();
    });
  });

  describe('Empty and Loading States', () => {
    it('returns null when credentials array is empty', () => {
      const { container } = render(
        <ExpiringCredentialsAlert credentials={[]} />
      );

      expect(container.firstChild).toBeNull();
    });

    it('returns null when isLoading is true', () => {
      const credentials = [makeCredential('cred-load', 5)];
      const { container } = render(
        <ExpiringCredentialsAlert credentials={credentials} isLoading />
      );

      expect(container.firstChild).toBeNull();
    });
  });

  describe('Truncation', () => {
    it('shows at most 10 credential entries', () => {
      const credentials = Array.from({ length: 12 }, (_, i) =>
        makeCredential(`cred-${String(i).padStart(8, '0')}`, 5)
      );
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      // Should show the +N more message
      expect(screen.getByText('+2 more expiring soon')).toBeInTheDocument();
    });

    it('does not show overflow message for 10 or fewer credentials', () => {
      const credentials = Array.from({ length: 10 }, (_, i) =>
        makeCredential(`cred-${String(i).padStart(8, '0')}`, 5)
      );
      render(<ExpiringCredentialsAlert credentials={credentials} />);

      expect(screen.queryByText(/more expiring soon/)).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('skips credentials without expiration dates', () => {
      const cred: Credential = {
        id: 'cred-noexp1',
        personId: 'person-1',
        procedureId: 'proc-1',
        status: 'active',
        competencyLevel: 'qualified',
        issued_date: null,
        expirationDate: null,
        last_verified_date: null,
        max_concurrent_residents: null,
        max_per_week: null,
        max_per_academicYear: null,
        notes: null,
        is_valid: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      // Even though there is 1 credential in the array, it has no expiration
      // The component checks credentials.length === 0 first, so it renders
      // but the credential won't appear in any severity group
      render(<ExpiringCredentialsAlert credentials={[cred]} />);

      // The component renders the header since credentials.length > 0
      expect(screen.getByText('Expiring Credentials')).toBeInTheDocument();
    });
  });
});
