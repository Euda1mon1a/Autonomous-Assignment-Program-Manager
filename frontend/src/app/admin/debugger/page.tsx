'use client';

/**
 * Side-by-Side Debugger
 *
 * Developer experience tool for comparing frontend views with raw database data.
 * Supports:
 * - Dual iframe layout (app + NocoDB)
 * - API request inspector
 * - Direct database queries via MCP
 * - Claude Chrome extension integration hints
 *
 * @see docs/development/SIDE_BY_SIDE_DEBUGGER.md
 */

import { useState, useEffect, useCallback, useRef } from 'react';
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
  Play,
  X,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
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

interface ApiCall {
  id: string;
  timestamp: Date;
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  url: string;
  status: number;
  duration: number;
  requestBody?: unknown;
  responseBody?: unknown;
  error?: string;
}

type SplitRatio = 25 | 50 | 75;

// ============================================================================
// Constants
// ============================================================================

const DEFAULT_LEFT_URL = '/schedule';
const DEFAULT_NOCODB_URL = 'http://localhost:8085';

const PRESET_URLS: { label: string; url: string; type: PanelConfig['type'] }[] = [
  { label: 'Schedule', url: '/schedule', type: 'app' },
  { label: 'People', url: '/people', type: 'app' },
  { label: 'Call Hub', url: '/call-hub', type: 'app' },
  { label: 'Block Explorer', url: '/admin/block-explorer', type: 'app' },
  { label: 'Compliance', url: '/compliance', type: 'app' },
  { label: 'NocoDB', url: DEFAULT_NOCODB_URL, type: 'nocodb' },
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
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
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

// ============================================================================
// Main Component
// ============================================================================

export default function DebuggerPage() {
  // Panel state
  const [leftUrl, setLeftUrl] = useState(DEFAULT_LEFT_URL);
  const [rightUrl, setRightUrl] = useState(DEFAULT_NOCODB_URL);
  const [splitRatio, setSplitRatio] = useState<SplitRatio>(50);
  const [leftRefreshKey, setLeftRefreshKey] = useState(0);
  const [rightRefreshKey, setRightRefreshKey] = useState(0);

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
    const tempUrl = leftUrl;
    setLeftUrl(rightUrl);
    setRightUrl(tempUrl);
  }, [leftUrl, rightUrl]);

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

        {/* Right Panel */}
        {rightWidth > 0 && (
          <div className="flex flex-col" style={{ width: `${rightWidth}%` }}>
            <UrlBar
              value={rightUrl}
              onChange={setRightUrl}
              onRefresh={handleRefreshRight}
              label="Database"
              presets={PRESET_URLS.filter((p) => p.type === 'nocodb' || p.type === 'custom')}
            />
            <div className="relative flex-1">
              <IframePanel url={rightUrl} refreshKey={rightRefreshKey} />
              <button
                onClick={() => setFullscreenPanel(fullscreenPanel === 'right' ? null : 'right')}
                className="absolute top-2 right-2 p-1.5 bg-slate-800/80 text-slate-400 hover:text-white rounded"
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
        )}
      </div>

      {/* Footer status */}
      <footer className="bg-slate-800/50 border-t border-slate-700/50 px-4 py-2 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span>Left: <span className="text-white font-mono">{leftUrl}</span></span>
          <span className="text-slate-600">|</span>
          <span>Right: <span className="text-white font-mono">{rightUrl}</span></span>
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
