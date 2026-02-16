/**
 * ADK Evaluation Criteria
 *
 * Defines evaluation metrics for testing agent behavior:
 * - Tool trajectory (did it call the right tools?)
 * - Response quality (did it answer correctly?)
 * - Safety (no harmful outputs?)
 */

import { z } from 'zod';

/**
 * Expected tool call in a trajectory
 */
export const ExpectedToolCallSchema = z.object({
  name: z.string(),
  args: z.record(z.unknown()).optional(),
  matchMode: z.enum(['exact', 'contains', 'any']).optional().default('contains'),
});

export type ExpectedToolCall = z.infer<typeof ExpectedToolCallSchema>;

/**
 * Evaluation test case
 */
export const TestCaseSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().optional(),

  // Input
  userMessage: z.string(),
  context: z.record(z.unknown()).optional(),

  // Expected behavior
  expectedToolCalls: z.array(ExpectedToolCallSchema).optional(),
  expectedResponseContains: z.array(z.string()).optional(),
  expectedResponseNotContains: z.array(z.string()).optional(),

  // Thresholds
  minToolTrajectoryScore: z.number().min(0).max(1).optional().default(0.9),
  minResponseMatchScore: z.number().min(0).max(1).optional().default(0.8),

  // Tags for filtering
  tags: z.array(z.string()).optional(),
});

export type TestCase = z.infer<typeof TestCaseSchema>;

/**
 * Evaluation result
 */
export interface EvaluationResult {
  testCase: TestCase;
  passed: boolean;
  toolTrajectoryScore: number;
  responseMatchScore: number;
  actualToolCalls: string[];
  actualResponse: string;
  errors: string[];
  duration: number;
}

/**
 * Calculate tool trajectory score
 *
 * Compares actual tool calls against expected sequence.
 * Supports different match modes:
 * - exact: Must match exactly in order
 * - contains: Expected tools must appear somewhere
 * - any: Any expected tool appearing counts
 */
export function calculateToolTrajectoryScore(
  actual: string[],
  expected: ExpectedToolCall[],
): number {
  if (expected.length === 0) return 1.0;
  if (actual.length === 0) return 0.0;

  let matches = 0;
  for (const exp of expected) {
    const found = actual.some((a) => {
      if (exp.matchMode === 'exact') {
        return a === exp.name;
      }
      return a.includes(exp.name) || exp.name.includes(a);
    });
    if (found) matches++;
  }

  return matches / expected.length;
}

/**
 * Calculate response match score
 *
 * Checks if response contains expected phrases
 * and doesn't contain forbidden phrases.
 */
export function calculateResponseMatchScore(
  response: string,
  expectedContains: string[],
  expectedNotContains: string[],
): number {
  const lowerResponse = response.toLowerCase();

  // Check contains
  let containsScore = 1.0;
  if (expectedContains.length > 0) {
    const matches = expectedContains.filter((phrase) =>
      lowerResponse.includes(phrase.toLowerCase()),
    ).length;
    containsScore = matches / expectedContains.length;
  }

  // Check not contains (penalty)
  let notContainsPenalty = 0;
  if (expectedNotContains.length > 0) {
    const violations = expectedNotContains.filter((phrase) =>
      lowerResponse.includes(phrase.toLowerCase()),
    ).length;
    notContainsPenalty = violations * 0.2; // 20% penalty per violation
  }

  return Math.max(0, containsScore - notContainsPenalty);
}
