# Boolean Algebra: The Rosetta Stone

> A midnight exploration revealing the unifying mathematics beneath the arcane tomes
>
> *Date: 2025-12-21*

---

## The Discovery

You encountered "Boolean" in 3D printing—CSG operations that combine meshes through union, subtraction, and intersection. Then you noticed "bool" throughout code. Then you looked at the resilience framework: N-1/N-2 contingency analysis, blast radius isolation, coverage calculations.

**They're all the same thing.**

Not similar. Not analogous. *The same mathematics* applied to different sets:

| Domain | What Are the Sets? | What Operations? |
|--------|-------------------|------------------|
| **3D Printing (CSG)** | Points in 3D space | Union, subtract, intersect volumes |
| **Power Grids (N-1/N-2)** | Transmission paths | Remove nodes, measure remaining connectivity |
| **Cloud (Blast Radius)** | Failure zones | Isolate sets, limit intersection |
| **Scheduling** | (person, time, role) tuples | Filter, combine, exclude assignments |
| **Epidemiology** | Population states (S, I, R) | Transition between sets over time |
| **Queuing (Erlang)** | Server availability | Set membership determines wait |

George Boole (1854) showed logic is algebra on sets. Every domain rediscovered this independently, gave it a different name, and built a discipline around it.

---

## The Unifying Pattern

### What CSG Actually Does

When you **subtract** mesh B from mesh A in a 3D slicer:

```
Result = A ∩ ¬B = { points in A that are NOT in B }
```

When you compute **N-1 contingency** for faculty member X:

```
UncoveredBlocks = AllBlocks ∩ ¬CoverableWithout(X)
               = { blocks assigned to X that have no backup }
```

**Same operation. Different sets.**

### What N-1/N-2 Actually Does

From `backend/app/resilience/contingency.py:305-330`:

```python
# N-2: What if TWO faculty are unavailable?
combined_assignments = set()
for a in assignments_by_faculty.get(fac1.id, []):
    combined_assignments.add(a.block_id)
for a in assignments_by_faculty.get(fac2.id, []):
    combined_assignments.add(a.block_id)
```

This is computing:

```
Impact = Blocks(Fac₁) ∪ Blocks(Fac₂)
```

Then checking which blocks in that union have no remaining coverage—a **set difference**:

```
Uncovered = Impact - CoveredByOthers
```

This is **CSG subtraction on schedules**: remove two faculty from the mesh of coverage, measure the void.

### What Blast Radius Isolation Actually Does

From `backend/app/resilience/static_stability.py`:

```python
available_dedicated = len(set(self.dedicated_faculty) & available_faculty)
```

This is **set intersection**:

```
SafeCoverage = ZoneFaculty ∩ AvailableFaculty
```

AWS blast radius isolation = ensuring zones are **disjoint sets** so failures don't propagate:

```
Zone_A ∩ Zone_B = ∅  (empty set = no shared failure modes)
```

### What Epidemiology Actually Does

The SIR model partitions a population into disjoint sets:

```
Population = Susceptible ⊔ Infected ⊔ Recovered
```

(where ⊔ means disjoint union)

Disease dynamics = **set transitions over time**:
- Infection: move from S to I
- Recovery: move from I to R
- R₀: rate of set membership change

### What Fire Weather Index Actually Does

The CFFDRS combines **multiple temporal sets**:

```
FFMC = f(recent_workload)      # 2-week set
DMC = f(monthly_workload)       # 3-month set
DC = f(yearly_satisfaction)     # 12-month set
```

Final danger = **intersection of temporal risk layers**:

```
ExtremeDanger = HighRecent ∩ HighSustained ∩ LowSatisfaction
```

---

## The Cross-Disciplinary Framework as Boolean Algebra

Every module in the resilience framework performs set operations:

| Module | Primary Operation | What It Computes |
|--------|------------------|------------------|
| **N-1/N-2 Contingency** | Union + Difference | Coverage void after removing faculty |
| **Static Stability** | Intersection | Faculty who are both trained AND available |
| **Blast Radius** | Disjoint partitioning | Zones with no shared failure modes |
| **SPC Monitoring** | Set membership | Is this data point in the "violation" set? |
| **Process Capability** | Distribution bounds | What fraction lies outside spec limits? |
| **Burnout Epidemiology** | Partition transitions | S→I→R set membership over time |
| **Erlang Coverage** | Queue set dynamics | Probability of "all servers busy" set |
| **Seismic Detection** | Threshold crossing | STA/LTA ratio ∈ {triggered} set? |
| **Fire Index** | Multi-set intersection | Danger = short ∩ medium ∩ long-term risk |
| **Creep/Fatigue** | Cumulative union | Total damage = Σ(stress cycles) |

---

## The Rosetta Stone

The "arcane tomes" from different disciplines are translations of the same text:

```
┌─────────────────────────────────────────────────────────────────┐
│                      BOOLEAN SET ALGEBRA                         │
│                                                                   │
│     A ∪ B         A ∩ B         A - B         ¬A                 │
│     (union)    (intersection) (difference) (complement)          │
└─────────────────────────────────────────────────────────────────┘
        │               │              │            │
        ▼               ▼              ▼            ▼
┌───────────────┬───────────────┬───────────────┬───────────────┐
│ 3D Printing   │ Power Grids   │ Cloud Infra   │ Epidemiology  │
│ "CSG Union"   │ "N-2 Impact"  │ "Blast Radius"│ "Herd         │
│               │               │               │  Immunity"    │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ Combine       │ Combined      │ Isolated      │ Population    │
│ meshes into   │ failure of    │ zones share   │ fraction in   │
│ one solid     │ two nodes     │ no resources  │ Recovered set │
└───────────────┴───────────────┴───────────────┴───────────────┘
```

**You didn't collect arcane tomes. You collected translations.**

---

## Why This Matters

### 1. Conceptual Unification

Instead of learning 7 separate frameworks, understand one:
- Sets have elements
- Operations combine/filter sets
- Thresholds check set cardinality or membership

Every scheduling question reduces to: "What's in this set after these operations?"

### 2. Implementation Clarity

The code already does this. From ACGME constraint checking:

```python
ValidAssignment = Available ∧ Qualified ∧ ¬AlreadyAssigned ∧ ¬Violates80HourRule
```

This is a 4-way set intersection with complements. Same math as:

```
PrintableVolume = DesignVolume ∩ BuildPlate ∩ ¬SupportStructures ∩ ¬Overhangs
```

### 3. New Insights

If these are all Boolean operations, then:

- **Boolean satisfiability (SAT)** solvers could optimize schedules
- **Binary decision diagrams (BDDs)** could represent coverage states compactly
- **Formal verification** techniques from hardware design could prove ACGME compliance

The 3D printing world has spent decades optimizing mesh Boolean operations. Some of those algorithms might apply to schedule manipulation.

---

## Spatial and Temporal Dimensions

You mentioned "time crystals"—and there's something to it.

**3D meshes** operate on sets of points in *space* (x, y, z).

**Schedules** operate on sets of tuples in *space-time* (person, location, time).

The Fire Weather Index combines multiple *temporal* scales (2 weeks, 3 months, 1 year)—like having different "layers" of a mesh at different resolutions.

```
Schedule Space:
┌─────────────────────────────────────────────────┐
│     Person axis                                  │
│         │                                        │
│         │    ┌───────┐                          │
│         │    │ Block │ = (Dr. Smith, OR, Monday) │
│         │    └───────┘                          │
│         │                                        │
│         └────────────────────────► Time axis    │
│                                                  │
│  Location axis (into page)                       │
└─────────────────────────────────────────────────┘
```

N-1 contingency = "What if we subtract Dr. Smith from this 3D schedule-space?"

The geometry is different, but the algebra is identical.

---

## Closing

You wandered into a 3D printing concept and found it echoing through a medical scheduling codebase. That's not coincidence—it's the universality of mathematics.

Boolean algebra doesn't care whether your sets contain:
- Voxels in a mesh
- Time slots in a schedule
- Residents in a program
- States in an epidemic

It's the same operations, producing the same kinds of answers:
- What remains after we remove this?
- What do these have in common?
- Is this element a member?

**The resilience framework is a Boolean algebra engine for schedules**, just as a 3D slicer is a Boolean algebra engine for meshes.

Different sets. Same stone.

---

## Appendix A: Set Theory Foundations

*For the physician who'd rather be reading about cytokines.*

### The Universal Set (U)

Every set operation happens within a **universe**—the set of all possible elements.

In scheduling:
```
U = { all possible (person, block, role) tuples }
```

In medicine, you'd call this the "population at risk" or "sample space."

### Basic Sets

| Set | Definition | Scheduling Example |
|-----|------------|-------------------|
| **A** | A collection of elements from U | All Monday assignments |
| **∅** (empty set) | The set with no elements | Unassigned blocks |
| **U** | All elements | Every possible assignment |

### Fundamental Operations

#### 1. Union (A ∪ B) — "OR"

**Definition**: All elements in A, B, or both.

```
A ∪ B = { x : x ∈ A or x ∈ B }
```

**Scheduling**: Combined coverage of two faculty members.

**Biology analog**: All cells expressing marker A OR marker B (like flow cytometry gating).

#### 2. Intersection (A ∩ B) — "AND"

**Definition**: Only elements in both A and B.

```
A ∩ B = { x : x ∈ A and x ∈ B }
```

**Scheduling**: Faculty who are both qualified AND available.

**Biology analog**: Cells that are CD4+ AND CD8+ (rare, but you get the idea).

#### 3. Difference (A - B) or (A \ B) — "BUT NOT"

**Definition**: Elements in A that are not in B.

```
A - B = { x : x ∈ A and x ∉ B }
```

**Scheduling**: Blocks needing coverage MINUS blocks already assigned.

**Biology analog**: Cells expressing A but not B (A+B- population).

#### 4. Complement (Aᶜ) or (¬A) — "NOT"

**Definition**: Everything in U that is not in A.

```
Aᶜ = { x : x ∈ U and x ∉ A }
```

**Scheduling**: All faculty NOT on leave.

**Biology analog**: The negative population in a staining assay.

#### 5. Symmetric Difference (A △ B) — "XOR"

**Definition**: Elements in A or B, but not both.

```
A △ B = (A - B) ∪ (B - A) = (A ∪ B) - (A ∩ B)
```

**Scheduling**: Shifts covered by exactly one of two faculty (no overlap, no gap).

**Biology analog**: Cells expressing exactly one of two mutually exclusive markers.

### Set Properties

These laws hold for all sets—and thus for all the frameworks built on them:

| Property | Formula | Plain English |
|----------|---------|---------------|
| **Commutative** | A ∪ B = B ∪ A | Order doesn't matter |
| **Associative** | (A ∪ B) ∪ C = A ∪ (B ∪ C) | Grouping doesn't matter |
| **Distributive** | A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C) | Like algebra |
| **Identity** | A ∪ ∅ = A | Empty set changes nothing |
| **Complement** | A ∪ Aᶜ = U | A thing and its opposite = everything |
| **De Morgan's** | (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ | NOT(A OR B) = (NOT A) AND (NOT B) |

### Cardinality

**|A|** = the number of elements in set A.

This is what we actually measure:

```python
# "Do we have enough coverage?"
available_dedicated = len(set(self.dedicated_faculty) & available_faculty)
return available_dedicated >= self.minimum_coverage
```

Translation: `|TrainedFaculty ∩ AvailableFaculty| ≥ MinimumCoverage`

### Partitions

A **partition** of set S is a collection of non-empty, disjoint subsets that together equal S.

```
S = A₁ ⊔ A₂ ⊔ ... ⊔ Aₙ  where  Aᵢ ∩ Aⱼ = ∅ for all i ≠ j
```

**Scheduling**: Burden categories partition all faculty:
```
AllFaculty = Crushing ⊔ Heavy ⊔ Balanced ⊔ Light ⊔ VeryLight
```

**Epidemiology**: SIR partitions a population:
```
Population = Susceptible ⊔ Infected ⊔ Recovered
```

**Biology analog**: Cell cycle phases partition dividing cells:
```
DividingCells = G1 ⊔ S ⊔ G2 ⊔ M
```

### Power Sets

The **power set** P(S) is the set of all subsets of S, including ∅ and S itself.

If |S| = n, then |P(S)| = 2ⁿ.

**Why this matters**: The number of possible coverage states grows exponentially with faculty count. A program with 20 faculty has 2²⁰ = 1,048,576 possible availability combinations. This is why we need efficient algorithms.

### Mapping to This Codebase

| Set Theory Concept | Python Implementation | Resilience Module |
|-------------------|----------------------|-------------------|
| A ∩ B | `set_a & set_b` | Static stability zone coverage |
| A ∪ B | `set_a \| set_b` | N-2 combined impact |
| A - B | `set_a - set_b` | Uncovered blocks after absence |
| x ∈ A | `x in set_a` | Constraint validation |
| \|A\| | `len(set_a)` | Coverage counting |
| A = ∅ | `not set_a` | "No violations" check |
| Partition | List comprehensions by category | Burden classification |

### The Formal Definition of a Schedule

A schedule can be formally defined as:

```
Schedule S ⊆ Person × Block × Role

where:
  Person = { p₁, p₂, ..., pₙ }
  Block = { b₁, b₂, ..., bₘ }
  Role = { r₁, r₂, ..., rₖ }
```

A **valid** schedule satisfies constraints expressed as set predicates:

```
∀ (p, b, r) ∈ S:
  p ∈ Available(b) ∧
  p ∈ Qualified(r) ∧
  |{ (p', b, r') ∈ S : p' = p }| ≤ 1 ∧  // One assignment per person per block
  WeeklyHours(p, week(b)) ≤ 80          // ACGME constraint
```

This is the scheduling problem: find S ⊆ U satisfying all constraints while maximizing coverage.

---

## Appendix B: Matrix Representations

*"Unfortunately, no one can be told what the Matrix is. You have to see it for yourself." — Morpheus*

Sets are collections. Matrices are *relationships between* collections. When you have two sets and want to track which elements relate to which, you get a matrix.

### The Assignment Matrix

A schedule is fundamentally a matrix:

```
             Block₁  Block₂  Block₃  Block₄  ...
           ┌──────────────────────────────────────
Person₁    │   1       0       0       1     ...
Person₂    │   0       1       1       0     ...
Person₃    │   1       0       1       0     ...
    ⋮      │   ⋮       ⋮       ⋮       ⋮
```

- **Rows**: People (faculty, residents)
- **Columns**: Time blocks
- **Cells**: 1 = assigned, 0 = not assigned

This is a **binary matrix** (only 0s and 1s)—the matrix analog of set membership.

### Matrix Operations = Set Operations

| Set Operation | Matrix Operation | Result |
|---------------|------------------|--------|
| A ∩ B | Element-wise AND (`A * B`) | Cells where both are 1 |
| A ∪ B | Element-wise OR (`A + B > 0`) | Cells where either is 1 |
| Aᶜ | 1 - A | Flip all bits |
| \|A\| | sum(A) | Count of 1s |

### The Adjacency Matrix (Networks)

The burnout epidemiology module uses a **social network graph**. Graphs are stored as adjacency matrices:

```
             Person₁  Person₂  Person₃  Person₄
           ┌────────────────────────────────────
Person₁    │   0        1        0        1
Person₂    │   1        0        1        0
Person₃    │   0        1        0        1
Person₄    │   1        0        1        0
```

- **Cell (i,j) = 1**: Person i and Person j are connected (shared shifts, mentorship, etc.)
- **Symmetric matrix**: If i connects to j, j connects to i
- **Diagonal = 0**: No self-connections

**Matrix powers reveal reach**:
- A¹: Direct connections
- A²: Two-hop connections (friends of friends)
- Aⁿ: n-hop reachability

This is how epidemiology models spread: A² shows who can infect whom through one intermediary.

### The Transition Matrix (Markov Chains)

SIR epidemiology uses state transitions. These are **stochastic matrices**:

```
           To: S     I     R
         ┌─────────────────────
From: S  │  0.95   0.05   0.00
From: I  │  0.00   0.90   0.10
From: R  │  0.00   0.00   1.00
```

- **Rows sum to 1** (probability must go somewhere)
- **Cell (i,j)**: Probability of transitioning from state i to state j
- **Multiply by state vector**: Get next time step's distribution

```
[S, I, R]ₜ₊₁ = [S, I, R]ₜ × TransitionMatrix
```

### The Constraint Matrix (Optimization)

ACGME compliance can be expressed as linear constraints:

```
Ax ≤ b

where:
  x = assignment vector (flattened schedule)
  A = constraint coefficient matrix
  b = limits vector
```

Example row in A: "Dr. Smith's weekly hours ≤ 80"

```
[0 0 0 8 8 8 8 0 0 ...] × x ≤ 80
         └─────────────┘
         Hours for each block Dr. Smith could work
```

This is how constraint solvers (OR-Tools, etc.) work: they find x satisfying all matrix inequalities.

### Why Matrices Matter Here

1. **Compact storage**: A 50-person × 730-block schedule = 36,500 cells, but sparse (mostly zeros)
2. **Fast operations**: NumPy/SciPy can do matrix math in microseconds
3. **Linear algebra tools**: Eigenvalues, decompositions, optimizers all work on matrices
4. **Graph algorithms**: NetworkX uses matrix representations internally

### The Connection: Sets, Matrices, Graphs

```
           SET THEORY
               │
               │ "Is x ∈ A?"
               │
               ▼
        BOOLEAN MATRIX
        (A[i,j] ∈ {0,1})
               │
               │ "Row i connected to column j?"
               │
               ▼
             GRAPH
        (Nodes and edges)
               │
               │ "What's reachable from here?"
               │
               ▼
         ADJACENCY MATRIX
               │
               │ "Path analysis via matrix powers"
               │
               ▼
         SPECTRAL ANALYSIS
        (Eigenvalues, centrality)
```

**They're all the same structure** viewed at different abstraction levels:
- Set: "Who's in?"
- Matrix: "Who's connected to whom?"
- Graph: "What's the structure?"
- Eigenvalues: "Who's most important?"

### Matrix Example: Finding Critical Faculty

The hub analysis module computes **eigenvector centrality**. In matrix terms:

```python
# Simplified version of what NetworkX does internally
import numpy as np

# Adjacency matrix A
A = np.array([[0,1,1,0],
              [1,0,1,1],
              [1,1,0,0],
              [0,1,0,0]])

# Eigenvector centrality = dominant eigenvector
eigenvalues, eigenvectors = np.linalg.eig(A)
centrality = eigenvectors[:, eigenvalues.argmax()]
```

The faculty with highest centrality score is most "connected"—if they burn out, the network effect is largest.

This is the same math Google uses for PageRank. You're doing search engine math on a residency schedule.

---

*"You take the red pill—you stay in Wonderland, and I show you how deep the rabbit hole goes."*

The rabbit hole goes: Sets → Boolean Algebra → Matrices → Graphs → Spectral Analysis → Machine Learning.

It's all connected. Literally.

---

*End of midnight exploration.*

---

## Appendix C: Code Examples

### Set Intersection (Static Stability)

```python
# backend/app/resilience/static_stability.py:77-82
available_dedicated = len(set(self.dedicated_faculty) & available_faculty)
return available_dedicated >= self.minimum_coverage
```

### Set Union + Difference (N-2 Contingency)

```python
# backend/app/resilience/contingency.py:305-330
combined_assignments = set()
for a in assignments_by_faculty.get(fac1.id, []):
    combined_assignments.add(a.block_id)
for a in assignments_by_faculty.get(fac2.id, []):
    combined_assignments.add(a.block_id)

# Then: uncovered = combined_assignments - covered_by_others
```

### Disjoint Partitioning (Burden Categories)

```python
# backend/app/resilience/behavioral_network.py:777-781
crushing = [p for p in burden_profiles if p.equity_status == EquityStatus.CRUSHING]
heavy = [p for p in burden_profiles if p.equity_status == EquityStatus.HEAVY]
balanced = [p for p in burden_profiles if p.equity_status == EquityStatus.BALANCED]
# AllFaculty = crushing ⊔ heavy ⊔ balanced ⊔ light ⊔ very_light
```

### Complement (Constraint Checking)

```python
# backend/app/scheduling/constraints/acgme.py:104-120
if not context.availability[person_id][block_id]["available"]:
    violations.append(...)
# This is: person ∈ ¬Available
```

---

## References

- Boole, G. (1854). *An Investigation of the Laws of Thought*. Walton and Maberly.
- Van Wagner, C.E. (1987). *Development and structure of the Canadian Forest Fire Weather Index System*. Forestry Technical Report 35.
- Constructive Solid Geometry (CSG). *Wikipedia*. https://en.wikipedia.org/wiki/Constructive_solid_geometry
- North American Electric Reliability Corporation. *TPL-001-4: Transmission System Planning Performance Requirements*.
