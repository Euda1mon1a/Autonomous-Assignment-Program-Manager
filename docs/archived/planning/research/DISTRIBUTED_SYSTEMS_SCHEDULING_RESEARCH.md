# Distributed Systems & Fault Tolerance Research for Scheduling

**Research Date:** 2025-12-20
**Purpose:** Investigate exotic distributed systems patterns for multi-facility scheduling resilience
**Status:** Research Complete

---

## Executive Summary

This report examines seven distributed systems concepts and their application to multi-facility medical residency scheduling. The residency scheduler already implements Circuit Breaker, Defense in Depth (5-level nuclear safety model), and Blast Radius Containment (zone isolation). This research focuses on extending these patterns for distributed, multi-site deployment with Byzantine fault tolerance and consensus mechanisms.

### Key Findings

1. **Current State**: Single-facility deployment with strong resilience primitives
2. **Gap Analysis**: Lacks multi-site coordination, consensus, and Byzantine fault protection
3. **Priority Recommendations**:
   - Implement Bulkhead Pattern for resource pool isolation
   - Add Backpressure mechanisms for load regulation
   - Introduce Consensus-based schedule synchronization for multi-site
   - Develop Chaos Engineering test suite
   - Design Byzantine fault detection for schedule tampering

---

## Table of Contents

1. [Byzantine Fault Tolerance](#1-byzantine-fault-tolerance)
2. [CAP Theorem](#2-cap-theorem)
3. [Consensus Algorithms](#3-consensus-algorithms)
4. [Circuit Breaker Pattern](#4-circuit-breaker-pattern)
5. [Bulkhead Pattern](#5-bulkhead-pattern)
6. [Backpressure](#6-backpressure)
7. [Chaos Engineering](#7-chaos-engineering)
8. [Implementation Roadmap](#implementation-roadmap)
9. [References](#references)

---

## 1. Byzantine Fault Tolerance

### Core Principle

**Byzantine Generals Problem**: In a distributed system, some nodes may fail in arbitrary ways (crash, return incorrect data, or behave maliciously). Byzantine Fault Tolerance (BFT) ensures the system reaches correct consensus despite up to f Byzantine (malicious) nodes in a system of 3f+1 total nodes.

**Key Insight**: Traditional fault tolerance assumes "fail-stop" behavior (nodes crash). BFT assumes "fail-arbitrary" (nodes can lie, tamper, or collude).

### Application to Multi-Site Scheduling

#### Scenario: Cross-Facility Schedule Coordination

**Problem**: Three hospitals (MTF Alpha, Bravo, Charlie) share residents and faculty. A malicious insider at MTF Bravo attempts to manipulate schedules to create favoritism or hide safety violations.

**Byzantine Threats**:
1. **Schedule Tampering**: Coordinator at one facility modifies assignments post-approval
2. **ACGME Violation Hiding**: Site reports false compliance metrics to avoid citations
3. **Collusion**: Two sites coordinate to overwork residents at third site
4. **Split-Brain**: Network partition causes sites to have conflicting "official" schedules

#### BFT Solution Architecture

```
Multi-Facility Schedule Consensus (Byzantine-Resistant)

┌─────────────────────────────────────────────────────────────┐
│                    Schedule Proposal                        │
│  MTF Alpha: "Assign Dr. Smith to ICU on 2025-12-25"       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  MTF Alpha    │   │  MTF Bravo    │   │  MTF Charlie  │
│  PROPOSES     │   │  VALIDATES    │   │  VALIDATES    │
│               │   │               │   │               │
│  Digital      │   │  Digital      │   │  Digital      │
│  Signature    │   │  Signature    │   │  Signature    │
└───────────────┘   └───────────────┘   └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Byzantine Quorum   │
                 │  (2 of 3 agree)     │
                 │                     │
                 │  ✓ Alpha: YES       │
                 │  ✓ Bravo: YES       │
                 │  ✗ Charlie: NO      │
                 │                     │
                 │  Consensus: ACCEPT  │
                 └─────────────────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Immutable Ledger   │
                 │  (append-only log)  │
                 │                     │
                 │  Block #4521        │
                 │  Hash: 0xABC...     │
                 │  Prev: 0x123...     │
                 │  Assignment: {...}  │
                 └─────────────────────┘
```

#### Implementation Strategy

**1. Cryptographic Commitment**

```python
# backend/app/resilience/byzantine/schedule_commitment.py

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

@dataclass
class ScheduleCommitment:
    """
    Cryptographic commitment to a schedule change.

    Byzantine-resistant through:
    - Digital signatures (ed25519)
    - Merkle tree of assignments
    - Chain of custody tracking
    """
    proposal_id: UUID
    facility_id: str  # MTF Alpha, Bravo, Charlie
    proposer_id: UUID  # Person proposing change
    assignment_data: dict[str, Any]  # The actual change
    timestamp: datetime

    # Cryptographic binding
    merkle_root: str  # Hash of all assignments in proposal
    previous_hash: str  # Hash of previous accepted proposal
    signature: str  # Ed25519 signature from proposer

    # Validation state
    validators: dict[str, str]  # facility_id -> signature
    status: str  # "proposed", "quorum", "accepted", "rejected"

    def compute_merkle_root(self) -> str:
        """Compute Merkle root of assignment tree."""
        # Serialize assignments in canonical order
        serialized = self._canonical_serialize(self.assignment_data)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def verify_signature(self, public_key: bytes) -> bool:
        """Verify proposer's signature."""
        # Use ed25519 signature verification
        message = f"{self.proposal_id}{self.merkle_root}{self.timestamp}".encode()
        # In production: use cryptography.hazmat.primitives.asymmetric.ed25519
        return True  # Placeholder

    def has_byzantine_quorum(self, total_facilities: int) -> bool:
        """
        Check if proposal has Byzantine quorum.

        BFT requires 2f+1 votes for f Byzantine nodes.
        For 3 facilities (f=1), need 2 votes.
        For 4 facilities (f=1), need 3 votes.
        For 7 facilities (f=2), need 5 votes.
        """
        f = (total_facilities - 1) // 3  # Max Byzantine nodes
        required_votes = 2 * f + 1
        return len(self.validators) >= required_votes


class ByzantineScheduleValidator:
    """
    Validates schedule changes using Byzantine fault tolerance.

    Protects against:
    - Single-point schedule manipulation
    - Conflicting assignments across facilities
    - Retroactive schedule tampering
    - ACGME metric falsification
    """

    def __init__(self, facility_id: str, total_facilities: int = 3):
        self.facility_id = facility_id
        self.total_facilities = total_facilities
        self.pending_proposals: dict[UUID, ScheduleCommitment] = {}
        self.accepted_chain: list[ScheduleCommitment] = []

    def propose_change(
        self,
        assignment_data: dict,
        proposer_id: UUID,
    ) -> ScheduleCommitment:
        """Propose a schedule change for Byzantine consensus."""
        proposal = ScheduleCommitment(
            proposal_id=uuid4(),
            facility_id=self.facility_id,
            proposer_id=proposer_id,
            assignment_data=assignment_data,
            timestamp=datetime.now(),
            merkle_root="",  # Computed below
            previous_hash=self._get_latest_hash(),
            signature="",  # Sign below
            validators={},
            status="proposed",
        )

        # Compute cryptographic binding
        proposal.merkle_root = proposal.compute_merkle_root()
        proposal.signature = self._sign_proposal(proposal)

        self.pending_proposals[proposal.proposal_id] = proposal
        return proposal

    def validate_proposal(
        self,
        proposal_id: UUID,
        validator_facility: str,
        validator_signature: str,
    ) -> bool:
        """Receive validation from another facility."""
        proposal = self.pending_proposals.get(proposal_id)
        if not proposal:
            return False

        # Add validator signature
        proposal.validators[validator_facility] = validator_signature

        # Check for Byzantine quorum
        if proposal.has_byzantine_quorum(self.total_facilities):
            proposal.status = "quorum"
            self._accept_proposal(proposal)
            return True

        return False

    def _accept_proposal(self, proposal: ScheduleCommitment):
        """Accept proposal into immutable chain."""
        proposal.status = "accepted"
        self.accepted_chain.append(proposal)
        del self.pending_proposals[proposal.proposal_id]

    def detect_byzantine_behavior(
        self,
        proposal: ScheduleCommitment,
    ) -> list[str]:
        """
        Detect signs of Byzantine (malicious) behavior.

        Returns list of detected anomalies.
        """
        anomalies = []

        # Check 1: Hash chain integrity
        if proposal.previous_hash != self._get_latest_hash():
            anomalies.append("CHAIN_BREAK: Proposal doesn't reference correct parent")

        # Check 2: Timestamp sanity
        if self.accepted_chain:
            last_timestamp = self.accepted_chain[-1].timestamp
            if proposal.timestamp < last_timestamp:
                anomalies.append("TIME_TRAVEL: Proposal timestamp is in the past")

        # Check 3: Double-assignment
        if self._has_double_assignment(proposal):
            anomalies.append("DOUBLE_ASSIGN: Person assigned to multiple locations")

        # Check 4: ACGME violation injection
        if self._violates_acgme(proposal):
            anomalies.append("ACGME_VIOLATION: Proposal creates compliance violation")

        # Check 5: Signature forgery
        if not proposal.verify_signature(self._get_public_key(proposal.facility_id)):
            anomalies.append("FORGED_SIGNATURE: Invalid cryptographic signature")

        return anomalies

    def _get_latest_hash(self) -> str:
        """Get hash of most recent accepted proposal."""
        if not self.accepted_chain:
            return "GENESIS"
        return self.accepted_chain[-1].merkle_root
```

**2. Practical Byzantine Detection**

```python
# backend/app/resilience/byzantine/anomaly_detection.py

from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ByzantineAnomaly:
    """Detected Byzantine behavior."""
    facility_id: str
    anomaly_type: str
    severity: str  # "warning", "suspicious", "malicious"
    detected_at: datetime
    evidence: dict
    confidence: float  # 0.0 to 1.0


class ByzantineAnomalyDetector:
    """
    Detects Byzantine behavior through pattern analysis.

    Unlike crash failures (easy to detect), Byzantine failures
    require statistical analysis and cross-validation.
    """

    def __init__(self):
        self.anomaly_history: list[ByzantineAnomaly] = []
        self.facility_trust_scores: dict[str, float] = {}

    def analyze_proposal_pattern(
        self,
        facility_id: str,
        proposals: list[ScheduleCommitment],
    ) -> list[ByzantineAnomaly]:
        """
        Analyze proposal patterns for Byzantine behavior.

        Red flags:
        - Consistently proposing ACGME violations
        - Always benefiting same individuals
        - Hiding overload from other facilities
        - Proposal timestamps that don't match network time
        """
        anomalies = []

        # Pattern 1: Favoritism detection
        beneficiary_count: dict[UUID, int] = {}
        for proposal in proposals:
            person_id = proposal.assignment_data.get("person_id")
            if person_id:
                beneficiary_count[person_id] = beneficiary_count.get(person_id, 0) + 1

        # Check for outliers (one person gets >3x average)
        if beneficiary_count:
            avg = sum(beneficiary_count.values()) / len(beneficiary_count)
            for person_id, count in beneficiary_count.items():
                if count > avg * 3:
                    anomalies.append(ByzantineAnomaly(
                        facility_id=facility_id,
                        anomaly_type="FAVORITISM",
                        severity="suspicious",
                        detected_at=datetime.now(),
                        evidence={
                            "person_id": str(person_id),
                            "assignment_count": count,
                            "average": avg,
                        },
                        confidence=0.7,
                    ))

        # Pattern 2: ACGME violation hiding
        violation_rate = self._calculate_violation_rate(proposals)
        if violation_rate > 0.3:  # >30% of proposals violate ACGME
            anomalies.append(ByzantineAnomaly(
                facility_id=facility_id,
                anomaly_type="ACGME_EVASION",
                severity="malicious",
                detected_at=datetime.now(),
                evidence={
                    "violation_rate": violation_rate,
                    "proposal_count": len(proposals),
                },
                confidence=0.9,
            ))

        # Pattern 3: Timestamp manipulation
        for i in range(1, len(proposals)):
            time_delta = (proposals[i].timestamp - proposals[i-1].timestamp).total_seconds()
            if time_delta < 0:
                anomalies.append(ByzantineAnomaly(
                    facility_id=facility_id,
                    anomaly_type="TIME_MANIPULATION",
                    severity="malicious",
                    detected_at=datetime.now(),
                    evidence={
                        "proposal_id": str(proposals[i].proposal_id),
                        "time_delta_seconds": time_delta,
                    },
                    confidence=1.0,
                ))

        return anomalies

    def calculate_trust_score(self, facility_id: str) -> float:
        """
        Calculate trust score for a facility (0.0 to 1.0).

        Lower scores indicate higher likelihood of Byzantine behavior.
        Used to weight votes in consensus.
        """
        recent_anomalies = [
            a for a in self.anomaly_history
            if a.facility_id == facility_id
            and a.detected_at > datetime.now() - timedelta(days=30)
        ]

        if not recent_anomalies:
            return 1.0  # Perfect trust

        # Deduct trust based on anomaly severity
        trust = 1.0
        for anomaly in recent_anomalies:
            if anomaly.severity == "warning":
                trust -= 0.05
            elif anomaly.severity == "suspicious":
                trust -= 0.15
            elif anomaly.severity == "malicious":
                trust -= 0.40

        return max(0.0, trust)
```

#### When to Use BFT

**Use BFT when**:
- Multiple facilities share scheduling authority
- Regulatory compliance requires tamper-proof audit trail
- Insider threats are a concern (disgruntled coordinators)
- Cross-facility resource sharing creates incentive for cheating

**Don't use BFT when**:
- Single facility with trusted staff
- Performance overhead (3x message passing) unacceptable
- Byzantine failures are not in threat model

#### Performance Tradeoffs

- **Latency**: 3x increase (need 2f+1 responses)
- **Bandwidth**: 3x increase (broadcast to all validators)
- **Storage**: Append-only ledger grows indefinitely
- **Complexity**: Significantly more complex than simple replication

**Mitigation**: Use BFT only for critical operations (final schedule approval, ACGME reporting), not real-time updates.

---

## 2. CAP Theorem

### Core Principle

**CAP Theorem (Brewer's Theorem)**: A distributed system can satisfy at most 2 of 3 properties:
- **C**onsistency: All nodes see the same data at the same time
- **A**vailability: Every request receives a response (success or failure)
- **P**artition tolerance: System continues despite network splits

**Key Insight**: Network partitions WILL happen, so you must choose between consistency and availability.

### Application to Multi-Site Scheduling

#### CAP Triangle for Scheduling

```
                    Consistency
                         △
                        / \
                       /   \
                      /  ?  \
                     /       \
                    /         \
                   /           \
                  /             \
      Availability △─────────────△ Partition Tolerance

      MUST CHOOSE 2 OF 3

Option 1 (CP): Consistent + Partition Tolerant
- Refuse to schedule if facilities can't reach consensus
- Use case: Final schedule approval (must be identical everywhere)

Option 2 (AP): Available + Partition Tolerant
- Allow facilities to schedule independently during partition
- Use case: Emergency coverage (can't wait for consensus)
```

#### Partition Scenarios

**Scenario 1: Network Split Between Facilities**

```
Before Partition:
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │◄─────►│ MTF Bravo   │◄─────►│ MTF Charlie │
│             │       │             │       │             │
│ Database    │       │ Database    │       │ Database    │
└─────────────┘       └─────────────┘       └─────────────┘
      All facilities synchronized

During Partition (Alpha isolated):
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │   ✗   │ MTF Bravo   │◄─────►│ MTF Charlie │
│             │       │             │       │             │
│ Database    │       │ Database    │       │ Database    │
└─────────────┘       └─────────────┘       └─────────────┘
      Alpha can't sync with others

CP Strategy (Consistency + Partition Tolerance):
- Alpha REFUSES new schedules: "Error: Cannot reach quorum"
- Bravo/Charlie continue with 2/3 consensus
- Result: Alpha is unavailable, but Bravo/Charlie stay consistent

AP Strategy (Availability + Partition Tolerance):
- All three facilities continue scheduling independently
- Alpha: "Warning: Disconnected mode, will sync later"
- Result: All available, but may have conflicts on reconnect
```

#### Implementation: Tunable CAP

```python
# backend/app/resilience/distributed/cap_policy.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CAPMode(str, Enum):
    """CAP theorem mode selection."""
    CP_CONSISTENCY = "cp"  # Favor consistency over availability
    AP_AVAILABILITY = "ap"  # Favor availability over consistency
    ADAPTIVE = "adaptive"  # Switch based on context


class PartitionState(str, Enum):
    """Network partition state."""
    CONNECTED = "connected"  # All facilities reachable
    MINORITY = "minority"  # This facility in minority partition
    MAJORITY = "majority"  # This facility in majority partition
    ISOLATED = "isolated"  # This facility completely isolated


@dataclass
class CAPPolicy:
    """
    CAP theorem policy for distributed scheduling.

    Different operations may require different CAP tradeoffs:
    - Critical operations (final approval): CP mode
    - Emergency operations (night coverage): AP mode
    - Routine operations (swap requests): Adaptive
    """
    operation_type: str  # "final_approval", "emergency", "routine"
    default_mode: CAPMode
    partition_state: PartitionState

    # Override rules
    allow_divergence: bool = False  # Can facilities diverge?
    require_quorum: bool = True  # Need majority to proceed?
    conflict_resolution: str = "last_write_wins"  # "lww", "manual", "abort"

    def can_proceed_during_partition(self) -> bool:
        """Determine if operation can proceed during network partition."""

        # CP mode: Require connectivity
        if self.default_mode == CAPMode.CP_CONSISTENCY:
            if self.partition_state == PartitionState.CONNECTED:
                return True
            elif self.partition_state == PartitionState.MAJORITY and self.require_quorum:
                return True  # Majority quorum can proceed
            else:
                return False  # No connectivity or in minority

        # AP mode: Always proceed
        elif self.default_mode == CAPMode.AP_AVAILABILITY:
            return True  # Availability favored, accept conflicts

        # Adaptive: Context-dependent
        elif self.default_mode == CAPMode.ADAPTIVE:
            # Emergency operations always proceed
            if self.operation_type == "emergency":
                return True
            # Critical operations require consensus
            elif self.operation_type == "final_approval":
                return self.partition_state in (PartitionState.CONNECTED, PartitionState.MAJORITY)
            # Routine operations proceed if allow_divergence
            else:
                return self.allow_divergence or self.partition_state == PartitionState.CONNECTED

        return False


class CAPAwareScheduler:
    """
    Scheduler that adapts to network partitions using CAP theorem.

    Key insight: Different scheduling operations have different
    consistency requirements. Emergency coverage must be available
    (AP), but final ACGME reporting must be consistent (CP).
    """

    def __init__(self, facility_id: str):
        self.facility_id = facility_id
        self.partition_state = PartitionState.CONNECTED
        self.divergent_changes: list[dict] = []  # Track changes made during partition

    def create_assignment(
        self,
        person_id: UUID,
        block_id: UUID,
        operation_type: str = "routine",
    ) -> tuple[bool, Optional[str]]:
        """
        Create schedule assignment with CAP-aware logic.

        Returns: (success, error_message)
        """
        # Determine CAP policy
        if operation_type == "final_approval":
            policy = CAPPolicy(
                operation_type=operation_type,
                default_mode=CAPMode.CP_CONSISTENCY,
                partition_state=self.partition_state,
                require_quorum=True,
            )
        elif operation_type == "emergency":
            policy = CAPPolicy(
                operation_type=operation_type,
                default_mode=CAPMode.AP_AVAILABILITY,
                partition_state=self.partition_state,
                allow_divergence=True,
            )
        else:
            policy = CAPPolicy(
                operation_type=operation_type,
                default_mode=CAPMode.ADAPTIVE,
                partition_state=self.partition_state,
                allow_divergence=False,
            )

        # Check if can proceed
        if not policy.can_proceed_during_partition():
            return False, (
                f"Cannot create assignment: Network partition detected. "
                f"This operation requires {policy.default_mode.value} consistency. "
                f"Partition state: {self.partition_state.value}"
            )

        # Proceed with assignment
        assignment_data = {
            "person_id": person_id,
            "block_id": block_id,
            "created_at": datetime.now(),
            "facility_id": self.facility_id,
        }

        # Track if created during partition
        if self.partition_state != PartitionState.CONNECTED:
            self.divergent_changes.append({
                "type": "assignment",
                "data": assignment_data,
                "policy": policy,
            })

        # In production: Write to local database
        # await db.execute(insert(Assignment).values(**assignment_data))

        return True, None

    def detect_partition(self, reachable_facilities: list[str], total_facilities: int):
        """Update partition state based on network connectivity."""
        if len(reachable_facilities) == total_facilities - 1:
            # Can reach all other facilities
            self.partition_state = PartitionState.CONNECTED
        elif len(reachable_facilities) >= total_facilities // 2:
            # Can reach majority
            self.partition_state = PartitionState.MAJORITY
        elif len(reachable_facilities) > 0:
            # Can reach some but not majority
            self.partition_state = PartitionState.MINORITY
        else:
            # Completely isolated
            self.partition_state = PartitionState.ISOLATED

    def reconcile_after_partition(self) -> dict:
        """
        Reconcile divergent changes after partition heals.

        Returns report of conflicts and resolutions.
        """
        conflicts = []
        resolved = []

        for change in self.divergent_changes:
            # Check for conflicts with other facilities
            conflict = self._detect_conflict(change)

            if conflict:
                conflicts.append({
                    "change": change,
                    "conflict": conflict,
                    "resolution": self._resolve_conflict(change, conflict),
                })
            else:
                resolved.append(change)

        self.divergent_changes.clear()

        return {
            "total_divergent_changes": len(self.divergent_changes),
            "conflicts_detected": len(conflicts),
            "auto_resolved": len(resolved),
            "conflicts": conflicts,
        }
```

#### Real-World CAP Decisions

| Operation | CAP Mode | Rationale |
|-----------|----------|-----------|
| Final schedule approval | CP | Must be identical across facilities for ACGME |
| Emergency night coverage | AP | Can't wait for consensus, must assign immediately |
| Swap request | Adaptive | Routine: CP, Emergency: AP |
| Leave request | CP | Must sync to prevent double-booking |
| Viewing schedule | AP | Read-only, eventual consistency OK |
| ACGME reporting | CP | Regulatory requirement for consistency |

#### Partition Healing

```python
# backend/app/resilience/distributed/partition_healing.py

class PartitionHealer:
    """
    Reconciles divergent state after network partition heals.

    Strategies:
    1. Last-Write-Wins (LWW): Keep change with latest timestamp
    2. Vector Clocks: Detect causality violations
    3. CRDTs: Commutative operations that auto-merge
    4. Manual: Flag conflicts for human review
    """

    def reconcile_assignments(
        self,
        local_changes: list[dict],
        remote_changes: list[dict],
    ) -> dict:
        """Reconcile schedule assignments from different facilities."""

        conflicts = []

        # Build conflict map: block_id -> list of assignments
        block_assignments: dict[UUID, list[dict]] = {}

        for change in local_changes + remote_changes:
            block_id = change["block_id"]
            if block_id not in block_assignments:
                block_assignments[block_id] = []
            block_assignments[block_id].append(change)

        # Detect conflicts (multiple assignments to same block)
        for block_id, assignments in block_assignments.items():
            if len(assignments) > 1:
                # Conflict: Multiple facilities assigned same block
                winner = self._resolve_conflict_lww(assignments)
                conflicts.append({
                    "block_id": block_id,
                    "conflicting_assignments": assignments,
                    "resolution": "last_write_wins",
                    "winner": winner,
                })

        return {
            "total_conflicts": len(conflicts),
            "conflicts": conflicts,
        }

    def _resolve_conflict_lww(self, assignments: list[dict]) -> dict:
        """Resolve conflict using Last-Write-Wins."""
        return max(assignments, key=lambda a: a["created_at"])
```

---

## 3. Consensus Algorithms (Paxos, Raft)

### Core Principle

**Consensus Problem**: Multiple nodes must agree on a single value despite failures. Used for leader election, distributed locking, and state machine replication.

**Paxos**: Academic consensus algorithm (notoriously difficult to implement)
**Raft**: Practical consensus algorithm designed for understandability

### Raft Algorithm Overview

```
Raft has 3 roles:
- Leader: Accepts client requests, replicates to followers
- Follower: Passive, accepts logs from leader
- Candidate: Follower seeking to become leader

Leader Election:
1. Follower times out waiting for heartbeat
2. Becomes Candidate, requests votes
3. If receives majority votes, becomes Leader
4. If split vote, retry with random timeout

Log Replication:
1. Client sends command to Leader
2. Leader appends to log, replicates to Followers
3. Once majority acknowledge, Leader commits
4. Committed entries are durable
```

### Application to Multi-Facility Scheduling

#### Scenario: Distributed Schedule Lock

**Problem**: Three facilities need to agree on who has the "schedule lock" for editing. Only one facility can edit at a time to prevent conflicts.

```
Raft-Based Schedule Lock Manager

Time 0: All facilities are followers
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │       │ MTF Bravo   │       │ MTF Charlie │
│ FOLLOWER    │       │ FOLLOWER    │       │ FOLLOWER    │
└─────────────┘       └─────────────┘       └─────────────┘

Time 1: Bravo wants lock, becomes Candidate
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │◄──────│ MTF Bravo   │──────►│ MTF Charlie │
│ FOLLOWER    │  Vote?│ CANDIDATE   │ Vote? │ FOLLOWER    │
└─────────────┘       └─────────────┘       └─────────────┘
      │                      │                      │
      └──────── YES ─────────┴──────── YES ─────────┘

Time 2: Bravo wins majority (2/3), becomes Leader
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │◄──────│ MTF Bravo   │──────►│ MTF Charlie │
│ FOLLOWER    │ ❤️    │ LEADER      │  ❤️   │ FOLLOWER    │
└─────────────┘       └─────────────┘       └─────────────┘
                      Has Schedule Lock

Time 3: Bravo edits schedule, replicates to followers
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │◄──────│ MTF Bravo   │──────►│ MTF Charlie │
│ Log: [...]  │  Sync │ Log: [...   │ Sync  │ Log: [...]  │
│             │◄──ACK─│     Entry]  │──ACK─►│             │
└─────────────┘       └─────────────┘       └─────────────┘

Time 4: Majority ACK, Bravo commits
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ MTF Alpha   │       │ MTF Bravo   │       │ MTF Charlie │
│ Committed✓  │       │ Committed✓  │       │ Committed✓  │
└─────────────┘       └─────────────┘       └─────────────┘
```

#### Implementation: Raft for Schedule Consensus

```python
# backend/app/resilience/distributed/raft_scheduler.py

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import asyncio
import random

class RaftRole(str, Enum):
    """Raft consensus roles."""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class LogEntry:
    """Entry in the Raft replicated log."""
    term: int  # Election term when entry was created
    index: int  # Position in log
    command: dict  # The actual schedule change
    committed: bool = False


@dataclass
class RaftState:
    """Raft consensus state for a facility."""
    # Persistent state
    current_term: int = 0
    voted_for: Optional[str] = None
    log: list[LogEntry] = field(default_factory=list)

    # Volatile state
    role: RaftRole = RaftRole.FOLLOWER
    commit_index: int = 0
    last_applied: int = 0

    # Leader state
    next_index: dict[str, int] = field(default_factory=dict)
    match_index: dict[str, int] = field(default_factory=dict)

    # Timing
    last_heartbeat: Optional[datetime] = None
    election_timeout: float = 3.0  # seconds


class RaftScheduleNode:
    """
    Raft consensus node for distributed schedule management.

    Uses Raft to ensure all facilities agree on schedule changes
    without conflicts or lost updates.
    """

    def __init__(
        self,
        facility_id: str,
        peer_facilities: list[str],
    ):
        self.facility_id = facility_id
        self.peers = peer_facilities
        self.state = RaftState()

        # Randomize election timeout to prevent split votes
        self.state.election_timeout = random.uniform(3.0, 6.0)

        self._running = False

    async def start(self):
        """Start Raft consensus protocol."""
        self._running = True
        asyncio.create_task(self._run_follower_loop())

    async def _run_follower_loop(self):
        """Follower mode: Wait for heartbeats, start election if timeout."""
        while self._running and self.state.role == RaftRole.FOLLOWER:
            await asyncio.sleep(0.1)

            # Check for election timeout
            if self.state.last_heartbeat:
                elapsed = (datetime.now() - self.state.last_heartbeat).total_seconds()
                if elapsed > self.state.election_timeout:
                    # Start election
                    await self._start_election()

    async def _start_election(self):
        """Transition to Candidate and request votes."""
        logger.info(f"{self.facility_id} starting election for term {self.state.current_term + 1}")

        # Become candidate
        self.state.role = RaftRole.CANDIDATE
        self.state.current_term += 1
        self.state.voted_for = self.facility_id

        # Vote for self
        votes_received = 1

        # Request votes from peers
        vote_requests = [
            self._request_vote(peer) for peer in self.peers
        ]

        # Wait for majority
        vote_results = await asyncio.gather(*vote_requests, return_exceptions=True)

        for result in vote_results:
            if isinstance(result, bool) and result:
                votes_received += 1

        # Check if won election
        quorum = (len(self.peers) + 1) // 2 + 1
        if votes_received >= quorum:
            await self._become_leader()
        else:
            # Lost election, revert to follower
            self.state.role = RaftRole.FOLLOWER
            logger.info(f"{self.facility_id} lost election (got {votes_received}/{quorum} votes)")

    async def _request_vote(self, peer: str) -> bool:
        """Request vote from a peer."""
        # In production: Send RPC to peer
        # For now: Simulate network call
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Simulate: 70% chance of yes vote
        return random.random() < 0.7

    async def _become_leader(self):
        """Transition to Leader role."""
        logger.info(f"{self.facility_id} became LEADER for term {self.state.current_term}")

        self.state.role = RaftRole.LEADER

        # Initialize leader state
        for peer in self.peers:
            self.state.next_index[peer] = len(self.state.log)
            self.state.match_index[peer] = 0

        # Start sending heartbeats
        asyncio.create_task(self._send_heartbeats())

    async def _send_heartbeats(self):
        """Send periodic heartbeats to maintain leadership."""
        heartbeat_interval = 1.0  # seconds

        while self._running and self.state.role == RaftRole.LEADER:
            # Send heartbeat to all peers
            for peer in self.peers:
                asyncio.create_task(self._send_append_entries(peer))

            await asyncio.sleep(heartbeat_interval)

    async def _send_append_entries(self, peer: str):
        """Send AppendEntries RPC (heartbeat or log replication)."""
        # In production: Send RPC with log entries
        # For now: Simulate
        pass

    async def propose_change(self, command: dict) -> bool:
        """
        Propose a schedule change (client request to leader).

        Args:
            command: Schedule change to propose

        Returns:
            True if change committed, False otherwise
        """
        if self.state.role != RaftRole.LEADER:
            logger.warning(f"{self.facility_id} is not leader, cannot propose change")
            return False

        # Append to log
        entry = LogEntry(
            term=self.state.current_term,
            index=len(self.state.log),
            command=command,
            committed=False,
        )
        self.state.log.append(entry)

        # Replicate to followers
        acks = 1  # Leader counts as ack

        replication_tasks = [
            self._replicate_to_peer(peer, entry) for peer in self.peers
        ]

        results = await asyncio.gather(*replication_tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, bool) and result:
                acks += 1

        # Check for majority
        quorum = (len(self.peers) + 1) // 2 + 1
        if acks >= quorum:
            # Commit entry
            entry.committed = True
            self.state.commit_index = entry.index
            logger.info(f"{self.facility_id} committed entry {entry.index}")
            return True
        else:
            logger.warning(f"{self.facility_id} failed to commit entry (got {acks}/{quorum} acks)")
            return False

    async def _replicate_to_peer(self, peer: str, entry: LogEntry) -> bool:
        """Replicate log entry to a peer."""
        # In production: Send AppendEntries RPC with entry
        await asyncio.sleep(random.uniform(0.05, 0.15))

        # Simulate: 90% success rate
        return random.random() < 0.9
```

#### When to Use Consensus

**Use Consensus (Raft/Paxos) when**:
- Need strong consistency across facilities
- Schedule changes must be durable and agreed upon
- Leader election needed (who can edit schedule?)
- Distributed locking required

**Don't use Consensus when**:
- Single facility deployment
- Can tolerate eventual consistency
- Low latency more important than strong consistency
- Read-heavy workload (use leaderless replication instead)

#### Performance Considerations

- **Latency**: 2 RTT (round-trip times) minimum per write
- **Throughput**: Limited by leader's capacity (single write path)
- **Availability**: Requires majority quorum (can tolerate f failures in 2f+1 nodes)

**Optimization**: Use Raft only for critical metadata (schedule locks, ACGME reports), not individual assignments.

---

## 4. Circuit Breaker Pattern

### Core Principle

**Circuit Breaker**: Automatically prevent cascading failures by "opening the circuit" when error rate exceeds threshold. Borrowed from electrical engineering.

**States**:
- **Closed**: Normal operation, requests flow through
- **Open**: Too many failures, reject all requests immediately
- **Half-Open**: Testing recovery, allow limited requests

### Existing Implementation

**Status**: ✅ **Already Implemented**

The system has two circuit breaker implementations:

1. **MCP Server Circuit Breaker** (`mcp-server/src/scheduler_mcp/error_handling.py`):
   - Tracks failure rates per service
   - Opens after 5 consecutive failures
   - Half-open after 60 second timeout
   - Tests recovery with limited concurrent calls

2. **MTF Compliance Circuit Breaker** (`backend/app/resilience/mtf_compliance.py`):
   - **Safety Stand-Down Protocol**
   - Opens on N-1 failure, coverage collapse, allostatic overload
   - Locks scheduling operations (returns HTTP 451)
   - Requires commander override to resume

### Enhancement Opportunities

#### Multi-Facility Circuit Coordination

**Problem**: Circuit breaker at one facility should signal others to prepare for increased load.

```python
# backend/app/resilience/distributed/circuit_breaker_mesh.py

from dataclasses import dataclass
from typing import Callable

@dataclass
class CircuitBreakerEvent:
    """Event broadcast when circuit changes state."""
    facility_id: str
    service_name: str
    state: str  # "open", "half_open", "closed"
    triggered_at: datetime
    reason: str


class DistributedCircuitBreakerMesh:
    """
    Coordinates circuit breakers across multiple facilities.

    When one facility's circuit opens, others are notified to:
    - Increase capacity buffers
    - Prepare backup resources
    - Route traffic elsewhere
    """

    def __init__(self, facility_id: str):
        self.facility_id = facility_id
        self.local_breakers: dict[str, CircuitBreaker] = {}
        self.remote_breaker_states: dict[str, dict[str, str]] = {}
        self.event_handlers: list[Callable] = []

    def on_circuit_open(self, service: str, reason: str):
        """Local circuit breaker opened - notify peers."""
        event = CircuitBreakerEvent(
            facility_id=self.facility_id,
            service_name=service,
            state="open",
            triggered_at=datetime.now(),
            reason=reason,
        )

        # Broadcast to peer facilities
        self._broadcast_event(event)

        # Trigger local handlers
        for handler in self.event_handlers:
            handler(event)

    def on_remote_circuit_event(self, event: CircuitBreakerEvent):
        """Received circuit event from remote facility."""
        logger.warning(
            f"Remote facility {event.facility_id} circuit {event.state}: "
            f"{event.service_name} - {event.reason}"
        )

        # Update remote state tracking
        if event.facility_id not in self.remote_breaker_states:
            self.remote_breaker_states[event.facility_id] = {}
        self.remote_breaker_states[event.facility_id][event.service_name] = event.state

        # Proactive response: If peer's circuit opens, prepare to absorb load
        if event.state == "open":
            self._prepare_for_increased_load(event)

    def _prepare_for_increased_load(self, event: CircuitBreakerEvent):
        """Prepare this facility for increased load from failed peer."""
        # Example responses:
        # 1. Increase capacity buffer
        # 2. Activate backup faculty pool
        # 3. Preemptively shed low-priority load
        # 4. Notify administrators

        logger.info(
            f"Preparing for potential load increase due to {event.facility_id} failure"
        )
```

---

## 5. Bulkhead Pattern

### Core Principle

**Bulkhead Pattern**: Isolate resources into pools to prevent total system failure. Named after ship bulkheads that compartmentalize flooding.

**Key Insight**: Don't let one failing subsystem exhaust all resources and take down the entire system.

### Application to Scheduling

#### Resource Pool Isolation

```
Traditional (No Bulkheads):
┌──────────────────────────────────────────────────────┐
│            Single Faculty Pool (20 faculty)          │
│                                                      │
│  ICU │ Clinic │ Procedures │ Call │ Education       │
│   ↓       ↓         ↓          ↓         ↓          │
│              All draw from same pool                 │
│                                                      │
│  Problem: Runaway ICU demand exhausts entire pool   │
└──────────────────────────────────────────────────────┘

With Bulkheads:
┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
│ ICU Pool   │  │Clinic Pool │  │Procedure   │  │ Call Pool  │
│ (6 faculty)│  │ (8 faculty)│  │Pool        │  │ (4 faculty)│
│            │  │            │  │(4 faculty) │  │            │
│  Max: 6    │  │  Max: 8    │  │  Max: 4    │  │  Max: 4    │
│  Guaranteed│  │  Guaranteed│  │  Shared    │  │ Protected  │
└────────────┘  └────────────┘  └────────────┘  └────────────┘
      ↑               ↑               ↑               ↑
      └───────────────┴───────────────┴───────────────┘
           2 faculty in "Flex Pool" (shared emergency)

Benefit: ICU surge cannot starve Clinic (has guaranteed 8)
```

#### Implementation

```python
# backend/app/resilience/bulkhead/resource_pools.py

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

@dataclass
class ResourceBulkhead:
    """
    Isolated resource pool (bulkhead).

    Prevents resource exhaustion in one area from affecting others.
    """
    name: str
    capacity: int  # Max resources allowed
    reserved_capacity: int  # Guaranteed minimum (protected)

    # Current state
    allocated: list[UUID] = field(default_factory=list)
    borrowed: list[UUID] = field(default_factory=list)

    # Limits
    max_borrow: int = 2  # Can borrow up to N from other pools
    can_lend: bool = True

    # Metrics
    allocation_count: int = 0
    rejection_count: int = 0

    def available_capacity(self) -> int:
        """Get available capacity (not yet allocated)."""
        return self.capacity - len(self.allocated)

    def can_allocate(self) -> bool:
        """Check if can allocate more resources."""
        return len(self.allocated) < self.capacity

    def can_lend_resources(self) -> bool:
        """Check if can lend to other pools."""
        if not self.can_lend:
            return False
        # Only lend if above reserved capacity
        return len(self.allocated) < self.reserved_capacity

    def allocate(self, resource_id: UUID) -> bool:
        """Allocate a resource from this pool."""
        if not self.can_allocate():
            self.rejection_count += 1
            return False

        self.allocated.append(resource_id)
        self.allocation_count += 1
        return True

    def release(self, resource_id: UUID):
        """Release a resource back to the pool."""
        if resource_id in self.allocated:
            self.allocated.remove(resource_id)


class BulkheadManager:
    """
    Manages isolated resource pools (bulkheads).

    Prevents cascading failures by limiting resource sharing.
    """

    def __init__(self):
        self.bulkheads: dict[str, ResourceBulkhead] = {}
        self.global_flex_pool: list[UUID] = []  # Shared emergency pool

    def create_bulkhead(
        self,
        name: str,
        capacity: int,
        reserved_capacity: int,
        max_borrow: int = 2,
    ) -> ResourceBulkhead:
        """Create a new resource bulkhead."""
        bulkhead = ResourceBulkhead(
            name=name,
            capacity=capacity,
            reserved_capacity=reserved_capacity,
            max_borrow=max_borrow,
        )

        self.bulkheads[name] = bulkhead
        logger.info(f"Created bulkhead: {name} (capacity: {capacity}, reserved: {reserved_capacity})")
        return bulkhead

    def create_default_bulkheads(self, total_faculty: int):
        """Create default bulkhead configuration."""
        # Allocate 90% to bulkheads, 10% to flex pool
        bulkhead_capacity = int(total_faculty * 0.9)
        flex_capacity = total_faculty - bulkhead_capacity

        # ICU: 30% of bulkhead capacity
        self.create_bulkhead(
            name="icu",
            capacity=int(bulkhead_capacity * 0.3),
            reserved_capacity=int(bulkhead_capacity * 0.25),
            max_borrow=2,
        )

        # Clinic: 40% of bulkhead capacity
        self.create_bulkhead(
            name="clinic",
            capacity=int(bulkhead_capacity * 0.4),
            reserved_capacity=int(bulkhead_capacity * 0.35),
            max_borrow=3,
        )

        # Procedures: 20% of bulkhead capacity
        self.create_bulkhead(
            name="procedures",
            capacity=int(bulkhead_capacity * 0.2),
            reserved_capacity=int(bulkhead_capacity * 0.15),
            max_borrow=2,
        )

        # Call: 10% of bulkhead capacity (protected)
        self.create_bulkhead(
            name="call",
            capacity=int(bulkhead_capacity * 0.1),
            reserved_capacity=int(bulkhead_capacity * 0.1),  # Fully reserved
            max_borrow=0,  # Cannot borrow (critical)
        )

        logger.info(f"Created {len(self.bulkheads)} bulkheads with {flex_capacity} flex pool faculty")

    def allocate_resource(
        self,
        bulkhead_name: str,
        resource_id: UUID,
    ) -> tuple[bool, Optional[str]]:
        """
        Allocate a resource from a bulkhead.

        Returns: (success, error_message)
        """
        bulkhead = self.bulkheads.get(bulkhead_name)
        if not bulkhead:
            return False, f"Unknown bulkhead: {bulkhead_name}"

        # Try direct allocation
        if bulkhead.allocate(resource_id):
            return True, None

        # Bulkhead full - try borrowing from flex pool
        if len(bulkhead.borrowed) < bulkhead.max_borrow and self.global_flex_pool:
            flex_resource = self.global_flex_pool.pop(0)
            bulkhead.borrowed.append(flex_resource)
            logger.info(f"Borrowed flex resource for bulkhead {bulkhead_name}")
            return True, None

        # Cannot allocate - bulkhead limit reached
        return False, (
            f"Bulkhead '{bulkhead_name}' at capacity ({bulkhead.capacity}). "
            f"Cannot borrow more (limit: {bulkhead.max_borrow}). "
            f"This prevents resource exhaustion in other areas."
        )

    def get_bulkhead_status(self) -> dict:
        """Get status of all bulkheads."""
        return {
            name: {
                "capacity": bulkhead.capacity,
                "reserved": bulkhead.reserved_capacity,
                "allocated": len(bulkhead.allocated),
                "borrowed": len(bulkhead.borrowed),
                "available": bulkhead.available_capacity(),
                "utilization": len(bulkhead.allocated) / bulkhead.capacity if bulkhead.capacity > 0 else 0,
                "rejections": bulkhead.rejection_count,
            }
            for name, bulkhead in self.bulkheads.items()
        }
```

#### Benefits of Bulkheads

1. **Fault Isolation**: ICU surge doesn't starve clinic
2. **Guaranteed Capacity**: Critical services have protected minimums
3. **Graceful Degradation**: Non-critical services shed first
4. **Predictable Behavior**: Each pool has known limits

---

## 6. Backpressure

### Core Principle

**Backpressure**: When downstream system is overwhelmed, propagate "slow down" signal upstream rather than crashing. Borrowed from fluid dynamics.

**Key Insight**: Better to reject requests early (fail fast) than accept them and fail slowly.

### Application to Scheduling

#### Scenario: Schedule Request Overload

```
Without Backpressure:
┌────────────┐       ┌────────────┐       ┌────────────┐
│ Swap       │──100──►│ Scheduler  │──100──►│ Database   │
│ Requests/s │ req/s │ Service    │ req/s │ (Max 20/s) │
└────────────┘       └────────────┘       └────────────┘
                           │                      │
                           │                      ▼
                           │               ❌ CRASH
                           └──────────► All 100 requests fail

With Backpressure:
┌────────────┐       ┌────────────┐       ┌────────────┐
│ Swap       │──20───►│ Scheduler  │──20───►│ Database   │
│ Requests/s │ req/s │ Service    │ req/s │ (Max 20/s) │
└────────────┘       └────────────┘       └────────────┘
      ▲                    │                      │
      │                    │                      ▼
      └─────429───────────┘               ✓ Healthy
       "Slow down!"                        (Accepting 20/s)

80 requests rejected with:
"HTTP 429 Too Many Requests
Retry-After: 5 seconds"
```

#### Implementation

```python
# backend/app/resilience/backpressure/flow_control.py

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class BackpressureMetrics:
    """Metrics for backpressure monitoring."""
    current_queue_size: int
    max_queue_size: int
    processing_rate: float  # requests/second
    rejection_count: int
    last_rejection: Optional[datetime]


class BackpressureController:
    """
    Implements backpressure for flow control.

    When system is overwhelmed, rejects new requests rather
    than accepting them and failing slowly.
    """

    def __init__(
        self,
        name: str,
        max_queue_size: int = 100,
        max_processing_rate: float = 10.0,  # requests/second
    ):
        self.name = name
        self.max_queue_size = max_queue_size
        self.max_processing_rate = max_processing_rate

        self.queue: deque = deque()
        self.rejection_count = 0
        self.last_rejection: Optional[datetime] = None

        # Rate limiting (token bucket)
        self.tokens = max_processing_rate
        self.last_refill = datetime.now()

    async def submit(self, request: dict) -> tuple[bool, Optional[str]]:
        """
        Submit request with backpressure.

        Returns: (accepted, error_message)
        """
        # Check queue capacity
        if len(self.queue) >= self.max_queue_size:
            self.rejection_count += 1
            self.last_rejection = datetime.now()

            return False, (
                f"HTTP 429 Too Many Requests: "
                f"Service '{self.name}' queue full ({len(self.queue)}/{self.max_queue_size}). "
                f"System is under load. Please retry in 5 seconds."
            )

        # Check rate limit
        self._refill_tokens()
        if self.tokens < 1.0:
            self.rejection_count += 1
            self.last_rejection = datetime.now()

            return False, (
                f"HTTP 429 Too Many Requests: "
                f"Service '{self.name}' processing rate limit reached "
                f"({self.max_processing_rate} req/s). "
                f"Please slow down and retry in 2 seconds."
            )

        # Accept request
        self.queue.append(request)
        self.tokens -= 1.0
        return True, None

    def _refill_tokens(self):
        """Refill token bucket based on elapsed time."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()

        # Add tokens based on rate
        tokens_to_add = elapsed * self.max_processing_rate
        self.tokens = min(self.max_processing_rate, self.tokens + tokens_to_add)

        self.last_refill = now

    async def process(self):
        """Process queued requests."""
        while self.queue:
            request = self.queue.popleft()
            # Process request
            await self._handle_request(request)

    def get_metrics(self) -> BackpressureMetrics:
        """Get current backpressure metrics."""
        return BackpressureMetrics(
            current_queue_size=len(self.queue),
            max_queue_size=self.max_queue_size,
            processing_rate=self.max_processing_rate,
            rejection_count=self.rejection_count,
            last_rejection=self.last_rejection,
        )


class AdaptiveBackpressure:
    """
    Adaptive backpressure that adjusts limits based on system health.

    When system is healthy: Accept more
    When system is stressed: Reject more
    """

    def __init__(self, name: str):
        self.name = name
        self.controller = BackpressureController(name)

        # Adaptive parameters
        self.target_utilization = 0.7  # Target 70% utilization
        self.current_utilization = 0.0

    async def adjust_limits(self, system_metrics: dict):
        """Adjust backpressure limits based on system health."""
        # Get current utilization from metrics
        cpu_usage = system_metrics.get("cpu_usage", 0.0)
        queue_depth = system_metrics.get("queue_depth", 0)
        error_rate = system_metrics.get("error_rate", 0.0)

        # Calculate utilization (0.0 to 1.0)
        self.current_utilization = max(
            cpu_usage,
            queue_depth / self.controller.max_queue_size if self.controller.max_queue_size > 0 else 0,
            error_rate,
        )

        # Adjust processing rate
        if self.current_utilization < self.target_utilization:
            # System healthy - increase capacity
            self.controller.max_processing_rate *= 1.1
            logger.info(f"{self.name}: Increased processing rate to {self.controller.max_processing_rate:.1f} req/s")
        elif self.current_utilization > self.target_utilization + 0.1:
            # System stressed - decrease capacity
            self.controller.max_processing_rate *= 0.9
            logger.warning(f"{self.name}: Decreased processing rate to {self.controller.max_processing_rate:.1f} req/s")
```

#### Backpressure Strategies

1. **Queue-Based**: Buffer requests up to limit, reject overflow
2. **Rate-Based**: Limit requests per second (token bucket)
3. **Adaptive**: Adjust limits based on system health
4. **Downstream Signals**: Propagate slow-down signals from database/services

---

## 7. Chaos Engineering

### Core Principle

**Chaos Engineering**: Intentionally inject failures in production to test resilience. Pioneered by Netflix.

**Key Insight**: "You don't know if your system is resilient until you break it in production."

### Application to Scheduling

#### Chaos Experiments for Scheduler

```python
# backend/app/resilience/chaos/experiments.py

from dataclasses import dataclass
from enum import Enum
import random
from typing import Callable, Optional

class ChaosExperimentType(str, Enum):
    """Types of chaos experiments."""
    FACULTY_LOSS = "faculty_loss"  # Random faculty unavailable
    DATABASE_LATENCY = "database_latency"  # Slow database
    NETWORK_PARTITION = "network_partition"  # Split facilities
    BYZANTINE_FAULT = "byzantine_fault"  # Malicious coordinator
    LOAD_SPIKE = "load_spike"  # Sudden demand surge
    CASCADING_FAILURE = "cascading_failure"  # Multi-component failure


@dataclass
class ChaosExperiment:
    """A chaos engineering experiment."""
    name: str
    experiment_type: ChaosExperimentType
    description: str

    # Blast radius (how much to affect)
    blast_radius: float = 0.1  # Affect 10% of system

    # Duration
    duration_seconds: int = 60

    # Safety
    rollback_on_alert: bool = True  # Auto-rollback if alerts fire
    max_error_rate: float = 0.05  # Rollback if >5% errors

    # Execution
    is_running: bool = False
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None

    # Results
    observations: list[str] = field(default_factory=list)
    weaknesses_found: list[str] = field(default_factory=list)


class ChaosEngineer:
    """
    Chaos engineering framework for scheduling resilience.

    Runs controlled experiments to find weaknesses before they
    cause real incidents.
    """

    def __init__(self, is_production: bool = False):
        self.is_production = is_production
        self.experiments: list[ChaosExperiment] = []
        self.safety_checks: list[Callable] = []

    def register_safety_check(self, check: Callable[[], bool]):
        """Register a safety check that must pass before/during experiments."""
        self.safety_checks.append(check)

    async def run_experiment(self, experiment: ChaosExperiment) -> dict:
        """
        Run a chaos experiment.

        Safety protocol:
        1. Check all safety conditions
        2. Start with small blast radius
        3. Monitor for alerts
        4. Rollback if unsafe
        5. Document findings
        """
        logger.warning(f"Starting chaos experiment: {experiment.name}")

        # Safety check
        if not self._is_safe_to_experiment():
            return {
                "success": False,
                "error": "Safety checks failed - aborting experiment",
            }

        experiment.is_running = True
        experiment.started_at = datetime.now()

        try:
            # Execute experiment based on type
            if experiment.experiment_type == ChaosExperimentType.FACULTY_LOSS:
                await self._inject_faculty_loss(experiment)
            elif experiment.experiment_type == ChaosExperimentType.DATABASE_LATENCY:
                await self._inject_database_latency(experiment)
            elif experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
                await self._inject_network_partition(experiment)
            elif experiment.experiment_type == ChaosExperimentType.LOAD_SPIKE:
                await self._inject_load_spike(experiment)

            # Monitor during experiment
            await self._monitor_experiment(experiment)

        finally:
            # Always cleanup
            await self._rollback_experiment(experiment)
            experiment.is_running = False
            experiment.stopped_at = datetime.now()

        return {
            "success": True,
            "observations": experiment.observations,
            "weaknesses": experiment.weaknesses_found,
        }

    def _is_safe_to_experiment(self) -> bool:
        """Check if it's safe to run chaos experiments."""
        # Don't run during on-call hours (nights/weekends)
        now = datetime.now()
        if now.hour < 9 or now.hour > 17:  # Outside business hours
            logger.warning("Chaos experiments only run during business hours")
            return False

        # Don't run if system already stressed
        for check in self.safety_checks:
            if not check():
                logger.warning("Safety check failed")
                return False

        return True

    async def _inject_faculty_loss(self, experiment: ChaosExperiment):
        """
        Chaos: Randomly mark faculty as unavailable.

        Tests: N-1/N-2 contingency, backup pool activation, load shedding
        """
        # Get all faculty
        total_faculty = 20  # Placeholder
        affected_count = int(total_faculty * experiment.blast_radius)

        logger.warning(f"Chaos: Marking {affected_count} faculty as unavailable")

        # In production: Actually mark faculty unavailable
        # For now: Simulate
        experiment.observations.append(
            f"Removed {affected_count} faculty ({experiment.blast_radius*100:.0f}%)"
        )

        # Check if N-1 still passes
        # In production: Run actual N-1 check
        n1_pass = random.random() > 0.3  # 70% chance of failure

        if not n1_pass:
            experiment.weaknesses_found.append(
                "WEAKNESS: N-1 contingency failed with faculty loss. "
                "System cannot tolerate losing any additional faculty."
            )

    async def _inject_database_latency(self, experiment: ChaosExperiment):
        """
        Chaos: Add artificial latency to database queries.

        Tests: Timeout handling, user experience degradation, backpressure
        """
        latency_ms = 500  # Add 500ms latency

        logger.warning(f"Chaos: Injecting {latency_ms}ms database latency")

        # In production: Use network proxy to inject latency
        # For now: Simulate
        await asyncio.sleep(latency_ms / 1000.0)

        experiment.observations.append(f"Database latency increased by {latency_ms}ms")

        # Check if timeouts occur
        # In production: Monitor actual timeout rate
        timeout_rate = random.random() * 0.1  # 0-10%

        if timeout_rate > 0.05:
            experiment.weaknesses_found.append(
                f"WEAKNESS: {timeout_rate*100:.1f}% timeout rate with database latency. "
                f"Need to increase timeout thresholds or add retries."
            )

    async def _inject_network_partition(self, experiment: ChaosExperiment):
        """
        Chaos: Partition facilities (simulate network split).

        Tests: CAP behavior, partition healing, consensus
        """
        logger.warning("Chaos: Simulating network partition between facilities")

        # In production: Use iptables to drop packets between facilities
        # For now: Simulate

        experiment.observations.append("Network partition created between MTF Alpha and Bravo")

        # Check CAP behavior
        # Does system continue? (AP) or refuse operations? (CP)

        experiment.weaknesses_found.append(
            "OBSERVATION: System chose availability over consistency during partition. "
            "This may lead to conflicting schedules that require reconciliation."
        )

    async def _inject_load_spike(self, experiment: ChaosExperiment):
        """
        Chaos: Generate sudden load spike.

        Tests: Backpressure, autoscaling, performance degradation
        """
        normal_load = 10  # requests/second
        spike_load = int(normal_load * (1 + experiment.blast_radius * 10))

        logger.warning(f"Chaos: Injecting load spike ({normal_load} -> {spike_load} req/s)")

        # Generate spike
        for _ in range(spike_load):
            # Simulate request
            await asyncio.sleep(0.01)

        experiment.observations.append(f"Load spike: {spike_load} req/s (normal: {normal_load})")

        # Check if backpressure activated
        # In production: Check actual backpressure metrics
        if spike_load > normal_load * 5:
            experiment.weaknesses_found.append(
                "WEAKNESS: No backpressure activated during 5x load spike. "
                "System accepted all requests and may crash under sustained load."
            )

    async def _monitor_experiment(self, experiment: ChaosExperiment):
        """Monitor system health during experiment."""
        duration = timedelta(seconds=experiment.duration_seconds)
        start = datetime.now()

        while datetime.now() - start < duration:
            # Check safety conditions
            if experiment.rollback_on_alert:
                # In production: Check actual alerts/error rate
                error_rate = random.random() * 0.1  # 0-10%

                if error_rate > experiment.max_error_rate:
                    logger.error(
                        f"Chaos experiment {experiment.name} exceeded error threshold "
                        f"({error_rate*100:.1f}% > {experiment.max_error_rate*100:.1f}%) - ROLLING BACK"
                    )
                    experiment.weaknesses_found.append(
                        f"CRITICAL: Experiment caused {error_rate*100:.1f}% error rate"
                    )
                    break

            await asyncio.sleep(5)  # Check every 5 seconds

    async def _rollback_experiment(self, experiment: ChaosExperiment):
        """Rollback chaos experiment (restore normal state)."""
        logger.info(f"Rolling back chaos experiment: {experiment.name}")

        # In production: Restore affected resources
        # - Mark faculty as available again
        # - Remove network partitions
        # - Remove latency injection
        # etc.


# Example chaos experiments
CHAOS_EXPERIMENTS = [
    ChaosExperiment(
        name="Single Faculty Loss",
        experiment_type=ChaosExperimentType.FACULTY_LOSS,
        description="Remove one random faculty to test N-1 contingency",
        blast_radius=0.05,  # 5% of faculty
        duration_seconds=300,  # 5 minutes
    ),
    ChaosExperiment(
        name="Database Slowdown",
        experiment_type=ChaosExperimentType.DATABASE_LATENCY,
        description="Add 500ms latency to test timeout handling",
        blast_radius=1.0,  # All queries
        duration_seconds=180,
    ),
    ChaosExperiment(
        name="Multi-Facility Partition",
        experiment_type=ChaosExperimentType.NETWORK_PARTITION,
        description="Partition facilities to test CAP behavior",
        blast_radius=0.5,  # 50% of facilities
        duration_seconds=600,
    ),
    ChaosExperiment(
        name="10x Load Spike",
        experiment_type=ChaosExperimentType.LOAD_SPIKE,
        description="Generate 10x normal load to test backpressure",
        blast_radius=1.0,  # 10x multiplier
        duration_seconds=120,
    ),
]
```

#### Chaos Engineering Schedule

```
Month 1: Faculty Loss Experiments
- Week 1: Remove 1 faculty (5%) - test N-1
- Week 2: Remove 2 faculty (10%) - test N-2
- Week 3: Remove critical faculty (specialty bottleneck)
- Week 4: Remove faculty during peak hours

Month 2: Infrastructure Experiments
- Week 1: Database latency (500ms)
- Week 2: Database unavailable (30 seconds)
- Week 3: Redis cache failure
- Week 4: API timeout (external service)

Month 3: Distributed Systems Experiments
- Week 1: Network partition (2 facilities)
- Week 2: Byzantine node (malicious coordinator)
- Week 3: Clock skew (time desync)
- Week 4: Split brain (conflicting leaders)

Month 4: Load Experiments
- Week 1: 2x load spike
- Week 2: 5x load spike
- Week 3: 10x load spike
- Week 4: Sustained overload (1 hour)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)

**Priority: HIGH**

1. **Bulkhead Pattern**
   - Implement resource pool isolation
   - Create ICU, Clinic, Procedures, Call bulkheads
   - Add flex pool for emergency borrowing
   - **Deliverable**: `backend/app/resilience/bulkhead/resource_pools.py`

2. **Backpressure**
   - Add queue-based backpressure controller
   - Implement adaptive rate limiting
   - Add HTTP 429 responses with Retry-After
   - **Deliverable**: `backend/app/resilience/backpressure/flow_control.py`

3. **Chaos Engineering Framework**
   - Create chaos experiment runner
   - Implement 4 basic experiments (faculty loss, latency, partition, load)
   - Add safety checks and auto-rollback
   - **Deliverable**: `backend/app/resilience/chaos/experiments.py`

### Phase 2: Multi-Site Preparation (Months 3-4)

**Priority: MEDIUM**

4. **CAP-Aware Scheduler**
   - Implement partition detection
   - Add CP/AP mode switching
   - Create reconciliation logic
   - **Deliverable**: `backend/app/resilience/distributed/cap_policy.py`

5. **Byzantine Fault Detection**
   - Add cryptographic commitments
   - Implement anomaly detection
   - Create trust scoring
   - **Deliverable**: `backend/app/resilience/byzantine/schedule_commitment.py`

6. **Distributed Circuit Breaker Mesh**
   - Coordinate circuit breakers across facilities
   - Add proactive load preparation
   - Broadcast circuit events
   - **Deliverable**: `backend/app/resilience/distributed/circuit_breaker_mesh.py`

### Phase 3: Multi-Site Deployment (Months 5-6)

**Priority: LOW** (Only if multi-facility deployment confirmed)

7. **Raft Consensus**
   - Implement Raft for schedule lock
   - Add leader election
   - Create log replication
   - **Deliverable**: `backend/app/resilience/distributed/raft_scheduler.py`

8. **Byzantine Consensus**
   - Add 2f+1 quorum voting
   - Implement digital signatures
   - Create immutable audit ledger
   - **Deliverable**: `backend/app/resilience/byzantine/schedule_validator.py`

9. **Partition Healing**
   - Implement conflict detection
   - Add last-write-wins reconciliation
   - Create manual review workflow
   - **Deliverable**: `backend/app/resilience/distributed/partition_healing.py`

### Testing Requirements

**Each Phase Must Include:**

1. **Unit Tests**: 80%+ coverage of new modules
2. **Integration Tests**: End-to-end scenarios
3. **Chaos Tests**: Automated chaos experiments
4. **Load Tests**: Performance under stress
5. **Documentation**: Architecture docs and runbooks

---

## References

### Academic Papers

1. Lamport, L. (1998). "The Part-Time Parliament" (Paxos)
2. Ongaro, D. & Ousterhout, J. (2014). "In Search of an Understandable Consensus Algorithm" (Raft)
3. Castro, M. & Liskov, B. (1999). "Practical Byzantine Fault Tolerance"
4. Brewer, E. (2000). "Towards Robust Distributed Systems" (CAP Theorem)
5. Vogels, W. (2009). "Eventually Consistent"

### Industry Resources

1. **Netflix**: Chaos Engineering (https://netflixtechblog.com/tagged/chaos-engineering)
2. **AWS**: Blast Radius Architecture (https://aws.amazon.com/builders-library/avoiding-overload-in-distributed-systems/)
3. **Google SRE**: Error Budgets and Resilience (https://sre.google/sre-book/table-of-contents/)
4. **Microsoft**: Circuit Breaker Pattern (https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
5. **Cloudflare**: Backpressure (https://blog.cloudflare.com/the-problem-with-event-loops/)

### Books

1. Kleppmann, M. (2017). *Designing Data-Intensive Applications*
2. Tanenbaum, A. & Van Steen, M. (2017). *Distributed Systems*
3. Rotem-Gal-Oz, A. (2012). *SOA Patterns*
4. Nygard, M. (2018). *Release It! 2nd Edition*

---

## Appendix A: Distributed Systems Decision Matrix

| Scenario | Recommended Pattern | Priority | Complexity |
|----------|---------------------|----------|------------|
| Single facility, need fault isolation | **Bulkhead** | HIGH | Low |
| API overload protection | **Backpressure** | HIGH | Low |
| Test resilience in production | **Chaos Engineering** | HIGH | Medium |
| Prevent cascade failures | **Circuit Breaker** (✓ Done) | HIGH | Low |
| Multi-facility scheduling | **CAP-Aware** | MEDIUM | High |
| Malicious coordinator | **Byzantine Detection** | LOW | High |
| Schedule synchronization | **Raft Consensus** | LOW | Very High |
| Network partitions | **Partition Healing** | MEDIUM | High |

---

## Appendix B: Performance Impact

| Pattern | Latency Increase | Throughput Impact | Storage Overhead |
|---------|------------------|-------------------|------------------|
| Circuit Breaker | <1ms | None (already implemented) | Minimal |
| Bulkhead | None | None (logical partitioning) | None |
| Backpressure | None (reject early) | Intentional (prevents overload) | Minimal |
| Chaos Engineering | Testing only | Testing only | Logs only |
| CAP (CP mode) | 100-200ms (consensus) | -30% (quorum required) | Log storage |
| CAP (AP mode) | None | None | Reconciliation storage |
| Raft Consensus | 200-400ms (2 RTT) | -50% (single leader) | Full log |
| Byzantine Consensus | 400-800ms (3x msgs) | -70% (3x validation) | Immutable ledger |

**Recommendation**: Implement high-priority, low-complexity patterns first (Bulkhead, Backpressure, Chaos). Defer consensus algorithms until multi-facility deployment is confirmed.

---

**End of Report**
