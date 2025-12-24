/**
 * MCP Capabilities Panel
 *
 * Displays all available MCP tools organized by category with descriptions
 * of what each tool does and when to use it.
 */
import React, { useState } from 'react';
import './MCPCapabilitiesPanel.css';

interface MCPTool {
  name: string;
  description: string;
  whenToUse: string;
  examplePrompt?: string;
}

interface MCPCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  tools: MCPTool[];
}

const MCP_CATEGORIES: MCPCategory[] = [
  {
    id: 'scheduling',
    name: 'Scheduling & Compliance',
    icon: '📅',
    description: 'Core scheduling tools for ACGME validation, conflict detection, and swap management.',
    tools: [
      {
        name: 'validate_schedule',
        description: 'Validates schedule against ACGME regulations including work hours, supervision, rest periods, and consecutive duty.',
        whenToUse: 'Before finalizing any schedule, after making changes, or to audit compliance.',
        examplePrompt: 'Validate the schedule for January 2025 and show any ACGME violations',
      },
      {
        name: 'detect_conflicts',
        description: 'Scans for double-bookings, work hour violations, supervision gaps, and scheduling conflicts.',
        whenToUse: 'After importing data, before publishing schedules, or when residents report issues.',
        examplePrompt: 'Check for any scheduling conflicts in the next 2 weeks',
      },
      {
        name: 'analyze_swap_candidates',
        description: 'Uses intelligent matching to find optimal swap partners based on rotation compatibility and mutual benefit.',
        whenToUse: 'When a faculty member requests a swap or needs coverage.',
        examplePrompt: 'Find swap candidates for Dr. Smith\'s clinic shift on January 15th',
      },
      {
        name: 'run_contingency_analysis',
        description: 'Simulates absence scenarios and identifies impact on coverage, compliance, and workload.',
        whenToUse: 'For workforce planning, before approving leave, or to stress-test the schedule.',
        examplePrompt: 'What happens if we lose 2 faculty members for the next month?',
      },
    ],
  },
  {
    id: 'resilience',
    name: 'Resilience Framework',
    icon: '🛡️',
    description: 'Cross-industry best practices for schedule stability and failure prevention.',
    tools: [
      {
        name: 'check_utilization_threshold',
        description: 'Checks system utilization against the 80% threshold from queuing theory. Above 80%, cascade failures become likely.',
        whenToUse: 'Daily monitoring, before adding workload, or when coverage feels tight.',
        examplePrompt: 'Check current utilization levels across all rotations',
      },
      {
        name: 'get_defense_level',
        description: 'Returns current defense-in-depth level (GREEN/YELLOW/ORANGE/RED/BLACK) based on coverage rates.',
        whenToUse: 'Dashboard monitoring, status checks, or when escalating concerns.',
        examplePrompt: 'What is our current defense level?',
      },
      {
        name: 'run_contingency_analysis_resilience',
        description: 'N-1/N-2 analysis: Can we survive losing any 1 or 2 faculty members?',
        whenToUse: 'Weekly planning, before approving leave, or assessing schedule robustness.',
        examplePrompt: 'Run N-1 and N-2 contingency analysis for the EM rotation',
      },
      {
        name: 'get_static_fallbacks',
        description: 'Retrieves pre-computed fallback schedules for crisis scenarios.',
        whenToUse: 'During emergencies or when planning backup coverage.',
        examplePrompt: 'Show available fallback schedules for the ICU rotation',
      },
      {
        name: 'execute_sacrifice_hierarchy',
        description: 'Implements triage-based load shedding to maintain critical functions.',
        whenToUse: 'During crisis situations when some activities must be suspended.',
        examplePrompt: 'Simulate load shedding to ORANGE level - what gets suspended?',
      },
      {
        name: 'analyze_homeostasis',
        description: 'Monitors feedback loops and allostatic load (cumulative stress) on the system.',
        whenToUse: 'Understanding long-term schedule health and burnout risk.',
        examplePrompt: 'Analyze homeostasis and allostatic load for the current block',
      },
      {
        name: 'calculate_blast_radius',
        description: 'Analyzes how failures are contained within scheduling zones.',
        whenToUse: 'Understanding failure propagation and zone isolation.',
        examplePrompt: 'Calculate blast radius if the medicine rotation fails',
      },
      {
        name: 'analyze_hub_centrality',
        description: 'Identifies "hub" faculty whose removal would cause disproportionate disruption.',
        whenToUse: 'Identifying single points of failure and dependency risks.',
        examplePrompt: 'Who are our most critical faculty members?',
      },
    ],
  },
  {
    id: 'async',
    name: 'Background Tasks',
    icon: '⚡',
    description: 'Long-running operations that execute asynchronously via Celery.',
    tools: [
      {
        name: 'start_background_task',
        description: 'Triggers long-running tasks like resilience analysis, metrics computation, or contingency planning.',
        whenToUse: 'For operations that take more than a few seconds.',
        examplePrompt: 'Start a resilience health check in the background',
      },
      {
        name: 'get_task_status',
        description: 'Polls task progress and retrieves results or errors.',
        whenToUse: 'Checking on running tasks or getting results.',
        examplePrompt: 'Check the status of task abc-123',
      },
      {
        name: 'cancel_task',
        description: 'Revokes a queued or running background task.',
        whenToUse: 'When a task is no longer needed or taking too long.',
        examplePrompt: 'Cancel task abc-123',
      },
      {
        name: 'list_active_tasks',
        description: 'Lists all currently queued or running tasks.',
        whenToUse: 'Monitoring system load or finding tasks to cancel.',
        examplePrompt: 'Show all active background tasks',
      },
    ],
  },
  {
    id: 'deployment',
    name: 'Deployment & CI/CD',
    icon: '🚀',
    description: 'Tools for managing deployments, security scans, and rollbacks.',
    tools: [
      {
        name: 'validate_deployment',
        description: 'Pre-deployment validation including tests, security scan, and environment readiness.',
        whenToUse: 'Before any deployment to staging or production.',
        examplePrompt: 'Validate deployment of main branch to staging',
      },
      {
        name: 'run_security_scan',
        description: 'Comprehensive security scan: dependency vulnerabilities, SAST, and secret detection.',
        whenToUse: 'Before deployments or as part of security audits.',
        examplePrompt: 'Run security scan on the current codebase',
      },
      {
        name: 'run_smoke_tests',
        description: 'Tests basic functionality: API health, database, Redis, and critical user journeys.',
        whenToUse: 'After deployments to verify everything works.',
        examplePrompt: 'Run smoke tests on staging environment',
      },
      {
        name: 'promote_to_production',
        description: 'Promotes a staging deployment to production (requires approval token).',
        whenToUse: 'After staging validation is complete.',
        examplePrompt: 'Promote v1.2.3 from staging to production',
      },
      {
        name: 'rollback_deployment',
        description: 'Rolls back to a previous stable version.',
        whenToUse: 'When a deployment causes issues in production.',
        examplePrompt: 'Rollback production to the previous version',
      },
      {
        name: 'get_deployment_status',
        description: 'Detailed deployment status including logs and health checks.',
        whenToUse: 'Monitoring ongoing or recent deployments.',
        examplePrompt: 'Get status of deployment deploy-12345',
      },
      {
        name: 'list_deployments',
        description: 'Lists recent deployment history.',
        whenToUse: 'Finding deployment IDs or reviewing history.',
        examplePrompt: 'List last 5 production deployments',
      },
    ],
  },
  {
    id: 'advanced',
    name: 'Advanced Analytics',
    icon: '🔬',
    description: 'Specialized cross-disciplinary analysis tools.',
    tools: [
      {
        name: 'analyze_le_chatelier',
        description: 'Applies Le Chatelier\'s principle: when stress is applied, the system shifts to a new equilibrium.',
        whenToUse: 'Understanding system response to schedule changes.',
        examplePrompt: 'Analyze equilibrium shift if we add 3 more clinic slots',
      },
      {
        name: 'assess_cognitive_load',
        description: 'Monitors decision queue complexity using Miller\'s Law (7±2 items).',
        whenToUse: 'When coordinators feel overwhelmed or decisions are piling up.',
        examplePrompt: 'Assess current cognitive load and decision queue',
      },
      {
        name: 'get_behavioral_patterns',
        description: 'Analyzes preference trails from faculty scheduling decisions (stigmergy).',
        whenToUse: 'Understanding collective preferences and optimal patterns.',
        examplePrompt: 'What behavioral patterns have emerged from recent scheduling?',
      },
      {
        name: 'analyze_stigmergy',
        description: 'Provides stigmergy-based scheduling suggestions for specific slots.',
        whenToUse: 'Getting AI-suggested faculty assignments based on historical patterns.',
        examplePrompt: 'Who should we assign to the Thursday AM clinic slot?',
      },
      {
        name: 'check_mtf_compliance',
        description: 'Military-style Multi-Tier Functionality compliance with DRRS ratings.',
        whenToUse: 'Generating compliance reports for military medical programs.',
        examplePrompt: 'Generate MTF compliance SITREP',
      },
    ],
  },
];

interface MCPCapabilitiesPanelProps {
  onSelectPrompt?: (prompt: string) => void;
  compact?: boolean;
}

const MCPCapabilitiesPanel: React.FC<MCPCapabilitiesPanelProps> = ({
  onSelectPrompt,
  compact = false,
}) => {
  const [expandedCategory, setExpandedCategory] = useState<string | null>(
    compact ? null : 'scheduling'
  );
  const [searchQuery, setSearchQuery] = useState('');

  const toggleCategory = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? null : categoryId);
  };

  const filteredCategories = MCP_CATEGORIES.map((category) => ({
    ...category,
    tools: category.tools.filter(
      (tool) =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.whenToUse.toLowerCase().includes(searchQuery.toLowerCase())
    ),
  })).filter((category) => category.tools.length > 0);

  const totalTools = MCP_CATEGORIES.reduce(
    (acc, cat) => acc + cat.tools.length,
    0
  );

  return (
    <div className={`mcp-capabilities-panel ${compact ? 'compact' : ''}`}>
      <div className="mcp-panel-header">
        <h3>MCP Capabilities</h3>
        <span className="tool-count">{totalTools} tools available</span>
      </div>

      <div className="mcp-search">
        <input
          type="text"
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mcp-search-input"
        />
        {searchQuery && (
          <button
            className="mcp-search-clear"
            onClick={() => setSearchQuery('')}
          >
            ✕
          </button>
        )}
      </div>

      <div className="mcp-categories">
        {filteredCategories.map((category) => (
          <div
            key={category.id}
            className={`mcp-category ${
              expandedCategory === category.id ? 'expanded' : ''
            }`}
          >
            <button
              className="mcp-category-header"
              onClick={() => toggleCategory(category.id)}
            >
              <span className="mcp-category-icon">{category.icon}</span>
              <div className="mcp-category-info">
                <span className="mcp-category-name">{category.name}</span>
                <span className="mcp-category-count">
                  {category.tools.length} tools
                </span>
              </div>
              <span className="mcp-category-toggle">
                {expandedCategory === category.id ? '−' : '+'}
              </span>
            </button>

            {expandedCategory === category.id && (
              <div className="mcp-category-content">
                <p className="mcp-category-description">
                  {category.description}
                </p>
                <div className="mcp-tools-list">
                  {category.tools.map((tool) => (
                    <div key={tool.name} className="mcp-tool">
                      <div className="mcp-tool-header">
                        <code className="mcp-tool-name">{tool.name}</code>
                      </div>
                      <p className="mcp-tool-description">{tool.description}</p>
                      <div className="mcp-tool-when">
                        <strong>When to use:</strong> {tool.whenToUse}
                      </div>
                      {tool.examplePrompt && onSelectPrompt && (
                        <button
                          className="mcp-tool-try"
                          onClick={() => onSelectPrompt(tool.examplePrompt!)}
                        >
                          Try: "{tool.examplePrompt}"
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredCategories.length === 0 && searchQuery && (
        <div className="mcp-no-results">
          No tools found matching "{searchQuery}"
        </div>
      )}

      <div className="mcp-panel-footer">
        <p>
          Ask Claude natural questions - it will automatically select the right
          tools.
        </p>
      </div>
    </div>
  );
};

export default MCPCapabilitiesPanel;
