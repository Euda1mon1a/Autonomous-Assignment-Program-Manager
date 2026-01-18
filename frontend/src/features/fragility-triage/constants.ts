/**
 * Fragility Triage Constants
 *
 * Scenario definitions and mock data generation for the fragility triage visualization.
 */

import { DayData, Scenario } from './types';

/**
 * Black swan scenarios that can be injected to stress-test the system.
 */
export const SCENARIOS: Scenario[] = [
  {
    id: 'deployment',
    label: 'MAJ Deployment',
    impact: 15,
    description: 'Unexpected deployment of senior resident.',
  },
  {
    id: 'flu',
    label: 'Multi-Intern Flu',
    impact: 25,
    description: 'Viral outbreak affects 40% of intern class.',
  },
  {
    id: 'fmit',
    label: 'FMIT Anchor Loss',
    impact: 35,
    description: 'Critical loss of Faculty Medical Inpatient Team anchor.',
  },
];

/**
 * Generate mock day data for a 28-day cycle.
 * Creates randomized fragility levels with associated SPOFs and violations.
 */
export function generateMockDays(): DayData[] {
  return Array.from({ length: 28 }, (_, i) => {
    const isHighRisk = Math.random() < 0.25;
    const isMediumRisk = Math.random() < 0.4;

    let fragility = Math.random() * 0.3; // Base noise
    if (isHighRisk) fragility += 0.5;
    else if (isMediumRisk) fragility += 0.2;

    const spof =
      fragility > 0.7
        ? Math.random() > 0.5
          ? 'Faculty Alpha'
          : 'Faculty Beta'
        : null;

    const violations: string[] = [];
    if (fragility > 0.6) violations.push('1:2 Intern Supervision Ratio');
    if (fragility > 0.8) violations.push('ACGME Duty Hour Limit Risk');
    if (fragility > 0.5 && Math.random() > 0.5)
      violations.push('Clinic Throughput < 60%');

    return {
      day: i + 1,
      fragility: Math.min(fragility, 1.0),
      spof,
      violations,
      staffingLevel: 100 - fragility * 40, // Inverse correlation
    };
  });
}
