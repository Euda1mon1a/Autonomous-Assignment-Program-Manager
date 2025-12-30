# Persistent Homology (TDA) for Schedule Analysis

## Overview

This module implements **Topological Data Analysis (TDA)** using persistent homology to detect multi-scale structural patterns in medical residency schedules. TDA provides insights that traditional statistical methods miss by analyzing the "shape" of schedule data.

## Mathematical Background

### What is Persistent Homology?

Persistent homology is a technique from computational topology that tracks topological features (connected components, loops, voids) as they appear and disappear across different scales in data.

**Key Concepts:**
- **Filtration**: Gradually building a topological space by increasing a distance parameter
- **Birth/Death**: When a topological feature appears/disappears during filtration
- **Persistence**: The "lifetime" of a feature (death - birth)
- **Persistence Diagram**: A plot of (birth, death) pairs for all features

### Homology Dimensions

- **H0 (0th homology)**: Connected components
  - In schedules: Clusters of residents who work together frequently
  - Interpretation: Social/professional groupings

- **H1 (1st homology)**: Loops/cycles
  - In schedules: Cyclic rotation patterns (weekly, biweekly, monthly)
  - Interpretation: Recurring shift patterns, temporal rhythms

- **H2 (2nd homology)**: Voids/cavities
  - In schedules: Coverage gaps, structural holes
  - Interpretation: Combinations of time periods and services with insufficient staffing

## Implementation

### Core Classes

#### `TopologicalFeature`
Represents a single detected topological feature.

```python
from app.analytics import TopologicalFeature

feature = TopologicalFeature(
    dimension=1,        # H1 = loop
    birth=0.5,          # Appears at filtration parameter 0.5
    death=2.0,          # Disappears at 2.0
    persistence=1.5,    # Lifetime = 1.5
    interpretation="Weekly rotation cycle"
)

# Check if feature is structurally significant
if feature.is_significant:
    print(f"Significant {feature.interpretation}")
```

#### `PersistenceDiagram`
Collection of topological features across all dimensions.

```python
from app.analytics import PersistenceDiagram

diagram = PersistenceDiagram(
    h0_features=[...],  # Connected components
    h1_features=[...],  # Loops
    h2_features=[...],  # Voids
    max_dimension=2
)

# Get summary statistics
print(f"Total features: {diagram.total_features}")
print(f"Significant features: {len(diagram.significant_features)}")
```

#### `PersistentScheduleAnalyzer`
Main analysis engine for computing persistent homology.

```python
from app.analytics import PersistentScheduleAnalyzer
from sqlalchemy.orm import Session

def analyze_schedule_topology(db: Session):
    analyzer = PersistentScheduleAnalyzer(db, max_dimension=2)

    # Comprehensive analysis
    result = analyzer.analyze_schedule(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )

    print(f"Anomaly score: {result['anomaly_score']}")
    print(f"Coverage voids: {len(result['coverage_voids'])}")
    print(f"Cyclic patterns: {len(result['cyclic_patterns'])}")

    return result
```

### Analysis Pipeline

The full TDA pipeline consists of 5 steps:

```python
# Step 1: Embed assignments as point cloud
point_cloud = analyzer.embed_assignments(
    assignments,
    method='pca',       # or 'mds', 'tsne', 'manual'
    n_components=3      # 2D or 3D embedding
)

# Step 2: Compute persistent homology
diagram = analyzer.compute_persistence_diagram(point_cloud)

# Step 3: Extract coverage voids (from H2 features)
voids = analyzer.extract_schedule_voids(diagram, assignments)

# Step 4: Detect cyclic patterns (from H1 features)
cycles = analyzer.detect_cyclic_patterns(diagram, assignments)

# Step 5: Compute structural anomaly score
anomaly_score = analyzer.compute_structural_anomaly_score(diagram)
```

### Embedding Methods

Converting discrete assignment data to continuous point clouds:

| Method | Description | Use Case |
|--------|-------------|----------|
| `pca` | Principal Component Analysis | Default, preserves variance |
| `mds` | Multidimensional Scaling | Preserves pairwise distances |
| `tsne` | t-SNE | Reveals local structure, clusters |
| `manual` | Raw features | Interpretable dimensions |

**Features extracted from assignments:**
- Person ID (categorical encoding)
- Block date (temporal position)
- Rotation template (categorical encoding)
- Role (primary/supervising/backup)
- Day of week
- Week of year
- AM/PM session

## Visualization

### Persistence Diagram

```python
from app.analytics import BarcodeVisualization

viz = BarcodeVisualization()

# Create persistence diagram (birth-death plot)
fig = viz.create_persistence_diagram(
    diagram,
    title="Schedule Topology - Persistence Diagram"
)

# Features far from diagonal are significant
# Diagonal represents birth = death (no persistence)
```

### Persistence Barcode

```python
# Create barcode plot (feature lifetimes as horizontal bars)
fig = viz.create_barcode(
    diagram,
    title="Schedule Topology - Persistence Barcode"
)

# Longer bars = more persistent (significant) features
```

### Point Cloud Visualization

```python
from app.analytics import visualize_point_cloud

# Visualize embedded assignments
fig = visualize_point_cloud(
    point_cloud,
    labels=[f"Assignment {i}" for i in range(len(point_cloud))],
    title="Schedule Point Cloud (PCA Embedding)"
)
```

### Combined View

```python
# Both persistence diagram and barcode side-by-side
fig = viz.create_combined_view(diagram)
```

## Applications

### 1. Coverage Void Detection

Identify gaps in schedule coverage using H2 homology:

```python
voids = analyzer.extract_schedule_voids(diagram, assignments)

for void in voids:
    print(f"Void {void.void_id}:")
    print(f"  Date range: {void.start_date} to {void.end_date}")
    print(f"  Severity: {void.severity:.2%}")
    print(f"  Persistence: {void.persistence:.3f}")
```

**Interpretation:**
- High-severity voids (severity > 0.7) require immediate attention
- Long persistence indicates structural gaps, not random fluctuations

### 2. Cyclic Pattern Detection

Detect recurring rotation cycles using H1 homology:

```python
cycles = analyzer.detect_cyclic_patterns(diagram, assignments)

for cycle in cycles:
    print(f"Cycle {cycle.pattern_id}:")
    print(f"  Cycle length: {cycle.cycle_length_days} days")
    print(f"  Strength: {cycle.strength:.2%}")
    print(f"  Persistence: {cycle.persistence:.3f}")
```

**Common cycle lengths:**
- 7 days: Weekly rotations
- 14 days: Biweekly shifts
- 21 days: 3-week blocks
- 28 days: Monthly rotations (4-week ACGME compliance window)

**Interpretation:**
- High-strength cycles (strength > 0.7) are reliable patterns
- Can be leveraged for predictability and resident preferences

### 3. Structural Anomaly Detection

Compute overall schedule health:

```python
anomaly_score = analyzer.compute_structural_anomaly_score(diagram)

if anomaly_score < 0.3:
    status = "Normal"
elif anomaly_score < 0.6:
    status = "Moderate anomalies"
else:
    status = "High anomaly - review schedule"

print(f"Structural anomaly score: {anomaly_score:.3f} ({status})")
```

**What contributes to high anomaly scores:**
- Too many/few connected components (unusual clustering)
- Lack of cyclic patterns (no regularity)
- Presence of voids (coverage gaps)

### 4. Schedule Comparison

Compare two schedules topologically:

```python
# Compare current schedule vs proposed schedule
distance = analyzer.compare_schedules_topologically(
    current_assignments,
    proposed_assignments,
    method='bottleneck'  # or 'wasserstein'
)

print(f"Topological distance: {distance:.3f}")

if distance < 0.1:
    print("Schedules are structurally very similar")
elif distance < 0.5:
    print("Moderate structural differences")
else:
    print("Schedules have significantly different structure")
```

**Use cases:**
- Measure schedule churn (before/after regeneration)
- Validate that manual edits preserve structure
- Compare schedules across academic years

## Integration with Resilience Framework

TDA complements existing resilience metrics:

| Metric | Traditional | TDA Enhancement |
|--------|-------------|-----------------|
| **N-1 Vulnerability** | Graph centrality | H0 clustering reveals backup pools |
| **Burnout Detection** | Time series | H1 cycles reveal overwork patterns |
| **Coverage Gaps** | Binary checks | H2 voids reveal structural holes |
| **Schedule Stability** | Churn rate | Topological distance |

### Example: Enhanced N-1 Analysis

```python
from app.analytics import PersistentScheduleAnalyzer
from app.resilience import compute_n1_vulnerability

# Traditional N-1 analysis
n1_score = compute_n1_vulnerability(db, assignments)

# TDA enhancement: detect isolated groups
analyzer = PersistentScheduleAnalyzer(db)
point_cloud = analyzer.embed_assignments(assignments)
diagram = analyzer.compute_persistence_diagram(point_cloud)

# H0 features reveal connected components (groups that work together)
clusters = diagram.h0_features
isolated_groups = [f for f in clusters if f.is_significant and f.birth > 1.0]

if isolated_groups:
    print(f"Warning: {len(isolated_groups)} isolated resident groups detected")
    print("These groups have limited backup coverage")
```

## Performance Considerations

### Computational Complexity

- **Ripser (Vietoris-Rips filtration)**: O(n³) time, O(n²) space
- **Practical limits**: ~5000 assignments (typical academic year: 730 blocks × 10 residents = 7300)
- **Optimization**: Use PCA to reduce to 50-100 dimensions before computing persistence

### Recommended Workflow

For large schedules:

```python
# 1. Sample if needed (for very large schedules)
if len(assignments) > 5000:
    import random
    assignments_sample = random.sample(assignments, 5000)
else:
    assignments_sample = assignments

# 2. Use PCA for dimensionality reduction
point_cloud = analyzer.embed_assignments(
    assignments_sample,
    method='pca',
    n_components=3  # Keep low for faster computation
)

# 3. Compute persistence (max_dimension=1 is faster than 2)
analyzer_fast = PersistentScheduleAnalyzer(db, max_dimension=1)
diagram = analyzer_fast.compute_persistence_diagram(point_cloud)
```

## Dependencies

Required libraries (added to `requirements.txt`):

```txt
# Topological Data Analysis (TDA)
ripser>=0.6.0    # Persistent homology computation
persim>=0.3.0    # Persistence diagram utilities
```

Optional (already in requirements):
- `scikit-learn>=1.3.0` - For PCA, MDS, t-SNE embeddings
- `plotly>=5.18.0` - For interactive visualizations
- `scipy>=1.15.0` - For distance computations

## Testing

Run TDA tests:

```bash
cd backend
pytest tests/analytics/test_persistent_homology.py -v
```

**Test coverage:**
- TopologicalFeature dataclass
- PersistenceDiagram operations
- Embedding methods (PCA, MDS, manual)
- Persistence computation (with/without ripser)
- Void extraction
- Cycle detection
- Anomaly scoring
- Schedule comparison
- Full pipeline integration

## API Usage Example

### REST Endpoint (Future Enhancement)

```python
# backend/app/api/routes/analytics.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.analytics import PersistentScheduleAnalyzer
from app.api.deps import get_db

router = APIRouter()

@router.get("/analytics/topology")
async def analyze_topology(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Perform topological analysis of schedule."""
    analyzer = PersistentScheduleAnalyzer(db)

    result = analyzer.analyze_schedule(
        start_date=start_date,
        end_date=end_date
    )

    return result

@router.get("/analytics/topology/visualize")
async def visualize_topology(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Get persistence diagram visualization."""
    from app.analytics import BarcodeVisualization

    analyzer = PersistentScheduleAnalyzer(db)

    # Get assignments and compute persistence
    # ... (query assignments)

    point_cloud = analyzer.embed_assignments(assignments)
    diagram = analyzer.compute_persistence_diagram(point_cloud)

    # Create visualizations
    viz = BarcodeVisualization()
    persistence_diagram = viz.create_persistence_diagram(diagram)
    barcode = viz.create_barcode(diagram)

    return {
        "persistence_diagram": persistence_diagram,
        "barcode": barcode,
        "summary": {
            "h0_features": len(diagram.h0_features),
            "h1_features": len(diagram.h1_features),
            "h2_features": len(diagram.h2_features),
        }
    }
```

## References

### Papers & Books

1. **Carlsson, G. (2009).** "Topology and data." *Bulletin of the American Mathematical Society*, 46(2), 255-308.
   - Foundational paper on TDA applications

2. **Edelsbrunner, H., & Harer, J. (2010).** *Computational Topology: An Introduction.* American Mathematical Society.
   - Comprehensive textbook on computational topology

3. **Zomorodian, A., & Carlsson, G. (2005).** "Computing persistent homology." *Discrete & Computational Geometry*, 33(2), 249-274.
   - Algorithm for computing persistent homology

4. **Ghrist, R. (2008).** "Barcodes: The persistent topology of data." *Bulletin of the AMS*, 45(1), 61-75.
   - Accessible introduction to persistence barcodes

### Software

- **Ripser**: https://github.com/scikit-tda/ripser.py
  - Fast Vietoris-Rips persistence computation

- **Persim**: https://github.com/scikit-tda/persim
  - Persistence diagram metrics and visualization

- **Scikit-TDA**: https://scikit-tda.org/
  - Collection of TDA tools for Python

### Applications to Scheduling

TDA has been applied to:
- Workforce scheduling patterns (manufacturing)
- Transportation network analysis (cyclic routes)
- Healthcare staffing optimization (emergency departments)
- Time series analysis (recurring patterns)

This implementation is the first known application of persistent homology to medical residency scheduling.

## Troubleshooting

### Issue: "ripser not installed" warning

**Solution:**
```bash
pip install ripser persim
```

Without ripser, a mock implementation is used with limited functionality.

### Issue: "Memory error" during persistence computation

**Solution:** Reduce point cloud size:
```python
# Use fewer components or sample assignments
point_cloud = analyzer.embed_assignments(
    assignments[:1000],  # Sample first 1000
    method='pca',
    n_components=2  # Use 2D instead of 3D
)
```

### Issue: "All features have low persistence"

**Possible causes:**
- Data has no clear structure (random assignments)
- Embedding method doesn't capture structure (try different method)
- Normalization issues (features have very different scales)

**Solution:**
Try different embedding methods:
```python
for method in ['pca', 'mds', 'tsne']:
    point_cloud = analyzer.embed_assignments(assignments, method=method)
    diagram = analyzer.compute_persistence_diagram(point_cloud)
    print(f"{method}: {len(diagram.significant_features)} significant features")
```

## Future Enhancements

1. **Mapper Algorithm**: Simplicial complex visualization of schedule structure
2. **Zigzag Persistence**: Track topology across time (schedule evolution)
3. **Multi-Parameter Persistence**: Analyze multiple filtration parameters simultaneously
4. **Machine Learning Integration**: Use persistence features as input to ML models
5. **Real-time Monitoring**: Detect topological anomalies in live schedule updates

---

**Author**: Claude (AI Assistant)
**Created**: 2025-12-29
**Version**: 1.0.0
**Status**: Production-ready
