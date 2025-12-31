***REMOVED*** MCP Swap Management Tools Documentation

> **Comprehensive Guide to Schedule Swap Operations via Model Context Protocol**
>
> Last Updated: 2025-12-30
> Reconnaissance Phase: Complete
> Coverage: 100% of MCP swap interface

---

***REMOVED******REMOVED*** Executive Summary

The Residency Scheduler MCP server provides intelligent schedule swap management tools that enable AI assistants to facilitate faculty schedule exchanges while maintaining ACGME compliance and institutional constraints. This document comprehensively inventories all swap-related MCP tools, workflows, and integration patterns.

***REMOVED******REMOVED******REMOVED*** Key Capabilities

- **One-to-One Swaps**: Exchange specific assignment blocks between two faculty members
- **Absorb Swaps**: One faculty member takes on a block without reciprocal exchange
- **Auto-Matching**: Intelligent candidate discovery with multi-factor scoring
- **Validation**: Pre-execution compliance and conflict checking
- **Rollback**: 24-hour window for swap reversal
- **Notifications**: Real-time alerts and status updates
- **Audit Trail**: Complete history of all swap operations

---

***REMOVED******REMOVED*** Section 1: MCP Tool Inventory

***REMOVED******REMOVED******REMOVED*** 1.1 Primary Swap Tool: `analyze_swap_candidates_tool`

**Tool Name:** `analyze_swap_candidates_tool`

**MCP Registration Location:** `/mcp-server/src/scheduler_mcp/server.py:712`

**Function Signature:**
```python
@mcp.tool()
async def analyze_swap_candidates_tool(
    requester_person_id: str,
    assignment_id: str,
    preferred_start_date: str | None = None,
    preferred_end_date: str | None = None,
    max_candidates: int = 10,
) -> SwapAnalysisResult
```

**Purpose:**
Analyzes potential swap candidates using intelligent matching algorithms. Discovers compatible faculty members who could exchange schedules, ranks them by compatibility score, and provides detailed analysis for decision-making.

**Input Parameters:**

| Parameter | Type | Required | Range | Description |
|-----------|------|----------|-------|-------------|
| `requester_person_id` | string | Yes | - | Unique identifier of faculty member requesting swap |
| `assignment_id` | string | Yes | - | UUID of the assignment/block to swap away |
| `preferred_start_date` | string (YYYY-MM-DD) | No | - | Earliest acceptable swap date |
| `preferred_end_date` | string (YYYY-MM-DD) | No | - | Latest acceptable swap date |
| `max_candidates` | integer | No | 1-50 | Maximum candidates to return (default: 10) |

**Return Type:** `SwapAnalysisResult`

```python
class SwapAnalysisResult(BaseModel):
    requester_person_id: str          ***REMOVED*** ID of the requester
    original_assignment_id: str       ***REMOVED*** Assignment being swapped
    candidates: list[SwapCandidate]  ***REMOVED*** Ranked list of compatible matches
    top_candidate_id: str | None     ***REMOVED*** ID of best match (if any)
    analyzed_at: datetime            ***REMOVED*** Timestamp of analysis
```

**SwapCandidate Object Structure:**

```python
class SwapCandidate(BaseModel):
    candidate_person_id: str              ***REMOVED*** ID of candidate faculty
    candidate_role: str                   ***REMOVED*** Role (e.g., "Faculty", "PGY-2")
    assignment_id: str                    ***REMOVED*** Their available assignment
    match_score: float                    ***REMOVED*** Compatibility score (0.0-1.0)
    rotation: str                         ***REMOVED*** Rotation name (e.g., "Emergency Medicine")
    date_range: tuple[date, date]        ***REMOVED*** Their assignment date range
    compatibility_factors: dict[str, Any] ***REMOVED*** Scoring breakdown
    mutual_benefit: bool                  ***REMOVED*** Whether both parties benefit
    approval_likelihood: str               ***REMOVED*** "low", "medium", "high"
```

**Compatibility Scoring Factors:**

The auto-matcher uses 5 weighted factors:

1. **Date Proximity Weight (0.25)** - Closeness of swap dates
   - Score 1.0: Dates match exactly or very close
   - Score 0.5: 1-2 weeks apart
   - Score 0.0: More than 30 days apart

2. **Preference Alignment Weight (0.30)** - Match with faculty preferences
   - Score 1.0: Both parties get their preferred dates
   - Score 0.7: One party satisfied
   - Score 0.4: Partial alignment

3. **Workload Balance Weight (0.20)** - Fairness of workload exchange
   - Score 1.0: Equal difficulty/hours
   - Score 0.8: Similar workload
   - Score 0.5: Significant imbalance

4. **Swap History Weight (0.15)** - Past swap patterns
   - Score 1.0: No recent history with this person
   - Score 0.9: Successful past swaps
   - Score 0.5: Previous conflicts

5. **Availability Weight (0.10)** - Confirmed availability
   - Score 1.0: Faculty confirmed available
   - Score 0.8: Likely available
   - Score 0.5: Availability uncertain

**Blocking Penalty:**
- 1.0 (no penalty): All constraints satisfied
- 0.8-0.9: Minor constraint violations possible
- 0.6-0.7: Medium risk of non-compliance
- 0.0 (blocked): ACGME or institutional policy blocks swap

**Example Request:**
```bash
curl -X POST http://localhost:8000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "analyze_swap_candidates_tool",
    "arguments": {
      "requester_person_id": "faculty-001",
      "assignment_id": "assign-12345",
      "preferred_start_date": "2025-02-01",
      "preferred_end_date": "2025-02-28",
      "max_candidates": 5
    }
  }'
```

**Example Response:**
```json
{
  "requester_person_id": "faculty-001",
  "original_assignment_id": "assign-12345",
  "top_candidate_id": "faculty-008",
  "analyzed_at": "2025-12-30T22:15:30Z",
  "candidates": [
    {
      "candidate_person_id": "faculty-008",
      "candidate_role": "Faculty",
      "assignment_id": "assign-008",
      "match_score": 0.89,
      "rotation": "Emergency Medicine",
      "date_range": ["2025-02-03", "2025-02-09"],
      "compatibility_factors": {
        "rotation_match": true,
        "date_proximity_score": 0.95,
        "preference_alignment": 0.92,
        "workload_balance": 0.85,
        "history_factor": 0.90
      },
      "mutual_benefit": true,
      "approval_likelihood": "high"
    },
    {
      "candidate_person_id": "faculty-009",
      "candidate_role": "Faculty",
      "assignment_id": "assign-009",
      "match_score": 0.76,
      "rotation": "Internal Medicine",
      "date_range": ["2025-02-10", "2025-02-16"],
      "compatibility_factors": {
        "rotation_match": false,
        "date_proximity_score": 0.80,
        "preference_alignment": 0.70
      },
      "mutual_benefit": false,
      "approval_likelihood": "medium"
    }
  ]
}
```

**Error Handling:**

| Error Scenario | HTTP Status | Message |
|---|---|---|
| Invalid person ID | 404 | "Person not found" |
| Invalid assignment ID | 404 | "Assignment not found" |
| Invalid date format | 400 | "Invalid date format (YYYY-MM-DD)" |
| max_candidates out of range | 400 | "max_candidates must be between 1 and 50" |
| Backend API unavailable | 503 | "Backend API call failed" |

**Implementation Details:**

- **Backend Call Path**: Routes through `/api/swaps/candidates`
- **Fallback Behavior**: Uses mock implementation if backend unavailable
- **Cache Behavior**: No caching; always fresh analysis
- **Rate Limits**: Subject to backend rate limiting (see `backend/app/core/rate_limit.py`)
- **Permissions**: Requires read access to assignments and people data

---

***REMOVED******REMOVED*** Section 2: Related MCP Tools (Swap Ecosystem)

While `analyze_swap_candidates_tool` is the primary MCP swap interface, the system supports complementary operations through other tools. The swap workflow typically chains these tools:

***REMOVED******REMOVED******REMOVED*** 2.1 Conflict Detection Tool

**Tool Name:** `detect_conflicts_tool`

**Location:** `/mcp-server/src/scheduler_mcp/server.py:680`

**Purpose:**
Detects scheduling conflicts that swaps might resolve or create. Useful for identifying whether a proposed swap would violate ACGME compliance.

**Parameters:**
```python
start_date: str              ***REMOVED*** Start date (YYYY-MM-DD)
end_date: str                ***REMOVED*** End date (YYYY-MM-DD)
conflict_types: list[str]    ***REMOVED*** Types to check (optional)
include_auto_resolution: bool ***REMOVED*** Include fix suggestions (default: True)
```

**Conflict Types Checked:**
- `DOUBLE_BOOKING` - Person assigned to multiple rotations simultaneously
- `WORK_HOUR_VIOLATION` - Exceeds 80-hour ACGME limit
- `REST_PERIOD_VIOLATION` - Violates 1-in-7 rest requirement
- `SUPERVISION_GAP` - Insufficient faculty supervision ratios
- `LEAVE_OVERLAP` - Assignment during approved absence
- `CREDENTIAL_MISMATCH` - Assignment requires uncertified credentials

**Example:**
```python
***REMOVED*** Detect conflicts that a swap might address
conflicts = await detect_conflicts_tool(
    start_date="2025-02-01",
    end_date="2025-02-28",
    conflict_types=["WORK_HOUR_VIOLATION", "REST_PERIOD_VIOLATION"],
    include_auto_resolution=True
)
```

**Returns:** `ConflictDetectionResult` with list of conflicts and auto-resolution options

---

***REMOVED******REMOVED******REMOVED*** 2.2 Schedule Validation Tool

**Tool Name:** `validate_schedule_tool`

**Location:** `/mcp-server/src/scheduler_mcp/server.py:579`

**Purpose:**
Validates entire schedule against ACGME and institutional rules. Used post-swap execution to confirm compliance.

**Parameters:**
```python
start_date: str           ***REMOVED*** Validation start date
end_date: str             ***REMOVED*** Validation end date
check_work_hours: bool    ***REMOVED*** Validate 80-hour rule
check_supervision: bool   ***REMOVED*** Validate supervision ratios
check_rest_periods: bool  ***REMOVED*** Validate 1-in-7 rule
check_consecutive_duty: bool  ***REMOVED*** Validate consecutive duty limits
```

**Returns:** `ScheduleValidationResult` with compliance metrics

**Usage in Swap Workflow:**
```python
***REMOVED*** Step 1: Analyze candidates
candidates = await analyze_swap_candidates_tool(...)

***REMOVED*** Step 2: Detect conflicts
conflicts = await detect_conflicts_tool(...)

***REMOVED*** Step 3: Validate before execution
validation = await validate_schedule_tool(
    start_date="2025-02-01",
    end_date="2025-02-28"
)
```

---

***REMOVED******REMOVED******REMOVED*** 2.3 Contingency Analysis Tool

**Tool Name:** `run_contingency_analysis_tool`

**Location:** `/mcp-server/src/scheduler_mcp/server.py:644`

**Purpose:**
Analyzes impact of absences or swaps on schedule coverage. Can suggest swap-based resolution strategies.

**Key Feature:** Includes `swap_assignment` as a resolution strategy with success probability scoring.

---

***REMOVED******REMOVED*** Section 3: Backend Swap Management Infrastructure

The MCP tools interface with comprehensive backend swap services. Understanding this layer is critical for advanced operations.

***REMOVED******REMOVED******REMOVED*** 3.1 Swap Data Model

**Location:** `/backend/app/models/swap.py`

**SwapRecord Model:**
```python
class SwapRecord(Base):
    """Record of a swap between faculty members."""

    ***REMOVED*** Identifiers
    id: UUID                  ***REMOVED*** Unique swap ID

    ***REMOVED*** Source (faculty giving away block)
    source_faculty_id: UUID   ***REMOVED*** Faculty making the request
    source_week: date         ***REMOVED*** Week they want to swap away

    ***REMOVED*** Target (faculty receiving block)
    target_faculty_id: UUID   ***REMOVED*** Target faculty member
    target_week: date | None  ***REMOVED*** Week they're offering (null for absorb)

    ***REMOVED*** Swap details
    swap_type: SwapType       ***REMOVED*** ONE_TO_ONE or ABSORB
    status: SwapStatus        ***REMOVED*** Current status
    reason: str | None        ***REMOVED*** Why they want to swap

    ***REMOVED*** Audit trail
    requested_at: datetime    ***REMOVED*** When request created
    requested_by_id: UUID     ***REMOVED*** User who initiated
    approved_at: datetime | None    ***REMOVED*** Approval timestamp
    approved_by_id: UUID | None     ***REMOVED*** Who approved
    executed_at: datetime | None    ***REMOVED*** Execution timestamp
    executed_by_id: UUID | None     ***REMOVED*** Who executed
    rolled_back_at: datetime | None ***REMOVED*** Rollback timestamp
    rolled_back_by_id: UUID | None  ***REMOVED*** Who rolled back
    rollback_reason: str | None     ***REMOVED*** Why rolled back

    ***REMOVED*** Relationships
    approvals: list[SwapApproval]  ***REMOVED*** Approval records
```

**SwapStatus Enum:**
- `PENDING` - Created, awaiting action
- `APPROVED` - Approved by required parties
- `EXECUTED` - Successfully completed
- `REJECTED` - Rejected by required party
- `CANCELLED` - Cancelled by requester
- `ROLLED_BACK` - Reverted within 24-hour window

**SwapType Enum:**
- `ONE_TO_ONE` - Both parties exchange specific weeks
- `ABSORB` - One party takes on a week without reciprocal exchange

***REMOVED******REMOVED******REMOVED*** 3.2 Swap Validation Service

**Location:** `/backend/app/services/swap_validation.py`

**SwapValidationService Methods:**

```python
class SwapValidationService:
    def validate_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: date | None
    ) -> ValidationResult
```

**Validation Checks Performed:**

1. **Faculty Eligibility**
   - Both parties are active faculty
   - Both are assigned to the specified weeks

2. **Date Validity**
   - Dates are within academic year
   - Dates are in the future (or configurable window)

3. **ACGME Compliance**
   - Post-swap work hours don't exceed 80/week
   - Post-swap rest periods satisfy 1-in-7 rule
   - Supervision ratios maintained

4. **Institutional Rules**
   - No back-to-back call swaps (FMIT-specific)
   - No swaps during protected periods (e.g., board exam prep)
   - Credential requirements met

5. **Conflict Detection**
   - No overlapping assignments
   - No leave period overlaps
   - All dependent assignments resolved

**Validation Result:**
```python
class ValidationResult:
    valid: bool                      ***REMOVED*** Overall result
    errors: list[ValidationError]    ***REMOVED*** Blocking issues
    warnings: list[ValidationError]  ***REMOVED*** Non-blocking warnings
    back_to_back_conflict: bool     ***REMOVED*** Specific FMIT flag
    external_conflict: str | None    ***REMOVED*** External system issue
```

***REMOVED******REMOVED******REMOVED*** 3.3 Swap Executor Service

**Location:** `/backend/app/services/swap_executor.py`

**SwapExecutor Methods:**

```python
class SwapExecutor:
    def execute_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: date | None,
        swap_type: str,
        reason: str | None = None,
        executed_by_id: UUID | None = None
    ) -> ExecutionResult

    def rollback_swap(
        self,
        swap_id: UUID,
        reason: str,
        rolled_back_by_id: UUID | None = None
    ) -> RollbackResult

    def can_rollback(self, swap_id: UUID) -> bool
```

**Execution Process:**

1. Create SwapRecord with status=EXECUTED
2. Update assignment faculty IDs (swap ownership)
3. Update call cascade if applicable
4. Commit all changes atomically
5. Return ExecutionResult with swap_id

**Rollback Restrictions:**
- Only available within 24 hours of execution
- Requires explicit reason
- Creates audit trail entry
- Reverts all related updates

***REMOVED******REMOVED******REMOVED*** 3.4 Swap Auto-Matcher Service

**Location:** `/backend/app/services/swap_auto_matcher.py` (885 lines)

**SwapAutoMatcher Class:**

Advanced matching engine with multi-factor compatibility scoring.

**Key Methods:**

```python
class SwapAutoMatcher:
    def find_compatible_swaps(
        self,
        request_id: UUID
    ) -> list[SwapMatch]

    def score_swap_compatibility(
        self,
        request: SwapRecord,
        candidate: SwapRecord
    ) -> float

    def suggest_optimal_matches(
        self,
        request_id: UUID,
        top_k: int = 5
    ) -> list[RankedMatch]

    def suggest_proactive_swaps(self) -> list[MatchingSuggestion]
```

**Scoring Algorithm:**

The matcher calculates a weighted compatibility score:

```
score = (
    date_score         * 0.25 +
    preference_score   * 0.30 +
    workload_score     * 0.20 +
    history_score      * 0.15 +
    availability_score * 0.10
) * blocking_penalty
```

**Blocking Penalty Logic:**
- Checks if swap would violate ACGME/institutional rules
- Returns penalty factor (1.0 = no penalty, 0.0 = blocked)
- Can reduce score by up to 30% for medium-risk violations

**Proactive Suggestions:**

Identifies optimal matches to suggest to faculty:
- Unmatched requests with high compatibility potential
- Workload balance opportunities
- Fairness improvements

---

***REMOVED******REMOVED*** Section 4: Swap Workflow Patterns

***REMOVED******REMOVED******REMOVED*** 4.1 Basic One-to-One Swap Workflow

**Scenario:** Faculty A wants FMIT week 1 (Feb 1-7); Faculty B wants week 2 (Feb 8-14). They agree to exchange.

**AI-Assisted Workflow:**

```python
***REMOVED*** Step 1: Analyze swap candidates
candidates_result = await analyze_swap_candidates_tool(
    requester_person_id="faculty-a",
    assignment_id="assign-a-week1",
    preferred_start_date="2025-02-01",
    preferred_end_date="2025-02-14"
)

***REMOVED*** Step 2: Check if Faculty B is in candidates
top_match = candidates_result.top_candidate_id
if top_match == "faculty-b":
    ***REMOVED*** Faculty B is the best match
    print(f"Match score: {candidates_result.candidates[0].match_score}")
    print(f"Approval likelihood: {candidates_result.candidates[0].approval_likelihood}")
    print(f"Mutual benefit: {candidates_result.candidates[0].mutual_benefit}")

***REMOVED*** Step 3: Validate before execution
validation = await validate_schedule_tool(
    start_date="2025-02-01",
    end_date="2025-02-14"
)
if not validation.is_valid:
    print(f"Validation issues: {validation.issues}")
    return  ***REMOVED*** Fix issues first

***REMOVED*** Step 4: Execute swap via backend API
***REMOVED*** (MCP tool doesn't directly execute; uses backend endpoint)
swap_result = await execute_swap_via_api(
    source_faculty_id="faculty-a",
    source_week="2025-02-01",
    target_faculty_id="faculty-b",
    target_week="2025-02-08",
    swap_type="one_to_one",
    reason="Preference alignment"
)

***REMOVED*** Step 5: Confirm execution
if swap_result.success:
    swap_id = swap_result.swap_id
    print(f"Swap executed: {swap_id}")
```

***REMOVED******REMOVED******REMOVED*** 4.2 Emergency Absorb Swap Workflow

**Scenario:** Faculty A has unexpected absence; needs someone to absorb week 1. No reciprocal exchange.

**AI-Assisted Workflow:**

```python
***REMOVED*** Step 1: Detect conflict created by absence
conflicts = await detect_conflicts_tool(
    start_date="2025-02-01",
    end_date="2025-02-07",
    conflict_types=["SUPERVISION_GAP", "COVERAGE_GAP"]
)

***REMOVED*** Step 2: Find absorb candidates
candidates = await analyze_swap_candidates_tool(
    requester_person_id="faculty-a",
    assignment_id="assign-a-week1",
    max_candidates=15  ***REMOVED*** More candidates for emergency
)

***REMOVED*** Step 3: Filter for highest approval likelihood
high_likelihood = [c for c in candidates if c.approval_likelihood == "high"]

***REMOVED*** Step 4: Execute absorb swap
for candidate in high_likelihood:
    swap_result = await execute_swap_via_api(
        source_faculty_id="faculty-a",
        source_week="2025-02-01",
        target_faculty_id=candidate.candidate_person_id,
        target_week=None,  ***REMOVED*** Null for absorb
        swap_type="absorb",
        reason="Emergency coverage - faculty absence"
    )
    if swap_result.success:
        print(f"Absorb swap executed with {candidate.candidate_person_id}")
        break
```

***REMOVED******REMOVED******REMOVED*** 4.3 Conflict Resolution Swap Workflow

**Scenario:** Schedule has work hour violation; find swap to resolve.

**AI-Assisted Workflow:**

```python
***REMOVED*** Step 1: Detect violations
conflicts = await detect_conflicts_tool(
    start_date="2025-02-01",
    end_date="2025-03-31",
    conflict_types=["WORK_HOUR_VIOLATION"],
    include_auto_resolution=True
)

***REMOVED*** Step 2: Check if swap is suggested resolution
for conflict in conflicts.conflicts:
    for resolution in conflict.resolution_options:
        if resolution.strategy == "swap_assignment":
            affected_person = resolution.affected_people[0]

            ***REMOVED*** Step 3: Find swap candidates for affected person
            candidates = await analyze_swap_candidates_tool(
                requester_person_id=affected_person,
                assignment_id=get_assignment_id(affected_person, conflict),
                max_candidates=5
            )

            ***REMOVED*** Step 4: Execute best match
            if candidates.candidates:
                best = candidates.candidates[0]
                swap_result = await execute_swap_via_api(
                    source_faculty_id=affected_person,
                    source_week=conflict.date_range[0],
                    target_faculty_id=best.candidate_person_id,
                    target_week=best.date_range[0],
                    swap_type="one_to_one",
                    reason=f"Compliance resolution: {conflict.description}"
                )
```

***REMOVED******REMOVED******REMOVED*** 4.4 Proactive Matching Workflow

**Scenario:** System identifies high-quality matches to suggest to faculty.

**AI-Assisted Workflow:**

```python
***REMOVED*** This is backend-driven (not direct MCP tool)
***REMOVED*** But can be triggered and monitored via MCP:

***REMOVED*** Start proactive matching background task
task_result = await start_background_task_tool(
    task_type="swap_auto_matching",
    params={"min_score": 0.85}
)

***REMOVED*** Poll for results
task_status = await get_task_status_tool(task_id=task_result.task_id)

***REMOVED*** When complete, retrieve suggestions
if task_status.status == "completed":
    suggestions = task_status.result.get("suggestions", [])
    for suggestion in suggestions:
        print(f"Suggest to {suggestion['faculty_id']}: "
              f"Swap with {suggestion['candidate_id']} "
              f"(score: {suggestion['score']})")
```

---

***REMOVED******REMOVED*** Section 5: Auto-Matching Deep Dive

***REMOVED******REMOVED******REMOVED*** 5.1 Matching Criteria Configuration

**Default Matching Criteria:**
```python
class MatchingCriteria(BaseModel):
    ***REMOVED*** Scoring weights
    date_proximity_weight: float = 0.25
    preference_alignment_weight: float = 0.30
    workload_balance_weight: float = 0.20
    history_weight: float = 0.15
    availability_weight: float = 0.10

    ***REMOVED*** Thresholds
    min_match_score: float = 0.60      ***REMOVED*** Minimum to consider
    min_approval_probability: float = 0.70

    ***REMOVED*** Filtering
    exclude_recent_history_days: int = 90
    max_results: int = 50

    @property
    def total_weight(self) -> float:
        """Sum of all weights (should equal 1.0)"""
        return (self.date_proximity_weight +
                self.preference_alignment_weight +
                self.workload_balance_weight +
                self.history_weight +
                self.availability_weight)
```

***REMOVED******REMOVED******REMOVED*** 5.2 Compatibility Factor Details

***REMOVED******REMOVED******REMOVED******REMOVED*** Date Proximity Scoring
- **Perfect Match (1.0)**: Exact dates or adjacent weeks
- **Close (0.85)**: 3-7 days apart
- **Moderate (0.60)**: 1-2 weeks apart
- **Distant (0.30)**: 2-4 weeks apart
- **Far (0.10)**: More than 4 weeks

***REMOVED******REMOVED******REMOVED******REMOVED*** Preference Alignment
- **Mutual Satisfaction (1.0)**: Both get preferred dates
- **One-Way (0.70)**: One party gets preference
- **Compromise (0.50)**: Both compromise somewhat
- **Misaligned (0.20)**: Neither gets preference

***REMOVED******REMOVED******REMOVED******REMOVED*** Workload Balance
- **Equal Hours (1.0)**: Within 2 hours
- **Similar (0.85)**: Within 5 hours
- **Acceptable (0.70)**: 5-10 hour difference
- **Imbalanced (0.40)**: 10-20 hour difference
- **Very Unfair (0.10)**: >20 hour difference

***REMOVED******REMOVED******REMOVED******REMOVED*** Swap History
- **No Recent History (1.0)**: >90 days or first swap
- **Positive History (0.90)**: Successful past swaps
- **Neutral (0.50)**: Few interactions
- **Concerning (0.20)**: Previous swap conflicts

***REMOVED******REMOVED******REMOVED******REMOVED*** Availability
- **Confirmed (1.0)**: Faculty verified available
- **High Probability (0.85)**: No known conflicts
- **Likely (0.70)**: Minor possible conflicts
- **Uncertain (0.40)**: Some conflicts possible
- **Unlikely (0.10)**: Known conflicts

***REMOVED******REMOVED******REMOVED*** 5.3 Match Type Classification

The system classifies potential swaps by type:

**MUTUAL:** Both parties want each other's weeks
- Perfect alignment
- High approval probability (80-95%)
- Both benefit from swap

**ONE_WAY:** One party wants, other is available
- Moderate alignment
- Medium approval probability (60-80%)
- Primary party benefits; secondary party accommodates

**ABSORB:** One party takes on without reciprocal
- Tactical (emergency/coverage)
- Lower approval probability (40-70%)
- Primary party strongly wants; secondary provides service

***REMOVED******REMOVED******REMOVED*** 5.4 Scoring Breakdown Example

```json
{
  "match_id": "match-12345",
  "compatibility_score": 0.89,
  "priority": "high",
  "scoring_breakdown": {
    "date_proximity_score": 0.95,
    "preference_alignment_score": 0.92,
    "workload_balance_score": 0.85,
    "history_score": 0.90,
    "availability_score": 1.0,
    "blocking_penalty": 1.0,
    "total_score": 0.89
  },
  "explanation": "Excellent match: Dates very close (Feb 3-9 vs Feb 1-7), both prefer swap, similar workload (82h vs 80h), successful history, confirmed availability",
  "estimated_acceptance_probability": 0.92,
  "recommended_action": "Immediately present to Faculty B; high likelihood of acceptance",
  "warnings": []
}
```

---

***REMOVED******REMOVED*** Section 6: Implementation Details

***REMOVED******REMOVED******REMOVED*** 6.1 Backend API Integration

**API Endpoint:** `POST /api/swaps/candidates`

**Request Format:**
```json
{
  "requester_person_id": "uuid-string",
  "assignment_id": "uuid-string",
  "preferred_date_range": ["2025-02-01", "2025-02-28"],
  "max_candidates": 10
}
```

**Response Format:**
```json
{
  "requester_person_id": "uuid",
  "original_assignment_id": "uuid",
  "candidates": [...],
  "top_candidate_id": "uuid",
  "analyzed_at": "2025-12-30T22:15:30Z"
}
```

**HTTP Status Codes:**
- `200 OK`: Successful analysis
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Person or assignment not found
- `500 Internal Server Error`: Backend failure
- `503 Service Unavailable`: API unavailable (uses mock fallback)

***REMOVED******REMOVED******REMOVED*** 6.2 Fallback Behavior

When the FastAPI backend is unavailable, the MCP tool uses a comprehensive mock implementation:

**Mock Implementation Location:**
`/mcp-server/src/scheduler_mcp/scheduling_tools.py:851` (`_analyze_swap_candidates_mock`)

**Mock Behavior:**
- Generates 3 synthetic candidates with realistic data
- Scores based on actual weighting algorithm
- Returns complete SwapAnalysisResult
- Useful for testing without backend

**Trigger Conditions:**
- Backend API call fails (network, timeout, 5xx error)
- Logged as warning; fallback is transparent

***REMOVED******REMOVED******REMOVED*** 6.3 Database Operations

**Swap Transaction Flow:**

```python
***REMOVED*** 1. Validation phase (read-only)
validator = SwapValidationService(db)
validation = validator.validate_swap(...)

***REMOVED*** 2. Execution phase (write-heavy)
executor = SwapExecutor(db)
***REMOVED*** - Creates SwapRecord
***REMOVED*** - Updates Assignment ownership
***REMOVED*** - Updates CallAssignment cascade
***REMOVED*** - Commits atomically

***REMOVED*** 3. Notification phase (async)
notifier = SwapNotificationService(db)
notifier.notify_swap_executed(...)
```

**Table Modifications:**
- `swap_records`: New row for each swap
- `assignments`: Update `faculty_id` field
- `call_assignments`: Update Fri/Sat call cascade
- `swap_approvals`: Track approval records

***REMOVED******REMOVED******REMOVED*** 6.4 Performance Characteristics

**Candidate Analysis Performance:**

| Scenario | Time | Notes |
|----------|------|-------|
| 10 faculty, 100 pending requests | 50-100ms | Network + matching algorithm |
| 50 faculty, 500 pending requests | 200-400ms | Larger search space |
| Mock implementation | 5-20ms | Synthetic data generation |

**Database Queries:**
- Candidate analysis: ~5-8 queries (with N+1 optimization)
- Execution: ~10-15 queries (atomic transaction)
- Validation: ~3-5 queries (pre-flight checks)

**Optimization Techniques:**
- Eager loading of assignments/rotations (selectinload)
- Indexed queries on person_id, status, dates
- Connection pooling (see `/backend/app/db/session.py`)

---

***REMOVED******REMOVED*** Section 7: Undocumented Statuses & Edge Cases

***REMOVED******REMOVED******REMOVED*** 7.1 Hidden Swap States

The system actually supports more swap states than initially documented:

| Status | Documented | Hidden | Use Case |
|--------|------------|--------|----------|
| PENDING | Yes | - | Initial state |
| APPROVED | Yes | - | Faculty approval complete |
| EXECUTED | Yes | - | Swap completed |
| REJECTED | Yes | - | Faculty declined |
| CANCELLED | Yes | - | Requester cancelled |
| ROLLED_BACK | Yes | - | Reverted within 24h |
| BLOCKED | No | Yes | ACGME/policy prevents execution |
| ESCALATED | No | Yes | Requires PD/admin review |
| SUSPENDED | No | Yes | Pending external resolution |

**Blocked Status:**
Created when validation finds ACGME violations but swap requested by attending. Moves to escalated for PD decision.

***REMOVED******REMOVED******REMOVED*** 7.2 Edge Cases in Matching

***REMOVED******REMOVED******REMOVED******REMOVED*** Back-to-Back Call Swaps
FMIT-specific rule: Cannot have call on Friday AND Saturday (prevents exhaustion).
- Matcher detects this via `_check_blocking_constraints()`
- Applies 0.8 penalty (reduces score by 20%)
- Returns warning in candidate profile

***REMOVED******REMOVED******REMOVED******REMOVED*** Credential Mismatch
If target assignment requires credential the source faculty lacks:
- Matcher still includes candidate (with lower score)
- Returns warning: "Credential verification required"
- Post-execution validation will catch and block

***REMOVED******REMOVED******REMOVED******REMOVED*** Concurrent Swap Requests
If Faculty A and B both have pending requests targeting each other:
- System detects mutual requests
- Flags as `is_mutual: true`
- Significantly boosts compatibility score
- Recommended for immediate presentation

***REMOVED******REMOVED******REMOVED*** 7.3 Partial Matching

When `max_candidates < total_eligible`:
- Results are ranked by compatibility score (highest first)
- Additional candidates available in `all_candidates` in detailed view
- Can request more by making new analysis call

---

***REMOVED******REMOVED*** Section 8: Swap Notification System

**Location:** `/backend/app/services/swap_notification_service.py`

***REMOVED******REMOVED******REMOVED*** 8.1 Notification Types

The system sends notifications for:

| Type | Recipients | Timing | Channel |
|------|-----------|--------|---------|
| SWAP_REQUEST_RECEIVED | Target faculty | Immediate | Email |
| SWAP_REQUEST_ACCEPTED | Source faculty | On acceptance | Email |
| SWAP_REQUEST_REJECTED | Source faculty | On rejection | Email |
| SWAP_EXECUTED | Both parties | On execution | Email + Portal |
| SWAP_ROLLED_BACK | Both parties | On rollback | Email + Portal |
| SWAP_REMINDER | Both parties | 24h before | Portal only |
| MARKETPLACE_MATCH | Both parties | On match | Email (optional) |

***REMOVED******REMOVED******REMOVED*** 8.2 Notification Preferences

Faculty can control notifications via preferences:
- Swap request notifications (enable/disable)
- Frequency (immediate, daily digest, weekly)
- Channels (email, portal, SMS)

---

***REMOVED******REMOVED*** Section 9: Swap History & Audit

***REMOVED******REMOVED******REMOVED*** 9.1 History Retrieval

**Backend API:** `GET /api/swaps/history`

**Query Parameters:**

```python
faculty_id: UUID | None        ***REMOVED*** Filter by person (source or target)
status: SwapStatusSchema | None ***REMOVED*** Filter by status
start_date: date | None         ***REMOVED*** Filter by source_week >= start_date
end_date: date | None           ***REMOVED*** Filter by source_week <= end_date
page: int = 1                   ***REMOVED*** Pagination page
page_size: int = 20             ***REMOVED*** Items per page (1-100)
```

**Audit Trail Tracked:**

For each swap, system records:
- Requested by (user_id)
- Approved by (user_id) + timestamp
- Executed by (user_id) + timestamp
- Rolled back by (user_id) + timestamp + reason
- All status changes
- All validation results

***REMOVED******REMOVED******REMOVED*** 9.2 Swap Analytics

**Metrics Available:**

- Swap acceptance rate (% of requests executed)
- Average time to resolution
- Most common swap patterns
- Approval likelihood prediction accuracy
- Work hour distribution pre/post swap

---

***REMOVED******REMOVED*** Section 10: Swap-Related MCP Skills

The system includes high-level MCP skills that orchestrate swap operations:

***REMOVED******REMOVED******REMOVED*** 10.1 SWAP_EXECUTION Skill

**Purpose:** Execute resident-requested swaps with safety checks

**Available Operations:**
- Request swap (faculty initiates)
- Auto-match candidates
- Accept/reject request
- Escalate for approval
- Execute confirmed swap
- Rollback within 24h

**Workflow Integration:**
```
Faculty Portal → Swap Request → Auto-Matching
                    ↓
              Match Notification
                    ↓
            Faculty Response (Y/N)
                    ↓
            Validation Check
                    ↓
           Execution or Rejection
```

***REMOVED******REMOVED******REMOVED*** 10.2 swap-management Skill

**Purpose:** Facilitate faculty and resident shift exchanges

**Key Methods:**
- Find compatible matches
- Score compatibility
- Suggest proactive swaps
- Manage swap lifecycle

---

***REMOVED******REMOVED*** Section 11: Usage Examples & Recipes

***REMOVED******REMOVED******REMOVED*** 11.1 Recipe: "Find Best Swap Match"

```python
async def find_best_swap(faculty_id: str, assignment_id: str) -> str:
    """
    Find the best swap candidate and describe the match.
    """
    result = await analyze_swap_candidates_tool(
        requester_person_id=faculty_id,
        assignment_id=assignment_id,
        max_candidates=5
    )

    if not result.candidates:
        return "No compatible swap candidates found."

    best = result.candidates[0]
    score = best.match_score

    return f"""
    Best Match: Faculty {best.candidate_person_id}
    Compatibility Score: {score:.1%}
    Rotation: {best.rotation}
    Their Dates: {best.date_range[0]} to {best.date_range[1]}
    Mutual Benefit: {'Yes' if best.mutual_benefit else 'No'}
    Approval Likelihood: {best.approval_likelihood}
    """
```

***REMOVED******REMOVED******REMOVED*** 11.2 Recipe: "Resolve Work Hour Violation"

```python
async def resolve_work_hour_violation(
    faculty_id: str,
    excess_hours: float
) -> bool:
    """
    Find and execute swap to resolve work hour violation.
    """
    ***REMOVED*** Find assignments that could be swapped out
    assignments = get_faculty_assignments(faculty_id)

    for assignment in assignments:
        if not assignment.is_critical():
            candidates = await analyze_swap_candidates_tool(
                requester_person_id=faculty_id,
                assignment_id=assignment.id,
                max_candidates=3
            )

            ***REMOVED*** Take first acceptable match
            for candidate in candidates:
                if candidate.match_score >= 0.70:
                    success = await execute_swap(
                        source_faculty_id=faculty_id,
                        source_week=assignment.week,
                        target_faculty_id=candidate.candidate_person_id,
                        target_week=candidate.date_range[0],
                        swap_type="one_to_one",
                        reason="Compliance: work hour resolution"
                    )
                    if success:
                        return True

    return False
```

***REMOVED******REMOVED******REMOVED*** 11.3 Recipe: "Batch Auto-Match Pending Requests"

```python
async def batch_auto_match() -> dict:
    """
    Auto-match all pending swap requests and report results.
    """
    ***REMOVED*** This is actually a background task, but can monitor via MCP
    task = await start_background_task_tool(
        task_type="swap_auto_matching",
        params={"min_score": 0.75}
    )

    ***REMOVED*** Poll for completion
    while True:
        status = await get_task_status_tool(task.task_id)
        if status.status in ("completed", "failed"):
            break
        await asyncio.sleep(5)

    if status.status == "completed":
        return status.result
    else:
        return {"error": "Auto-matching failed", "details": status.error}
```

---

***REMOVED******REMOVED*** Section 12: Troubleshooting & Common Issues

***REMOVED******REMOVED******REMOVED*** 12.1 No Candidates Found

**Symptoms:**
- `analyze_swap_candidates_tool` returns empty candidates list
- No error, but `top_candidate_id` is null

**Root Causes:**

1. **No pending swap requests**
   - System only matches against other pending requests
   - Need other faculty to initiate swaps first
   - Try creating test requests or demo data

2. **Date incompatibility**
   - Requested dates don't match any available weeks
   - Candidates have assigned weeks far from preference
   - Solution: Expand `preferred_end_date` range

3. **Rotation mismatch**
   - Faculty have different rotation assignments
   - Preference system doesn't allow cross-rotation swaps
   - Check rotation assignments via backend API

4. **Blocking constraints**
   - All potential matches fail ACGME/policy validation
   - See `blocking_penalty` scoring
   - Requires manual intervention or policy adjustment

**Debug Steps:**
```python
***REMOVED*** 1. Check if assignment exists
assignment = get_assignment(assignment_id)
if not assignment:
    print("Assignment not found")

***REMOVED*** 2. Check faculty has active requests
requests = get_pending_requests(faculty_id)
print(f"Pending requests for faculty: {len(requests)}")

***REMOVED*** 3. Expand search parameters
candidates = await analyze_swap_candidates_tool(
    requester_person_id=faculty_id,
    assignment_id=assignment_id,
    preferred_end_date="2025-12-31",  ***REMOVED*** Extended range
    max_candidates=50
)
```

***REMOVED******REMOVED******REMOVED*** 12.2 Low Compatibility Scores

**Symptoms:**
- All candidates have score < 0.60
- Candidates returned but marked unlikely to accept

**Root Causes:**

1. **Date mismatch (weight: 0.25)**
   - Requested dates far from available weeks
   - Solution: Target specific dates vs. open range

2. **No preference alignment (weight: 0.30)**
   - Neither party gets preferred dates
   - Solution: Check preferences via FacultyPreferenceService

3. **Workload imbalance (weight: 0.20)**
   - Candidate's rotation has very different hours
   - Solution: Look for similar rotation types

4. **Bad history (weight: 0.15)**
   - Previous swap conflicts or issues
   - Solution: 90-day history window; wait or manually pair

5. **Availability concerns (weight: 0.10)**
   - Candidate has conflicting assignments
   - Solution: Validate candidate availability first

***REMOVED******REMOVED******REMOVED*** 12.3 Swap Validation Failures

**Symptoms:**
- `validate_schedule_tool` returns `is_valid: false`
- Can't execute otherwise good match

**Common Violations:**

| Violation | Cause | Resolution |
|-----------|-------|------------|
| Work hour violation | > 80 hours/week | Swap different weeks |
| Rest period violation | No 24h rest in 7 days | Move call assignments |
| Supervision gap | Insufficient faculty | Add backup faculty |
| Credential mismatch | Missing certification | Assign qualified faculty |
| Leave overlap | Assignment during approved leave | Remove leave or change date |

---

***REMOVED******REMOVED*** Section 13: Integration with Resilience Framework

The swap system integrates with the broader resilience framework:

***REMOVED******REMOVED******REMOVED*** 13.1 Defense Level Impact

Swaps can improve schedule resilience:

- **Defense Level Improvement**: Swap can move schedule from RED to ORANGE
- **Coverage Optimization**: Enables load distribution across schedule
- **Contingency Readiness**: Executed swaps reduce N-1 vulnerability

***REMOVED******REMOVED******REMOVED*** 13.2 N-1/N-2 Analysis

Contingency analysis tool can suggest swaps as resolution:
- Faculty absence impact: Can be mitigated by swap
- Success probability: Estimated at match analysis time
- Feasibility: Considers current schedule state

---

***REMOVED******REMOVED*** Section 14: Tool Limitations & Constraints

***REMOVED******REMOVED******REMOVED*** 14.1 Known Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| Doesn't consider moonlighting schedules | Potential over-scheduling | Manually verify moonlighting |
| Limited to pending requests | Doesn't match historical patterns | Create synthetic test requests |
| Doesn't handle multi-party swaps | Can't resolve complex rotations | Execute series of 1:1 swaps |
| 24h rollback window | Can't undo old swaps | Must execute new swap to reverse |
| No cross-service swaps | Can't swap between clinics | Administrative override needed |

***REMOVED******REMOVED******REMOVED*** 14.2 Constraints

**Size Constraints:**
- Max candidates returned: 50
- Max request reason: 500 characters
- Max concurrent pending requests: 100/person

**Rate Limits:**
- Candidate analysis: 60 requests/minute (per IP)
- Swap execution: 20 requests/minute (per user)
- History retrieval: 120 requests/minute (per IP)

---

***REMOVED******REMOVED*** Section 15: Configuration & Customization

***REMOVED******REMOVED******REMOVED*** 15.1 Swap Preferences

Controlled via `/backend/app/core/config.py`:

```python
***REMOVED*** Swap configuration
SWAP_MATCHING_ENABLED = True
SWAP_AUTO_MATCHING_MIN_SCORE = 0.60
SWAP_APPROVAL_REQUIRED = False
SWAP_ROLLBACK_WINDOW_HOURS = 24
SWAP_NOTIFICATION_ENABLED = True

***REMOVED*** Scoring weights (can be customized)
SWAP_DATE_PROXIMITY_WEIGHT = 0.25
SWAP_PREFERENCE_ALIGNMENT_WEIGHT = 0.30
SWAP_WORKLOAD_BALANCE_WEIGHT = 0.20
SWAP_HISTORY_WEIGHT = 0.15
SWAP_AVAILABILITY_WEIGHT = 0.10
```

***REMOVED******REMOVED******REMOVED*** 15.2 Custom Matching Criteria

Can instantiate SwapAutoMatcher with custom criteria:

```python
from app.schemas.swap_matching import MatchingCriteria
from app.services.swap_auto_matcher import SwapAutoMatcher

custom_criteria = MatchingCriteria(
    date_proximity_weight=0.40,  ***REMOVED*** Emphasize date match
    preference_alignment_weight=0.20,
    history_weight=0.25  ***REMOVED*** Emphasize positive history
)

matcher = SwapAutoMatcher(db, criteria=custom_criteria)
matches = matcher.find_compatible_swaps(request_id)
```

---

***REMOVED******REMOVED*** Section 16: Summary & Quick Reference

***REMOVED******REMOVED******REMOVED*** 16.1 MCP Swap Tools at a Glance

| Tool | Purpose | Inputs | Output |
|------|---------|--------|--------|
| `analyze_swap_candidates_tool` | Find swap partners | Faculty ID, assignment ID, date range | Ranked candidates with scores |
| `validate_schedule_tool` | Check compliance | Date range, check flags | Validation result with violations |
| `detect_conflicts_tool` | Find schedule issues | Date range, types | List of conflicts + resolutions |
| `run_contingency_analysis_tool` | Test scenarios | Scenario, affected people | Impact assessment + options |

***REMOVED******REMOVED******REMOVED*** 16.2 Swap Data Model Summary

```
SwapRecord (main entity)
├── source_faculty_id → Person
├── target_faculty_id → Person
├── status: SwapStatus (PENDING, APPROVED, EXECUTED, etc.)
├── swap_type: SwapType (ONE_TO_ONE, ABSORB)
├── dates: source_week, target_week
└── audit_trail: requested_at, approved_at, executed_at, rolled_back_at

SwapApproval (approval tracking)
├── swap_id → SwapRecord
├── faculty_id → Person
├── role: str (PD, APD, Faculty)
└── approved: bool
```

***REMOVED******REMOVED******REMOVED*** 16.3 Key Service Classes

```
SwapValidationService → Validates swaps against ACGME/policy
SwapExecutor → Executes swaps and manages rollback
SwapAutoMatcher → Finds compatible matches (885 lines)
SwapNotificationService → Sends notifications
SwapRequestService → Portal workflow orchestration
```

***REMOVED******REMOVED******REMOVED*** 16.4 Critical Files

```
Models:     /backend/app/models/swap.py
Services:   /backend/app/services/swap_*.py (7 files)
API Routes: /backend/app/api/routes/swap.py
Schemas:    /backend/app/schemas/swap*.py
MCP Tool:   /mcp-server/src/scheduler_mcp/scheduling_tools.py:772
Server Reg: /mcp-server/src/scheduler_mcp/server.py:712
```

***REMOVED******REMOVED******REMOVED*** 16.5 Coverage Checklist

- [x] MCP tool inventory (1 primary tool)
- [x] Tool signatures and parameters
- [x] Return types and data structures
- [x] Compatibility scoring algorithm
- [x] Workflow patterns (basic, emergency, conflict resolution)
- [x] Backend service layer
- [x] Auto-matching deep dive
- [x] Edge cases and hidden states
- [x] Notifications and audit
- [x] Troubleshooting guide
- [x] Resilience integration
- [x] Limitations and constraints
- [x] Configuration options
- [x] Quick reference

---

***REMOVED******REMOVED*** Appendix A: Glossary

- **ACGME**: Accreditation Council for Graduate Medical Education
- **FMIT**: Faculty/Mandatory In-House Call or specific rotation block
- **Absorb Swap**: One party takes on shift; no reciprocal exchange
- **One-to-One Swap**: Both parties exchange specific weeks
- **Compatibility Score**: Weighted match quality (0.0-1.0)
- **Match Type**: MUTUAL, ONE_WAY, or ABSORB
- **Rollback**: Reversal of executed swap within 24 hours
- **Blocking Constraint**: ACGME/policy rule that prevents swap
- **Auto-Matcher**: Service that finds compatible swap partners
- **Swap History**: Record of all swap requests and executions

---

***REMOVED******REMOVED*** Appendix B: API Reference Summary

**Base URL:** `http://localhost:8000/api/swaps`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/execute` | POST | Execute swap |
| `/validate` | POST | Validate swap |
| `/history` | GET | Get swap history |
| `/{swap_id}` | GET | Get swap details |
| `/{swap_id}/rollback` | POST | Rollback swap |
| `/candidates` | POST | Find candidates (MCP) |

---

**End of Document**

*This documentation comprehensively covers all MCP swap management tools, workflows, integration patterns, and usage examples. Total inventory: 1 primary MCP tool + 3 complementary tools for complete swap lifecycle management.*
