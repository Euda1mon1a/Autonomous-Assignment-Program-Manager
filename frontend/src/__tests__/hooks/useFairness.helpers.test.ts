import {
  getFairnessColorClass,
  getFairnessLabel,
  getFairnessStatus,
  getWorkloadDeviation,
  getDeviationColorClass,
} from '@/hooks/useFairness';

const workload = {
  personId: '1',
  personName: 'Faculty',
  name: 'Faculty',
  callCount: 1,
  fmitWeeks: 0,
  clinicHalfdays: 0,
  adminHalfdays: 0,
  academicHalfdays: 0,
  totalScore: 10,
  totalHalfDays: 0,
  callHalfDays: 0,
  fmitHalfDays: 0,
  clinicHalfDays: 0,
  adminHalfDays: 0,
};

describe('fairness helpers', () => {
  it('maps fairness index to color/label/status', () => {
    expect(getFairnessColorClass(0.96)).toBe('text-green-500');
    expect(getFairnessLabel(0.9)).toBe('Good');
    expect(getFairnessStatus(0.74)).toBe('critical');
  });

  it('calculates workload deviation and deviation color', () => {
    expect(getWorkloadDeviation(workload, 10)).toBe(0);
    expect(getWorkloadDeviation(workload, 5)).toBe(100);
    expect(getDeviationColorClass(5)).toBe('text-green-500');
    expect(getDeviationColorClass(20)).toBe('text-yellow-500');
    expect(getDeviationColorClass(30)).toBe('text-red-500');
  });
});
