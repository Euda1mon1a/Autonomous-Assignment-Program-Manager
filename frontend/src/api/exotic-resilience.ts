/**
 * Exotic Resilience API Client
 *
 * API functions for exotic resilience endpoints:
 * - Thermodynamics (entropy, phase transitions)
 * - Immune System (AIS anomaly detection)
 * - Hopfield Networks (energy landscapes, attractors)
 * - Metastability detection
 *
 * These endpoints power the Holographic Hub visualization with real backend data.
 *
 * @module api/exotic-resilience
 */
import { post } from "@/lib/api";

const BASE_URL = "/resilience/exotic";

// =============================================================================
// Request Types (camelCase for TypeScript)
// =============================================================================

export interface EntropyAnalysisRequest {
  scheduleId?: string;
  startDate?: string;
  endDate?: string;
}

export interface ImmuneAssessmentRequest {
  scheduleId?: string;
  featureVector?: number[];
}

export interface HopfieldEnergyRequest {
  startDate: string;
  endDate: string;
  scheduleId?: string;
}

export interface MetastabilityRequest {
  currentEnergy: number;
  energyLandscape: number[];
  barrierSamples: number[];
  temperature?: number;
}

export interface NearbyAttractorsRequest {
  startDate: string;
  endDate: string;
  maxDistance?: number; // 1-50, default 10
}

export interface BasinDepthRequest {
  startDate: string;
  endDate: string;
  numPerturbations?: number; // 10-1000, default 100
}

export interface SpuriousAttractorsRequest {
  startDate: string;
  endDate: string;
  searchRadius?: number; // 5-50, default 20
}

// =============================================================================
// Response Types (camelCase for TypeScript - axios converts from snake_case)
// =============================================================================

export interface EntropyMetricsResponse {
  personEntropy: number;
  rotationEntropy: number;
  timeEntropy: number;
  jointEntropy: number;
  mutualInformation: number;
  normalizedEntropy: number;
  entropyProductionRate: number;
  interpretation: string;
  recommendations: string[];
  computedAt: string;
  source: string;
}

export interface ImmuneAssessmentResponse {
  isAnomaly: boolean;
  anomalyScore: number;
  matchingDetectors: number;
  totalDetectors: number;
  closestDetectorDistance: number;
  suggestedRepairs: Array<{
    repairType: string;
    description: string;
    estimatedEffort: string;
  }>;
  immuneHealth: string;
  source: string;
}

export interface EnergyMetricsResponse {
  totalEnergy: number;
  normalizedEnergy: number;
  energyDensity: number;
  interactionEnergy: number;
  stabilityScore: number;
  gradientMagnitude: number;
  isLocalMinimum: boolean;
  distanceToMinimum: number;
}

export interface HopfieldEnergyResponse {
  analyzedAt: string;
  scheduleId: string | null;
  periodStart: string;
  periodEnd: string;
  assignmentsAnalyzed: number;
  metrics: EnergyMetricsResponse;
  stabilityLevel: string;
  interpretation: string;
  recommendations: string[];
  source: string;
}

export interface MetastabilityResponse {
  energy: number;
  barrierHeight: number;
  escapeRate: number;
  lifetime: number;
  isMetastable: boolean;
  stabilityScore: number;
  nearestStableState: number | null;
  riskLevel: string;
  recommendations: string[];
  source: string;
}

// Hopfield Attractor Types
export type StabilityLevel =
  | "very_stable"
  | "stable"
  | "marginally_stable"
  | "unstable"
  | "highly_unstable";

export type AttractorType =
  | "global_minimum"
  | "local_minimum"
  | "spurious"
  | "metastable"
  | "saddle_point";

export interface AttractorInfoResponse {
  attractorId: string;
  attractorType: AttractorType;
  energyLevel: number;
  basinDepth: number;
  basinVolume: number;
  hammingDistance: number;
  patternDescription: string;
  confidence: number;
}

export interface NearbyAttractorsResponse {
  analyzedAt: string;
  currentStateEnergy: number;
  attractorsFound: number;
  attractors: AttractorInfoResponse[];
  globalMinimumIdentified: boolean;
  currentBasinId: string | null;
  interpretation: string;
  recommendations: string[];
  source: string;
}

export interface BasinMetricsResponse {
  minEscapeEnergy: number;
  avgEscapeEnergy: number;
  maxEscapeEnergy: number;
  basinStabilityIndex: number;
  numEscapePaths: number;
  nearestSaddleDistance: number;
  basinRadius: number;
  criticalPerturbationSize: number;
}

export interface BasinDepthResponse {
  analyzedAt: string;
  scheduleId: string | null;
  attractorId: string;
  metrics: BasinMetricsResponse;
  stabilityLevel: StabilityLevel;
  isRobust: boolean;
  robustnessThreshold: number;
  interpretation: string;
  recommendations: string[];
  source: string;
}

export interface SpuriousAttractorInfoResponse {
  attractorId: string;
  energyLevel: number;
  basinSize: number;
  antiPatternType: string;
  description: string;
  riskLevel: string;
  distanceFromValid: number;
  probabilityOfCapture: number;
  mitigationStrategy: string;
}

export interface SpuriousAttractorsResponse {
  analyzedAt: string;
  spuriousAttractorsFound: number;
  spuriousAttractors: SpuriousAttractorInfoResponse[];
  totalBasinCoverage: number;
  highestRiskAttractor: string | null;
  isCurrentStateSpurious: boolean;
  interpretation: string;
  recommendations: string[];
  source: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Analyze schedule entropy using information theory.
 *
 * Calculates Shannon entropy across multiple dimensions:
 * - Person entropy: Workload distribution balance
 * - Rotation entropy: Service coverage diversity
 * - Time entropy: Temporal assignment balance
 *
 * @param request - Optional schedule ID and date range
 * @returns Entropy metrics with interpretation
 */
export async function analyzeEntropy(
  request: EntropyAnalysisRequest = {}
): Promise<EntropyMetricsResponse> {
  return post<EntropyMetricsResponse>(
    `${BASE_URL}/thermodynamics/entropy`,
    request
  );
}

/**
 * Assess schedule using artificial immune system.
 *
 * Detects anomalies by comparing schedule patterns against
 * learned "self" patterns using negative selection.
 *
 * @param request - Optional schedule ID or feature vector
 * @returns Immune assessment with anomaly detection results
 */
export async function assessImmune(
  request: ImmuneAssessmentRequest = {}
): Promise<ImmuneAssessmentResponse> {
  return post<ImmuneAssessmentResponse>(`${BASE_URL}/immune/assess`, request);
}

/**
 * Calculate Hopfield network energy for schedule stability.
 *
 * Models the schedule as a Hopfield network to analyze:
 * - Energy landscape topology
 * - Attractor basin depth
 * - Stability characteristics
 *
 * @param request - Date range and optional schedule ID
 * @returns Energy metrics with stability assessment
 */
export async function analyzeHopfieldEnergy(
  request: HopfieldEnergyRequest
): Promise<HopfieldEnergyResponse> {
  return post<HopfieldEnergyResponse>(`${BASE_URL}/hopfield/energy`, request);
}

/**
 * Find nearby attractors in the energy landscape.
 *
 * Identifies stable states near the current schedule configuration
 * using Hamming distance exploration.
 *
 * @param request - Date range and optional max distance
 * @returns Nearby attractors with basin information
 */
export async function findNearbyAttractors(
  request: NearbyAttractorsRequest
): Promise<NearbyAttractorsResponse> {
  return post<NearbyAttractorsResponse>(
    `${BASE_URL}/hopfield/attractors`,
    request
  );
}

/**
 * Measure basin of attraction depth.
 *
 * Determines how robust the current schedule state is by
 * analyzing escape energy barriers.
 *
 * @param request - Date range and perturbation count
 * @returns Basin metrics with robustness assessment
 */
export async function measureBasinDepth(
  request: BasinDepthRequest
): Promise<BasinDepthResponse> {
  return post<BasinDepthResponse>(`${BASE_URL}/hopfield/basin-depth`, request);
}

/**
 * Detect spurious attractors (scheduling anti-patterns).
 *
 * Identifies local minima that represent suboptimal or
 * invalid scheduling configurations.
 *
 * @param request - Date range and search radius
 * @returns Spurious attractors with risk assessment
 */
export async function detectSpuriousAttractors(
  request: SpuriousAttractorsRequest
): Promise<SpuriousAttractorsResponse> {
  return post<SpuriousAttractorsResponse>(
    `${BASE_URL}/hopfield/spurious`,
    request
  );
}

/**
 * Detect metastability in the schedule state.
 *
 * Analyzes whether the schedule is trapped in a local minimum
 * that could collapse under perturbation.
 *
 * @param request - Current energy and barrier information
 * @returns Metastability analysis with risk assessment
 */
export async function detectMetastability(
  request: MetastabilityRequest
): Promise<MetastabilityResponse> {
  return post<MetastabilityResponse>(
    `${BASE_URL}/exotic/metastability`,
    request
  );
}

// =============================================================================
// Aggregated Holographic Data Types
// =============================================================================

/**
 * Combined exotic resilience data for holographic visualization.
 * Aggregates data from multiple exotic endpoints.
 */
export interface ExoticResilienceData {
  entropy: EntropyMetricsResponse | null;
  immune: ImmuneAssessmentResponse | null;
  hopfield: HopfieldEnergyResponse | null;
  metastability: MetastabilityResponse | null;
  fetchedAt: string;
  errors: string[];
}

/**
 * Fetch all exotic resilience data in parallel.
 *
 * @param startDate - Start date for analysis (YYYY-MM-DD)
 * @param endDate - End date for analysis (YYYY-MM-DD)
 * @returns Combined exotic resilience data with any errors
 */
export async function fetchAllExoticData(
  startDate: string,
  endDate: string
): Promise<ExoticResilienceData> {
  const errors: string[] = [];

  // Run all requests in parallel, catching errors individually
  const [entropyResult, immuneResult, hopfieldResult, metastabilityResult] =
    await Promise.allSettled([
      analyzeEntropy({ startDate, endDate }),
      assessImmune({}),
      analyzeHopfieldEnergy({ startDate, endDate }),
      // Metastability needs sample data - provide reasonable defaults
      detectMetastability({
        currentEnergy: 0.5,
        energyLandscape: [0.3, 0.4, 0.5, 0.6, 0.7],
        barrierSamples: [0.1, 0.2, 0.15, 0.25, 0.1],
        temperature: 1.0,
      }),
    ]);

  // Extract results or capture errors
  const entropy =
    entropyResult.status === "fulfilled" ? entropyResult.value : null;
  if (entropyResult.status === "rejected") {
    errors.push(`Entropy: ${entropyResult.reason?.message || "Unknown error"}`);
  }

  const immune =
    immuneResult.status === "fulfilled" ? immuneResult.value : null;
  if (immuneResult.status === "rejected") {
    errors.push(`Immune: ${immuneResult.reason?.message || "Unknown error"}`);
  }

  const hopfield =
    hopfieldResult.status === "fulfilled" ? hopfieldResult.value : null;
  if (hopfieldResult.status === "rejected") {
    errors.push(
      `Hopfield: ${hopfieldResult.reason?.message || "Unknown error"}`
    );
  }

  const metastability =
    metastabilityResult.status === "fulfilled"
      ? metastabilityResult.value
      : null;
  if (metastabilityResult.status === "rejected") {
    errors.push(
      `Metastability: ${metastabilityResult.reason?.message || "Unknown error"}`
    );
  }

  return {
    entropy,
    immune,
    hopfield,
    metastability,
    fetchedAt: new Date().toISOString(),
    errors,
  };
}
