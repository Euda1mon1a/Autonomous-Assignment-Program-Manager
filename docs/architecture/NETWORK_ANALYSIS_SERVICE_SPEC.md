# Network Analysis Service - Implementation Specification

**Version**: 1.0
**Date**: 2025-12-26
**Status**: Production-Ready Specification
**Owner**: Resilience Engineering Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Service Architecture](#2-service-architecture)
3. [API Endpoints](#3-api-endpoints)
4. [Graph Types](#4-graph-types)
5. [Analysis Modules](#5-analysis-modules)
6. [Integration with Existing Code](#6-integration-with-existing-code)
7. [Visualization API](#7-visualization-api)
8. [Performance Optimization](#8-performance-optimization)
9. [Testing Strategy](#9-testing-strategy)
10. [Deployment](#10-deployment)
11. [Future Enhancements](#11-future-enhancements)

---

## 1. Executive Summary

### Purpose

The Network Analysis Service provides comprehensive network-based resilience analysis for the residency scheduler using graph theory and NetworkX. It extends the existing `hub_analysis.py` module with advanced topology analysis, community detection, robustness metrics, and predictive capabilities.

### Key Features

- **Topology Analysis**: Small-world detection, scale-free analysis, clustering coefficient
- **Robustness Metrics**: Percolation thresholds, attack tolerance, k-core decomposition
- **Centrality Measures**: Comprehensive suite (degree, betweenness, closeness, eigenvector, PageRank, Katz, harmonic, current flow)
- **Community Detection**: Louvain, label propagation, Girvan-Newman, greedy modularity
- **Temporal Analysis**: Network evolution tracking, link prediction, pattern detection
- **Visualization**: D3.js-compatible JSON exports with pre-computed layouts

### Integration Points

- **Extends**: `backend/app/resilience/hub_analysis.py`
- **Integrates with**: N-1/N-2 contingency analysis, burnout epidemiology
- **Feeds into**: Resilience dashboard, schedule optimization, coverage gap detection

---

## 2. Service Architecture

### 2.1 Module Structure

```
backend/app/resilience/
├── hub_analysis.py                    # EXISTING - Basic centrality
├── network_analysis/                  # NEW - Advanced analysis
│   ├── __init__.py
│   ├── service.py                    # Main service class
│   ├── topology.py                   # Topology analyzers
│   ├── centrality.py                 # Centrality calculators
│   ├── community.py                  # Community detection
│   ├── robustness.py                 # Robustness analyzers
│   ├── temporal.py                   # Temporal network analysis
│   ├── visualization.py              # Graph export for viz
│   └── cache.py                      # Redis caching layer
```

### 2.2 Core Service Class

**File**: `backend/app/resilience/network_analysis/service.py`

```python
"""
Network Analysis Service - Main orchestrator.

Coordinates all network analysis modules and provides unified interface.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import logging

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from .topology import TopologyAnalyzer
from .centrality import CentralityCalculator
from .community import CommunityDetector
from .robustness import RobustnessAnalyzer
from .temporal import TemporalAnalyzer
from .visualization import NetworkVisualizer
from .cache import NetworkCache
from ..hub_analysis import HubAnalyzer

logger = logging.getLogger(__name__)


class NetworkAnalysisService:
    """
    Comprehensive network analysis service.

    Extends HubAnalyzer with advanced graph theory analysis.
    """

    def __init__(
        self,
        cache_ttl_seconds: int = 900,  # 15 minutes
        enable_expensive_ops: bool = True,
        max_nodes_for_expensive: int = 100
    ):
        # Existing hub analyzer
        self.hub_analyzer = HubAnalyzer(use_networkx=True)

        # New analysis modules
        self.topology = TopologyAnalyzer()
        self.centrality = CentralityCalculator()
        self.community = CommunityDetector()
        self.robustness = RobustnessAnalyzer()
        self.temporal = TemporalAnalyzer()
        self.visualizer = NetworkVisualizer()

        # Cache
        self.cache = NetworkCache(ttl_seconds=cache_ttl_seconds)

        # Configuration
        self.enable_expensive_ops = enable_expensive_ops
        self.max_nodes_for_expensive = max_nodes_for_expensive

        # Graph storage
        self._current_graph: Optional[nx.Graph] = None
        self._graph_timestamp: Optional[datetime] = None
        self._temporal_snapshots: List[Tuple[nx.Graph, datetime]] = []

    async def build_coverage_network(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        graph_type: str = "coverage"
    ) -> nx.Graph:
        """
        Build network graph from schedule data.

        Args:
            db: Database session
            start_date: Analysis period start
            end_date: Analysis period end
            graph_type: Type of graph (coverage, supervision, swap)

        Returns:
            NetworkX graph
        """
        cache_key = f"graph:{graph_type}:{start_date}:{end_date}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        if graph_type == "coverage":
            G = await self._build_coverage_graph(db, start_date, end_date)
        elif graph_type == "supervision":
            G = await self._build_supervision_graph(db, start_date, end_date)
        elif graph_type == "swap":
            G = await self._build_swap_graph(db, start_date, end_date)
        else:
            raise ValueError(f"Unknown graph type: {graph_type}")

        await self.cache.set(cache_key, G)
        self._current_graph = G
        self._graph_timestamp = datetime.now()

        return G

    async def run_comprehensive_analysis(
        self,
        graph: Optional[nx.Graph] = None
    ) -> Dict:
        """
        Run all network analyses and return comprehensive report.

        Args:
            graph: Pre-built graph (uses current if None)

        Returns:
            Complete analysis report
        """
        G = graph or self._current_graph
        if G is None:
            raise ValueError("No graph available. Call build_coverage_network first.")

        cache_key = f"analysis:{hash(frozenset(G.edges()))}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        n = G.number_of_nodes()

        report = {
            "timestamp": datetime.now().isoformat(),
            "graph_info": {
                "nodes": n,
                "edges": G.number_of_edges(),
                "density": nx.density(G),
                "is_connected": nx.is_connected(G),
                "num_components": nx.number_connected_components(G)
            }
        }

        # 1. Topology Analysis
        logger.info("Running topology analysis...")
        report["topology"] = await self._run_topology_analysis(G)

        # 2. Centrality Analysis
        logger.info("Running centrality analysis...")
        report["centrality"] = await self._run_centrality_analysis(G)

        # 3. Community Detection
        logger.info("Running community detection...")
        report["communities"] = await self._run_community_analysis(G)

        # 4. Robustness Analysis
        logger.info("Running robustness analysis...")
        report["robustness"] = await self._run_robustness_analysis(G)

        # 5. Integration with hub analyzer
        logger.info("Integrating with hub analysis...")
        report["hub_analysis"] = self._get_hub_analysis_summary()

        await self.cache.set(cache_key, report)

        return report

    async def _run_topology_analysis(self, G: nx.Graph) -> Dict:
        """Run topology analysis suite."""
        return {
            "small_world": self.topology.analyze_small_world(G),
            "scale_free": self.topology.detect_scale_free(G),
            "clustering": self.topology.analyze_clustering(G),
            "bridges": self.topology.identify_bridges(G)
        }

    async def _run_centrality_analysis(self, G: nx.Graph) -> Dict:
        """Run centrality analysis suite."""
        n = G.number_of_nodes()

        # Calculate all centrality measures
        all_centrality = self.centrality.calculate_all_measures(
            G,
            enable_expensive=self.enable_expensive_ops and n < self.max_nodes_for_expensive
        )

        # Consensus ranking
        consensus = self.centrality.calculate_consensus_ranking(all_centrality)

        return {
            "measures": all_centrality,
            "consensus_top_20": consensus[:20],
            "critical_nodes": self.centrality.identify_critical_nodes(G, all_centrality)
        }

    async def _run_community_analysis(self, G: nx.Graph) -> Dict:
        """Run community detection."""
        return {
            "louvain": self.community.detect_louvain(G),
            "comparison": self.community.compare_algorithms(G),
            "stability": self.community.analyze_stability(
                self._temporal_snapshots
            ) if self._temporal_snapshots else None
        }

    async def _run_robustness_analysis(self, G: nx.Graph) -> Dict:
        """Run robustness analysis."""
        return {
            "attack_tolerance": self.robustness.compare_attack_tolerance(G),
            "percolation": self.robustness.calculate_percolation_threshold(G),
            "k_core": self.robustness.analyze_k_core(G)
        }

    def _get_hub_analysis_summary(self) -> Dict:
        """Get summary from hub analyzer."""
        return self.hub_analyzer.get_hub_status()

    # Graph builders
    async def _build_coverage_graph(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> nx.Graph:
        """Build coverage network (faculty ↔ rotation edges)."""
        # TODO: Implement query logic
        # Query assignments in date range
        # Build bipartite graph: faculty <-> rotations
        # Project to faculty-faculty graph (shared rotations)
        pass

    async def _build_supervision_graph(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> nx.Graph:
        """Build supervision network (faculty → resident edges)."""
        # TODO: Implement directed graph for supervision
        pass

    async def _build_swap_graph(
        self,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> nx.Graph:
        """Build swap network (historical swap connections)."""
        # TODO: Implement from swap_requests table
        pass
```

### 2.3 Caching Strategy

**File**: `backend/app/resilience/network_analysis/cache.py`

```python
"""
Redis caching for network analysis results.

Expensive graph computations are cached with TTL.
"""

import pickle
from typing import Any, Optional
from datetime import timedelta
import logging

import networkx as nx
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class NetworkCache:
    """Redis cache for network analysis."""

    def __init__(self, ttl_seconds: int = 900):
        self.ttl = timedelta(seconds=ttl_seconds)
        self.redis: Optional[Redis] = None
        self._enabled = settings.REDIS_ENABLED

    async def connect(self):
        """Initialize Redis connection."""
        if not self._enabled:
            return

        try:
            self.redis = Redis.from_url(settings.REDIS_URL)
            await self.redis.ping()
            logger.info("Network cache connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._enabled = False

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve from cache."""
        if not self._enabled or not self.redis:
            return None

        try:
            data = await self.redis.get(f"network:{key}")
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")

        return None

    async def set(self, key: str, value: Any):
        """Store in cache with TTL."""
        if not self._enabled or not self.redis:
            return

        try:
            serialized = pickle.dumps(value)
            await self.redis.setex(
                f"network:{key}",
                self.ttl,
                serialized
            )
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern."""
        if not self._enabled or not self.redis:
            return

        try:
            keys = []
            async for key in self.redis.scan_iter(f"network:{pattern}*"):
                keys.append(key)

            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
```

---

## 3. API Endpoints

### 3.1 Endpoint Specification

**File**: `backend/app/api/routes/network_analysis.py`

```python
"""
Network Analysis API Endpoints.

RESTful API for graph theory analysis of schedule resilience.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.resilience.network_analysis.service import NetworkAnalysisService
from app.schemas.network_analysis import (
    NetworkTopologyResponse,
    CentralityResponse,
    CommunityResponse,
    RobustnessResponse,
    GraphExportResponse,
    TemporalAnalysisResponse
)

router = APIRouter(prefix="/network", tags=["network-analysis"])

# Service instance (consider dependency injection in production)
network_service = NetworkAnalysisService()


@router.on_event("startup")
async def startup():
    """Initialize network analysis service."""
    await network_service.cache.connect()


@router.get("/topology", response_model=NetworkTopologyResponse)
async def get_network_topology(
    start_date: datetime = Query(..., description="Analysis period start"),
    end_date: datetime = Query(..., description="Analysis period end"),
    graph_type: str = Query("coverage", regex="^(coverage|supervision|swap)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get network topology metrics.

    Returns:
    - Small-world coefficient
    - Scale-free distribution test
    - Clustering coefficient
    - Bridge identification
    """
    G = await network_service.build_coverage_network(db, start_date, end_date, graph_type)
    topology = await network_service._run_topology_analysis(G)

    return NetworkTopologyResponse(
        timestamp=datetime.now(),
        graph_type=graph_type,
        period_start=start_date,
        period_end=end_date,
        **topology
    )


@router.get("/centrality", response_model=CentralityResponse)
async def get_centrality_measures(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    graph_type: str = Query("coverage", regex="^(coverage|supervision|swap)$"),
    include_expensive: bool = Query(False, description="Include O(n³) algorithms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate all centrality measures.

    Includes:
    - Degree, betweenness, closeness
    - Eigenvector, PageRank, Katz
    - Harmonic, load centrality
    - Current flow (if include_expensive=true)
    - Consensus ranking
    """
    G = await network_service.build_coverage_network(db, start_date, end_date, graph_type)

    # Temporarily enable expensive ops if requested
    original_setting = network_service.enable_expensive_ops
    network_service.enable_expensive_ops = include_expensive

    centrality = await network_service._run_centrality_analysis(G)

    network_service.enable_expensive_ops = original_setting

    return CentralityResponse(
        timestamp=datetime.now(),
        graph_type=graph_type,
        period_start=start_date,
        period_end=end_date,
        **centrality
    )


@router.get("/communities", response_model=CommunityResponse)
async def detect_communities(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    graph_type: str = Query("coverage", regex="^(coverage|supervision|swap)$"),
    algorithm: str = Query("louvain", regex="^(louvain|label_propagation|greedy|all)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detect community structure.

    Algorithms:
    - louvain: Modularity optimization (default)
    - label_propagation: Fast, semi-random
    - greedy: Greedy modularity
    - all: Compare all algorithms
    """
    G = await network_service.build_coverage_network(db, start_date, end_date, graph_type)

    if algorithm == "all":
        result = network_service.community.compare_algorithms(G)
    elif algorithm == "louvain":
        result = network_service.community.detect_louvain(G)
    elif algorithm == "label_propagation":
        result = network_service.community.detect_label_propagation(G)
    elif algorithm == "greedy":
        result = network_service.community.detect_greedy_modularity(G)

    return CommunityResponse(
        timestamp=datetime.now(),
        graph_type=graph_type,
        algorithm=algorithm,
        **result
    )


@router.get("/robustness", response_model=RobustnessResponse)
async def analyze_robustness(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    graph_type: str = Query("coverage", regex="^(coverage|supervision|swap)$"),
    include_percolation: bool = Query(True),
    num_trials: int = Query(50, ge=10, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyze network robustness.

    Returns:
    - Attack tolerance (random vs targeted)
    - Percolation threshold (optional, expensive)
    - k-core decomposition
    - Vulnerability ratio
    """
    G = await network_service.build_coverage_network(db, start_date, end_date, graph_type)

    result = {
        "attack_tolerance": network_service.robustness.compare_attack_tolerance(G),
        "k_core": network_service.robustness.analyze_k_core(G)
    }

    if include_percolation:
        result["percolation"] = network_service.robustness.calculate_percolation_threshold(
            G,
            num_trials=num_trials
        )

    return RobustnessResponse(
        timestamp=datetime.now(),
        graph_type=graph_type,
        **result
    )


@router.get("/predictions", response_model=TemporalAnalysisResponse)
async def predict_coverage_gaps(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    prediction_horizon_days: int = Query(30, ge=7, le=90),
    top_n: int = Query(20, ge=5, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Predict future coverage needs using link prediction.

    Returns:
    - Recommended faculty pairs for cross-training
    - Emerging hub patterns
    - Coverage gap predictions
    """
    # Build temporal sequence
    await network_service.temporal.build_temporal_sequence(
        db,
        start_date,
        end_date,
        window_days=7
    )

    # Current graph
    G_current = await network_service.build_coverage_network(
        db,
        end_date - timedelta(days=30),
        end_date
    )

    predictions = network_service.temporal.predict_future_links(
        G_current,
        network_service._temporal_snapshots,
        top_n=top_n
    )

    emerging_patterns = network_service.temporal.detect_emerging_patterns(
        network_service._temporal_snapshots
    )

    return TemporalAnalysisResponse(
        timestamp=datetime.now(),
        analysis_period_start=start_date,
        analysis_period_end=end_date,
        prediction_horizon_days=prediction_horizon_days,
        predicted_links=predictions,
        emerging_patterns=emerging_patterns
    )


@router.get("/export/{format}", response_model=GraphExportResponse)
async def export_graph(
    format: str = Query(..., regex="^(d3|graphml|gexf|json)$"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    graph_type: str = Query("coverage", regex="^(coverage|supervision|swap)$"),
    include_layout: bool = Query(True),
    layout_algorithm: str = Query("spring", regex="^(spring|kamada_kawai|circular)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export network graph for visualization.

    Formats:
    - d3: D3.js force-directed layout (default)
    - graphml: GraphML XML
    - gexf: GEXF (Gephi)
    - json: NetworkX node-link JSON

    Includes pre-computed layouts for frontend.
    """
    G = await network_service.build_coverage_network(db, start_date, end_date, graph_type)

    export_data = network_service.visualizer.export_graph(
        G,
        format=format,
        include_layout=include_layout,
        layout_algorithm=layout_algorithm
    )

    return GraphExportResponse(
        timestamp=datetime.now(),
        graph_type=graph_type,
        format=format,
        data=export_data
    )
```

### 3.2 API Response Schemas

**File**: `backend/app/schemas/network_analysis.py`

```python
"""Pydantic schemas for network analysis API responses."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field


class SmallWorldMetrics(BaseModel):
    """Small-world topology metrics."""
    clustering_coefficient: float
    avg_path_length: float
    small_world_sigma: float
    is_small_world: bool
    interpretation: str


class ScaleFreeMetrics(BaseModel):
    """Scale-free distribution metrics."""
    gamma: float = Field(description="Power-law exponent")
    xmin: int = Field(description="Minimum degree for power-law fit")
    is_scale_free: bool
    power_law_vs_exponential_R: float
    power_law_vs_lognormal_R: float
    log_log_r_squared: float
    interpretation: str


class ClusteringMetrics(BaseModel):
    """Clustering analysis metrics."""
    global_clustering: float
    average_clustering: float
    clustering_std: float
    num_triangles: int
    num_4_cliques: int
    num_5plus_cliques: int
    highly_clustered_nodes: List[Dict[str, Any]]
    interpretation: str


class NetworkTopologyResponse(BaseModel):
    """Response for topology analysis endpoint."""
    timestamp: datetime
    graph_type: str
    period_start: datetime
    period_end: datetime

    small_world: SmallWorldMetrics
    scale_free: ScaleFreeMetrics
    clustering: ClusteringMetrics
    bridges: List[Dict[str, str]]


class CentralityMeasures(BaseModel):
    """All centrality measures for a node."""
    node_id: str
    degree: float
    betweenness: float
    closeness: float
    eigenvector: float
    pagerank: float
    katz: Optional[float] = None
    harmonic: float
    load: float
    current_flow: Optional[float] = None
    communicability: Optional[float] = None


class CentralityResponse(BaseModel):
    """Response for centrality analysis endpoint."""
    timestamp: datetime
    graph_type: str
    period_start: datetime
    period_end: datetime

    measures: Dict[str, Dict[str, float]]
    consensus_top_20: List[Dict[str, float]]
    critical_nodes: List[Dict[str, Any]]


class CommunityInfo(BaseModel):
    """Community detection result."""
    community_id: int
    size: int
    density: float
    avg_degree: float
    clustering: float
    members: List[str]


class CommunityResponse(BaseModel):
    """Response for community detection endpoint."""
    timestamp: datetime
    graph_type: str
    algorithm: str

    num_communities: int
    modularity: float
    communities: List[CommunityInfo]
    inter_community_edges: List[Dict[str, Any]]
    interpretation: str


class AttackToleranceMetrics(BaseModel):
    """Attack tolerance analysis."""
    robustness_random: float
    robustness_degree_attack: float
    robustness_betweenness_attack: float
    vulnerability_ratio_degree: float
    vulnerability_ratio_betweenness: float
    network_type: str
    recommendation: str


class PercolationMetrics(BaseModel):
    """Percolation threshold analysis."""
    percolation_threshold: float
    theoretical_threshold: float
    critical_faculty_loss: int
    fragmentation_curve: List[float]
    interpretation: str


class KCoreMetrics(BaseModel):
    """k-core decomposition metrics."""
    k_max: int
    nucleus_size: int
    periphery_size: int
    core_ratio: float
    nucleus_nodes: List[str]
    k_core_sizes: Dict[int, int]
    interpretation: str


class RobustnessResponse(BaseModel):
    """Response for robustness analysis endpoint."""
    timestamp: datetime
    graph_type: str

    attack_tolerance: AttackToleranceMetrics
    k_core: KCoreMetrics
    percolation: Optional[PercolationMetrics] = None


class LinkPrediction(BaseModel):
    """Predicted future link."""
    faculty_1: str
    faculty_2: str
    likelihood: float
    reason: str


class EmergingPattern(BaseModel):
    """Emerging coverage pattern."""
    pattern_type: str
    nodes: List[str]
    trend_strength: float
    description: str


class TemporalAnalysisResponse(BaseModel):
    """Response for temporal/predictive analysis."""
    timestamp: datetime
    analysis_period_start: datetime
    analysis_period_end: datetime
    prediction_horizon_days: int

    predicted_links: List[LinkPrediction]
    emerging_patterns: List[EmergingPattern]
    recommendations: List[str]


class GraphExportResponse(BaseModel):
    """Response for graph export endpoint."""
    timestamp: datetime
    graph_type: str
    format: str
    data: Any  # Format-specific data
```

---

## 4. Graph Types

### 4.1 Coverage Network

**Type**: Undirected bipartite projection
**Nodes**: Faculty
**Edges**: Two faculty are connected if they share rotation coverage

**Construction**:
```python
async def _build_coverage_graph(
    self,
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> nx.Graph:
    """
    Build coverage network.

    Steps:
    1. Query assignments in date range
    2. Build bipartite graph: faculty <-> rotations
    3. Project to faculty-faculty graph
    4. Weight edges by number of shared rotations
    """
    from sqlalchemy import select
    from app.models import Assignment, Person, Rotation

    # Query assignments
    stmt = (
        select(Assignment)
        .join(Block)
        .where(Block.date >= start_date)
        .where(Block.date <= end_date)
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()

    # Build bipartite graph
    B = nx.Graph()

    for asn in assignments:
        fac_id = f"faculty_{asn.person_id}"
        rot_id = f"rotation_{asn.rotation_id}"

        B.add_node(fac_id, type="faculty", person_id=asn.person_id)
        B.add_node(rot_id, type="rotation", rotation_id=asn.rotation_id)
        B.add_edge(fac_id, rot_id)

    # Project to faculty-faculty graph
    faculty_nodes = [n for n, d in B.nodes(data=True) if d.get("type") == "faculty"]
    G = nx.bipartite.weighted_projected_graph(B, faculty_nodes)

    return G
```

**Use Cases**:
- Hub identification
- Community detection (natural teams)
- Cross-training recommendations

### 4.2 Supervision Network

**Type**: Directed
**Nodes**: Faculty and residents
**Edges**: Faculty → Resident (supervision relationship)

**Construction**:
```python
async def _build_supervision_graph(
    self,
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> nx.DiGraph:
    """
    Build supervision network.

    Directed edges from attending faculty to supervised residents.
    """
    from sqlalchemy import select
    from app.models import Assignment, Person

    # Query assignments with supervision data
    stmt = (
        select(Assignment)
        .join(Block)
        .join(Person, Assignment.person_id == Person.id)
        .where(Block.date >= start_date)
        .where(Block.date <= end_date)
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()

    G = nx.DiGraph()

    # Group by rotation/block to find supervision pairs
    rotation_assignments = {}
    for asn in assignments:
        key = (asn.block_id, asn.rotation_id)
        if key not in rotation_assignments:
            rotation_assignments[key] = {"faculty": [], "residents": []}

        person = asn.person
        if person.role == "FACULTY":
            rotation_assignments[key]["faculty"].append(person.id)
        elif person.role in ["RESIDENT", "PGY1", "PGY2", "PGY3"]:
            rotation_assignments[key]["residents"].append(person.id)

    # Create supervision edges
    for (block, rotation), people in rotation_assignments.items():
        for fac_id in people["faculty"]:
            for res_id in people["residents"]:
                G.add_edge(
                    f"faculty_{fac_id}",
                    f"resident_{res_id}",
                    block_id=block,
                    rotation_id=rotation
                )

    return G
```

**Use Cases**:
- ACGME supervision ratio validation
- Mentorship network analysis
- Resident experience diversity

### 4.3 Swap Network

**Type**: Undirected, weighted
**Nodes**: Faculty
**Edges**: Historical swap connections (weighted by frequency)

**Construction**:
```python
async def _build_swap_graph(
    self,
    db: AsyncSession,
    start_date: datetime,
    end_date: datetime
) -> nx.Graph:
    """
    Build swap network from historical swap requests.

    Edge weight = number of successful swaps between two faculty.
    """
    from sqlalchemy import select
    from app.models import SwapRequest

    stmt = (
        select(SwapRequest)
        .where(SwapRequest.status == "completed")
        .where(SwapRequest.created_at >= start_date)
        .where(SwapRequest.created_at <= end_date)
    )
    result = await db.execute(stmt)
    swaps = result.scalars().all()

    G = nx.Graph()

    for swap in swaps:
        # One-to-one swap
        if swap.swap_type == "ONE_TO_ONE":
            requester = f"faculty_{swap.requester_id}"
            counterparty = f"faculty_{swap.counterparty_id}"

            if G.has_edge(requester, counterparty):
                G[requester][counterparty]["weight"] += 1
            else:
                G.add_edge(requester, counterparty, weight=1)

    return G
```

**Use Cases**:
- Predict compatible swap partners
- Identify frequent swap patterns
- Detect schedule inflexibility issues

---

## 5. Analysis Modules

### 5.1 Topology Analyzer

**File**: `backend/app/resilience/network_analysis/topology.py`

```python
"""
Topology Analysis Module.

Detects small-world, scale-free, and clustering properties.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple
from scipy import stats

try:
    import powerlaw
    HAS_POWERLAW = True
except ImportError:
    HAS_POWERLAW = False


class TopologyAnalyzer:
    """Analyze network topology properties."""

    def analyze_small_world(self, G: nx.Graph) -> Dict:
        """
        Analyze small-world properties.

        Returns:
        - Clustering coefficient
        - Average path length
        - Small-world sigma (>1 indicates small-world)
        """
        # Implementation from research doc
        # (Code from NETWORK_RESILIENCE_DEEP_DIVE.md lines 74-134)
        ...

    def detect_scale_free(self, G: nx.Graph) -> Dict:
        """
        Test if degree distribution follows power law.

        Uses MLE and goodness-of-fit tests.
        """
        # Implementation from research doc
        # (Code from lines 252-395)
        ...

    def analyze_clustering(self, G: nx.Graph) -> Dict:
        """
        Analyze clustering structure.

        Returns:
        - Global/average clustering
        - Highly-clustered nodes
        - Clique counts
        """
        # Implementation from research doc
        # (Code from lines 438-569)
        ...

    def identify_bridges(self, G: nx.Graph) -> List[Tuple[str, str]]:
        """
        Identify bridge edges connecting clusters.

        Critical for small-world topology.
        """
        # Implementation from research doc
        # (Code from lines 136-166)
        ...
```

### 5.2 Centrality Calculator

**File**: `backend/app/resilience/network_analysis/centrality.py`

```python
"""
Centrality Calculation Module.

Comprehensive suite of centrality measures.
"""

import networkx as nx
from typing import Dict, List, Tuple


class CentralityCalculator:
    """Calculate all centrality measures."""

    def calculate_all_measures(
        self,
        G: nx.Graph,
        enable_expensive: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate comprehensive centrality measures.

        Returns dictionary mapping measure name to node scores.
        """
        # Implementation from research doc
        # (Code from lines 1021-1091)
        ...

    def calculate_consensus_ranking(
        self,
        centrality_results: Dict[str, Dict[str, float]],
        weights: Dict[str, float] = None
    ) -> List[Tuple[str, float]]:
        """
        Rank nodes by consensus across multiple centrality measures.

        Uses weighted Borda count.
        """
        # Implementation from research doc
        # (Code from lines 1094-1142)
        ...

    def identify_critical_nodes(
        self,
        G: nx.Graph,
        centrality_results: Dict,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Identify most critical nodes by combining k-core and centrality.

        Critical score = k_core × (1 + betweenness_centrality)
        """
        # Implementation from research doc
        # (Code from lines 971-1005)
        ...
```

### 5.3 Community Detector

**File**: `backend/app/resilience/network_analysis/community.py`

```python
"""
Community Detection Module.

Multiple algorithms for community structure discovery.
"""

import networkx as nx
from typing import Dict, List, Set
from sklearn.metrics import normalized_mutual_info_score


class CommunityDetector:
    """Detect community structure."""

    def detect_louvain(
        self,
        G: nx.Graph,
        resolution: float = 1.0
    ) -> Dict:
        """
        Detect communities using Louvain algorithm.

        Returns communities and modularity score.
        """
        # Implementation from research doc
        # (Code from lines 1183-1243)
        ...

    def compare_algorithms(self, G: nx.Graph) -> Dict:
        """
        Compare multiple community detection algorithms.

        Algorithms:
        - Louvain
        - Label Propagation
        - Greedy Modularity
        - Girvan-Newman (small networks only)
        """
        # Implementation from research doc
        # (Code from lines 1269-1335)
        ...

    def analyze_stability(
        self,
        snapshots: List[Tuple[nx.Graph, str]]
    ) -> Dict:
        """
        Track community stability over time.

        Uses Normalized Mutual Information between consecutive snapshots.
        """
        # Implementation from research doc
        # (Code from lines 1348-1430)
        ...
```

### 5.4 Robustness Analyzer

**File**: `backend/app/resilience/network_analysis/robustness.py`

```python
"""
Robustness Analysis Module.

Percolation, attack tolerance, k-core decomposition.
"""

import networkx as nx
import numpy as np
from typing import Dict, List


class RobustnessAnalyzer:
    """Analyze network robustness to failures."""

    def calculate_percolation_threshold(
        self,
        G: nx.Graph,
        removal_strategy: str = 'random',
        num_trials: int = 100
    ) -> Dict:
        """
        Estimate percolation threshold via simulation.

        Strategies: random, degree, betweenness
        """
        # Implementation from research doc
        # (Code from lines 603-754)
        ...

    def compare_attack_tolerance(self, G: nx.Graph) -> Dict:
        """
        Compare robustness to random vs targeted attacks.

        Returns:
        - Robustness metrics (area under fragmentation curve)
        - Vulnerability ratio (R_random / R_attack)
        - Network type classification
        """
        # Implementation from research doc
        # (Code from lines 777-860)
        ...

    def analyze_k_core(self, G: nx.Graph) -> Dict:
        """
        Perform k-core decomposition.

        Identifies nested core structure and nucleus.
        """
        # Implementation from research doc
        # (Code from lines 887-1005)
        ...
```

### 5.5 Temporal Analyzer

**File**: `backend/app/resilience/network_analysis/temporal.py`

```python
"""
Temporal Network Analysis Module.

Evolution tracking and link prediction.
"""

import networkx as nx
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class TemporalAnalyzer:
    """Analyze temporal network evolution."""

    async def build_temporal_sequence(
        self,
        db,
        start_date: datetime,
        end_date: datetime,
        window_days: int = 30
    ) -> List[Tuple[nx.Graph, datetime]]:
        """
        Build sequence of network snapshots.

        Uses rolling window to create temporal graphs.
        """
        # Implementation from research doc
        # (Code from lines 1456-1506)
        ...

    def predict_future_links(
        self,
        G_current: nx.Graph,
        historical_snapshots: List[nx.Graph],
        top_n: int = 20
    ) -> List[Tuple[str, str, float]]:
        """
        Predict future connections using link prediction.

        Uses ensemble of:
        - Common neighbors
        - Jaccard coefficient
        - Adamic-Adar index
        - Preferential attachment
        - Resource allocation
        """
        # Implementation from research doc
        # (Code from lines 1611-1672)
        ...

    def detect_emerging_patterns(
        self,
        snapshots: List[Tuple[nx.Graph, datetime]],
        lookback_windows: int = 4
    ) -> Dict:
        """
        Detect emerging coverage patterns.

        Identifies:
        - New service combinations
        - Emerging hubs
        - Strengthening communities
        """
        # Implementation from research doc
        # (Code from lines 1674-1760)
        ...
```

---

## 6. Integration with Existing Code

### 6.1 Extending HubAnalyzer

The `NetworkAnalysisService` **extends** (not replaces) the existing `HubAnalyzer`:

```python
# In NetworkAnalysisService.__init__
self.hub_analyzer = HubAnalyzer(use_networkx=True)

# Delegate to hub analyzer for basic centrality
async def calculate_basic_centrality(self, ...):
    return self.hub_analyzer.calculate_centrality(...)

# Add advanced centrality on top
async def calculate_advanced_centrality(self, ...):
    basic = await self.calculate_basic_centrality(...)
    advanced = self.centrality.calculate_all_measures(G)

    # Merge results
    return {**basic, **advanced}
```

### 6.2 Integration with Contingency Analysis

**File**: `backend/app/resilience/n1_n2_analysis.py`

```python
# Add network analysis to contingency detection

from app.resilience.network_analysis.service import NetworkAnalysisService

class ContingencyAnalyzer:
    def __init__(self):
        self.network_service = NetworkAnalysisService()

    async def detect_n1_vulnerabilities(self, db, schedule_id):
        # Build coverage network
        G = await self.network_service.build_coverage_network(
            db,
            start_date,
            end_date
        )

        # Use k-core to find critical nodes
        k_core = self.network_service.robustness.analyze_k_core(G)
        nucleus_nodes = k_core["nucleus_nodes"]

        # Test removal of nucleus nodes (N-1)
        for node in nucleus_nodes:
            G_copy = G.copy()
            G_copy.remove_node(node)

            # Check if network fragments
            if not nx.is_connected(G_copy):
                logger.warning(f"N-1 failure detected: {node}")
                # ... generate contingency plan
```

### 6.3 Integration with Burnout Epidemiology

**File**: `backend/app/resilience/burnout_epidemiology.py`

```python
# Use community detection for burnout contagion modeling

from app.resilience.network_analysis.service import NetworkAnalysisService

class BurnoutEpidemiologyAnalyzer:
    def __init__(self):
        self.network_service = NetworkAnalysisService()

    async def model_burnout_spread(self, db, seed_faculty_ids):
        # Build supervision network (burnout spreads via supervision)
        G = await self.network_service.build_coverage_network(
            db,
            start_date,
            end_date,
            graph_type="supervision"
        )

        # Detect communities (burnout clusters)
        communities = self.network_service.community.detect_louvain(G)

        # Run SIR model on each community
        for comm in communities["communities"]:
            community_graph = G.subgraph(comm["members"])

            # Estimate R0 for this community
            avg_degree = comm["avg_degree"]
            R0 = self._estimate_r0(avg_degree, contact_rate=0.3)

            # Simulate spread
            sir_result = self._run_sir_simulation(
                community_graph,
                seed_nodes=[n for n in seed_faculty_ids if n in comm["members"]],
                R0=R0
            )

            logger.info(
                f"Community {comm['community_id']}: "
                f"R0={R0:.2f}, peak_infected={sir_result['peak_infected']}"
            )
```

### 6.4 API Integration Points

**Existing Endpoints Enhanced**:

1. **`GET /api/v1/resilience/hub-analysis`** - Add network topology summary
2. **`GET /api/v1/resilience/contingency`** - Use k-core for critical node detection
3. **`GET /api/v1/resilience/health-check`** - Include network resilience score

**New Endpoints**:

4. **`GET /api/v1/network/topology`** - Topology metrics
5. **`GET /api/v1/network/centrality`** - All centrality measures
6. **`GET /api/v1/network/communities`** - Community detection
7. **`GET /api/v1/network/robustness`** - Attack tolerance
8. **`GET /api/v1/network/predictions`** - Link prediction

---

## 7. Visualization API

### 7.1 NetworkVisualizer

**File**: `backend/app/resilience/network_analysis/visualization.py`

```python
"""
Network Visualization Module.

Export graphs for D3.js, Gephi, and other visualization tools.
"""

import json
import networkx as nx
from typing import Dict, Any
import xml.etree.ElementTree as ET


class NetworkVisualizer:
    """Export network graphs for visualization."""

    def export_graph(
        self,
        G: nx.Graph,
        format: str = "d3",
        include_layout: bool = True,
        layout_algorithm: str = "spring"
    ) -> Any:
        """
        Export graph in specified format.

        Args:
            G: NetworkX graph
            format: Output format (d3, graphml, gexf, json)
            include_layout: Compute layout positions
            layout_algorithm: spring, kamada_kawai, circular

        Returns:
            Format-specific data structure
        """
        if format == "d3":
            return self._export_d3(G, include_layout, layout_algorithm)
        elif format == "graphml":
            return self._export_graphml(G)
        elif format == "gexf":
            return self._export_gexf(G)
        elif format == "json":
            return self._export_json(G, include_layout, layout_algorithm)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _export_d3(
        self,
        G: nx.Graph,
        include_layout: bool,
        layout_algorithm: str
    ) -> Dict:
        """
        Export for D3.js force-directed layout.

        Format:
        {
            "nodes": [{"id": "node1", "x": 0.5, "y": 0.3, ...}],
            "links": [{"source": "node1", "target": "node2", "weight": 1}]
        }
        """
        # Calculate layout if requested
        if include_layout:
            pos = self._calculate_layout(G, layout_algorithm)
        else:
            pos = None

        # Build node list
        nodes = []
        for node_id, node_data in G.nodes(data=True):
            node_dict = {
                "id": str(node_id),
                **node_data
            }

            if pos:
                node_dict["x"] = float(pos[node_id][0])
                node_dict["y"] = float(pos[node_id][1])

            nodes.append(node_dict)

        # Build edge list
        links = []
        for u, v, edge_data in G.edges(data=True):
            link_dict = {
                "source": str(u),
                "target": str(v),
                **edge_data
            }
            links.append(link_dict)

        return {
            "nodes": nodes,
            "links": links,
            "metadata": {
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "layout_algorithm": layout_algorithm if include_layout else None
            }
        }

    def _export_json(
        self,
        G: nx.Graph,
        include_layout: bool,
        layout_algorithm: str
    ) -> Dict:
        """
        Export as NetworkX node-link JSON.

        Standard NetworkX JSON format.
        """
        data = nx.node_link_data(G)

        if include_layout:
            pos = self._calculate_layout(G, layout_algorithm)
            for node in data["nodes"]:
                node_id = node["id"]
                node["x"] = float(pos[node_id][0])
                node["y"] = float(pos[node_id][1])

        return data

    def _export_graphml(self, G: nx.Graph) -> str:
        """
        Export as GraphML XML.

        Compatible with yEd, Gephi, NetworkX.
        """
        from io import BytesIO

        # Use NetworkX built-in GraphML writer
        buffer = BytesIO()
        nx.write_graphml(G, buffer)

        return buffer.getvalue().decode('utf-8')

    def _export_gexf(self, G: nx.Graph) -> str:
        """
        Export as GEXF (Gephi native format).

        Gephi-compatible XML.
        """
        from io import BytesIO

        buffer = BytesIO()
        nx.write_gexf(G, buffer)

        return buffer.getvalue().decode('utf-8')

    def _calculate_layout(
        self,
        G: nx.Graph,
        algorithm: str
    ) -> Dict[Any, tuple]:
        """
        Calculate node positions using layout algorithm.

        Args:
            G: NetworkX graph
            algorithm: spring, kamada_kawai, circular

        Returns:
            Dictionary mapping node_id to (x, y) coordinates
        """
        if algorithm == "spring":
            return nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        elif algorithm == "kamada_kawai":
            return nx.kamada_kawai_layout(G)
        elif algorithm == "circular":
            return nx.circular_layout(G)
        else:
            # Default to spring
            return nx.spring_layout(G, seed=42)

    def export_with_communities(
        self,
        G: nx.Graph,
        communities: List[Set],
        format: str = "d3"
    ) -> Dict:
        """
        Export graph with community colors.

        Assigns "community" attribute to each node.
        """
        # Add community attribute to nodes
        G_copy = G.copy()

        community_map = {}
        for i, comm in enumerate(communities):
            for node in comm:
                community_map[node] = i

        nx.set_node_attributes(G_copy, community_map, "community")

        # Export with community data
        return self.export_graph(G_copy, format=format)
```

### 7.2 Frontend Integration Example

**React component using D3 export**:

```typescript
// frontend/app/components/NetworkVisualization.tsx

import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useQuery } from '@tanstack/react-query';

interface NetworkVizProps {
  startDate: string;
  endDate: string;
  graphType: 'coverage' | 'supervision' | 'swap';
}

export const NetworkVisualization: React.FC<NetworkVizProps> = ({
  startDate,
  endDate,
  graphType
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['network-export', graphType, startDate, endDate],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/network/export/d3?` +
        `start_date=${startDate}&end_date=${endDate}&graph_type=${graphType}`
      );
      return response.json();
    }
  });

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const width = 800;
    const height = 600;

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height);

    // Clear previous
    svg.selectAll('*').remove();

    // Create force simulation if layout not pre-computed
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Draw edges
    const link = svg.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', (d: any) => Math.sqrt(d.weight || 1));

    // Draw nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .join('circle')
      .attr('r', 5)
      .attr('fill', (d: any) => {
        // Color by community if available
        const colors = d3.schemeCategory10;
        return colors[d.community % 10];
      })
      .call(drag(simulation));

    // Labels
    const label = svg.append('g')
      .selectAll('text')
      .data(data.nodes)
      .join('text')
      .text((d: any) => d.id)
      .attr('font-size', 10)
      .attr('dx', 8)
      .attr('dy', 4);

    // Update positions
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

  }, [data]);

  if (isLoading) return <div>Loading network...</div>;

  return <svg ref={svgRef} />;
};
```

---

## 8. Performance Optimization

### 8.1 Caching Strategy

**Cache Levels**:

1. **Redis Cache** (15 min TTL)
   - Graph construction results
   - Expensive analysis results (percolation, current flow betweenness)

2. **In-Memory Cache**
   - Current graph reference
   - Temporal snapshots

3. **Database Query Optimization**
   - Index on `assignments.block_id`, `assignments.person_id`
   - Materialized view for frequent coverage queries

### 8.2 Algorithm Complexity Management

**Adaptive Algorithm Selection**:

```python
def _run_centrality_analysis(self, G: nx.Graph) -> Dict:
    n = G.number_of_nodes()

    if n < 50:
        # All algorithms
        return self.centrality.calculate_all_measures(G, enable_expensive=True)
    elif n < 100:
        # Skip O(n³) algorithms
        return self.centrality.calculate_all_measures(G, enable_expensive=False)
    else:
        # Sampling for betweenness
        return self.centrality.calculate_sampled_measures(G, sample_size=50)
```

**Complexity Table**:

| Algorithm | Complexity | Limit | Alternative |
|-----------|-----------|-------|-------------|
| Degree centrality | O(n+m) | None | N/A |
| Betweenness | O(nm) | < 200 nodes | Sampled betweenness |
| Eigenvector | O(n²) | < 500 nodes | PageRank |
| Current flow | O(n³) | < 100 nodes | Skip |
| Louvain | O(m log n) | None | N/A |
| Percolation (MC) | O(trials × n²) | < 200 nodes | Reduce trials |

### 8.3 Parallel Processing

**Celery Tasks for Expensive Operations**:

```python
# backend/app/resilience/network_analysis/tasks.py

from app.core.celery_app import celery_app

@celery_app.task(name="network_analysis.calculate_percolation")
def calculate_percolation_async(
    graph_data: dict,
    strategy: str,
    num_trials: int
):
    """
    Calculate percolation threshold asynchronously.

    Args:
        graph_data: Serialized NetworkX graph (node-link format)
        strategy: random, degree, betweenness
        num_trials: Number of Monte Carlo trials
    """
    import networkx as nx
    from app.resilience.network_analysis.robustness import RobustnessAnalyzer

    # Deserialize graph
    G = nx.node_link_graph(graph_data)

    # Calculate
    analyzer = RobustnessAnalyzer()
    result = analyzer.calculate_percolation_threshold(G, strategy, num_trials)

    return result
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**File**: `backend/tests/resilience/test_network_analysis.py`

```python
"""Unit tests for network analysis modules."""

import pytest
import networkx as nx
from datetime import datetime, timedelta

from app.resilience.network_analysis.service import NetworkAnalysisService
from app.resilience.network_analysis.topology import TopologyAnalyzer
from app.resilience.network_analysis.centrality import CentralityCalculator


class TestTopologyAnalyzer:
    """Test topology analysis."""

    def test_small_world_detection(self):
        """Test small-world coefficient calculation."""
        # Watts-Strogatz small-world graph
        G = nx.watts_strogatz_graph(n=50, k=4, p=0.1, seed=42)

        analyzer = TopologyAnalyzer()
        result = analyzer.analyze_small_world(G)

        assert result["is_small_world"] is True
        assert result["small_world_sigma"] > 1.0
        assert 0 < result["clustering_coefficient"] < 1

    def test_scale_free_detection(self):
        """Test scale-free distribution detection."""
        # Barabási-Albert scale-free graph
        G = nx.barabasi_albert_graph(n=100, m=2, seed=42)

        analyzer = TopologyAnalyzer()
        result = analyzer.detect_scale_free(G)

        assert result["is_scale_free"] is True
        assert 2.0 < result["gamma"] < 3.5

    def test_clustering_analysis(self):
        """Test clustering coefficient analysis."""
        # Complete graph (maximum clustering)
        G = nx.complete_graph(10)

        analyzer = TopologyAnalyzer()
        result = analyzer.analyze_clustering(G)

        assert result["global_clustering"] == 1.0
        assert result["average_clustering"] == 1.0


class TestCentralityCalculator:
    """Test centrality calculations."""

    def test_all_measures(self):
        """Test comprehensive centrality calculation."""
        G = nx.karate_club_graph()

        calc = CentralityCalculator()
        result = calc.calculate_all_measures(G, enable_expensive=True)

        # Should have all measures
        assert "degree" in result
        assert "betweenness" in result
        assert "eigenvector" in result
        assert "pagerank" in result
        assert "current_flow" in result

        # All nodes should have scores
        assert len(result["degree"]) == G.number_of_nodes()

    def test_consensus_ranking(self):
        """Test consensus ranking across measures."""
        G = nx.karate_club_graph()

        calc = CentralityCalculator()
        all_measures = calc.calculate_all_measures(G)
        consensus = calc.calculate_consensus_ranking(all_measures)

        # Should be sorted by score
        scores = [score for node, score in consensus]
        assert scores == sorted(scores, reverse=True)


class TestNetworkAnalysisService:
    """Integration tests for network analysis service."""

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self):
        """Test full analysis pipeline."""
        # Create sample graph
        G = nx.karate_club_graph()

        service = NetworkAnalysisService()
        service._current_graph = G

        report = await service.run_comprehensive_analysis()

        assert "topology" in report
        assert "centrality" in report
        assert "communities" in report
        assert "robustness" in report
```

### 9.2 Integration Tests

```python
class TestNetworkAPIIntegration:
    """Test API endpoints."""

    @pytest.mark.asyncio
    async def test_topology_endpoint(self, client, db):
        """Test GET /api/v1/network/topology."""
        response = await client.get(
            "/api/v1/network/topology",
            params={
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2024-01-31T23:59:59",
                "graph_type": "coverage"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "small_world" in data
        assert "scale_free" in data
        assert "clustering" in data
```

### 9.3 Performance Tests

```python
@pytest.mark.performance
class TestNetworkPerformance:
    """Performance benchmarks."""

    def test_large_graph_analysis(self):
        """Test analysis on large graph (200 nodes)."""
        import time

        G = nx.barabasi_albert_graph(n=200, m=3, seed=42)

        service = NetworkAnalysisService()
        service._current_graph = G

        start = time.time()
        report = service.run_comprehensive_analysis()
        elapsed = time.time() - start

        # Should complete in < 30 seconds
        assert elapsed < 30.0
```

---

## 10. Deployment

### 10.1 Dependencies

**Add to `backend/requirements.txt`**:

```
networkx>=3.0
scipy>=1.11.0
scikit-learn>=1.3.0  # For NMI in community stability
powerlaw>=1.5  # Optional, for scale-free detection
```

### 10.2 Database Migrations

**No schema changes required** - uses existing tables:
- `assignments`
- `blocks`
- `persons`
- `rotations`
- `swap_requests`

### 10.3 Configuration

**Add to `backend/app/core/config.py`**:

```python
class Settings(BaseSettings):
    # ... existing settings

    # Network Analysis
    NETWORK_ANALYSIS_CACHE_TTL: int = 900  # 15 minutes
    NETWORK_ANALYSIS_MAX_NODES_EXPENSIVE: int = 100
    NETWORK_ANALYSIS_ENABLE_EXPENSIVE_OPS: bool = True
```

### 10.4 Docker Updates

**No Docker changes needed** - NetworkX already included in backend container.

---

## 11. Future Enhancements

### 11.1 Phase 2 Features

1. **Weighted Graphs**: Edge weights based on shift hours, not just connections
2. **Multilayer Networks**: Separate layers for different rotation types
3. **Hypergraphs**: Model N-way interactions (team assignments)
4. **Temporal Motifs**: Detect recurring temporal patterns

### 11.2 Advanced Analytics

1. **Spreading Dynamics**: SIS/SIR models for burnout contagion
2. **Network Controllability**: Identify minimum driver nodes
3. **Structural Balance**: Detect triadic closure patterns
4. **Network Immunization**: Optimal vaccination strategy (cross-training)

### 11.3 Visualization Enhancements

1. **Interactive D3 Dashboard**: Drag nodes, filter by metrics
2. **Temporal Animation**: Watch network evolve over time
3. **3D Visualization**: For large, complex networks
4. **Gephi Integration**: Export for advanced offline analysis

---

## Appendix A: Research Reference

All implementations are based on:
- **`docs/research/NETWORK_RESILIENCE_DEEP_DIVE.md`** - Comprehensive research on graph theory applications

Key papers:
- Watts & Strogatz (1998) - Small-world networks
- Barabási & Albert (1999) - Scale-free networks
- Newman (2018) - Networks textbook
- Blondel et al. (2008) - Louvain algorithm

---

## Appendix B: API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/network/topology` | GET | Network topology metrics |
| `/api/v1/network/centrality` | GET | All centrality measures |
| `/api/v1/network/communities` | GET | Community detection |
| `/api/v1/network/robustness` | GET | Attack tolerance analysis |
| `/api/v1/network/predictions` | GET | Link prediction |
| `/api/v1/network/export/{format}` | GET | Export graph for viz |

---

**Document Status**: Production-Ready
**Implementation Priority**: High
**Estimated Effort**: 3-4 weeks (1 developer)

**Next Steps**:
1. Review and approve specification
2. Create GitHub issues for each module
3. Implement in phases: Topology → Centrality → Community → Robustness → Temporal
4. Deploy to staging for testing
5. Roll out to production

---

*End of Specification*
