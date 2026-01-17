/**
 * Data Ingest Pipeline for Holographic Visualization Hub
 *
 * This pipeline receives constraint data from all Far Realm sessions (1-8),
 * normalizes it to a standard format, performs dimensionality reduction,
 * and prepares it for 3D rendering.
 *
 * Pipeline stages:
 * 1. Ingest: Receive session data exports
 * 2. Normalize: Convert to standard ConstraintDataPoint format
 * 3. Merge: Combine all session data, deduplicate constraints
 * 4. Project: Reduce N-dimensions to 3D using PCA/UMAP/t-SNE
 * 5. Colorize: Apply visual properties based on constraint type and layer
 * 6. Output: Generate ManifoldPoint array for rendering
 */

import {
  ConstraintDataPoint,
  ConstraintType,
  SpectralLayer,
  SessionDataExport,
  HolographicDataset,
  ManifoldPoint,
  ProjectionConfig,
  CONSTRAINT_COLORS,
  LAYER_COLORS,
} from "./types";

// ============================================================================
// Dimensionality Reduction Algorithms
// ============================================================================

/**
 * Principal Component Analysis (PCA) implementation
 * Projects N-dimensional data to 3D while preserving maximum variance
 */
export function projectPCA(
  data: number[][],
  nComponents = 3
): { projected: number[][]; explainedVariance: number[] } {
  if (data.length === 0) {
    return { projected: [], explainedVariance: [] };
  }

  const n = data.length;
  const m = data[0].length;

  // Step 1: Center the data (subtract mean)
  const means = new Array(m).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < m; j++) {
      means[j] += data[i][j];
    }
  }
  for (let j = 0; j < m; j++) {
    means[j] /= n;
  }

  const centered = data.map((row) => row.map((val, j) => val - means[j]));

  // Step 2: Compute covariance matrix
  const covariance: number[][] = Array(m)
    .fill(null)
    .map(() => Array(m).fill(0));

  for (let i = 0; i < m; i++) {
    for (let j = 0; j < m; j++) {
      let sum = 0;
      for (let k = 0; k < n; k++) {
        sum += centered[k][i] * centered[k][j];
      }
      covariance[i][j] = sum / (n - 1);
    }
  }

  // Step 3: Power iteration for eigenvalue decomposition (simplified)
  // For production, use a proper linear algebra library
  const eigenvectors: number[][] = [];
  const eigenvalues: number[] = [];

  for (let comp = 0; comp < Math.min(nComponents, m); comp++) {
    // Start with random vector
    let vector = new Array(m).fill(0).map(() => Math.random() - 0.5);
    let eigenvalue = 0;

    // Power iteration
    for (let iter = 0; iter < 100; iter++) {
      // Multiply by covariance matrix
      const newVector = new Array(m).fill(0);
      for (let i = 0; i < m; i++) {
        for (let j = 0; j < m; j++) {
          newVector[i] += covariance[i][j] * vector[j];
        }
      }

      // Deflate by previous eigenvectors
      for (const prev of eigenvectors) {
        const dot = newVector.reduce((sum, v, i) => sum + v * prev[i], 0);
        for (let i = 0; i < m; i++) {
          newVector[i] -= dot * prev[i];
        }
      }

      // Compute magnitude
      const mag = Math.sqrt(newVector.reduce((sum, v) => sum + v * v, 0));
      if (mag < 1e-10) break;

      // Normalize
      for (let i = 0; i < m; i++) {
        newVector[i] /= mag;
      }

      eigenvalue = mag;
      vector = newVector;
    }

    eigenvectors.push(vector);
    eigenvalues.push(eigenvalue);
  }

  // Step 4: Project data onto principal components
  const projected = centered.map((row) => {
    return eigenvectors.map((ev) => row.reduce((sum, v, i) => sum + v * ev[i], 0));
  });

  // Compute explained variance ratios
  const totalVariance = eigenvalues.reduce((a, b) => a + b, 0);
  const explainedVariance = eigenvalues.map((ev) => ev / (totalVariance || 1));

  return { projected, explainedVariance };
}

/**
 * UMAP-inspired projection (simplified implementation)
 * Uses local neighborhood preservation with fuzzy simplicial sets
 */
export function projectUMAP(
  data: number[][],
  config: { nNeighbors: number; minDist: number }
): number[][] {
  if (data.length === 0) return [];

  const n = data.length;
  const { nNeighbors, minDist } = config;

  // Step 1: Compute k-nearest neighbors graph
  const distances: { idx: number; dist: number }[][] = data.map((point, i) => {
    const dists = data.map((other, j) => ({
      idx: j,
      dist:
        i === j ? Infinity : Math.sqrt(point.reduce((sum, v, k) => sum + (v - other[k]) ** 2, 0)),
    }));
    return dists.sort((a, b) => a.dist - b.dist).slice(0, nNeighbors);
  });

  // Step 2: Initialize low-dimensional embedding (spectral-like)
  const embedding: number[][] = data.map((_, i) => {
    const angle = (2 * Math.PI * i) / n;
    const radius = 1 + Math.random() * 0.5;
    return [
      Math.cos(angle) * radius + (Math.random() - 0.5) * 0.1,
      Math.sin(angle) * radius + (Math.random() - 0.5) * 0.1,
      (Math.random() - 0.5) * 2,
    ];
  });

  // Step 3: Gradient descent optimization (simplified)
  const learningRate = 1.0;
  const nIterations = 100;

  for (let iter = 0; iter < nIterations; iter++) {
    const alpha = learningRate * (1 - iter / nIterations);

    for (let i = 0; i < n; i++) {
      // Attractive forces from neighbors
      for (const neighbor of distances[i]) {
        const j = neighbor.idx;
        if (j === i) continue;

        const diff = embedding[i].map((v, k) => v - embedding[j][k]);
        const dist = Math.sqrt(diff.reduce((sum, v) => sum + v * v, 0)) + 1e-6;

        // Attraction
        const attraction = (2 * alpha * Math.max(0, dist - minDist)) / dist;
        for (let k = 0; k < 3; k++) {
          embedding[i][k] -= attraction * diff[k];
        }
      }

      // Repulsive forces from random samples
      const nSamples = Math.min(5, n - 1);
      for (let s = 0; s < nSamples; s++) {
        const j = Math.floor(Math.random() * n);
        if (j === i) continue;

        const diff = embedding[i].map((v, k) => v - embedding[j][k]);
        const dist = Math.sqrt(diff.reduce((sum, v) => sum + v * v, 0)) + 1e-6;

        // Repulsion (only for non-neighbors)
        if (!distances[i].some((d) => d.idx === j)) {
          const repulsion = (alpha / (dist * dist + 1));
          for (let k = 0; k < 3; k++) {
            embedding[i][k] += repulsion * diff[k];
          }
        }
      }
    }
  }

  return embedding;
}

/**
 * t-SNE projection (simplified implementation)
 * Preserves local structure through probability distributions
 */
export function projectTSNE(
  data: number[][],
  config: { perplexity: number; learningRate: number; nIterations: number }
): number[][] {
  if (data.length === 0) return [];

  const n = data.length;
  const { perplexity, learningRate, nIterations } = config;

  // Step 1: Compute pairwise distances
  const distances: number[][] = data.map((point) =>
    data.map((other) =>
      Math.sqrt(point.reduce((sum, v, k) => sum + (v - other[k]) ** 2, 0))
    )
  );

  // Step 2: Compute P matrix (joint probabilities in high-D)
  const P: number[][] = Array(n)
    .fill(null)
    .map(() => Array(n).fill(0));

  // Compute conditional probabilities with binary search for perplexity
  for (let i = 0; i < n; i++) {
    let beta = 1.0;
    let betaMin = -Infinity;
    let betaMax = Infinity;

    for (let iter = 0; iter < 50; iter++) {
      // Compute conditional probabilities
      let sum = 0;
      for (let j = 0; j < n; j++) {
        if (i !== j) {
          P[i][j] = Math.exp(-beta * distances[i][j] * distances[i][j]);
          sum += P[i][j];
        }
      }

      // Normalize
      for (let j = 0; j < n; j++) {
        P[i][j] /= sum + 1e-10;
      }

      // Compute entropy
      let H = 0;
      for (let j = 0; j < n; j++) {
        if (i !== j && P[i][j] > 1e-10) {
          H -= P[i][j] * Math.log2(P[i][j]);
        }
      }

      const Hdiff = H - Math.log2(perplexity);
      if (Math.abs(Hdiff) < 1e-5) break;

      if (Hdiff > 0) {
        betaMin = beta;
        beta = betaMax === Infinity ? beta * 2 : (beta + betaMax) / 2;
      } else {
        betaMax = beta;
        beta = betaMin === -Infinity ? beta / 2 : (beta + betaMin) / 2;
      }
    }
  }

  // Symmetrize P
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const pij = (P[i][j] + P[j][i]) / (2 * n);
      P[i][j] = pij;
      P[j][i] = pij;
    }
  }

  // Step 3: Initialize embedding
  const Y: number[][] = Array(n)
    .fill(null)
    .map(() => [
      (Math.random() - 0.5) * 0.01,
      (Math.random() - 0.5) * 0.01,
      (Math.random() - 0.5) * 0.01,
    ]);

  const velocities: number[][] = Array(n)
    .fill(null)
    .map(() => [0, 0, 0]);

  // Step 4: Gradient descent
  for (let iter = 0; iter < nIterations; iter++) {
    // Compute Q matrix (joint probabilities in low-D)
    const Q: number[][] = Array(n)
      .fill(null)
      .map(() => Array(n).fill(0));
    let Qsum = 0;

    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const dist =
          (Y[i][0] - Y[j][0]) ** 2 + (Y[i][1] - Y[j][1]) ** 2 + (Y[i][2] - Y[j][2]) ** 2;
        const qij = 1 / (1 + dist);
        Q[i][j] = qij;
        Q[j][i] = qij;
        Qsum += 2 * qij;
      }
    }

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        Q[i][j] /= Qsum + 1e-10;
      }
    }

    // Compute gradients
    const gradients: number[][] = Array(n)
      .fill(null)
      .map(() => [0, 0, 0]);

    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (i !== j) {
          const dist =
            (Y[i][0] - Y[j][0]) ** 2 + (Y[i][1] - Y[j][1]) ** 2 + (Y[i][2] - Y[j][2]) ** 2;
          const pq = P[i][j] - Q[i][j];
          const multiplier = 4 * pq / (1 + dist);

          for (let k = 0; k < 3; k++) {
            gradients[i][k] += multiplier * (Y[i][k] - Y[j][k]);
          }
        }
      }
    }

    // Update positions with momentum
    const momentum = iter < 250 ? 0.5 : 0.8;
    for (let i = 0; i < n; i++) {
      for (let k = 0; k < 3; k++) {
        velocities[i][k] = momentum * velocities[i][k] - learningRate * gradients[i][k];
        Y[i][k] += velocities[i][k];
      }
    }
  }

  return Y;
}

// ============================================================================
// Pipeline Functions
// ============================================================================

/**
 * Normalize raw session data to standard ConstraintDataPoint format
 */
export function normalizeSessionData(sessionData: SessionDataExport): ConstraintDataPoint[] {
  return sessionData.constraints.map((constraint) => ({
    ...constraint,
    layer: sessionData.sessionName,
    timestamp: sessionData.timestamp,
  }));
}

/**
 * Merge constraint data from multiple sessions
 * Deduplicates constraints based on ID while preserving layer information
 */
export function mergeSessionData(sessions: SessionDataExport[]): ConstraintDataPoint[] {
  const constraintMap = new Map<string, ConstraintDataPoint>();

  for (const session of sessions) {
    const normalized = normalizeSessionData(session);
    for (const constraint of normalized) {
      const key = `${constraint.id}-${constraint.layer}`;
      constraintMap.set(key, constraint);
    }
  }

  return Array.from(constraintMap.values());
}

/**
 * Project N-dimensional constraint data to 3D
 */
export function projectToManifold(
  constraints: ConstraintDataPoint[],
  config: ProjectionConfig
): ManifoldPoint[] {
  if (constraints.length === 0) return [];

  // Extract dimension vectors
  const dimensionData = constraints.map((c) => c.dimensions);

  // Ensure all vectors have same length (pad with zeros)
  const maxDim = Math.max(...dimensionData.map((d) => d.length));
  const paddedData = dimensionData.map((d) => {
    const padded = [...d];
    while (padded.length < maxDim) padded.push(0);
    return padded;
  });

  // Project based on method
  let projected: number[][];
  let projectionQuality = 0.8; // Default quality estimate

  switch (config.method) {
    case "pca":
      const pcaResult = projectPCA(paddedData, 3);
      projected = pcaResult.projected;
      projectionQuality = pcaResult.explainedVariance.reduce((a, b) => a + b, 0);
      break;

    case "umap":
      projected = projectUMAP(paddedData, config.umap || { nNeighbors: 15, minDist: 0.1 });
      break;

    case "tsne":
      projected = projectTSNE(
        paddedData,
        config.tsne || { perplexity: 30, learningRate: 200, nIterations: 500 }
      );
      break;

    default:
      // Fallback to first 3 dimensions
      projected = paddedData.map((d) => [d[0] || 0, d[1] || 0, d[2] || 0]);
  }

  // Normalize projected coordinates to [-1, 1] range
  const bounds = {
    min: [Infinity, Infinity, Infinity],
    max: [-Infinity, -Infinity, -Infinity],
  };

  for (const p of projected) {
    for (let i = 0; i < 3; i++) {
      bounds.min[i] = Math.min(bounds.min[i], p[i]);
      bounds.max[i] = Math.max(bounds.max[i], p[i]);
    }
  }

  const normalizedProjected = projected.map((p) =>
    p.map((v, i) => {
      const range = bounds.max[i] - bounds.min[i];
      return range > 0 ? ((v - bounds.min[i]) / range) * 2 - 1 : 0;
    })
  );

  // Convert to ManifoldPoints with visual properties
  return constraints.map((constraint, idx) => {
    const pos = normalizedProjected[idx] || [0, 0, 0];
    const baseColor = CONSTRAINT_COLORS[constraint.type] || CONSTRAINT_COLORS.custom;
    const layerColor = LAYER_COLORS[constraint.layer] || [0.5, 0.5, 0.5];

    // Blend base color with layer tint
    const blendedColor: [number, number, number] = [
      baseColor[0] * 0.7 + layerColor[0] * 0.3,
      baseColor[1] * 0.7 + layerColor[1] * 0.3,
      baseColor[2] * 0.7 + layerColor[2] * 0.3,
    ];

    return {
      id: `manifold-${constraint.id}-${constraint.layer}`,
      constraintId: constraint.id,
      type: constraint.type,
      layer: constraint.layer,
      position: {
        x: pos[0] * 5, // Scale to world units
        y: pos[1] * 5,
        z: pos[2] * 5,
      },
      projectionConfidence: projectionQuality,
      visual: {
        color: blendedColor,
        opacity: constraint.severity > 0.5 ? 1.0 : 0.6,
        size: 0.1 + constraint.severity * 0.2,
        glowIntensity: constraint.severity > 0.8 ? 1.0 : 0.3,
      },
      status: {
        isSatisfied: constraint.severity === 0,
        isViolated: constraint.severity > 0,
        isCritical: constraint.severity > 0.8,
        tension: constraint.weight * constraint.severity,
      },
      severity: constraint.severity,
      label: constraint.label,
    };
  });
}

/**
 * Build complete holographic dataset from session exports
 */
export function buildHolographicDataset(
  sessions: SessionDataExport[],
  projectionConfig: ProjectionConfig
): HolographicDataset {
  const allConstraints = mergeSessionData(sessions);
  const manifoldPoints = projectToManifold(allConstraints, projectionConfig);

  // Compute statistics
  const constraintsByType: Record<ConstraintType, number> = {
    acgme: 0,
    fairness: 0,
    fatigue: 0,
    temporal: 0,
    preference: 0,
    coverage: 0,
    skill: 0,
    custom: 0,
  };

  const constraintsByLayer: Record<SpectralLayer, number> = {
    quantum: 0,
    temporal: 0,
    topological: 0,
    spectral: 0,
    evolutionary: 0,
    gravitational: 0,
    phase: 0,
    thermodynamic: 0,
  };

  for (const constraint of allConstraints) {
    constraintsByType[constraint.type]++;
    constraintsByLayer[constraint.layer]++;
  }

  const avgSeverity =
    allConstraints.reduce((sum, c) => sum + c.severity, 0) / (allConstraints.length || 1);

  return {
    timestamp: new Date().toISOString(),
    sessions,
    allConstraints,
    manifoldPoints,
    globalStats: {
      totalUniqueConstraints: allConstraints.length,
      constraintsByType,
      constraintsByLayer,
      overallHealth: Math.max(0, 1 - avgSeverity),
      projectionMethod: projectionConfig.method,
      projectionQuality:
        manifoldPoints.length > 0 ? manifoldPoints[0].projectionConfidence : 0,
    },
  };
}

// ============================================================================
// Mock Data Generator (for testing without backend)
// ============================================================================

/**
 * Generate mock session data for testing
 */
export function generateMockSessionData(sessionLayer: SpectralLayer): SessionDataExport {
  const layerIndexMap: Record<SpectralLayer, number> = {
    quantum: 0,
    temporal: 1,
    topological: 2,
    spectral: 3,
    evolutionary: 4,
    gravitational: 5,
    phase: 6,
    thermodynamic: 7,
  };
  const constraintTypes: ConstraintType[] = [
    "acgme",
    "fairness",
    "fatigue",
    "temporal",
    "preference",
    "coverage",
    "skill",
  ];

  const nConstraints = 20 + Math.floor(Math.random() * 30);
  const constraints: ConstraintDataPoint[] = [];

  for (let i = 0; i < nConstraints; i++) {
    const type = constraintTypes[Math.floor(Math.random() * constraintTypes.length)];
    const severity = Math.random() > 0.7 ? Math.random() : 0;

    // Generate random N-dimensional vector (8-16 dimensions)
    const nDims = 8 + Math.floor(Math.random() * 8);
    const dimensions = Array(nDims)
      .fill(0)
      .map(() => Math.random() * 2 - 1);

    constraints.push({
      id: `${sessionLayer}-constraint-${i}`,
      type,
      layer: sessionLayer,
      dimensions,
      severity,
      weight: 0.5 + Math.random() * 0.5,
      entities: {
        personIds: [`person-${Math.floor(Math.random() * 20)}`],
        blockIds: [`block-${Math.floor(Math.random() * 100)}`],
      },
      label: `${type.toUpperCase()} constraint ${i + 1}`,
      metadata: {
        source: sessionLayer,
        generated: true,
      },
      timestamp: new Date().toISOString(),
    });
  }

  const satisfiedCount = constraints.filter((c) => c.severity === 0).length;
  const violatedCount = constraints.filter((c) => c.severity > 0 && c.severity <= 0.8).length;
  const criticalCount = constraints.filter((c) => c.severity > 0.8).length;

  return {
    sessionId: (layerIndexMap[sessionLayer] ?? 0) + 1,
    sessionName: sessionLayer,
    timestamp: new Date().toISOString(),
    version: "1.0.0",
    constraints,
    metrics: {
      totalConstraints: constraints.length,
      satisfiedCount,
      violatedCount,
      criticalCount,
      averageSeverity:
        constraints.reduce((sum, c) => sum + c.severity, 0) / constraints.length,
      averageTension:
        constraints.reduce((sum, c) => sum + c.weight * c.severity, 0) / constraints.length,
    },
  };
}

/**
 * Generate complete mock holographic dataset
 */
export function generateMockHolographicData(
  layers: SpectralLayer[] = ["quantum", "temporal", "evolutionary", "spectral"]
): HolographicDataset {
  const sessions = layers.map(generateMockSessionData);
  return buildHolographicDataset(sessions, { method: "pca" });
}
