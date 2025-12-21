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

*End of midnight exploration.*

---

## Appendix: Code Examples

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
