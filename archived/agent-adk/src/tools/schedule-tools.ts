/**
 * Schedule-related ADK tools that call the backend API.
 *
 * These tools wrap our FastAPI endpoints, making them available
 * to ADK agents with proper Zod schema validation.
 */

import { FunctionTool } from '@google/adk';
import { z } from 'zod';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/api';

/**
 * Get current schedule data
 */
export const getScheduleTool = new FunctionTool({
  name: 'get_schedule',
  description: 'Retrieves the current schedule or a specific schedule by ID',
  parameters: z.object({
    scheduleId: z.string().optional().describe('Schedule ID (optional, defaults to current)'),
    startDate: z.string().optional().describe('Start date filter (YYYY-MM-DD)'),
    endDate: z.string().optional().describe('End date filter (YYYY-MM-DD)'),
  }),
  execute: async ({ scheduleId, startDate, endDate }) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = scheduleId
      ? `${API_BASE}/schedules/${scheduleId}?${params}`
      : `${API_BASE}/schedules/current?${params}`;

    const response = await fetch(url);
    if (!response.ok) {
      return { error: `Failed to fetch schedule: ${response.statusText}` };
    }
    return response.json();
  },
});

/**
 * Validate ACGME compliance
 */
export const validateAcgmeComplianceTool = new FunctionTool({
  name: 'validate_acgme_compliance',
  description: 'Checks a schedule for ACGME compliance violations including 80-hour rule, 1-in-7 day off, and supervision ratios',
  parameters: z.object({
    scheduleId: z.string().describe('Schedule ID to validate'),
    checkHours: z.boolean().optional().default(true).describe('Check 80-hour weekly limit'),
    checkDaysOff: z.boolean().optional().default(true).describe('Check 1-in-7 day off rule'),
    checkSupervision: z.boolean().optional().default(true).describe('Check supervision ratios'),
  }),
  execute: async ({ scheduleId, checkHours, checkDaysOff, checkSupervision }) => {
    const response = await fetch(`${API_BASE}/compliance/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        schedule_id: scheduleId,
        check_hours: checkHours,
        check_days_off: checkDaysOff,
        check_supervision: checkSupervision,
      }),
    });

    if (!response.ok) {
      return { error: `Validation failed: ${response.statusText}` };
    }
    return response.json();
  },
});

/**
 * Find swap matches
 */
export const findSwapMatchesTool = new FunctionTool({
  name: 'find_swap_matches',
  description: 'Finds compatible swap partners for a given shift using the auto-matching algorithm',
  parameters: z.object({
    personId: z.string().describe('ID of person requesting the swap'),
    shiftDate: z.string().describe('Date of shift to swap (YYYY-MM-DD)'),
    shiftSession: z.enum(['AM', 'PM']).describe('Session of shift (AM or PM)'),
    swapType: z.enum(['one_to_one', 'absorb']).optional().default('one_to_one'),
  }),
  execute: async ({ personId, shiftDate, shiftSession, swapType }) => {
    const response = await fetch(`${API_BASE}/swap/matches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        person_id: personId,
        shift_date: shiftDate,
        shift_session: shiftSession,
        swap_type: swapType,
      }),
    });

    if (!response.ok) {
      return { error: `Match finding failed: ${response.statusText}` };
    }
    return response.json();
  },
});

/**
 * Check utilization threshold
 */
export const checkUtilizationTool = new FunctionTool({
  name: 'check_utilization',
  description: 'Checks if system utilization is within the 80% queuing theory threshold',
  parameters: z.object({
    startDate: z.string().optional().describe('Start date for calculation'),
    endDate: z.string().optional().describe('End date for calculation'),
  }),
  execute: async ({ startDate, endDate }) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await fetch(`${API_BASE}/resilience/utilization?${params}`);
    if (!response.ok) {
      return { error: `Utilization check failed: ${response.statusText}` };
    }
    return response.json();
  },
});

/**
 * Run contingency analysis
 */
export const runContingencyAnalysisTool = new FunctionTool({
  name: 'run_contingency_analysis',
  description: 'Runs N-1/N-2 contingency analysis to identify single points of failure',
  parameters: z.object({
    scheduleId: z.string().describe('Schedule ID to analyze'),
    analysisType: z.enum(['N-1', 'N-2']).optional().default('N-1'),
  }),
  execute: async ({ scheduleId, analysisType }) => {
    const response = await fetch(`${API_BASE}/resilience/contingency`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        schedule_id: scheduleId,
        analysis_type: analysisType,
      }),
    });

    if (!response.ok) {
      return { error: `Contingency analysis failed: ${response.statusText}` };
    }
    return response.json();
  },
});

// Export all tools
export const scheduleTools = [
  getScheduleTool,
  validateAcgmeComplianceTool,
  findSwapMatchesTool,
  checkUtilizationTool,
  runContingencyAnalysisTool,
];
