'use client';

/**
 * Board Review Curriculum Planner
 *
 * Tripler AMC Family Medicine — 78 sessions, 202 FMCAs, 5 ABFM domains.
 * Mock-first frontend, backend integration later.
 *
 * @see docs/design/BOARD_REVIEW_CURRICULUM_DESIGN.md
 */

import { useState, useMemo } from 'react';
import {
  BookOpen,
  BarChart3,
  GraduationCap,
  LayoutDashboard,
  Search,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  CheckCircle2,
  Clock,
  Circle,
  Target,
} from 'lucide-react';

import {
  useBoardReviewDashboard,
  useBoardReviewBlocks,
  useBoardReviewAnalytics,
  useIteAnalysis,
  useUpdateSession,
  useBoardReviewFilters,
  getStatusColor,
  getStatusLabel,
  getDomainBgClass,
  getNextStatus,
} from '@/hooks/useBoardReview';
import { DOMAINS } from '@/data/board-review-data';
import { DomainTracker } from '@/components/analytics/DomainTracker';
import { HeatMapTable } from '@/components/analytics/HeatMapTable';
import { GapAnalysis } from '@/components/analytics/GapAnalysis';
import { TimelineStrip } from '@/components/analytics/TimelineStrip';
import type {
  BoardReviewTab,
  AbfmDomainCode,
  SessionStatus,
  BoardReviewBlock,
  BoardReviewSession,
  IteScores,
} from '@/types/board-review';

// ============ Types ============

interface TabConfig {
  id: BoardReviewTab;
  label: string;
  icon: React.ElementType;
  description: string;
}

// ============ Constants ============

const TABS: TabConfig[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, description: 'Overview & domain coverage' },
  { id: 'curriculum', label: 'Curriculum', icon: BookOpen, description: 'Block & session browser' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, description: 'Domain distribution & gaps' },
  { id: 'ite', label: 'ITE Mapping', icon: GraduationCap, description: 'Score-based remediation' },
];

const DOMAIN_FILTER_OPTIONS: { value: AbfmDomainCode | ''; label: string }[] = [
  { value: '', label: 'All Domains' },
  { value: 'ACD', label: 'ACD \u2014 Acute Care & Diagnosis' },
  { value: 'CCM', label: 'CCM \u2014 Chronic Care Management' },
  { value: 'UEC', label: 'UEC \u2014 Emergent & Urgent Care' },
  { value: 'PC', label: 'PC \u2014 Preventive Care' },
  { value: 'FOC', label: 'FOC \u2014 Foundations of Care' },
];

const STATUS_FILTER_OPTIONS: { value: SessionStatus | ''; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'not_started', label: 'Not Started' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
];

// ============ Sub-Components ============

function StatusIcon({ status }: { status: SessionStatus }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className="w-4 h-4 text-green-400" />;
    case 'in_progress':
      return <Clock className="w-4 h-4 text-amber-400" />;
    default:
      return <Circle className="w-4 h-4 text-slate-500" />;
  }
}

function SessionRow({
  session,
  onToggleStatus,
}: {
  session: BoardReviewSession;
  onToggleStatus: (sessionId: number, newStatus: SessionStatus) => void;
}) {
  const domainEntries = Object.entries(session.domains).filter(
    ([, fmcas]) => fmcas.length > 0
  );

  return (
    <div className="flex items-start gap-3 py-3 px-4 border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors">
      <button
        onClick={() => onToggleStatus(session.id, getNextStatus(session.status))}
        className="mt-0.5 flex-shrink-0 hover:scale-110 transition-transform"
        title={`Click to change: ${getStatusLabel(session.status)}`}
      >
        <StatusIcon status={session.status} />
      </button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-500 font-mono">#{session.id}</span>
          <span className="text-sm text-white font-medium">{session.title}</span>
          <span
            className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${getStatusColor(session.status)}`}
          >
            {getStatusLabel(session.status)}
          </span>
        </div>

        {/* Domain pills */}
        <div className="flex flex-wrap gap-1 mt-1.5">
          {domainEntries.map(([domainCode, fmcas]) => (
            <span
              key={domainCode}
              className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${getDomainBgClass(domainCode as AbfmDomainCode)}`}
              title={fmcas.join(', ')}
            >
              {domainCode} ({fmcas.length})
            </span>
          ))}
        </div>

        {/* Presenter / Date / Notes inline */}
        {(session.presenter || session.date || session.notes) && (
          <div className="flex gap-3 mt-1 text-xs text-slate-500">
            {session.presenter && <span>Presenter: {session.presenter}</span>}
            {session.date && <span>Date: {session.date}</span>}
            {session.notes && <span className="truncate max-w-xs">Notes: {session.notes}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function BlockCard({
  block,
  onToggleStatus,
  defaultExpanded,
}: {
  block: BoardReviewBlock;
  onToggleStatus: (sessionId: number, newStatus: SessionStatus) => void;
  defaultExpanded?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded ?? false);
  const completed = block.sessions.filter((s) => s.status === 'completed').length;
  const total = block.sessions.length;

  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{block.icon}</span>
          <div className="text-left">
            <span className="text-white font-semibold text-sm">
              Block {block.id}: {block.name}
            </span>
            <span className="text-xs text-slate-400 ml-2">
              {block.weeks}w &middot; {total} sessions &middot; {completed}/{total} done
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Mini progress bar */}
          <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500/70 rounded-full transition-all"
              style={{ width: `${total > 0 ? (completed / total) * 100 : 0}%` }}
            />
          </div>
          {expanded ? (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-slate-700/30">
          {block.sessions.map((session) => (
            <SessionRow
              key={session.id}
              session={session}
              onToggleStatus={onToggleStatus}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ============ Tab Panels ============

function DashboardTab() {
  const { data: dashboard, isLoading } = useBoardReviewDashboard();
  const { data: blocks } = useBoardReviewBlocks();

  const timelineBlocks = useMemo(() => {
    if (!blocks) return [];
    return blocks.map((b) => {
      const completed = b.sessions.filter((s) => s.status === 'completed').length;
      const total = b.sessions.length;
      const hasInProgress = b.sessions.some((s) => s.status === 'in_progress');
      let blockStatus: 'not_started' | 'in_progress' | 'completed' | 'mixed' = 'not_started';
      if (completed === total) blockStatus = 'completed';
      else if (hasInProgress || completed > 0) blockStatus = 'mixed';
      return {
        id: b.id,
        name: b.name,
        weeks: b.weeks,
        icon: b.icon,
        status: blockStatus,
        completedCount: completed,
        totalCount: total,
      };
    });
  }, [blocks]);

  if (isLoading || !dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Total Sessions</p>
          <p className="text-2xl font-bold text-white mt-1">{dashboard.totalSessions}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Completed</p>
          <p className="text-2xl font-bold text-green-400 mt-1">{dashboard.completedSessions}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">In Progress</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">{dashboard.inProgressSessions}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Completion</p>
          <p className="text-2xl font-bold text-indigo-400 mt-1">{dashboard.completionRate}%</p>
        </div>
      </div>

      {/* Current Block / Next Session */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Current Block</p>
          <p className="text-sm text-white mt-1">{dashboard.currentBlock ?? '\u2014'}</p>
        </div>
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider">Next Session</p>
          <p className="text-sm text-white mt-1 line-clamp-1">{dashboard.nextSession ?? '\u2014'}</p>
        </div>
      </div>

      {/* Domain Coverage */}
      <DomainTracker
        title="ABFM Domain Coverage"
        domains={dashboard.domainCoverage.map((d) => ({
          code: d.code,
          name: d.name,
          color: d.color,
          target: d.target,
          current: d.percentage,
          completed: d.completed,
          label: d.name,
        }))}
      />

      {/* Stacked bar comparison */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-4">
          Curriculum Distribution vs ABFM Target
        </h3>
        <div className="space-y-3">
          {dashboard.domainCoverage.map((d) => (
            <div key={d.code} className="flex items-center gap-3">
              <span
                className="w-8 text-xs font-bold text-right"
                style={{ color: d.color }}
              >
                {d.code}
              </span>
              <div className="flex-1 flex gap-1 h-6">
                {/* Actual */}
                <div
                  className="h-full rounded-l flex items-center justify-center text-[10px] font-bold text-white"
                  style={{
                    width: `${d.percentage}%`,
                    backgroundColor: d.color,
                    minWidth: d.percentage > 0 ? '24px' : '0',
                  }}
                >
                  {d.percentage > 5 ? `${d.percentage}%` : ''}
                </div>
                {/* Target marker */}
                <div
                  className="relative"
                  style={{ left: `${d.target - d.percentage}%` }}
                >
                  <div className="absolute -top-1 w-0.5 h-8 bg-white/40" title={`Target: ${d.target}%`} />
                </div>
              </div>
              <span className="w-12 text-xs text-slate-400 text-right">
                T:{d.target}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <TimelineStrip
        title="18-Month Curriculum Timeline"
        blocks={timelineBlocks}
      />
    </div>
  );
}

function CurriculumTab() {
  const { filters, setDomain, setStatus, setSearch } = useBoardReviewFilters();
  const { data: blocks, isLoading } = useBoardReviewBlocks(filters);
  const updateSession = useUpdateSession();

  const handleToggleStatus = (sessionId: number, newStatus: SessionStatus) => {
    updateSession.mutate({ sessionId, status: newStatus });
  };

  const sessionCount = blocks?.reduce((sum, b) => sum + b.sessions.length, 0) ?? 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filters.domain ?? ''}
          onChange={(e) => setDomain(e.target.value as AbfmDomainCode | '')}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          {DOMAIN_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <select
          value={filters.status ?? ''}
          onChange={(e) => setStatus(e.target.value as SessionStatus | '')}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search sessions, FMCAs..."
            value={filters.search ?? ''}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-400"
          />
        </div>
        <span className="text-sm text-slate-400">
          {sessionCount} session(s) in {blocks?.length ?? 0} block(s)
        </span>
      </div>

      {/* Block cards */}
      <div className="space-y-3">
        {blocks && blocks.length > 0 ? (
          blocks.map((block) => (
            <BlockCard
              key={block.id}
              block={block}
              onToggleStatus={handleToggleStatus}
              defaultExpanded={blocks.length <= 3}
            />
          ))
        ) : (
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-8 text-center">
            <BookOpen className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">No sessions match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
}

function AnalyticsTab() {
  const { data: analytics, isLoading } = useBoardReviewAnalytics();

  const domainColumns = Object.values(DOMAINS).map((d) => ({
    key: d.code,
    label: d.code,
    color: d.color,
  }));

  const blockRows = analytics?.blockDomainCounts.map((b) => b.blockName) ?? [];

  const fmcaGapItems = useMemo(() => {
    if (!analytics) return [];
    return analytics.fmcaGaps.map((g) => ({
      name: g.fmca,
      category: DOMAINS[g.domain]?.name ?? g.domain,
      categoryColor: DOMAINS[g.domain]?.color,
      covered: g.covered,
      count: g.sessionIds.length,
    }));
  }, [analytics]);

  if (isLoading || !analytics) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Per-block domain distribution */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-4">
          Per-Block Domain Coverage
        </h3>
        <div className="space-y-2">
          {analytics.blockDomainCounts.map((block) => {
            const total = Object.values(block.counts).reduce((s, v) => s + v, 0);
            return (
              <div key={block.blockId} className="flex items-center gap-2">
                <span className="w-36 text-xs text-slate-300 truncate text-right">
                  {block.blockName}
                </span>
                <div className="flex-1 flex h-5 rounded overflow-hidden">
                  {Object.entries(block.counts).map(([code, count]) => {
                    if (count === 0) return null;
                    const pct = total > 0 ? (count / total) * 100 : 0;
                    return (
                      <div
                        key={code}
                        className="h-full flex items-center justify-center text-[9px] font-bold text-white"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: DOMAINS[code as AbfmDomainCode]?.color ?? '#6B7280',
                          minWidth: '16px',
                        }}
                        title={`${code}: ${count}`}
                      >
                        {pct > 10 ? code : ''}
                      </div>
                    );
                  })}
                </div>
                <span className="w-6 text-xs text-slate-500 text-right">{total}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Heat map */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <HeatMapTable
          title="Domain \u00d7 Block Heat Map"
          cells={analytics.heatMap}
          columns={domainColumns}
          rows={blockRows}
        />
      </div>

      {/* FMCA Gap Analysis */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
        <GapAnalysis
          title="FMCA Gap Analysis"
          items={fmcaGapItems}
          coveredLabel="covered"
          uncoveredLabel="gap"
        />
      </div>
    </div>
  );
}

function IteTab() {
  const [scores, setScores] = useState<IteScores>({
    /* eslint-disable @typescript-eslint/naming-convention -- ABFM domain codes */
    ACD: null, CCM: null, UEC: null, PC: null, FOC: null,
    /* eslint-enable @typescript-eslint/naming-convention */
  });
  const [submitted, setSubmitted] = useState(false);
  const { data: remediation, isLoading } = useIteAnalysis(submitted ? scores : null);

  const handleScoreChange = (domain: AbfmDomainCode, value: string) => {
    const num = value === '' ? null : Math.min(100, Math.max(0, parseInt(value, 10)));
    setScores((prev) => ({ ...prev, [domain]: isNaN(num as number) ? null : num }));
    setSubmitted(false);
  };

  const handleAnalyze = () => {
    setSubmitted(true);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-400 bg-red-500/10 border-red-500/30';
      case 'medium':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
      default:
        return 'text-green-400 bg-green-500/10 border-green-500/30';
    }
  };

  return (
    <div className="space-y-6">
      {/* Score input */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-2">ITE Domain Scores</h3>
        <p className="text-sm text-slate-400 mb-4">
          Enter your ITE domain percentile scores. The tool will highlight which curriculum
          blocks and sessions to prioritize for remediation.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-4 mb-4">
          {Object.values(DOMAINS).map((domain) => (
            <div key={domain.code}>
              <label
                className="block text-xs font-semibold mb-1"
                style={{ color: domain.color }}
              >
                {domain.code} &mdash; {domain.name}
              </label>
              <input
                type="number"
                min={0}
                max={100}
                placeholder="Percentile"
                value={scores[domain.code] ?? ''}
                onChange={(e) => handleScoreChange(domain.code, e.target.value)}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
              />
            </div>
          ))}
        </div>

        <button
          onClick={handleAnalyze}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors text-sm font-medium"
        >
          <Target className="w-4 h-4" />
          Analyze &amp; Generate Remediation Plan
        </button>
      </div>

      {/* Remediation results */}
      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
        </div>
      )}

      {remediation && (
        <div className="space-y-4">
          {remediation
            .sort((a, b) => {
              const order = { high: 0, medium: 1, low: 2 };
              return order[a.priority] - order[b.priority];
            })
            .map((item) => (
              <div
                key={item.domain}
                className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span
                      className="text-sm font-bold"
                      style={{ color: DOMAINS[item.domain]?.color }}
                    >
                      {item.domain}
                    </span>
                    <span className="text-sm text-white">{item.domainName}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-400">
                      Score: {item.score !== null ? `${item.score}th` : '\u2014'}
                    </span>
                    <span
                      className={`px-2 py-0.5 text-xs font-medium rounded border ${getPriorityColor(item.priority)}`}
                    >
                      {item.priority} priority
                    </span>
                  </div>
                </div>

                {item.sessions.length > 0 ? (
                  <div className="space-y-1">
                    <p className="text-xs text-slate-400 mb-2">
                      {item.sessions.length} session(s) mapped to this domain:
                    </p>
                    {item.sessions.slice(0, 10).map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center gap-2 text-xs py-1"
                      >
                        <StatusIcon status={s.status} />
                        <span className="text-slate-500 font-mono">#{s.id}</span>
                        <span className="text-white">{s.title}</span>
                        <span className="text-slate-500">({s.blockName})</span>
                      </div>
                    ))}
                    {item.sessions.length > 10 && (
                      <p className="text-xs text-slate-500">
                        +{item.sessions.length - 10} more sessions
                      </p>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">
                    No specific sessions mapped (cross-domain review sessions cover all domains)
                  </p>
                )}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

// ============ Main Component ============

export default function BoardReviewPage() {
  const [activeTab, setActiveTab] = useState<BoardReviewTab>('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-indigo-500/10 rounded-lg">
              <BookOpen className="w-8 h-8 text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                Board Review Curriculum Planner
              </h1>
              <p className="text-sm text-slate-400">
                Tripler AMC Family Medicine &mdash; 78 Sessions, 202 FMCAs, 5 ABFM Domains
              </p>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 mt-4 -mb-px overflow-x-auto" role="tablist">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`${tab.id}-panel`}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-slate-900 text-white border-t border-x border-slate-700'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
                  }`}
                  title={tab.description}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div role="tabpanel" id={`${activeTab}-panel`}>
          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'curriculum' && <CurriculumTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
          {activeTab === 'ite' && <IteTab />}
        </div>
      </main>

      {/* Mock Data Banner */}
      <div className="fixed bottom-4 right-4 px-4 py-2 bg-amber-600/90 text-white rounded-lg text-sm shadow-lg">
        Demo Mode &mdash; Using Mock Data
      </div>
    </div>
  );
}
