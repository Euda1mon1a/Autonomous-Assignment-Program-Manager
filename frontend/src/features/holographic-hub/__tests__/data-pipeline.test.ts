/**
 * Tests for Holographic Data Pipeline
 */

import {
  projectPCA,
  projectUMAP,
  projectTSNE,
  normalizeSessionData,
  mergeSessionData,
  projectToManifold,
  buildHolographicDataset,
  generateMockSessionData,
  generateMockHolographicData,
} from "../data-pipeline";
import { ConstraintDataPoint, SessionDataExport, SpectralLayer } from "../types";

describe("Data Pipeline", () => {
  describe("projectPCA", () => {
    it("returns empty arrays for empty input", () => {
      const result = projectPCA([], 3);
      expect(result.projected).toEqual([]);
      expect(result.explainedVariance).toEqual([]);
    });

    it("projects data to specified number of components", () => {
      const data = [
        [1, 2, 3, 4, 5],
        [2, 3, 4, 5, 6],
        [3, 4, 5, 6, 7],
        [4, 5, 6, 7, 8],
        [5, 6, 7, 8, 9],
      ];

      const result = projectPCA(data, 3);

      expect(result.projected.length).toBe(5);
      expect(result.projected[0].length).toBe(3);
    });

    it("produces valid explained variance ratios", () => {
      const data = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 0],
        [0, 1, 1],
      ];

      const result = projectPCA(data, 3);

      const totalVariance = result.explainedVariance.reduce((a, b) => a + b, 0);
      expect(totalVariance).toBeCloseTo(1, 1);
    });

    it("handles single data point", () => {
      const data = [[1, 2, 3]];

      // Should not crash
      const result = projectPCA(data, 3);
      expect(result.projected.length).toBe(1);
    });
  });

  describe("projectUMAP", () => {
    it("returns empty array for empty input", () => {
      const result = projectUMAP([], { nNeighbors: 15, minDist: 0.1 });
      expect(result).toEqual([]);
    });

    it("projects data to 3D", () => {
      const data = [
        [1, 2, 3, 4],
        [2, 3, 4, 5],
        [3, 4, 5, 6],
        [4, 5, 6, 7],
        [5, 6, 7, 8],
      ];

      const result = projectUMAP(data, { nNeighbors: 3, minDist: 0.1 });

      expect(result.length).toBe(5);
      expect(result[0].length).toBe(3);
    });

    it("produces finite values", () => {
      const data = [
        [1, 2, 3],
        [2, 3, 4],
        [3, 4, 5],
      ];

      const result = projectUMAP(data, { nNeighbors: 2, minDist: 0.1 });

      for (const point of result) {
        for (const coord of point) {
          expect(isFinite(coord)).toBe(true);
        }
      }
    });
  });

  describe("projectTSNE", () => {
    it("returns empty array for empty input", () => {
      const result = projectTSNE([], {
        perplexity: 30,
        learningRate: 200,
        nIterations: 50,
      });
      expect(result).toEqual([]);
    });

    it("projects data to 3D", () => {
      const data = [
        [1, 2, 3, 4],
        [2, 3, 4, 5],
        [3, 4, 5, 6],
        [4, 5, 6, 7],
        [5, 6, 7, 8],
      ];

      const result = projectTSNE(data, {
        perplexity: 2,
        learningRate: 100,
        nIterations: 50,
      });

      expect(result.length).toBe(5);
      expect(result[0].length).toBe(3);
    });

    it("produces finite values", () => {
      const data = [
        [1, 2, 3],
        [2, 3, 4],
        [3, 4, 5],
        [4, 5, 6],
      ];

      const result = projectTSNE(data, {
        perplexity: 2,
        learningRate: 100,
        nIterations: 50,
      });

      for (const point of result) {
        for (const coord of point) {
          expect(isFinite(coord)).toBe(true);
        }
      }
    });
  });

  describe("normalizeSessionData", () => {
    it("normalizes session data with layer information", () => {
      const session: SessionDataExport = {
        sessionId: 1,
        sessionName: "quantum",
        timestamp: "2024-01-01T00:00:00Z",
        version: "1.0.0",
        constraints: [
          {
            id: "c1",
            type: "acgme",
            layer: "quantum",
            dimensions: [1, 2, 3],
            severity: 0.5,
            weight: 1,
            entities: {},
            label: "Test",
            metadata: {},
            timestamp: "2024-01-01T00:00:00Z",
          },
        ],
        metrics: {
          totalConstraints: 1,
          satisfiedCount: 0,
          violatedCount: 1,
          criticalCount: 0,
          averageSeverity: 0.5,
          averageTension: 0.5,
        },
      };

      const result = normalizeSessionData(session);

      expect(result.length).toBe(1);
      expect(result[0].layer).toBe("quantum");
    });
  });

  describe("mergeSessionData", () => {
    it("merges constraints from multiple sessions", () => {
      const sessions: SessionDataExport[] = [
        {
          sessionId: 1,
          sessionName: "quantum",
          timestamp: "2024-01-01T00:00:00Z",
          version: "1.0.0",
          constraints: [
            {
              id: "c1",
              type: "acgme",
              layer: "quantum",
              dimensions: [1, 2, 3],
              severity: 0.5,
              weight: 1,
              entities: {},
              label: "Constraint 1",
              metadata: {},
              timestamp: "2024-01-01T00:00:00Z",
            },
          ],
          metrics: {
            totalConstraints: 1,
            satisfiedCount: 0,
            violatedCount: 1,
            criticalCount: 0,
            averageSeverity: 0.5,
            averageTension: 0.5,
          },
        },
        {
          sessionId: 2,
          sessionName: "temporal",
          timestamp: "2024-01-01T00:00:00Z",
          version: "1.0.0",
          constraints: [
            {
              id: "c2",
              type: "fairness",
              layer: "temporal",
              dimensions: [4, 5, 6],
              severity: 0.3,
              weight: 0.8,
              entities: {},
              label: "Constraint 2",
              metadata: {},
              timestamp: "2024-01-01T00:00:00Z",
            },
          ],
          metrics: {
            totalConstraints: 1,
            satisfiedCount: 1,
            violatedCount: 0,
            criticalCount: 0,
            averageSeverity: 0.3,
            averageTension: 0.24,
          },
        },
      ];

      const result = mergeSessionData(sessions);

      expect(result.length).toBe(2);
    });

    it("handles empty sessions array", () => {
      const result = mergeSessionData([]);
      expect(result).toEqual([]);
    });
  });

  describe("projectToManifold", () => {
    it("returns empty array for empty constraints", () => {
      const result = projectToManifold([], { method: "pca" });
      expect(result).toEqual([]);
    });

    it("creates manifold points with position and visual properties", () => {
      const constraints: ConstraintDataPoint[] = [
        {
          id: "c1",
          type: "acgme",
          layer: "quantum",
          dimensions: [1, 2, 3, 4, 5],
          severity: 0.8,
          weight: 1,
          entities: {},
          label: "Test Constraint",
          metadata: {},
          timestamp: "2024-01-01T00:00:00Z",
        },
        {
          id: "c2",
          type: "fairness",
          layer: "temporal",
          dimensions: [2, 3, 4, 5, 6],
          severity: 0.2,
          weight: 0.5,
          entities: {},
          label: "Test Constraint 2",
          metadata: {},
          timestamp: "2024-01-01T00:00:00Z",
        },
      ];

      const result = projectToManifold(constraints, { method: "pca" });

      expect(result.length).toBe(2);
      expect(result[0]).toHaveProperty("position");
      expect(result[0]).toHaveProperty("visual");
      expect(result[0].visual).toHaveProperty("color");
      expect(result[0].visual).toHaveProperty("opacity");
    });

    it("normalizes positions to world scale", () => {
      const constraints: ConstraintDataPoint[] = Array(10)
        .fill(null)
        .map((_, i) => ({
          id: `c${i}`,
          type: "acgme" as const,
          layer: "quantum" as const,
          dimensions: Array(5)
            .fill(0)
            .map(() => Math.random() * 100),
          severity: Math.random(),
          weight: 1,
          entities: {},
          label: `Constraint ${i}`,
          metadata: {},
          timestamp: "2024-01-01T00:00:00Z",
        }));

      const result = projectToManifold(constraints, { method: "pca" });

      for (const point of result) {
        expect(point.position.x).toBeGreaterThanOrEqual(-10);
        expect(point.position.x).toBeLessThanOrEqual(10);
        expect(point.position.y).toBeGreaterThanOrEqual(-10);
        expect(point.position.y).toBeLessThanOrEqual(10);
        expect(point.position.z).toBeGreaterThanOrEqual(-10);
        expect(point.position.z).toBeLessThanOrEqual(10);
      }
    });

    it("applies correct colors based on constraint type", () => {
      const constraints: ConstraintDataPoint[] = [
        {
          id: "c1",
          type: "acgme",
          layer: "quantum",
          dimensions: [1, 2, 3],
          severity: 0.5,
          weight: 1,
          entities: {},
          label: "ACGME Constraint",
          metadata: {},
          timestamp: "2024-01-01T00:00:00Z",
        },
      ];

      const result = projectToManifold(constraints, { method: "pca" });

      // ACGME should have reddish color (0.9, 0.2, 0.2 base)
      expect(result[0].visual.color[0]).toBeGreaterThan(0.5); // Red component should be high
    });
  });

  describe("buildHolographicDataset", () => {
    it("builds complete dataset from sessions", () => {
      const sessions: SessionDataExport[] = [
        generateMockSessionData("quantum"),
        generateMockSessionData("temporal"),
      ];

      const result = buildHolographicDataset(sessions, { method: "pca" });

      expect(result).toHaveProperty("timestamp");
      expect(result).toHaveProperty("sessions");
      expect(result).toHaveProperty("allConstraints");
      expect(result).toHaveProperty("manifoldPoints");
      expect(result).toHaveProperty("globalStats");
      expect(result.sessions.length).toBe(2);
    });

    it("computes correct global statistics", () => {
      const sessions: SessionDataExport[] = [
        generateMockSessionData("quantum"),
      ];

      const result = buildHolographicDataset(sessions, { method: "pca" });

      expect(result.globalStats.totalUniqueConstraints).toBe(
        result.allConstraints.length
      );
      expect(result.globalStats.overallHealth).toBeGreaterThanOrEqual(0);
      expect(result.globalStats.overallHealth).toBeLessThanOrEqual(1);
    });
  });

  describe("generateMockSessionData", () => {
    it("generates valid session data for a layer", () => {
      const result = generateMockSessionData("quantum");

      expect(result.sessionName).toBe("quantum");
      expect(result.constraints.length).toBeGreaterThan(0);
      expect(result.metrics.totalConstraints).toBe(result.constraints.length);
    });

    it("generates constraints with required properties", () => {
      const result = generateMockSessionData("temporal");

      for (const constraint of result.constraints) {
        expect(constraint).toHaveProperty("id");
        expect(constraint).toHaveProperty("type");
        expect(constraint).toHaveProperty("dimensions");
        expect(constraint).toHaveProperty("severity");
        expect(constraint).toHaveProperty("weight");
        expect(constraint).toHaveProperty("label");
      }
    });
  });

  describe("generateMockHolographicData", () => {
    it("generates complete mock dataset", () => {
      const result = generateMockHolographicData();

      expect(result).toHaveProperty("timestamp");
      expect(result).toHaveProperty("sessions");
      expect(result).toHaveProperty("manifoldPoints");
      expect(result.manifoldPoints.length).toBeGreaterThan(0);
    });

    it("respects specified layers", () => {
      const layers: SpectralLayer[] = ["quantum", "evolutionary"];
      const result = generateMockHolographicData(layers);

      expect(result.sessions.length).toBe(2);
      expect(result.sessions.map((s) => s.sessionName).sort()).toEqual(
        layers.sort()
      );
    });
  });
});
