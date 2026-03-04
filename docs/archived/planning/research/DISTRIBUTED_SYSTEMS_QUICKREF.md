# Distributed Systems Quick Reference

**For:** Multi-Facility Residency Scheduling
**Date:** 2025-12-20

---

## TL;DR - What to Implement First

### ✅ Already Implemented
- Circuit Breaker Pattern (MCP server + MTF compliance)
- Defense in Depth (5-level nuclear safety model)
- Blast Radius Containment (zone isolation)

### 🔥 HIGH PRIORITY - Implement Next (Months 1-2)
1. **Bulkhead Pattern**: Isolate faculty pools (ICU, Clinic, Procedures can't starve each other)
2. **Backpressure**: Reject requests when overloaded (HTTP 429 with Retry-After)
3. **Chaos Engineering**: Test resilience by breaking things on purpose

### 🟡 MEDIUM PRIORITY - If Multi-Site Needed (Months 3-4)
4. **CAP-Aware Scheduling**: Choose consistency vs availability during network partitions
5. **Byzantine Detection**: Detect malicious schedule tampering
6. **Circuit Breaker Mesh**: Coordinate circuit breakers across facilities

### ⚪ LOW PRIORITY - Only for Distributed Deployment (Months 5-6)
7. **Raft Consensus**: Multi-facility schedule lock and leader election
8. **Byzantine Consensus**: 2f+1 quorum voting for tamper-proof schedules
9. **Partition Healing**: Reconcile conflicts after network split

---

## The 7 Patterns Explained (30 Second Version)

### 1. Byzantine Fault Tolerance
**Problem**: Malicious coordinator manipulates schedules
**Solution**: Require 2 of 3 facilities to agree before accepting changes
**When**: Multi-facility with insider threat concerns
**Cost**: 3x messages, immutable ledger storage

### 2. CAP Theorem
**Problem**: Network partition - choose consistency or availability?
**Solution**: CP mode (final approval) vs AP mode (emergency coverage)
**When**: Multi-facility deployment
**Cost**: 100-200ms latency (CP), conflict reconciliation (AP)

### 3. Consensus (Raft/Paxos)
**Problem**: Who has the "schedule lock"? Need to agree despite failures
**Solution**: Raft leader election + log replication
**When**: Distributed locking, state machine replication
**Cost**: 200-400ms latency, -50% throughput (single leader bottleneck)

### 4. Circuit Breaker ✅
**Problem**: Cascading failures when downstream service fails
**Solution**: Auto-reject requests after threshold failures
**When**: Always (already implemented)
**Cost**: <1ms latency overhead

### 5. Bulkhead Pattern 🔥
**Problem**: ICU surge exhausts all faculty, starves clinic
**Solution**: Isolate pools (ICU pool: 6, Clinic pool: 8, Flex pool: 2)
**When**: Always (critical for resource fairness)
**Cost**: None (logical partitioning)

### 6. Backpressure 🔥
**Problem**: Accept too many requests, system crashes
**Solution**: Return HTTP 429 early when queue full
**When**: Always (prevents overload)
**Cost**: None (intentional rejection)

### 7. Chaos Engineering 🔥
**Problem**: Don't know if system is resilient until production incident
**Solution**: Intentionally break things to find weaknesses
**When**: Monthly experiments during business hours
**Cost**: Testing time only

---

## Decision Tree

```
Start Here
│
├─ Single Facility?
│  ├─ YES → Implement Bulkhead + Backpressure + Chaos (High Priority)
│  └─ NO → Continue below
│
├─ Multiple Facilities?
│  ├─ YES → Continue below
│  └─ NO → Done (single facility patterns sufficient)
│
├─ Network Partitions Possible?
│  ├─ YES → Implement CAP-Aware Scheduling (Medium Priority)
│  └─ NO → Skip CAP logic
│
├─ Insider Threats Concern?
│  ├─ YES → Implement Byzantine Detection (Medium Priority)
│  └─ NO → Skip Byzantine logic
│
├─ Need Schedule Synchronization?
│  ├─ YES → Implement Raft Consensus (Low Priority)
│  └─ NO → Use eventual consistency
│
└─ Need Tamper-Proof Audit?
   ├─ YES → Implement Byzantine Consensus (Low Priority)
   └─ NO → Done
```

---

## Performance Cheat Sheet

| Pattern | Latency | Throughput | Storage |
|---------|---------|------------|---------|
| Circuit Breaker ✅ | +0ms | 0% | Minimal |
| Bulkhead 🔥 | +0ms | 0% | None |
| Backpressure 🔥 | +0ms | 0%* | Minimal |
| Chaos 🔥 | Testing only | Testing only | Logs |
| CAP (CP) | +100-200ms | -30% | Logs |
| CAP (AP) | +0ms | 0% | Conflicts |
| Raft | +200-400ms | -50% | Full log |
| Byzantine | +400-800ms | -70% | Ledger |

*Backpressure intentionally reduces throughput to prevent overload

---

## 5-Minute Implementation Examples

### Bulkhead Pattern

```python
# Create isolated resource pools
bulkhead_manager = BulkheadManager()
bulkhead_manager.create_bulkhead(
    name="icu",
    capacity=6,          # Max 6 faculty
    reserved_capacity=5, # Guaranteed 5 (protected)
    max_borrow=1,        # Can borrow 1 from flex pool
)

# Try to allocate
success, error = bulkhead_manager.allocate_resource("icu", faculty_id)
if not success:
    # ICU pool at capacity - prevents starving clinic
    print(error)  # "Bulkhead 'icu' at capacity (6)"
```

### Backpressure

```python
# Create backpressure controller
controller = BackpressureController(
    name="swap_requests",
    max_queue_size=100,
    max_processing_rate=10.0,  # 10 req/s
)

# Submit request
accepted, error = await controller.submit(swap_request)
if not accepted:
    # Return HTTP 429
    return JSONResponse(
        status_code=429,
        content={"error": error},
        headers={"Retry-After": "5"},
    )
```

### Chaos Experiment

```python
# Run chaos experiment
chaos = ChaosEngineer()
experiment = ChaosExperiment(
    name="Single Faculty Loss",
    experiment_type=ChaosExperimentType.FACULTY_LOSS,
    blast_radius=0.05,  # 5% of faculty
    duration_seconds=300,
)

result = await chaos.run_experiment(experiment)
print(result["weaknesses"])
# ["WEAKNESS: N-1 contingency failed with faculty loss"]
```

### CAP-Aware Scheduling

```python
# Detect network partition
scheduler.detect_partition(
    reachable_facilities=["MTF_Bravo"],  # Can't reach Charlie
    total_facilities=3,
)

# Try to create assignment
success, error = scheduler.create_assignment(
    person_id=person_id,
    block_id=block_id,
    operation_type="final_approval",  # Requires CP (consistency)
)

if not success:
    # Network partition prevents final approval
    print(error)
    # "Cannot create assignment: Network partition detected.
    #  This operation requires cp consistency.
    #  Partition state: minority"
```

---

## Files to Create (Implementation Checklist)

### Phase 1 (Months 1-2) - HIGH PRIORITY
- [ ] `/backend/app/resilience/bulkhead/resource_pools.py`
- [ ] `/backend/app/resilience/bulkhead/__init__.py`
- [ ] `/backend/app/resilience/backpressure/flow_control.py`
- [ ] `/backend/app/resilience/backpressure/__init__.py`
- [ ] `/backend/app/resilience/chaos/experiments.py`
- [ ] `/backend/app/resilience/chaos/__init__.py`
- [ ] `/backend/tests/resilience/test_bulkhead.py`
- [ ] `/backend/tests/resilience/test_backpressure.py`
- [ ] `/backend/tests/resilience/test_chaos.py`

### Phase 2 (Months 3-4) - MEDIUM PRIORITY
- [ ] `/backend/app/resilience/distributed/cap_policy.py`
- [ ] `/backend/app/resilience/distributed/circuit_breaker_mesh.py`
- [ ] `/backend/app/resilience/byzantine/schedule_commitment.py`
- [ ] `/backend/app/resilience/byzantine/anomaly_detection.py`
- [ ] `/backend/tests/resilience/test_cap_policy.py`
- [ ] `/backend/tests/resilience/test_byzantine.py`

### Phase 3 (Months 5-6) - LOW PRIORITY
- [ ] `/backend/app/resilience/distributed/raft_scheduler.py`
- [ ] `/backend/app/resilience/distributed/partition_healing.py`
- [ ] `/backend/app/resilience/byzantine/schedule_validator.py`
- [ ] `/backend/tests/resilience/test_raft.py`
- [ ] `/backend/tests/resilience/test_partition_healing.py`

---

## Common Mistakes to Avoid

### ❌ Don't
- Implement consensus algorithms for single facility (massive overkill)
- Use Byzantine consensus unless insider threats are real concern
- Run chaos experiments during nights/weekends
- Accept all requests during overload (crashes system)
- Share faculty pools without limits (one area starves others)

### ✅ Do
- Start with Bulkhead + Backpressure (high value, low complexity)
- Run chaos experiments during business hours with safety checks
- Reject requests early when overloaded (fail fast)
- Isolate resource pools with reserved minimums
- Implement CAP awareness only if multi-facility confirmed

---

## Real-World Examples

### Netflix
- **Chaos Engineering**: Chaos Monkey kills random servers
- **Circuit Breaker**: Hystrix library (now archived, use Resilience4j)
- **Bulkhead**: Isolated thread pools per service

### AWS
- **Blast Radius**: Availability zones isolate failures
- **Backpressure**: API Gateway throttling
- **CAP**: DynamoDB (AP), RDS (CP)

### Google
- **Consensus**: Chubby lock service (Paxos)
- **Byzantine**: Not used (trusted infrastructure)
- **Chaos**: DiRT (Disaster Recovery Testing)

---

## FAQ

**Q: Do we need Byzantine consensus?**
A: Probably not. Only if:
- Multiple facilities with untrusted coordinators
- Regulatory requirement for tamper-proof audit
- Insider threats are documented concern

**Q: Should we implement Raft?**
A: Only if you have confirmed multi-facility deployment. For single facility, use PostgreSQL transactions.

**Q: What's the ROI on Chaos Engineering?**
A: High. Netflix found 80% of production incidents were preventable with chaos testing.

**Q: Bulkhead vs Blast Radius - what's the difference?**
A: Bulkhead = resource pool isolation (faculty pools)
Blast Radius = failure containment zones (geographic/service zones)
Both are related but apply at different levels.

**Q: How do we test distributed systems locally?**
A: Use Docker Compose to run 3 instances, Toxiproxy for network failures, Chaos Mesh for experiment orchestration.

---

## Next Steps

1. **Read full research report**: `/docs/planning/research/DISTRIBUTED_SYSTEMS_SCHEDULING_RESEARCH.md`
2. **Start with Phase 1**: Implement Bulkhead, Backpressure, Chaos (Months 1-2)
3. **Run first chaos experiment**: Single faculty loss during business hours
4. **Measure baseline**: Latency, throughput, error rate before patterns
5. **Iterate**: Add patterns incrementally, measure impact

---

**Quick Links**
- Full Report: [DISTRIBUTED_SYSTEMS_SCHEDULING_RESEARCH.md](./DISTRIBUTED_SYSTEMS_SCHEDULING_RESEARCH.md)
- Existing Circuit Breaker: `/backend/app/resilience/mtf_compliance.py` (line 1296)
- Existing Defense in Depth: `/backend/app/resilience/defense_in_depth.py`
- Existing Blast Radius: `/backend/app/resilience/blast_radius.py`
