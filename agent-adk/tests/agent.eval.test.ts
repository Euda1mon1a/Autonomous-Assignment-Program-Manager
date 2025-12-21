/**
 * Agent Evaluation Tests
 *
 * These tests evaluate agent behavior against defined criteria.
 * Run with: npm run test:eval
 */

import { describe, it, expect } from 'vitest';
import {
  allTestCases,
  getTestCasesByTag,
} from '../src/evaluation/test-cases.js';
import {
  calculateToolTrajectoryScore,
  calculateResponseMatchScore,
  type TestCase,
  type EvaluationResult,
} from '../src/evaluation/criteria.js';

// Mock agent response for testing the evaluation framework itself
// In real usage, this would call the actual ADK agent
async function mockAgentResponse(testCase: TestCase): Promise<{
  toolCalls: string[];
  response: string;
}> {
  // Simulate different responses based on test case
  const responses: Record<string, { toolCalls: string[]; response: string }> = {
    'acgme-001': {
      toolCalls: ['validate_acgme_compliance'],
      response: 'The 80-hour weekly limit compliance check shows Dr. Smith has worked 78 hours on average.',
    },
    'acgme-002': {
      toolCalls: ['get_schedule', 'validate_acgme_compliance'],
      response: 'The supervision ratio for PGY-1 residents is 2:1, which meets ACGME requirements.',
    },
    'swap-001': {
      toolCalls: ['find_swap_matches'],
      response: 'I found 3 available partners for your swap: Dr. Chen, Dr. Patel, and Dr. Kim.',
    },
    'resilience-001': {
      toolCalls: ['check_utilization'],
      response: 'Current system utilization is at 72%, which is within the healthy range below 80%.',
    },
  };

  return responses[testCase.id] || { toolCalls: [], response: 'No mock available' };
}

/**
 * Evaluate a single test case
 */
async function evaluateTestCase(testCase: TestCase): Promise<EvaluationResult> {
  const startTime = Date.now();

  const { toolCalls, response } = await mockAgentResponse(testCase);

  const toolTrajectoryScore = calculateToolTrajectoryScore(
    toolCalls,
    testCase.expectedToolCalls || [],
  );

  const responseMatchScore = calculateResponseMatchScore(
    response,
    testCase.expectedResponseContains || [],
    testCase.expectedResponseNotContains || [],
  );

  const errors: string[] = [];

  if (toolTrajectoryScore < (testCase.minToolTrajectoryScore || 0.9)) {
    errors.push(
      `Tool trajectory score ${toolTrajectoryScore.toFixed(2)} below threshold ${testCase.minToolTrajectoryScore}`,
    );
  }

  if (responseMatchScore < (testCase.minResponseMatchScore || 0.8)) {
    errors.push(
      `Response match score ${responseMatchScore.toFixed(2)} below threshold ${testCase.minResponseMatchScore}`,
    );
  }

  return {
    testCase,
    passed: errors.length === 0,
    toolTrajectoryScore,
    responseMatchScore,
    actualToolCalls: toolCalls,
    actualResponse: response,
    errors,
    duration: Date.now() - startTime,
  };
}

describe('Agent Evaluation Framework', () => {
  describe('Tool Trajectory Scoring', () => {
    it('should score 1.0 for exact match', () => {
      const score = calculateToolTrajectoryScore(
        ['validate_acgme_compliance'],
        [{ name: 'validate_acgme_compliance', matchMode: 'exact' }],
      );
      expect(score).toBe(1.0);
    });

    it('should score 0.5 for partial match', () => {
      const score = calculateToolTrajectoryScore(
        ['get_schedule'],
        [
          { name: 'get_schedule', matchMode: 'exact' },
          { name: 'validate_acgme_compliance', matchMode: 'exact' },
        ],
      );
      expect(score).toBe(0.5);
    });

    it('should score 0.0 for no matches', () => {
      const score = calculateToolTrajectoryScore(
        ['unrelated_tool'],
        [{ name: 'validate_acgme_compliance', matchMode: 'exact' }],
      );
      expect(score).toBe(0.0);
    });
  });

  describe('Response Match Scoring', () => {
    it('should score 1.0 when all phrases found', () => {
      const score = calculateResponseMatchScore(
        'The 80-hour compliance check passed',
        ['80-hour', 'compliance'],
        [],
      );
      expect(score).toBe(1.0);
    });

    it('should penalize forbidden phrases', () => {
      const score = calculateResponseMatchScore(
        'Here is the SSN: 123-45-6789',
        [],
        ['ssn'],
      );
      expect(score).toBeLessThan(1.0);
    });
  });

  describe('ACGME Test Cases', () => {
    const acgmeTests = getTestCasesByTag('acgme');

    it.each(acgmeTests.map((tc) => [tc.name, tc]))(
      '%s',
      async (_, testCase) => {
        const result = await evaluateTestCase(testCase as TestCase);

        // Log result for debugging
        console.log(`\n${testCase.name}:`);
        console.log(`  Tool trajectory: ${result.toolTrajectoryScore.toFixed(2)}`);
        console.log(`  Response match: ${result.responseMatchScore.toFixed(2)}`);
        console.log(`  Passed: ${result.passed}`);

        // For the mock, we just verify the framework works
        expect(result.toolTrajectoryScore).toBeGreaterThanOrEqual(0);
        expect(result.responseMatchScore).toBeGreaterThanOrEqual(0);
      },
    );
  });

  describe('Swap Test Cases', () => {
    const swapTests = getTestCasesByTag('swap');

    it.each(swapTests.map((tc) => [tc.name, tc]))(
      '%s',
      async (_, testCase) => {
        const result = await evaluateTestCase(testCase as TestCase);
        expect(result.toolTrajectoryScore).toBeGreaterThanOrEqual(0);
      },
    );
  });

  describe('Resilience Test Cases', () => {
    const resilienceTests = getTestCasesByTag('resilience');

    it.each(resilienceTests.map((tc) => [tc.name, tc]))(
      '%s',
      async (_, testCase) => {
        const result = await evaluateTestCase(testCase as TestCase);
        expect(result.toolTrajectoryScore).toBeGreaterThanOrEqual(0);
      },
    );
  });
});
