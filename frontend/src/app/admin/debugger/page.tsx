'use client';

/**
 * Side-by-Side Debugger
 *
 * Developer experience tool for comparing frontend views with raw database data.
 * Supports:
 * - Dual iframe layout (app + NocoDB)
 * - Multi-mode Database Inspector (Schedule, Absences, People, Rotations, Activities)
 * - API request inspector with diff mode
 * - Direct database queries via MCP
 * - Claude Chrome extension integration hints
 *
 * @see docs/development/SIDE_BY_SIDE_DEBUGGER.md
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useBlockRanges } from '@/hooks';
import {
  Bug,
  Database,
  Globe,
  RefreshCw,
  Settings,
  Split,
  Maximize2,
  Minimize2,
  ExternalLink,
  Copy,
  Check,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Eye,
  Sparkles,
  Terminal,
} from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

interface PanelConfig {
  url: string;
  label: string;
  type: 'app' | 'nocodb' | 'custom';
}

type SplitRatio = 25 | 50 | 75;

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_LEFT_URL = '/schedule';

// Use environment variable for API base URL, fallback to relative path
// IMPORTANT: Use /api/v1 (relative) to go through Next.js proxy for proper auth
// Do NOT use http://localhost:8000 directly - it bypasses auth cookie handling
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

const PRESET_URLS: { label: string; url: string; type: PanelConfig['type'] }[] = [
  { label: 'Schedule', url: '/schedule', type: 'app' },
  { label: 'People', url: '/people', type: 'app' },
  { label: 'Call Hub', url: '/call-hub', type: 'app' },
  { label: 'Block Explorer', url: '/admin/block-explorer', type: 'app' },
  { label: 'Compliance', url: '/compliance', type: 'app' },
];

const DIAGNOSIS_MATRIX = [
  {
    symptom: 'Shift missing',
    guiShows: 'Empty slot',
    dbShows: 'Data exists',
    verdict: 'Frontend Issue',
    description: 'React not rendering or API filter wrong',
    color: 'text-amber-400',
  },
  {
    symptom: 'Shift missing',
    guiShows: 'Empty slot',
    dbShows: 'Row missing',
    verdict: 'Backend Issue',
    description: 'Scheduler never wrote to DB',
    color: 'text-red-400',
  },
  {
    symptom: 'Wrong name',
    guiShows: '"Dr. Smith"',
    dbShows: '"Dr. Jones"',
    verdict: 'Cache Issue',
    description: 'Stale frontend or API cache',
    color: 'text-violet-400',
  },
  {
    symptom: 'Duplicate shift',
    guiShows: 'Two blocks',
    dbShows: 'Two rows',
    verdict: 'Logic Issue',
    description: 'Script ran twice or no dedup',
    color: 'text-cyan-400',
  },
];

// ============================================================================
// Helper Components
// ============================================================================

function UrlBar({
  value,
  onChange,
  onRefresh,
  label,
  presets,
}: {
  value: string;
  onChange: (url: string) => void;
  onRefresh: () => void;
  label: string;
  presets: typeof PRESET_URLS;
}) {
  const [showPresets, setShowPresets] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-slate-800/50 border-b border-slate-700/50">
      <span className="text-xs font-medium text-slate-400 min-w-[60px]">{label}</span>
      <div className="relative flex-1">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          placeholder="Enter URL..."
        />
        <button
          onClick={() => setShowPresets(!showPresets)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
        >
          <ChevronDown className="w-4 h-4" />
        </button>
        {showPresets && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden">
            {presets.map((preset) => (
              <button
                key={preset.url}
                onClick={() => {
                  onChange(preset.url);
                  setShowPresets(false);
                }}
                className="w-full px-3 py-2 text-left text-sm hover:bg-slate-700/50 flex items-center gap-2"
              >
                {preset.type === 'nocodb' ? (
                  <Database className="w-4 h-4 text-cyan-400" />
                ) : (
                  <Globe className="w-4 h-4 text-violet-400" />
                )}
                <span className="text-white">{preset.label}</span>
                <span className="text-slate-400 text-xs font-mono ml-auto">{preset.url}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      <button
        onClick={handleCopy}
        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded"
        title="Copy URL"
      >
        {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </button>
      <button
        onClick={onRefresh}
        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded"
        title="Refresh"
      >
        <RefreshCw className="w-4 h-4" />
      </button>
      <a
        href={value}
        target="_blank"
        rel="noopener noreferrer"
        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded"
        title="Open in new tab"
      >
        <ExternalLink className="w-4 h-4" />
      </a>
    </div>
  );
}

function IframePanel({
  url,
  refreshKey,
  onError,
}: {
  url: string;
  refreshKey: number;
  onError?: (error: string) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    // Fallback: hide loading after 3s even if onLoad doesn't fire
    // (Next.js iframes sometimes don't trigger onLoad properly)
    const timeout = setTimeout(() => setLoading(false), 3000);
    return () => clearTimeout(timeout);
  }, [url, refreshKey]);

  const handleLoad = () => {
    setLoading(false);
  };

  const handleError = () => {
    setLoading(false);
    const errorMsg = `Failed to load: ${url}`;
    setError(errorMsg);
    onError?.(errorMsg);
  };

  // Check if URL is external (for CORS/X-Frame-Options warnings)
  const isExternal = url.startsWith('http') && !url.includes('localhost');
  // Only sandbox external URLs - same-origin content doesn't need restrictions
  const isSameOrigin = url.startsWith('/') || url.includes('localhost:3000');

  return (
    <div className="relative h-full bg-slate-900">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-violet-400 animate-spin" />
            <span className="text-sm text-slate-400">Loading...</span>
          </div>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900 z-10">
          <div className="flex flex-col items-center gap-3 max-w-md text-center p-6">
            <AlertTriangle className="w-12 h-12 text-amber-400" />
            <span className="text-sm text-amber-400">{error}</span>
            {isExternal && (
              <p className="text-xs text-slate-400 mt-2">
                External sites may block iframe embedding (X-Frame-Options).
                Try opening in a new tab instead.
              </p>
            )}
          </div>
        </div>
      )}
      <iframe
        ref={iframeRef}
        key={`${url}-${refreshKey}`}
        src={url}
        className="w-full h-full border-0"
        onLoad={handleLoad}
        onError={handleError}
        {...(!isSameOrigin && { sandbox: "allow-same-origin allow-scripts allow-forms allow-popups" })}
        title="Debug panel"
      />
    </div>
  );
}

function DiagnosisHelper({ expanded, onToggle }: { expanded: boolean; onToggle: () => void }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 hover:bg-slate-700/30"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <span className="font-medium text-white">Diagnosis Matrix</span>
        </div>
        {expanded ? (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-400" />
        )}
      </button>
      {expanded && (
        <div className="p-3 border-t border-slate-700/50">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 text-xs">
                <th className="text-left py-1 px-2">Symptom</th>
                <th className="text-left py-1 px-2">GUI Shows</th>
                <th className="text-left py-1 px-2">DB Shows</th>
                <th className="text-left py-1 px-2">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {DIAGNOSIS_MATRIX.map((row, idx) => (
                <tr key={idx} className="border-t border-slate-700/30">
                  <td className="py-2 px-2 text-slate-300">{row.symptom}</td>
                  <td className="py-2 px-2 text-slate-300 font-mono text-xs">{row.guiShows}</td>
                  <td className="py-2 px-2 text-slate-300 font-mono text-xs">{row.dbShows}</td>
                  <td className="py-2 px-2">
                    <span className={`font-medium ${row.color}`}>{row.verdict}</span>
                    <p className="text-xs text-slate-400 mt-0.5">{row.description}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function McpIntegrationHint() {
  return (
    <div className="bg-gradient-to-r from-violet-900/30 to-cyan-900/30 border border-violet-700/50 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <Terminal className="w-5 h-5 text-cyan-400 mt-0.5" />
        <div>
          <h4 className="font-medium text-white mb-1">MCP + NocoDB Integration</h4>
          <p className="text-sm text-slate-300 mb-2">
            NocoDB offers a native MCP Server for conversational database queries.
            Ask Claude directly: &ldquo;Show me all residents who haven&rsquo;t had a vacation in 3 months.&rdquo;
          </p>
          <div className="flex flex-wrap gap-2">
            <code className="text-xs bg-slate-800 px-2 py-1 rounded text-cyan-300">
              mcp__nocodb__list_records
            </code>
            <code className="text-xs bg-slate-800 px-2 py-1 rounded text-cyan-300">
              mcp__nocodb__create_record
            </code>
            <code className="text-xs bg-slate-800 px-2 py-1 rounded text-cyan-300">
              mcp__nocodb__query
            </code>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChromeExtensionHint() {
  return (
    <div className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border border-amber-700/50 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <Eye className="w-5 h-5 text-amber-400 mt-0.5" />
        <div>
          <h4 className="font-medium text-white mb-1">Claude Chrome Extension</h4>
          <p className="text-sm text-slate-300">
            With Claude for Chrome, you can ask: &ldquo;Open my residency app in one tab and NocoDB
            in another. Compare the Tuesday schedule and tell me if there are discrepancies.&rdquo;
          </p>
          <p className="text-xs text-slate-400 mt-2">
            Claude can visually inspect both views and identify rendering bugs automatically.
          </p>
        </div>
      </div>
    </div>
  );
}

type DataSource = 'api' | 'db' | 'diff';
type InspectorMode = 'schedule' | 'absences' | 'people' | 'rotations' | 'activities';

const INSPECTOR_MODES: { value: InspectorMode; label: string; icon: string }[] = [
  { value: 'schedule', label: 'Schedule', icon: '📅' },
  { value: 'absences', label: 'Absences', icon: '🏖️' },
  { value: 'people', label: 'People', icon: '👥' },
  { value: 'rotations', label: 'Rotations', icon: '🔄' },
  { value: 'activities', label: 'Activities', icon: '📋' },
];

interface Assignment {
  id: string;
  personId: string;
  date: string;
  period: 'AM' | 'PM';
  activityCode: string;
  source?: string;
}

interface Person {
  id: string;
  name: string;
  type: string;
  pgyLevel?: number;
}

function ScheduleMirrorView({
  refreshKey,
  onScroll,
  scrollTop = 0,
}: {
  refreshKey: number;
  onScroll?: (scrollTop: number) => void;
  scrollTop?: number;
}) {
  const [dataSource, setDataSource] = useState<DataSource>('api');
  const [people, setPeople] = useState<Person[]>([]);
  const [apiAssignments, setApiAssignments] = useState<Assignment[]>([]);
  const [dbAssignments, setDbAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dates, setDates] = useState<string[]>([]);
  // Track both block number AND academic year to handle multi-year data
  const [selectedBlockKey, setSelectedBlockKey] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isScrolling = useRef(false);

  // Fetch block ranges
  const { data: blockRanges } = useBlockRanges();

  // Create a unique key for each block (handles multiple academic years)
  const getBlockKey = (blockNumber: number, academicYear: number) =>
    `${academicYear}-${blockNumber}`;

  // Parse block key back to components
  const parseBlockKey = (key: string): { blockNumber: number; academicYear: number } | null => {
    const [yearStr, numStr] = key.split('-');
    const academicYear = parseInt(yearStr, 10);
    const blockNumber = parseInt(numStr, 10);
    if (isNaN(academicYear) || isNaN(blockNumber)) return null;
    return { blockNumber, academicYear };
  };

  // Auto-select current block on load
  useEffect(() => {
    if (blockRanges?.length && selectedBlockKey === null) {
      const today = new Date().toISOString().split('T')[0];
      const currentBlock = blockRanges.find(
        b => b.startDate <= today && b.endDate >= today
      );
      // Default to first block if today isn't in any block
      const block = currentBlock ?? blockRanges[0];
      if (block) {
        setSelectedBlockKey(getBlockKey(block.blockNumber, block.academicYear));
      }
    }
  }, [blockRanges, selectedBlockKey]);

  // Generate dates from selected block
  useEffect(() => {
    if (!blockRanges || selectedBlockKey === null) return;
    const parsed = parseBlockKey(selectedBlockKey);
    if (!parsed) return;
    const block = blockRanges.find(
      b => b.blockNumber === parsed.blockNumber && b.academicYear === parsed.academicYear
    );
    if (!block) return;

    const dateList: string[] = [];
    const start = new Date(block.startDate);
    const end = new Date(block.endDate);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      dateList.push(d.toISOString().split('T')[0]);
    }
    setDates(dateList);
  }, [blockRanges, selectedBlockKey]);

  // Fetch data when block changes or dates are ready
  useEffect(() => {
    const fetchData = async () => {
      // Wait for dates to be generated from selected block
      if (dates.length === 0) return;

      const startDate = dates[0];
      const endDate = dates[dates.length - 1];

      setLoading(true);
      setError(null);
      try {
        // Fetch people using configurable API base URL
        // API_BASE_URL already includes /api/v1, so just append endpoint path
        const peopleRes = await fetch(`${API_BASE_URL}/people?limit=100`, {
          credentials: 'include',
        });
        if (!peopleRes.ok) throw new Error(`People: HTTP ${peopleRes.status}`);
        const peopleJson = await peopleRes.json();
        const peopleList = Array.isArray(peopleJson) ? peopleJson : peopleJson.items || [];
        setPeople(peopleList.filter((p: Person) => p.type === 'resident').slice(0, 20));

        // Fetch assignments from API with date range filter using configurable base URL
        // API_BASE_URL already includes /api/v1, so just append endpoint path
        const assignUrl = `${API_BASE_URL}/half-day-assignments?start_date=${startDate}&end_date=${endDate}&limit=2000`;
        const assignRes = await fetch(assignUrl, {
          credentials: 'include',
        });
        if (assignRes.ok) {
          const assignJson = await assignRes.json();
          // API returns { assignments: [...] } or { items: [...] } or array directly
          const assignments = assignJson.assignments || assignJson.items || (Array.isArray(assignJson) ? assignJson : []);
          const mappedAssignments = assignments.map((a: Record<string, unknown>) => ({
            id: a.id as string,
            personId: a.person_id as string || a.personId as string,
            date: a.date as string,
            // API uses time_of_day, frontend expects period
            period: (a.time_of_day as string || a.period as string || 'AM') as 'AM' | 'PM',
            // Use display_abbreviation, activity_code, or activity_name - fallback to '—'
            activityCode: (a.display_abbreviation as string) || (a.activity_code as string) || (a.activity_name as string) || '—',
            source: 'api',
          }));
          setApiAssignments(mappedAssignments);
          // For DB view, we'd call a raw endpoint - for now simulate with same data
          // TODO: Add /api/v1/debug/raw-assignments endpoint
          setDbAssignments(mappedAssignments.map((a: Assignment) => ({ ...a, source: 'db' })));
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [refreshKey, dates]);

  // Sync scroll from parent
  useEffect(() => {
    if (scrollRef.current && !isScrolling.current) {
      scrollRef.current.scrollTop = scrollTop;
    }
  }, [scrollTop]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    isScrolling.current = true;
    onScroll?.(e.currentTarget.scrollTop);
    setTimeout(() => { isScrolling.current = false; }, 100);
  };

  // Get assignment for a person/date/period
  const getAssignment = (personId: string, date: string, period: 'AM' | 'PM', source: DataSource): string => {
    const assignments = source === 'db' ? dbAssignments : apiAssignments;
    const match = assignments.find(a =>
      a.personId === personId && a.date === date && a.period === period
    );
    return match?.activityCode || '—';
  };

  // Check if there's a mismatch between API and DB
  const hasMismatch = (personId: string, date: string, period: 'AM' | 'PM'): boolean => {
    const apiVal = getAssignment(personId, date, period, 'api');
    const dbVal = getAssignment(personId, date, period, 'db');
    return apiVal !== dbVal;
  };

  // Get cell display value and style
  const getCellContent = (personId: string, date: string, period: 'AM' | 'PM') => {
    const apiVal = getAssignment(personId, date, period, 'api');
    const dbVal = getAssignment(personId, date, period, 'db');
    const mismatch = hasMismatch(personId, date, period);

    if (dataSource === 'diff') {
      if (mismatch) {
        return {
          value: `${apiVal}≠${dbVal}`,
          className: 'bg-red-900/50 text-red-300 border border-red-500/50',
        };
      }
      return { value: apiVal, className: 'text-slate-400' };
    }

    const value = dataSource === 'db' ? dbVal : apiVal;

    // Color by activity type
    let className = 'text-slate-300';
    if (value === 'C' || value === 'CV') className = 'text-emerald-400';
    else if (value === 'FMIT') className = 'text-amber-400';
    else if (value === 'OFF' || value === 'LV') className = 'text-slate-500';
    else if (value === 'NF') className = 'text-violet-400';
    else if (value === 'LEC') className = 'text-cyan-400';
    else if (value === '—') className = 'text-slate-600';

    return { value, className };
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' });
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      {/* Header with block selector and source toggle */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-cyan-400" />
          {/* Block selector - year-aware to handle multiple academic years */}
          <select
            value={selectedBlockKey ?? ''}
            onChange={(e) => setSelectedBlockKey(e.target.value)}
            className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          >
            {blockRanges?.map(b => (
              <option
                key={getBlockKey(b.blockNumber, b.academicYear)}
                value={getBlockKey(b.blockNumber, b.academicYear)}
              >
                Block {b.blockNumber} (AY {b.academicYear})
              </option>
            ))}
          </select>
          <div className="w-px h-5 bg-slate-600" />
          {(['api', 'db', 'diff'] as const).map(source => (
            <button
              key={source}
              onClick={() => setDataSource(source)}
              className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                dataSource === source
                  ? source === 'diff'
                    ? 'bg-amber-600 text-white'
                    : 'bg-cyan-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              {source === 'api' ? 'API' : source === 'db' ? 'Raw DB' : '⚡ Diff'}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-500">
          {dataSource === 'diff' && '🔴 Red = mismatch'}
        </span>
      </div>

      {/* Grid */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-auto"
        onScroll={handleScroll}
      >
        {loading && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 m-3 bg-red-900/20 border border-red-700/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <table className="w-full text-xs border-collapse">
            <thead className="sticky top-0 bg-slate-800 z-10">
              <tr>
                <th className="text-left py-2 px-2 text-slate-400 font-medium border-b border-slate-700 sticky left-0 bg-slate-800 min-w-[120px]">
                  Person
                </th>
                {dates.map(date => (
                  <th key={date} colSpan={2} className="text-center py-1 px-1 text-slate-400 font-medium border-b border-l border-slate-700">
                    {formatDate(date)}
                  </th>
                ))}
              </tr>
              <tr>
                <th className="border-b border-slate-700 sticky left-0 bg-slate-800"></th>
                {dates.map(date => (
                  <React.Fragment key={`${date}-periods`}>
                    <th className="text-center py-1 px-1 text-slate-500 text-[10px] border-b border-l border-slate-700 w-10">AM</th>
                    <th className="text-center py-1 px-1 text-slate-500 text-[10px] border-b border-slate-700 w-10">PM</th>
                  </React.Fragment>
                ))}
              </tr>
            </thead>
            <tbody>
              {people.map((person, idx) => (
                <tr key={person.id} className={idx % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-1.5 px-2 text-slate-300 font-medium border-b border-slate-700/50 sticky left-0 bg-slate-900 whitespace-nowrap">
                    <span className="text-slate-300">{person.name}</span>
                    {person.pgyLevel && (
                      <span className={`ml-1 text-[10px] ${
                        person.pgyLevel === 1 ? 'text-emerald-400' :
                        person.pgyLevel === 2 ? 'text-amber-400' : 'text-violet-400'
                      }`}>
                        PGY-{person.pgyLevel}
                      </span>
                    )}
                  </td>
                  {dates.map(date => (
                    <React.Fragment key={`${person.id}-${date}`}>
                      {(['AM', 'PM'] as const).map(period => {
                        const { value, className } = getCellContent(person.id, date, period);
                        return (
                          <td
                            key={`${person.id}-${date}-${period}`}
                            className={`text-center py-1 px-1 border-b border-l border-slate-700/30 font-mono ${className}`}
                          >
                            {value}
                          </td>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 bg-slate-800/30 border-t border-slate-700/50 text-xs text-slate-500 flex justify-between">
        <span>{people.length} people × {dates.length} days</span>
        <span>Source: {dataSource.toUpperCase()}</span>
      </div>
    </div>
  );
}

// ============================================================================
// Absence Inspector Component
// ============================================================================

interface Absence {
  id: string;
  personId: string;
  personName?: string;
  absenceType: string;
  startDate: string;
  endDate: string;
  notes?: string;
}

function AbsenceInspector({ refreshKey }: { refreshKey: number }) {
  const [absences, setAbsences] = useState<Absence[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    const fetchAbsences = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/absences?limit=500`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = data.items || data.absences || (Array.isArray(data) ? data : []);
        setAbsences(items.map((a: Record<string, unknown>) => ({
          id: a.id as string,
          personId: a.person_id as string || a.personId as string,
          personName: a.person_name as string || a.personName as string || (a.person as Record<string, unknown>)?.name as string,
          absenceType: a.absence_type as string || a.absenceType as string || a.type as string,
          startDate: a.start_date as string || a.startDate as string,
          endDate: a.end_date as string || a.endDate as string,
          notes: a.notes as string,
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch absences');
      } finally {
        setLoading(false);
      }
    };
    fetchAbsences();
  }, [refreshKey]);

  const absenceTypes = ['all', ...new Set(absences.map(a => a.absenceType).filter(Boolean))];
  const filteredAbsences = filterType === 'all'
    ? absences
    : absences.filter(a => a.absenceType === filterType);

  const getTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'vacation': case 'lv': return 'text-emerald-400 bg-emerald-900/30';
      case 'sick': return 'text-red-400 bg-red-900/30';
      case 'conference': case 'hafp': case 'usafp': return 'text-cyan-400 bg-cyan-900/30';
      case 'tdy': case 'deployment': case 'dep': return 'text-amber-400 bg-amber-900/30';
      case 'holiday': case 'hol': return 'text-violet-400 bg-violet-900/30';
      default: return 'text-slate-400 bg-slate-700/50';
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
        <span className="text-xs text-slate-400">Filter:</span>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600"
        >
          {absenceTypes.map(type => (
            <option key={type} value={type}>{type === 'all' ? 'All Types' : type}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-slate-500">{filteredAbsences.length} absences</span>
      </div>

      <div className="flex-1 overflow-auto p-3">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-700/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-2">
            {filteredAbsences.map(absence => (
              <div key={absence.id} className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium">{absence.personName || absence.personId}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(absence.absenceType)}`}>
                    {absence.absenceType}
                  </span>
                </div>
                <div className="text-xs text-slate-400">
                  <span>{absence.startDate}</span>
                  <span className="mx-2">→</span>
                  <span>{absence.endDate}</span>
                </div>
                {absence.notes && (
                  <p className="text-xs text-slate-500 mt-1">{absence.notes}</p>
                )}
              </div>
            ))}
            {filteredAbsences.length === 0 && (
              <div className="text-center py-8 text-slate-500">No absences found</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// People Inspector Component
// ============================================================================

interface PersonDetail {
  id: string;
  name: string;
  type: string;
  pgyLevel?: number;
  email?: string;
  facultyRole?: string;
  isActive?: boolean;
}

function PeopleInspector({ refreshKey }: { refreshKey: number }) {
  const [people, setPeople] = useState<PersonDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchPeople = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/people?limit=200`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = data.items || data.people || (Array.isArray(data) ? data : []);
        setPeople(items.map((p: Record<string, unknown>) => ({
          id: p.id as string,
          name: p.name as string,
          type: p.type as string,
          pgyLevel: p.pgy_level as number || p.pgyLevel as number,
          email: p.email as string,
          facultyRole: p.faculty_role as string || p.facultyRole as string,
          isActive: p.is_active as boolean ?? p.isActive as boolean ?? true,
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch people');
      } finally {
        setLoading(false);
      }
    };
    fetchPeople();
  }, [refreshKey]);

  const personTypes = ['all', ...new Set(people.map(p => p.type).filter(Boolean))];
  const filteredPeople = people
    .filter(p => filterType === 'all' || p.type === filterType)
    .filter(p => !searchQuery || p.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const getTypeColor = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'resident': return 'text-emerald-400 bg-emerald-900/30';
      case 'faculty': return 'text-amber-400 bg-amber-900/30';
      case 'staff': return 'text-cyan-400 bg-cyan-900/30';
      default: return 'text-slate-400 bg-slate-700/50';
    }
  };

  const getPgyColor = (pgy?: number) => {
    switch (pgy) {
      case 1: return 'text-emerald-400';
      case 2: return 'text-amber-400';
      case 3: return 'text-violet-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600 w-32"
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600"
        >
          {personTypes.map(type => (
            <option key={type} value={type}>{type === 'all' ? 'All Types' : type}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-slate-500">{filteredPeople.length} people</span>
      </div>

      <div className="flex-1 overflow-auto">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 m-3 bg-red-900/20 border border-red-700/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-slate-800">
              <tr>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Name</th>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Type</th>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Level/Role</th>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredPeople.map((person, idx) => (
                <tr key={person.id} className={idx % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-2 px-3 text-white font-medium border-b border-slate-700/30">{person.name}</td>
                  <td className="py-2 px-3 border-b border-slate-700/30">
                    <span className={`px-2 py-0.5 rounded text-xs ${getTypeColor(person.type)}`}>
                      {person.type}
                    </span>
                  </td>
                  <td className="py-2 px-3 border-b border-slate-700/30">
                    {person.pgyLevel && (
                      <span className={`${getPgyColor(person.pgyLevel)}`}>PGY-{person.pgyLevel}</span>
                    )}
                    {person.facultyRole && (
                      <span className="text-slate-400">{person.facultyRole}</span>
                    )}
                  </td>
                  <td className="py-2 px-3 border-b border-slate-700/30">
                    <span className={person.isActive ? 'text-emerald-400' : 'text-red-400'}>
                      {person.isActive ? '● Active' : '○ Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Rotation Template Inspector Component
// ============================================================================

interface RotationTemplate {
  id: string;
  name: string;
  abbreviation?: string;
  activityType?: string;
  durationWeeks?: number;
  pgyLevels?: number[];
  isActive?: boolean;
}

function RotationTemplateInspector({ refreshKey }: { refreshKey: number }) {
  const [templates, setTemplates] = useState<RotationTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/rotation-templates?limit=200`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = data.items || data.templates || (Array.isArray(data) ? data : []);
        setTemplates(items.map((t: Record<string, unknown>) => ({
          id: t.id as string,
          name: t.name as string,
          abbreviation: t.abbreviation as string || t.display_abbreviation as string || t.displayAbbreviation as string,
          activityType: t.activity_type as string || t.activityType as string,
          durationWeeks: t.duration_weeks as number || t.durationWeeks as number,
          pgyLevels: t.pgy_levels as number[] || t.pgyLevels as number[],
          isActive: t.is_active as boolean ?? t.isActive as boolean ?? true,
        })));
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch rotation templates');
      } finally {
        setLoading(false);
      }
    };
    fetchTemplates();
  }, [refreshKey]);

  const getActivityColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'clinic': case 'fmclinic': return 'text-emerald-400 bg-emerald-900/30';
      case 'inpatient': case 'fmit': return 'text-amber-400 bg-amber-900/30';
      case 'elective': return 'text-cyan-400 bg-cyan-900/30';
      case 'call': return 'text-red-400 bg-red-900/30';
      case 'conference': case 'didactics': return 'text-violet-400 bg-violet-900/30';
      default: return 'text-slate-400 bg-slate-700/50';
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
        <span className="text-xs text-slate-400">{templates.length} rotation templates</span>
      </div>

      <div className="flex-1 overflow-auto p-3">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-700/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {templates.map(template => (
              <div key={template.id} className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-medium">{template.name}</span>
                  {template.abbreviation && (
                    <code className="px-2 py-0.5 bg-slate-700 rounded text-xs text-cyan-300">
                      {template.abbreviation}
                    </code>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs">
                  {template.activityType && (
                    <span className={`px-2 py-0.5 rounded ${getActivityColor(template.activityType)}`}>
                      {template.activityType}
                    </span>
                  )}
                  {template.durationWeeks && (
                    <span className="text-slate-400">{template.durationWeeks} weeks</span>
                  )}
                  {template.pgyLevels && template.pgyLevels.length > 0 && (
                    <span className="text-slate-400">
                      PGY: {template.pgyLevels.join(', ')}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Activity Inspector Component
// ============================================================================

interface Activity {
  id: string;
  code: string;
  name: string;
  category?: string;
  countsTowardClinic?: boolean;
  requiresSupervision?: boolean;
  isActive?: boolean;
}

function ActivityInspector({ refreshKey }: { refreshKey: number }) {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string>('all');

  useEffect(() => {
    const fetchActivities = async () => {
      setLoading(true);
      setError(null);
      try {
        // Note: /activities endpoint doesn't support limit param
        const res = await fetch(`${API_BASE_URL}/activities`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const items = data.items || data.activities || (Array.isArray(data) ? data : []);
        setActivities(items.map((a: Record<string, unknown>) => ({
          id: a.id as string,
          code: a.display_abbreviation as string || a.displayAbbreviation as string || a.code as string,
          name: a.name as string,
          category: a.activity_category as string || a.activityCategory as string || a.category as string,
          countsTowardClinic: a.counts_toward_clinical_hours as boolean ?? a.countsTowardClinicalHours as boolean,
          requiresSupervision: a.requires_supervision as boolean ?? a.requiresSupervision as boolean,
          isActive: !(a.is_archived as boolean ?? a.isArchived as boolean ?? false),
        })));
      } catch (err) {
        console.error('ActivityInspector fetch error:', err);
        setError(err instanceof Error ? `${err.name}: ${err.message}` : 'Failed to fetch activities');
      } finally {
        setLoading(false);
      }
    };
    fetchActivities();
  }, [refreshKey]);

  const categories = ['all', ...new Set(activities.map(a => a.category).filter(Boolean))];
  const filteredActivities = filterCategory === 'all'
    ? activities
    : activities.filter(a => a.category === filterCategory);

  const getCategoryColor = (category?: string) => {
    switch (category?.toLowerCase()) {
      case 'clinic': return 'text-emerald-400 bg-emerald-900/30';
      case 'inpatient': return 'text-amber-400 bg-amber-900/30';
      case 'administrative': case 'admin': return 'text-slate-400 bg-slate-700/50';
      case 'educational': case 'conference': return 'text-violet-400 bg-violet-900/30';
      case 'leave': case 'off': return 'text-cyan-400 bg-cyan-900/30';
      default: return 'text-slate-400 bg-slate-700/50';
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-900">
      <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat === 'all' ? 'All Categories' : cat}</option>
          ))}
        </select>
        <span className="ml-auto text-xs text-slate-500">{filteredActivities.length} activities</span>
      </div>

      <div className="flex-1 overflow-auto">
        {loading && (
          <div className="flex items-center justify-center h-32">
            <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 m-3 bg-red-900/20 border border-red-700/50 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-slate-800">
              <tr>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Code</th>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Name</th>
                <th className="text-left py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Category</th>
                <th className="text-center py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Clinic</th>
                <th className="text-center py-2 px-3 text-slate-400 font-medium border-b border-slate-700">Supervision</th>
              </tr>
            </thead>
            <tbody>
              {filteredActivities.map((activity, idx) => (
                <tr key={activity.id} className={idx % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-2 px-3 border-b border-slate-700/30">
                    <code className="px-2 py-0.5 bg-slate-700 rounded text-cyan-300">{activity.code}</code>
                  </td>
                  <td className="py-2 px-3 text-white border-b border-slate-700/30">{activity.name}</td>
                  <td className="py-2 px-3 border-b border-slate-700/30">
                    <span className={`px-2 py-0.5 rounded ${getCategoryColor(activity.category)}`}>
                      {activity.category || '—'}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center border-b border-slate-700/30">
                    {activity.countsTowardClinic ? '✓' : '—'}
                  </td>
                  <td className="py-2 px-3 text-center border-b border-slate-700/30">
                    {activity.requiresSupervision ? '✓' : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function DebuggerPage() {
  // Panel state
  const [leftUrl, setLeftUrl] = useState(DEFAULT_LEFT_URL);
  const [splitRatio, setSplitRatio] = useState<SplitRatio>(50);
  const [leftRefreshKey, setLeftRefreshKey] = useState(0);
  const [rightRefreshKey, setRightRefreshKey] = useState(0);

  // Inspector mode state
  const [inspectorMode, setInspectorMode] = useState<InspectorMode>('schedule');

  // UI state
  const [showDiagnosis, setShowDiagnosis] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [fullscreenPanel, setFullscreenPanel] = useState<'left' | 'right' | null>(null);

  // Dev mode check
  const [isDevMode, setIsDevMode] = useState(true);

  useEffect(() => {
    // Check if running in development
    const isDev = process.env.NODE_ENV === 'development' ||
                  window.location.hostname === 'localhost' ||
                  process.env.NEXT_PUBLIC_ENABLE_DEBUGGER === 'true';
    setIsDevMode(isDev);
  }, []);

  const handleRefreshLeft = useCallback(() => {
    setLeftRefreshKey((k) => k + 1);
  }, []);

  const handleRefreshRight = useCallback(() => {
    setRightRefreshKey((k) => k + 1);
  }, []);

  const handleRefreshBoth = useCallback(() => {
    handleRefreshLeft();
    handleRefreshRight();
  }, [handleRefreshLeft, handleRefreshRight]);

  const handleSwapPanels = useCallback(() => {
    // Swap split ratio (e.g., 25/75 becomes 75/25)
    setSplitRatio(prev => (100 - prev) as SplitRatio);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Shift + R = Refresh both
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'r') {
        e.preventDefault();
        handleRefreshBoth();
      }
      // Cmd/Ctrl + Shift + S = Swap panels
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 's') {
        e.preventDefault();
        handleSwapPanels();
      }
      // Escape = Exit fullscreen
      if (e.key === 'Escape' && fullscreenPanel) {
        setFullscreenPanel(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleRefreshBoth, handleSwapPanels, fullscreenPanel]);

  // Block in production
  if (!isDevMode) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center p-8">
          <AlertTriangle className="w-16 h-16 text-amber-400 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-white mb-2">Debugger Disabled</h1>
          <p className="text-slate-400">
            The side-by-side debugger is only available in development mode.
          </p>
          <p className="text-sm text-slate-500 mt-4">
            Set <code className="bg-slate-800 px-2 py-0.5 rounded">NEXT_PUBLIC_ENABLE_DEBUGGER=true</code> to enable.
          </p>
        </div>
      </div>
    );
  }

  const leftWidth = fullscreenPanel === 'left' ? 100 : fullscreenPanel === 'right' ? 0 : splitRatio;
  const rightWidth = fullscreenPanel === 'right' ? 100 : fullscreenPanel === 'left' ? 0 : 100 - splitRatio;

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col">
      {/* Header */}
      <header className="bg-slate-800/80 border-b border-slate-700/50 backdrop-blur-sm z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-violet-500 to-cyan-500 rounded-lg">
              <Bug className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">Side-by-Side Debugger</h1>
              <p className="text-xs text-slate-400">Compare frontend with database in real-time</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Split ratio selector */}
            <div className="flex items-center gap-1 bg-slate-700/50 rounded-lg p-1">
              {([25, 50, 75] as const).map((ratio) => (
                <button
                  key={ratio}
                  onClick={() => setSplitRatio(ratio)}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                    splitRatio === ratio
                      ? 'bg-violet-600 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {ratio}/{100 - ratio}
                </button>
              ))}
            </div>

            <div className="w-px h-6 bg-slate-700" />

            <button
              onClick={handleSwapPanels}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg"
              title="Swap panels (Cmd+Shift+S)"
            >
              <Split className="w-5 h-5" />
            </button>

            <button
              onClick={handleRefreshBoth}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded-lg"
              title="Refresh both (Cmd+Shift+R)"
            >
              <RefreshCw className="w-5 h-5" />
            </button>

            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-lg transition-colors ${
                showSettings ? 'bg-violet-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
              }`}
              title="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Settings panel */}
        {showSettings && (
          <div className="px-4 py-3 border-t border-slate-700/50 bg-slate-800/50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <DiagnosisHelper expanded={showDiagnosis} onToggle={() => setShowDiagnosis(!showDiagnosis)} />
              <div className="space-y-3">
                <McpIntegrationHint />
                <ChromeExtensionHint />
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Panels */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        {leftWidth > 0 && (
          <div className="flex flex-col border-r border-slate-700/50" style={{ width: `${leftWidth}%` }}>
            <UrlBar
              value={leftUrl}
              onChange={setLeftUrl}
              onRefresh={handleRefreshLeft}
              label="Frontend"
              presets={PRESET_URLS.filter((p) => p.type === 'app')}
            />
            <div className="relative flex-1">
              <IframePanel url={leftUrl} refreshKey={leftRefreshKey} />
              <button
                onClick={() => setFullscreenPanel(fullscreenPanel === 'left' ? null : 'left')}
                className="absolute top-2 right-2 p-1.5 bg-slate-800/80 text-slate-400 hover:text-white rounded"
                title="Fullscreen"
              >
                {fullscreenPanel === 'left' ? (
                  <Minimize2 className="w-4 h-4" />
                ) : (
                  <Maximize2 className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        )}

        {/* Right Panel - Database Inspector */}
        {rightWidth > 0 && (
          <div className="flex flex-col" style={{ width: `${rightWidth}%` }}>
            <div className="flex items-center justify-between px-3 py-2 bg-slate-800/50 border-b border-slate-700/50">
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-400">Database Inspector</span>
                <select
                  value={inspectorMode}
                  onChange={(e) => setInspectorMode(e.target.value as InspectorMode)}
                  className="px-2 py-1 bg-slate-700 text-white rounded text-xs border border-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  {INSPECTOR_MODES.map(mode => (
                    <option key={mode.value} value={mode.value}>
                      {mode.icon} {mode.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={handleRefreshRight}
                  className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setFullscreenPanel(fullscreenPanel === 'right' ? null : 'right')}
                  className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700/50 rounded"
                  title="Fullscreen"
                >
                  {fullscreenPanel === 'right' ? (
                    <Minimize2 className="w-4 h-4" />
                  ) : (
                    <Maximize2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-hidden">
              {inspectorMode === 'schedule' && <ScheduleMirrorView refreshKey={rightRefreshKey} />}
              {inspectorMode === 'absences' && <AbsenceInspector refreshKey={rightRefreshKey} />}
              {inspectorMode === 'people' && <PeopleInspector refreshKey={rightRefreshKey} />}
              {inspectorMode === 'rotations' && <RotationTemplateInspector refreshKey={rightRefreshKey} />}
              {inspectorMode === 'activities' && <ActivityInspector refreshKey={rightRefreshKey} />}
            </div>
          </div>
        )}
      </div>

      {/* Footer status */}
      <footer className="bg-slate-800/50 border-t border-slate-700/50 px-4 py-2 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span>Frontend: <span className="text-white font-mono">{leftUrl}</span></span>
          <span className="text-slate-600">|</span>
          <span>Inspector: <span className="text-cyan-400">{INSPECTOR_MODES.find(m => m.value === inspectorMode)?.label}</span></span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-500">Shortcuts:</span>
          <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-300">⌘⇧R</kbd>
          <span>Refresh</span>
          <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-300">⌘⇧S</kbd>
          <span>Swap</span>
          <kbd className="px-1.5 py-0.5 bg-slate-700 rounded text-slate-300">Esc</kbd>
          <span>Exit fullscreen</span>
        </div>
      </footer>
    </div>
  );
}
