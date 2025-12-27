/**
 * Correlation Engine for Multi-Spectral Analysis
 *
 * Detects patterns across quantum, temporal, spectral, and evolutionary data.
 * Implements cross-wavelength correlation algorithms for composite insight discovery.
 */

import type {
  WavelengthChannel,
  WavelengthPair,
  WAVELENGTH_PAIRS,
  CorrelationResult,
  CorrelationPattern,
  CorrelationVisualizationData,
  QuantumChannelData,
  TemporalChannelData,
  SpectralChannelData,
  EvolutionaryChannelData,
  TimeSeriesPoint,
  SpectralPoint,
} from './types';

// ============================================================================
// Correlation Computation Functions
// ============================================================================

/**
 * Compute Pearson correlation coefficient between two arrays
 */
export function pearsonCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length || x.length === 0) return 0;

  const n = x.length;
  const sumX = x.reduce((a, b) => a + b, 0);
  const sumY = y.reduce((a, b) => a + b, 0);
  const sumXY = x.reduce((acc, xi, i) => acc + xi * y[i], 0);
  const sumX2 = x.reduce((a, b) => a + b * b, 0);
  const sumY2 = y.reduce((a, b) => a + b * b, 0);

  const numerator = n * sumXY - sumX * sumY;
  const denominator = Math.sqrt(
    (n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY)
  );

  return denominator === 0 ? 0 : numerator / denominator;
}

/**
 * Compute Spearman rank correlation
 */
export function spearmanCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length || x.length === 0) return 0;

  const rankX = computeRanks(x);
  const rankY = computeRanks(y);

  return pearsonCorrelation(rankX, rankY);
}

function computeRanks(arr: number[]): number[] {
  const sorted = arr.map((v, i) => ({ value: v, index: i }))
    .sort((a, b) => a.value - b.value);

  const ranks = new Array(arr.length);
  for (let i = 0; i < sorted.length; i++) {
    ranks[sorted[i].index] = i + 1;
  }
  return ranks;
}

/**
 * Compute mutual information between two discrete distributions
 */
export function mutualInformation(x: number[], y: number[], bins: number = 10): number {
  if (x.length !== y.length || x.length === 0) return 0;

  // Discretize continuous values into bins
  const xBinned = discretize(x, bins);
  const yBinned = discretize(y, bins);

  // Compute joint and marginal probabilities
  const n = x.length;
  const pXY: Map<string, number> = new Map();
  const pX: Map<number, number> = new Map();
  const pY: Map<number, number> = new Map();

  for (let i = 0; i < n; i++) {
    const key = `${xBinned[i]},${yBinned[i]}`;
    pXY.set(key, (pXY.get(key) || 0) + 1 / n);
    pX.set(xBinned[i], (pX.get(xBinned[i]) || 0) + 1 / n);
    pY.set(yBinned[i], (pY.get(yBinned[i]) || 0) + 1 / n);
  }

  // Compute mutual information
  let mi = 0;
  for (const [key, pxy] of pXY.entries()) {
    const [xi, yi] = key.split(',').map(Number);
    const px = pX.get(xi) || 0;
    const py = pY.get(yi) || 0;
    if (pxy > 0 && px > 0 && py > 0) {
      mi += pxy * Math.log2(pxy / (px * py));
    }
  }

  return mi;
}

function discretize(arr: number[], bins: number): number[] {
  const min = Math.min(...arr);
  const max = Math.max(...arr);
  const binWidth = (max - min) / bins || 1;

  return arr.map(v => Math.floor((v - min) / binWidth));
}

/**
 * Compute transfer entropy (directional information flow)
 */
export function transferEntropy(
  source: number[],
  target: number[],
  lag: number = 1,
  bins: number = 10
): number {
  if (source.length !== target.length || source.length <= lag) return 0;

  const n = source.length - lag;
  const sourceBinned = discretize(source.slice(0, n), bins);
  const targetPast = discretize(target.slice(0, n), bins);
  const targetFuture = discretize(target.slice(lag), bins);

  // Compute joint probabilities
  const pJoint: Map<string, number> = new Map();
  const pTargetPastFuture: Map<string, number> = new Map();
  const pSourceTargetPast: Map<string, number> = new Map();
  const pTargetPast: Map<number, number> = new Map();

  for (let i = 0; i < n; i++) {
    const jointKey = `${sourceBinned[i]},${targetPast[i]},${targetFuture[i]}`;
    const tpfKey = `${targetPast[i]},${targetFuture[i]}`;
    const stpKey = `${sourceBinned[i]},${targetPast[i]}`;

    pJoint.set(jointKey, (pJoint.get(jointKey) || 0) + 1 / n);
    pTargetPastFuture.set(tpfKey, (pTargetPastFuture.get(tpfKey) || 0) + 1 / n);
    pSourceTargetPast.set(stpKey, (pSourceTargetPast.get(stpKey) || 0) + 1 / n);
    pTargetPast.set(targetPast[i], (pTargetPast.get(targetPast[i]) || 0) + 1 / n);
  }

  // Compute transfer entropy
  let te = 0;
  for (const [key, pjoint] of pJoint.entries()) {
    const [s, tp, tf] = key.split(',').map(Number);
    const ptpf = pTargetPastFuture.get(`${tp},${tf}`) || 0;
    const pstp = pSourceTargetPast.get(`${s},${tp}`) || 0;
    const ptp = pTargetPast.get(tp) || 0;

    if (pjoint > 0 && ptpf > 0 && pstp > 0 && ptp > 0) {
      te += pjoint * Math.log2((pjoint * ptp) / (ptpf * pstp));
    }
  }

  return Math.max(0, te);
}

/**
 * Compute cross-correlation at different lags
 */
export function crossCorrelation(
  x: number[],
  y: number[],
  maxLag: number = 20
): Array<{ lag: number; correlation: number }> {
  const results: Array<{ lag: number; correlation: number }> = [];

  for (let lag = -maxLag; lag <= maxLag; lag++) {
    const xShifted = lag >= 0 ? x.slice(lag) : x.slice(0, x.length + lag);
    const yShifted = lag >= 0 ? y.slice(0, y.length - lag) : y.slice(-lag);

    if (xShifted.length > 0) {
      results.push({
        lag,
        correlation: pearsonCorrelation(xShifted, yShifted),
      });
    }
  }

  return results;
}

/**
 * Compute coherence spectrum (frequency domain correlation)
 */
export function coherenceSpectrum(
  x: number[],
  y: number[],
  windowSize: number = 64
): Array<{ frequency: number; coherence: number }> {
  // Simple implementation using FFT-based coherence
  const n = Math.min(x.length, y.length, windowSize);
  const results: Array<{ frequency: number; coherence: number }> = [];

  // Compute FFT of both signals
  const fftX = simpleFFT(x.slice(0, n));
  const fftY = simpleFFT(y.slice(0, n));

  // Compute cross-spectral density and individual PSDs
  for (let i = 0; i < n / 2; i++) {
    const sxy = fftX[i] * fftY[i]; // Simplified cross-spectral
    const sxx = fftX[i] * fftX[i];
    const syy = fftY[i] * fftY[i];

    const coherence = sxx > 0 && syy > 0
      ? Math.abs(sxy) / Math.sqrt(sxx * syy)
      : 0;

    results.push({
      frequency: i / n,
      coherence: Math.min(1, coherence),
    });
  }

  return results;
}

/**
 * Simple FFT implementation (magnitude only)
 */
function simpleFFT(x: number[]): number[] {
  const n = x.length;
  const result = new Array(n).fill(0);

  for (let k = 0; k < n; k++) {
    let real = 0;
    let imag = 0;
    for (let t = 0; t < n; t++) {
      const angle = (2 * Math.PI * k * t) / n;
      real += x[t] * Math.cos(angle);
      imag -= x[t] * Math.sin(angle);
    }
    result[k] = Math.sqrt(real * real + imag * imag);
  }

  return result;
}

// ============================================================================
// Pattern Detection Functions
// ============================================================================

/**
 * Detect resonance patterns between two signals
 */
export function detectResonance(
  primary: number[],
  secondary: number[],
  threshold: number = 0.7
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];
  const crossCorr = crossCorrelation(primary, secondary, 30);

  // Find peaks in cross-correlation
  for (let i = 1; i < crossCorr.length - 1; i++) {
    const curr = crossCorr[i];
    const prev = crossCorr[i - 1];
    const next = crossCorr[i + 1];

    if (
      Math.abs(curr.correlation) > threshold &&
      Math.abs(curr.correlation) > Math.abs(prev.correlation) &&
      Math.abs(curr.correlation) > Math.abs(next.correlation)
    ) {
      patterns.push({
        patternId: `resonance-lag${curr.lag}`,
        type: 'resonance',
        strength: Math.abs(curr.correlation),
        description: `Resonance detected at lag ${curr.lag} with correlation ${curr.correlation.toFixed(3)}`,
        involvedEntities: [],
      });
    }
  }

  return patterns;
}

/**
 * Detect coupling patterns (strong local correlations)
 */
export function detectCoupling(
  data: Array<{ id: string; primary: number; secondary: number }>,
  threshold: number = 0.6
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Group by similar values and detect clusters
  const clusters = clusterByProximity(data);

  for (const cluster of clusters) {
    if (cluster.length >= 3) {
      const primaryValues = cluster.map(d => d.primary);
      const secondaryValues = cluster.map(d => d.secondary);
      const localCorr = pearsonCorrelation(primaryValues, secondaryValues);

      if (Math.abs(localCorr) > threshold) {
        patterns.push({
          patternId: `coupling-${cluster[0].id}`,
          type: 'coupling',
          strength: Math.abs(localCorr),
          description: `Strong local coupling detected among ${cluster.length} entities`,
          involvedEntities: cluster.map(d => d.id),
        });
      }
    }
  }

  return patterns;
}

function clusterByProximity(
  data: Array<{ id: string; primary: number; secondary: number }>,
  eps: number = 0.2
): Array<Array<{ id: string; primary: number; secondary: number }>> {
  const clusters: Array<Array<{ id: string; primary: number; secondary: number }>> = [];
  const visited = new Set<string>();

  for (const point of data) {
    if (visited.has(point.id)) continue;

    const cluster: Array<{ id: string; primary: number; secondary: number }> = [];
    const queue = [point];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current.id)) continue;

      visited.add(current.id);
      cluster.push(current);

      // Find neighbors
      for (const other of data) {
        if (!visited.has(other.id)) {
          const dist = Math.sqrt(
            Math.pow(current.primary - other.primary, 2) +
            Math.pow(current.secondary - other.secondary, 2)
          );
          if (dist < eps) {
            queue.push(other);
          }
        }
      }
    }

    if (cluster.length > 0) {
      clusters.push(cluster);
    }
  }

  return clusters;
}

/**
 * Detect cascade patterns (sequential activation)
 */
export function detectCascade(
  timeSeries: TimeSeriesPoint[],
  threshold: number = 0.5
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Detect sequences where peaks follow each other
  const peaks = findPeaks(timeSeries.map(p => p.value));
  const cascadeGroups: number[][] = [];
  let currentGroup: number[] = [];

  for (let i = 0; i < peaks.length; i++) {
    if (currentGroup.length === 0) {
      currentGroup.push(peaks[i]);
    } else {
      const lastPeak = currentGroup[currentGroup.length - 1];
      if (peaks[i] - lastPeak <= 5) { // Within 5 time steps
        currentGroup.push(peaks[i]);
      } else {
        if (currentGroup.length >= 3) {
          cascadeGroups.push([...currentGroup]);
        }
        currentGroup = [peaks[i]];
      }
    }
  }

  if (currentGroup.length >= 3) {
    cascadeGroups.push(currentGroup);
  }

  for (let i = 0; i < cascadeGroups.length; i++) {
    const group = cascadeGroups[i];
    patterns.push({
      patternId: `cascade-${i}`,
      type: 'cascade',
      strength: group.length / peaks.length,
      description: `Cascade of ${group.length} sequential activations detected`,
      involvedEntities: group.map(idx => timeSeries[idx]?.metadata?.personId || `point-${idx}`).filter(Boolean) as string[],
      temporalSpan: {
        start: timeSeries[group[0]]?.timestamp || '',
        end: timeSeries[group[group.length - 1]]?.timestamp || '',
      },
    });
  }

  return patterns;
}

function findPeaks(values: number[]): number[] {
  const peaks: number[] = [];
  for (let i = 1; i < values.length - 1; i++) {
    if (values[i] > values[i - 1] && values[i] > values[i + 1]) {
      peaks.push(i);
    }
  }
  return peaks;
}

/**
 * Detect feedback loops
 */
export function detectFeedback(
  primary: number[],
  secondary: number[]
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Compute transfer entropy in both directions
  const teForward = transferEntropy(primary, secondary);
  const teBackward = transferEntropy(secondary, primary);

  // Feedback loop if significant transfer in both directions
  if (teForward > 0.1 && teBackward > 0.1) {
    const ratio = Math.min(teForward, teBackward) / Math.max(teForward, teBackward);
    if (ratio > 0.3) { // Reasonably balanced bidirectional flow
      patterns.push({
        patternId: 'feedback-loop',
        type: 'feedback',
        strength: (teForward + teBackward) / 2,
        description: `Feedback loop detected: forward TE=${teForward.toFixed(3)}, backward TE=${teBackward.toFixed(3)}`,
        involvedEntities: [],
      });
    }
  }

  return patterns;
}

/**
 * Detect synchronization patterns
 */
export function detectSynchronization(
  signals: Array<{ id: string; values: number[] }>,
  threshold: number = 0.8
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];
  const syncGroups: string[][] = [];

  // Find groups of highly synchronized signals
  const visited = new Set<string>();

  for (const signal of signals) {
    if (visited.has(signal.id)) continue;

    const group = [signal.id];
    visited.add(signal.id);

    for (const other of signals) {
      if (!visited.has(other.id)) {
        const corr = pearsonCorrelation(signal.values, other.values);
        if (Math.abs(corr) > threshold) {
          group.push(other.id);
          visited.add(other.id);
        }
      }
    }

    if (group.length >= 2) {
      syncGroups.push(group);
    }
  }

  for (let i = 0; i < syncGroups.length; i++) {
    const group = syncGroups[i];
    patterns.push({
      patternId: `sync-group-${i}`,
      type: 'synchronization',
      strength: group.length / signals.length,
      description: `Synchronized group of ${group.length} entities`,
      involvedEntities: group,
    });
  }

  return patterns;
}

// ============================================================================
// Cross-Wavelength Correlation Functions
// ============================================================================

/**
 * Extract time series from quantum channel data
 */
export function extractQuantumTimeSeries(data: QuantumChannelData): number[] {
  return data.states.map(s => s.coherence);
}

/**
 * Extract time series from temporal channel data
 */
export function extractTemporalTimeSeries(data: TemporalChannelData): number[] {
  return data.timeSeries.map(p => p.value);
}

/**
 * Extract dominant frequency from spectral data
 */
export function extractSpectralFeatures(data: SpectralChannelData): number[] {
  return data.powerSpectrum.map(p => p.power);
}

/**
 * Extract fitness values from evolutionary data
 */
export function extractEvolutionaryTimeSeries(data: EvolutionaryChannelData): number[] {
  return data.populationHistory.map(p => p.totalFitness);
}

/**
 * Compute correlation between two wavelength channels
 */
export function computeWavelengthCorrelation(
  pair: WavelengthPair,
  primaryData: number[],
  secondaryData: number[]
): CorrelationResult {
  // Ensure same length
  const minLength = Math.min(primaryData.length, secondaryData.length);
  const primary = primaryData.slice(0, minLength);
  const secondary = secondaryData.slice(0, minLength);

  // Compute various correlation metrics
  const correlation = pearsonCorrelation(primary, secondary);
  const mi = mutualInformation(primary, secondary);
  const teForward = transferEntropy(primary, secondary);
  const teBackward = transferEntropy(secondary, primary);

  // Detect patterns
  const patterns: CorrelationPattern[] = [
    ...detectResonance(primary, secondary),
    ...detectFeedback(primary, secondary),
  ];

  // Add coupling patterns if we have entity IDs
  const entityData = primary.map((p, i) => ({
    id: `entity-${i}`,
    primary: p,
    secondary: secondary[i],
  }));
  patterns.push(...detectCoupling(entityData));

  // Generate visualization data
  const visualizationData = generateCorrelationVisualization(
    primary,
    secondary,
    entityData.map(e => e.id)
  );

  // Compute significance (simplified t-test based)
  const n = minLength;
  const t = correlation * Math.sqrt((n - 2) / (1 - correlation * correlation + 0.0001));
  const significance = 2 * (1 - tDistributionCDF(Math.abs(t), n - 2));

  return {
    pair,
    correlation,
    significance,
    mutualInformation: mi,
    transferEntropy: {
      primaryToSecondary: teForward,
      secondaryToPrimary: teBackward,
    },
    patterns,
    visualizationData,
  };
}

/**
 * Simplified t-distribution CDF approximation
 */
function tDistributionCDF(t: number, df: number): number {
  // Use normal approximation for large df
  if (df > 30) {
    return normalCDF(t);
  }
  // Simple approximation for smaller df
  const x = df / (df + t * t);
  return 1 - 0.5 * Math.pow(x, df / 2);
}

function normalCDF(x: number): number {
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;

  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x) / Math.sqrt(2);

  const t = 1.0 / (1.0 + p * x);
  const y = 1.0 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

  return 0.5 * (1.0 + sign * y);
}

/**
 * Generate visualization data for correlation
 */
function generateCorrelationVisualization(
  primary: number[],
  secondary: number[],
  entityIds: string[]
): CorrelationVisualizationData {
  // Normalize to 0-1 range for visualization
  const normalizedPrimary = normalize(primary);
  const normalizedSecondary = normalize(secondary);

  // Create scatter points
  const scatterPoints = normalizedPrimary.map((x, i) => ({
    x,
    y: normalizedSecondary[i],
    entityId: entityIds[i],
    metadata: { originalX: primary[i], originalY: secondary[i] },
  }));

  // Compute regression line
  const correlation = pearsonCorrelation(normalizedPrimary, normalizedSecondary);
  const meanX = normalizedPrimary.reduce((a, b) => a + b, 0) / normalizedPrimary.length;
  const meanY = normalizedSecondary.reduce((a, b) => a + b, 0) / normalizedSecondary.length;
  const stdX = Math.sqrt(normalizedPrimary.reduce((a, b) => a + (b - meanX) ** 2, 0) / normalizedPrimary.length);
  const stdY = Math.sqrt(normalizedSecondary.reduce((a, b) => a + (b - meanY) ** 2, 0) / normalizedSecondary.length);

  const slope = stdX > 0 ? correlation * (stdY / stdX) : 0;
  const intercept = meanY - slope * meanX;
  const r2 = correlation * correlation;

  // Generate density contours (simplified 2D histogram)
  const densityContours = generateDensityContours(normalizedPrimary, normalizedSecondary);

  // Generate correlation surface
  const resolution = 20;
  const xGrid = Array.from({ length: resolution }, (_, i) => i / (resolution - 1));
  const yGrid = Array.from({ length: resolution }, (_, i) => i / (resolution - 1));
  const zValues = generateCorrelationSurface(normalizedPrimary, normalizedSecondary, resolution);

  return {
    scatterPoints,
    regressionLine: { slope, intercept, r2 },
    densityContours,
    correlationSurface: { xGrid, yGrid, zValues },
  };
}

function normalize(arr: number[]): number[] {
  const min = Math.min(...arr);
  const max = Math.max(...arr);
  const range = max - min || 1;
  return arr.map(v => (v - min) / range);
}

function generateDensityContours(
  x: number[],
  y: number[]
): Array<{ level: number; path: Array<{ x: number; y: number }> }> {
  // Simple 2D histogram-based density estimation
  const bins = 10;
  const histogram: number[][] = Array(bins).fill(null).map(() => Array(bins).fill(0));

  for (let i = 0; i < x.length; i++) {
    const bx = Math.min(Math.floor(x[i] * bins), bins - 1);
    const by = Math.min(Math.floor(y[i] * bins), bins - 1);
    histogram[by][bx]++;
  }

  // Normalize
  const maxCount = Math.max(...histogram.flat());
  const normalizedHist = histogram.map(row => row.map(v => v / (maxCount || 1)));

  // Generate contours at different levels
  const levels = [0.25, 0.5, 0.75];
  const contours: Array<{ level: number; path: Array<{ x: number; y: number }> }> = [];

  for (const level of levels) {
    const path: Array<{ x: number; y: number }> = [];

    // Simple contour extraction (marching squares simplified)
    for (let i = 0; i < bins - 1; i++) {
      for (let j = 0; j < bins - 1; j++) {
        const avg = (
          normalizedHist[i][j] +
          normalizedHist[i][j + 1] +
          normalizedHist[i + 1][j] +
          normalizedHist[i + 1][j + 1]
        ) / 4;

        if (Math.abs(avg - level) < 0.15) {
          path.push({
            x: (j + 0.5) / bins,
            y: (i + 0.5) / bins,
          });
        }
      }
    }

    if (path.length > 0) {
      contours.push({ level, path });
    }
  }

  return contours;
}

function generateCorrelationSurface(
  x: number[],
  y: number[],
  resolution: number
): number[][] {
  const surface: number[][] = [];

  for (let i = 0; i < resolution; i++) {
    const row: number[] = [];
    for (let j = 0; j < resolution; j++) {
      const cx = j / (resolution - 1);
      const cy = i / (resolution - 1);

      // Compute local correlation strength (Gaussian weighted)
      let weightedCorr = 0;
      let totalWeight = 0;

      for (let k = 0; k < x.length; k++) {
        const dist = Math.sqrt((x[k] - cx) ** 2 + (y[k] - cy) ** 2);
        const weight = Math.exp(-dist * dist * 10);
        weightedCorr += weight * (x[k] - 0.5) * (y[k] - 0.5);
        totalWeight += weight;
      }

      row.push(totalWeight > 0 ? weightedCorr / totalWeight : 0);
    }
    surface.push(row);
  }

  return surface;
}

// ============================================================================
// Composite Insight Detection
// ============================================================================

/**
 * Detect circadian resonance (temporal × spectral)
 */
export function detectCircadianResonance(
  temporal: TemporalChannelData,
  spectral: SpectralChannelData
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Look for 24-hour period in spectral harmonics
  const dailyFreq = 1 / 24; // Cycles per hour
  const nearbyHarmonics = spectral.harmonics.filter(h =>
    Math.abs(h.frequency - dailyFreq) < 0.01 ||
    Math.abs(h.frequency - dailyFreq * 2) < 0.01 // Also check 12-hour
  );

  if (nearbyHarmonics.length > 0) {
    const strongestHarmonic = nearbyHarmonics.reduce((a, b) =>
      a.amplitude > b.amplitude ? a : b
    );

    patterns.push({
      patternId: 'circadian-resonance',
      type: 'resonance',
      strength: strongestHarmonic.amplitude,
      description: `Circadian resonance detected at ${(1 / strongestHarmonic.frequency).toFixed(1)}h period`,
      involvedEntities: [],
    });
  }

  // Check phase consistency in temporal clusters
  const dailyClusters = temporal.clusters.filter(c => c.pattern === 'daily');
  if (dailyClusters.length > 0) {
    const avgStrength = dailyClusters.reduce((a, b) => a + b.strength, 0) / dailyClusters.length;
    if (avgStrength > 0.5) {
      patterns.push({
        patternId: 'daily-pattern-sync',
        type: 'synchronization',
        strength: avgStrength,
        description: `${dailyClusters.length} daily pattern clusters detected with avg strength ${avgStrength.toFixed(2)}`,
        involvedEntities: dailyClusters.flatMap(c => c.members),
      });
    }
  }

  return patterns;
}

/**
 * Detect quantum fitness landscape (quantum × evolutionary)
 */
export function detectQuantumFitness(
  quantum: QuantumChannelData,
  evolutionary: EvolutionaryChannelData
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Correlate quantum coherence with fitness
  const coherenceValues = quantum.states.map(s => s.coherence);
  const fitnessValues = evolutionary.fitnessLandscape.map(p => p.fitness);

  if (coherenceValues.length > 0 && fitnessValues.length > 0) {
    // Resample to same length
    const minLen = Math.min(coherenceValues.length, fitnessValues.length);
    const corr = pearsonCorrelation(
      coherenceValues.slice(0, minLen),
      fitnessValues.slice(0, minLen)
    );

    if (Math.abs(corr) > 0.5) {
      patterns.push({
        patternId: 'quantum-fitness-coupling',
        type: 'coupling',
        strength: Math.abs(corr),
        description: `Quantum coherence ${corr > 0 ? 'positively' : 'negatively'} coupled with fitness (r=${corr.toFixed(3)})`,
        involvedEntities: quantum.states.map(s => s.stateId),
      });
    }
  }

  // Check for quantum tunneling between fitness basins
  const attractors = evolutionary.attractors;
  const highCoherenceStates = quantum.states.filter(s => s.coherence > 0.7);

  if (attractors.length > 1 && highCoherenceStates.length > 0) {
    patterns.push({
      patternId: 'quantum-tunneling-potential',
      type: 'cascade',
      strength: highCoherenceStates.length / quantum.states.length,
      description: `${highCoherenceStates.length} high-coherence states may tunnel between ${attractors.length} fitness basins`,
      involvedEntities: highCoherenceStates.map(s => s.stateId),
    });
  }

  return patterns;
}

/**
 * Detect harmonic stress patterns (spectral × thermal)
 */
export function detectHarmonicStress(
  spectral: SpectralChannelData,
  thermal: { points: Array<{ value: number; entityId: string }> }
): CorrelationPattern[] {
  const patterns: CorrelationPattern[] = [];

  // Check if high-frequency components correlate with thermal hotspots
  const highFreqPower = spectral.harmonics
    .filter(h => h.harmonic >= 3)
    .reduce((sum, h) => sum + h.amplitude, 0);

  const avgThermal = thermal.points.reduce((sum, p) => sum + p.value, 0) / thermal.points.length;
  const hotspots = thermal.points.filter(p => p.value > avgThermal * 1.5);

  if (highFreqPower > 0.3 && hotspots.length > 0) {
    patterns.push({
      patternId: 'harmonic-stress',
      type: 'coupling',
      strength: Math.min(1, highFreqPower * (hotspots.length / thermal.points.length) * 3),
      description: `High-frequency schedule oscillations (power=${highFreqPower.toFixed(2)}) correlated with ${hotspots.length} thermal hotspots`,
      involvedEntities: hotspots.map(h => h.entityId),
    });
  }

  return patterns;
}

// ============================================================================
// Correlation Engine Class
// ============================================================================

export class CorrelationEngine {
  private channelData: Partial<Record<WavelengthChannel, unknown>> = {};
  private correlationCache: Map<string, CorrelationResult> = new Map();

  /**
   * Update data for a wavelength channel
   */
  updateChannelData(channel: WavelengthChannel, data: unknown): void {
    this.channelData[channel] = data;
    // Invalidate cached correlations involving this channel
    for (const key of this.correlationCache.keys()) {
      if (key.includes(channel)) {
        this.correlationCache.delete(key);
      }
    }
  }

  /**
   * Get correlation between two channels
   */
  getCorrelation(pair: WavelengthPair): CorrelationResult | null {
    const cacheKey = `${pair.primary}-${pair.secondary}`;

    if (this.correlationCache.has(cacheKey)) {
      return this.correlationCache.get(cacheKey)!;
    }

    const primaryData = this.channelData[pair.primary];
    const secondaryData = this.channelData[pair.secondary];

    if (!primaryData || !secondaryData) {
      return null;
    }

    // Extract time series based on channel type
    const primarySeries = this.extractTimeSeries(pair.primary, primaryData);
    const secondarySeries = this.extractTimeSeries(pair.secondary, secondaryData);

    if (!primarySeries || !secondarySeries) {
      return null;
    }

    const result = computeWavelengthCorrelation(pair, primarySeries, secondarySeries);

    // Add composite patterns based on channel pair
    if (pair.primary === 'temporal' && pair.secondary === 'spectral') {
      result.patterns.push(...detectCircadianResonance(
        primaryData as TemporalChannelData,
        secondaryData as SpectralChannelData
      ));
    } else if (pair.primary === 'quantum' && pair.secondary === 'evolutionary') {
      result.patterns.push(...detectQuantumFitness(
        primaryData as QuantumChannelData,
        secondaryData as EvolutionaryChannelData
      ));
    }

    this.correlationCache.set(cacheKey, result);
    return result;
  }

  /**
   * Get all correlations for active channels
   */
  getAllCorrelations(pairs: WavelengthPair[]): CorrelationResult[] {
    return pairs
      .map(pair => this.getCorrelation(pair))
      .filter((r): r is CorrelationResult => r !== null);
  }

  /**
   * Extract time series from channel data
   */
  private extractTimeSeries(channel: WavelengthChannel, data: unknown): number[] | null {
    switch (channel) {
      case 'quantum':
        return extractQuantumTimeSeries(data as QuantumChannelData);
      case 'temporal':
        return extractTemporalTimeSeries(data as TemporalChannelData);
      case 'spectral':
        return extractSpectralFeatures(data as SpectralChannelData);
      case 'evolutionary':
        return extractEvolutionaryTimeSeries(data as EvolutionaryChannelData);
      case 'thermal':
        // Thermal is typically spatial, not time series
        return (data as { values: number[] }).values || null;
      case 'topological':
        // Topological metrics as time series
        return (data as { metrics: number[] }).metrics || null;
      default:
        return null;
    }
  }

  /**
   * Clear all cached correlations
   */
  clearCache(): void {
    this.correlationCache.clear();
  }

  /**
   * Get statistics about current correlations
   */
  getStatistics(): {
    channelsLoaded: WavelengthChannel[];
    correlationsComputed: number;
    strongestCorrelation: { pair: WavelengthPair; value: number } | null;
    totalPatterns: number;
  } {
    const channelsLoaded = Object.keys(this.channelData) as WavelengthChannel[];
    const correlationsComputed = this.correlationCache.size;

    let strongest: { pair: WavelengthPair; value: number } | null = null;
    let totalPatterns = 0;

    for (const result of this.correlationCache.values()) {
      totalPatterns += result.patterns.length;
      if (!strongest || Math.abs(result.correlation) > Math.abs(strongest.value)) {
        strongest = { pair: result.pair, value: result.correlation };
      }
    }

    return {
      channelsLoaded,
      correlationsComputed,
      strongestCorrelation: strongest,
      totalPatterns,
    };
  }
}

// Export singleton instance for convenience
export const correlationEngine = new CorrelationEngine();
