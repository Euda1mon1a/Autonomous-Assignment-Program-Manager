'use client';

import { useState, useCallback } from 'react';
import {
  AlertTriangle,
  AlertOctagon,
  AlertCircle,
  Info,
  Check,
  Clock,
  TrendingUp,
  TrendingDown,
  BarChart3,
  History,
  Layers,
  X,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { ConflictList } from './ConflictList';
import { ConflictResolutionSuggestions } from './ConflictResolutionSuggestions';
import { ManualOverrideModal } from './ManualOverrideModal';
import { ConflictHistory, ConflictHistoryTimeline } from './ConflictHistory';
import { BatchResolution } from './BatchResolution';
import { useConflictStatistics, useConflicts } from './hooks';
import type { Conflict, ConflictFilters } from './types';

// ============================================================================
// Props
// ============================================================================

interface ConflictDashboardProps {
  initialFilters?: ConflictFilters;
}

// ============================================================================
// View Types
// ============================================================================

type ActiveView = 'list' | 'suggestions' | 'history' | 'batch';

// ============================================================================
// Component
// ============================================================================

export function ConflictDashboard({ initialFilters }: ConflictDashboardProps) {
  // State
  const [activeView, setActiveView] = useState<ActiveView>('list');
  const [selectedConflict, setSelectedConflict] = useState<Conflict | null>(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [batchConflicts, setBatchConflicts] = useState<Conflict[]>([]);

  // Queries
  const { data: statistics, isLoading: statsLoading } = useConflictStatistics();
  const { data: conflictsData, refetch: refetchConflicts } = useConflicts(initialFilters);

  // Handlers
  const handleConflictSelect = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setActiveView('suggestions');
  }, []);

  const handleViewSuggestions = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setActiveView('suggestions');
  }, []);

  const handleViewHistory = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setActiveView('history');
  }, []);

  const handleOverride = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setShowOverrideModal(true);
  }, []);

  const handleIgnore = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setShowOverrideModal(true);
  }, []);

  const handleResolve = useCallback((conflict: Conflict) => {
    setSelectedConflict(conflict);
    setActiveView('suggestions');
  }, []);

  const handleBatchSelect = useCallback((conflicts: Conflict[]) => {
    setBatchConflicts(conflicts);
    setActiveView('batch');
  }, []);

  const handleResolved = useCallback(() => {
    setSelectedConflict(null);
    setActiveView('list');
    refetchConflicts();
  }, [refetchConflicts]);

  const handleClosePanel = useCallback(() => {
    setSelectedConflict(null);
    setActiveView('list');
  }, []);

  const handleBatchComplete = useCallback(() => {
    setBatchConflicts([]);
    setActiveView('list');
    refetchConflicts();
  }, [refetchConflicts]);

  // Stats summary
  const unresolvedCount = statistics?.by_status?.unresolved || 0;
  const criticalCount = statistics?.by_severity?.critical || 0;
  const resolutionRate = statistics?.resolution_rate || 0;
  const trendingUp = statistics?.trending_up ?? false;

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Header with statistics */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Conflict Resolution</h1>
              <p className="text-sm text-gray-500 mt-1">
                Detect, review, and resolve scheduling conflicts
              </p>
            </div>
            <button
              onClick={() => refetchConflicts()}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Statistics cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Unresolved conflicts */}
            <StatCard
              label="Unresolved Conflicts"
              value={unresolvedCount}
              icon={AlertTriangle}
              color="amber"
              loading={statsLoading}
            />

            {/* Critical conflicts */}
            <StatCard
              label="Critical"
              value={criticalCount}
              icon={AlertOctagon}
              color="red"
              loading={statsLoading}
            />

            {/* Resolution rate */}
            <StatCard
              label="Resolution Rate"
              value={`${Math.round(resolutionRate)}%`}
              icon={Check}
              color="green"
              loading={statsLoading}
            />

            {/* Trend */}
            <StatCard
              label="Trend"
              value={trendingUp ? 'Increasing' : 'Stable'}
              icon={trendingUp ? TrendingUp : TrendingDown}
              color={trendingUp ? 'red' : 'green'}
              loading={statsLoading}
            />
          </div>
        </div>

        {/* Secondary nav */}
        <div className="px-6 border-t">
          <nav className="flex gap-4 -mb-px">
            <NavTab
              label="All Conflicts"
              icon={Layers}
              isActive={activeView === 'list'}
              onClick={() => {
                setSelectedConflict(null);
                setActiveView('list');
              }}
            />
            <NavTab
              label="Patterns"
              icon={BarChart3}
              isActive={activeView === 'history' && !selectedConflict}
              onClick={() => {
                setSelectedConflict(null);
                setActiveView('history');
              }}
            />
          </nav>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - List */}
        <div className={`
          ${activeView === 'batch' ? 'hidden' : 'flex'}
          flex-col bg-white border-r
          ${selectedConflict ? 'w-1/2' : 'w-full'}
          transition-all duration-200
        `}>
          <ConflictList
            initialFilters={initialFilters}
            onConflictSelect={handleConflictSelect}
            onResolve={handleResolve}
            onViewSuggestions={handleViewSuggestions}
            onViewHistory={handleViewHistory}
            onOverride={handleOverride}
            onIgnore={handleIgnore}
            onBatchSelect={handleBatchSelect}
            selectable
          />
        </div>

        {/* Right panel - Details/Suggestions/History */}
        {selectedConflict && activeView !== 'batch' && (
          <div className="w-1/2 flex flex-col bg-white">
            {/* Panel header */}
            <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
              <div className="flex items-center gap-2">
                {activeView === 'suggestions' && (
                  <>
                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                    <span className="font-medium">Resolution Suggestions</span>
                  </>
                )}
                {activeView === 'history' && (
                  <>
                    <History className="w-5 h-5 text-blue-500" />
                    <span className="font-medium">Conflict History</span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2">
                {activeView === 'suggestions' && (
                  <button
                    onClick={() => setActiveView('history')}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <History className="w-4 h-4 inline mr-1" />
                    History
                  </button>
                )}
                {activeView === 'history' && (
                  <button
                    onClick={() => setActiveView('suggestions')}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    <AlertTriangle className="w-4 h-4 inline mr-1" />
                    Suggestions
                  </button>
                )}
                <button
                  onClick={handleClosePanel}
                  className="p-1.5 hover:bg-gray-200 rounded-lg"
                  aria-label="Close panel"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Panel content */}
            <div className="flex-1 overflow-hidden">
              {activeView === 'suggestions' && (
                <ConflictResolutionSuggestions
                  conflict={selectedConflict}
                  onResolved={handleResolved}
                  onClose={handleClosePanel}
                />
              )}
              {activeView === 'history' && (
                <div className="h-full overflow-y-auto p-4">
                  <ConflictHistoryTimeline conflictId={selectedConflict.id} />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Patterns view (when no conflict selected and in history mode) */}
        {!selectedConflict && activeView === 'history' && (
          <div className="w-full bg-white">
            <ConflictHistory showPatterns />
          </div>
        )}

        {/* Batch resolution view */}
        {activeView === 'batch' && batchConflicts.length > 0 && (
          <div className="w-full bg-white">
            <BatchResolution
              conflicts={batchConflicts}
              onComplete={handleBatchComplete}
              onCancel={() => {
                setBatchConflicts([]);
                setActiveView('list');
              }}
            />
          </div>
        )}
      </div>

      {/* Override modal */}
      <ManualOverrideModal
        isOpen={showOverrideModal}
        onClose={() => {
          setShowOverrideModal(false);
          setSelectedConflict(null);
        }}
        conflict={selectedConflict}
        onOverrideCreated={() => {
          setShowOverrideModal(false);
          setSelectedConflict(null);
          refetchConflicts();
        }}
      />
    </div>
  );
}

// ============================================================================
// Stat Card Component
// ============================================================================

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'amber' | 'red' | 'green' | 'blue' | 'gray';
  loading?: boolean;
}

function StatCard({ label, value, icon: Icon, color, loading }: StatCardProps) {
  const colorStyles: Record<string, { bg: string; icon: string; text: string }> = {
    amber: { bg: 'bg-amber-50', icon: 'text-amber-500', text: 'text-amber-900' },
    red: { bg: 'bg-red-50', icon: 'text-red-500', text: 'text-red-900' },
    green: { bg: 'bg-green-50', icon: 'text-green-500', text: 'text-green-900' },
    blue: { bg: 'bg-blue-50', icon: 'text-blue-500', text: 'text-blue-900' },
    gray: { bg: 'bg-gray-50', icon: 'text-gray-500', text: 'text-gray-900' },
  };

  const styles = colorStyles[color];

  return (
    <div className={`p-4 rounded-lg ${styles.bg}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">{label}</span>
        <Icon className={`w-5 h-5 ${styles.icon}`} />
      </div>
      {loading ? (
        <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
      ) : (
        <p className={`text-2xl font-bold ${styles.text}`}>{value}</p>
      )}
    </div>
  );
}

// ============================================================================
// Nav Tab Component
// ============================================================================

interface NavTabProps {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  isActive: boolean;
  onClick: () => void;
  badge?: number;
}

function NavTab({ label, icon: Icon, isActive, onClick, badge }: NavTabProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors
        ${isActive
          ? 'border-blue-500 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
        }
      `}
    >
      <Icon className="w-4 h-4" />
      {label}
      {badge !== undefined && badge > 0 && (
        <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
          {badge}
        </span>
      )}
    </button>
  );
}
