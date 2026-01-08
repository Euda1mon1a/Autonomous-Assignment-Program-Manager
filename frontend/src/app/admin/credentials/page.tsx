'use client';

/**
 * Admin Credentials Page
 *
 * Management interface for procedure credentialing with:
 * - Faculty × Procedure matrix view
 * - Expiring credentials alerts
 * - Filter by specialty/category
 */
import { useState, useCallback } from 'react';
import {
  Award,
  RefreshCw,
  Filter,
  AlertTriangle,
} from 'lucide-react';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { CredentialMatrix } from '@/components/admin/CredentialMatrix';
import { ExpiringCredentialsAlert } from '@/components/admin/ExpiringCredentialsAlert';
import { usePeople } from '@/hooks/usePeople';
import {
  useProcedures,
  useCredentials,
  useProcedureSpecialties,
  useExpiringCredentials,
} from '@/hooks/useProcedures';
import { useToast } from '@/contexts/ToastContext';

// ============================================================================
// Types
// ============================================================================

interface CredentialFilters {
  specialty: string;
  category: string;
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function AdminCredentialsPage() {
  const { toast } = useToast();

  // State
  const [filters, setFilters] = useState<CredentialFilters>({
    specialty: '',
    category: '',
  });
  const [showExpiringOnly, setShowExpiringOnly] = useState(false);

  // Queries
  const {
    data: facultyData,
    isLoading: facultyLoading,
    refetch: refetchFaculty,
  } = usePeople({ role: 'faculty' });

  const {
    data: proceduresData,
    isLoading: proceduresLoading,
    refetch: refetchProcedures,
  } = useProcedures(
    filters.specialty ? { specialty: filters.specialty } : undefined
  );

  const {
    data: credentialsData,
    isLoading: credentialsLoading,
    refetch: refetchCredentials,
  } = useCredentials();

  const { data: specialties } = useProcedureSpecialties();

  const {
    data: expiringData,
    isLoading: expiringLoading,
  } = useExpiringCredentials(30);

  // Handlers
  const handleRefresh = useCallback(() => {
    refetchFaculty();
    refetchProcedures();
    refetchCredentials();
    toast.info('Refreshing credentials...');
  }, [refetchFaculty, refetchProcedures, refetchCredentials, toast]);

  const isLoading = facultyLoading || proceduresLoading || credentialsLoading;

  const faculty = facultyData?.items || [];
  const procedures = proceduresData?.items || [];
  const credentials = credentialsData?.items || [];
  const expiringCredentials = expiringData?.items || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg">
                <Award className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">
                  Procedure Credentials
                </h1>
                <p className="text-sm text-slate-400">
                  Manage faculty procedure credentialing
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="p-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                title="Refresh"
              >
                <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Expiring Alerts Section */}
        {expiringCredentials.length > 0 && (
          <ExpiringCredentialsAlert
            credentials={expiringCredentials}
            isLoading={expiringLoading}
          />
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Specialty Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filters.specialty}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, specialty: e.target.value }))
              }
              className="px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            >
              <option value="">All Specialties</option>
              {specialties?.map((specialty) => (
                <option key={specialty} value={specialty}>
                  {specialty}
                </option>
              ))}
            </select>
          </div>

          {/* Show Expiring Toggle */}
          <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={showExpiringOnly}
              onChange={(e) => setShowExpiringOnly(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-amber-500 focus:ring-amber-500"
            />
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Show expiring only
          </label>

          {/* Stats */}
          <div className="flex-1" />
          <div className="text-sm text-slate-400">
            {faculty.length} faculty · {procedures.length} procedures · {credentials.length} credentials
          </div>
        </div>

        {/* Credential Matrix */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner />
          </div>
        ) : (
          <CredentialMatrix
            faculty={faculty}
            procedures={procedures}
            credentials={credentials}
            showExpiringOnly={showExpiringOnly}
          />
        )}
      </main>
    </div>
  );
}
