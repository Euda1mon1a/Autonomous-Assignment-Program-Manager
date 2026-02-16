/**
 * ADK Agent Entry Point
 *
 * Exports the root agent for ADK devtools.
 * Run with: npx @google/adk-devtools web src/agents/index.ts
 */

import { scheduleAgent } from './schedule-agent.js';

// Root agent for ADK
export const rootAgent = scheduleAgent;

// Re-export all agents
export * from './schedule-agent.js';
