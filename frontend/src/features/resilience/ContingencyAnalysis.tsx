/**
 * Contingency Analysis Component
 *
 * Displays N-1/N-2 contingency analysis results from the VulnerabilityReport API.
 * This component shows the CURRENT state of system vulnerability and phase transition risk.
 *
 * CURRENT FUNCTIONALITY:
 * - N-1 pass/fail status with vulnerability count
 * - N-2 pass/fail status with fatal pair count
 * - Phase transition risk assessment
 * - Recommended mitigation actions
 *
 * SCENARIO SIMULATION (Future Enhancement):
 * The UI includes a scenario selector for what-if analysis, but scenario simulation
 * is not yet wired to a REST API. The MCP tool `run_contingency_analysis_tool`
 * provides this capability for CLI/agent use.
 *
 * To enable scenario simulation in the UI:
 * 1. Add POST /resilience/scenario-simulation endpoint to backend
 * 2. Create useContingencySimulation mutation hook
 * 3. Wire the "Run Scenario Simulation" button to call the endpoint
 * 4. Display simulation results (impact assessment, coverage gaps, resolutions)
 *
 * @see N1Analysis for network-focused vulnerability visualization
 * @see useVulnerabilityReport for the current data source
 * @see mcp__residency-scheduler__run_contingency_analysis_tool for scenario simulation API
 */

import React, { useState } from "react";
import { useVulnerabilityReport } from "@/hooks/useResilience";
import {
  AlertTriangle,
  CheckCircle2,
  Play,
  RefreshCw,
  Shield,
  Users,
  Zap,
} from "lucide-react";

export interface ContingencyAnalysisProps {
  className?: string;
}

type ScenarioType = "faculty_absence" | "mass_absence" | "emergency_coverage";

interface ScenarioConfig {
  type: ScenarioType;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const SCENARIOS: ScenarioConfig[] = [
  {
    type: "faculty_absence",
    label: "Single Faculty Loss",
    description: "Simulate impact of losing one faculty member",
    icon: <Users className="w-4 h-4" />,
  },
  {
    type: "mass_absence",
    label: "Mass Absence",
    description: "Simulate multiple personnel unavailable",
    icon: <AlertTriangle className="w-4 h-4" />,
  },
  {
    type: "emergency_coverage",
    label: "Emergency Coverage",
    description: "Simulate emergency staffing needs",
    icon: <Zap className="w-4 h-4" />,
  },
];

export const ContingencyAnalysis: React.FC<ContingencyAnalysisProps> = ({
  className,
}) => {
  const { data, isLoading, error, refetch, isRefetching } =
    useVulnerabilityReport();
  const [selectedScenario, setSelectedScenario] =
    useState<ScenarioType>("faculty_absence");

  // Loading state
  if (isLoading) {
    return (
      <div
        className={`bg-slate-900/50 border border-slate-800 rounded-xl p-6 ${className}`}
      >
        <div className="flex items-center justify-center h-48">
          <div className="animate-pulse text-slate-500 text-sm flex items-center gap-2">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Analyzing contingency scenarios...
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div
        className={`bg-slate-900/50 border border-slate-800 rounded-xl p-6 ${className}`}
      >
        <div className="flex flex-col items-center justify-center h-48 text-center">
          <Shield className="w-10 h-10 text-slate-600 mb-3" />
          <h3 className="text-slate-400 font-medium">
            Contingency Data Unavailable
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Unable to load vulnerability analysis
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const n1VulnCount = data.n1Vulnerabilities?.length ?? 0;
  const n2PairCount = data.n2FatalPairs?.length ?? 0;
  const riskLevel = data.phaseTransitionRisk ?? "unknown";

  // Risk color mapping
  const getRiskColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case "low":
        return "text-green-400";
      case "medium":
        return "text-yellow-400";
      case "high":
        return "text-orange-400";
      case "critical":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  const getRiskBgColor = (risk: string) => {
    switch (risk.toLowerCase()) {
      case "low":
        return "bg-green-500/10 border-green-500/20";
      case "medium":
        return "bg-yellow-500/10 border-yellow-500/20";
      case "high":
        return "bg-orange-500/10 border-orange-500/20";
      case "critical":
        return "bg-red-500/10 border-red-500/20";
      default:
        return "bg-slate-500/10 border-slate-500/20";
    }
  };

  return (
    <div
      className={`bg-slate-900/50 border border-slate-800 rounded-xl p-6 ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            Contingency Analysis
          </h2>
          <p className="text-sm text-slate-400">
            N-1/N-2 scenario simulation
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          title="Refresh analysis"
        >
          <RefreshCw
            className={`w-4 h-4 ${isRefetching ? "animate-spin" : ""}`}
          />
        </button>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        <div
          className={`rounded-lg border p-3 ${
            data.n1Pass
              ? "bg-green-500/10 border-green-500/20"
              : "bg-red-500/10 border-red-500/20"
          }`}
        >
          <div className="flex items-center gap-2">
            {data.n1Pass ? (
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-red-400" />
            )}
            <span className="text-xs font-medium text-slate-300">N-1 Status</span>
          </div>
          <div
            className={`text-lg font-bold mt-1 ${
              data.n1Pass ? "text-green-400" : "text-red-400"
            }`}
          >
            {data.n1Pass ? "PASS" : "FAIL"}
          </div>
          <div className="text-xs text-slate-500">
            {n1VulnCount} vulnerabilities
          </div>
        </div>

        <div
          className={`rounded-lg border p-3 ${
            data.n2Pass
              ? "bg-green-500/10 border-green-500/20"
              : "bg-orange-500/10 border-orange-500/20"
          }`}
        >
          <div className="flex items-center gap-2">
            {data.n2Pass ? (
              <CheckCircle2 className="w-4 h-4 text-green-400" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-orange-400" />
            )}
            <span className="text-xs font-medium text-slate-300">N-2 Status</span>
          </div>
          <div
            className={`text-lg font-bold mt-1 ${
              data.n2Pass ? "text-green-400" : "text-orange-400"
            }`}
          >
            {data.n2Pass ? "PASS" : "FAIL"}
          </div>
          <div className="text-xs text-slate-500">{n2PairCount} fatal pairs</div>
        </div>
      </div>

      {/* Phase Transition Risk */}
      <div className={`rounded-lg border p-3 mb-6 ${getRiskBgColor(riskLevel)}`}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-300">
            Phase Transition Risk
          </span>
          <span className={`text-sm font-bold uppercase ${getRiskColor(riskLevel)}`}>
            {riskLevel}
          </span>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Likelihood of cascade failure under stress
        </p>
      </div>

      {/* Scenario Selector */}
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
          Simulation Scenarios
        </h3>
        <div className="space-y-2">
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.type}
              onClick={() => setSelectedScenario(scenario.type)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all text-left ${
                selectedScenario === scenario.type
                  ? "bg-blue-500/10 border-blue-500/30 text-blue-200"
                  : "bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600"
              }`}
            >
              <div
                className={`p-1.5 rounded ${
                  selectedScenario === scenario.type
                    ? "bg-blue-500/20"
                    : "bg-slate-700"
                }`}
              >
                {scenario.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium">{scenario.label}</div>
                <div className="text-xs text-slate-500 truncate">
                  {scenario.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Run Simulation Button */}
      <button
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-700 text-slate-400 font-medium rounded-lg cursor-not-allowed"
        title="Scenario simulation requires REST API endpoint. Use MCP tool run_contingency_analysis_tool for CLI access."
        disabled
        aria-disabled="true"
      >
        <Play className="w-4 h-4" />
        Run Scenario Simulation
      </button>
      <p className="text-xs text-slate-500 text-center mt-2">
        Current state shown above. Scenario simulation available via MCP CLI.
      </p>

      {/* Recommendations */}
      {data.recommendedActions && data.recommendedActions.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-800">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Recommended Actions
          </h3>
          <ul className="space-y-1.5">
            {data.recommendedActions.slice(0, 3).map((action, i) => (
              <li
                key={i}
                className="text-xs text-slate-300 flex items-start gap-2"
              >
                <span className="text-blue-400 mt-0.5">-</span>
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ContingencyAnalysis;
