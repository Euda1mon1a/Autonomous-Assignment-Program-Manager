/**
 * @scheduler/agent-adk
 *
 * Google ADK agents for Residency Scheduler.
 * Supports Gemini (default) and Claude models.
 */

// Agents
export { rootAgent, scheduleAgent, complianceAgent, agents } from './agents/index.js';

// Tools
export { scheduleTools } from './tools/schedule-tools.js';

// Evaluation
export {
  calculateToolTrajectoryScore,
  calculateResponseMatchScore,
  type TestCase,
  type EvaluationResult,
  type ExpectedToolCall,
} from './evaluation/criteria.js';

export {
  allTestCases,
  acgmeTestCases,
  swapTestCases,
  resilienceTestCases,
  safetyTestCases,
  getTestCasesByTag,
} from './evaluation/test-cases.js';
