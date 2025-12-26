# Agent Communication Protocols

> **Purpose:** Define how AI agents communicate, coordinate, and hand off work
> **Version:** 1.0.0
> **Last Updated:** 2025-12-26

---

## I. OVERVIEW

This document establishes the communication protocols for:
1. **Inter-Agent Communication**: How agents message each other
2. **Escalation Protocols**: When and how to escalate to humans
3. **Handoff Procedures**: Transferring work between agents
4. **Coordination Patterns**: Managing multi-agent workflows

**Guiding Principles:**
- **Structured Communication**: Use consistent message formats
- **Explicit Contracts**: Clear expectations for input/output
- **Graceful Failures**: Handle communication failures cleanly
- **Audit Trail**: Log all agent interactions

---

## II. MESSAGE FORMATS

### A. Standard Message Envelope

All inter-agent messages use this structure:

```json
{
  "message_id": "uuid-v4",
  "timestamp": "2025-12-26T14:30:00Z",
  "sender": {
    "agent_id": "agent-main-001",
    "agent_type": "orchestrator",
    "skill": null
  },
  "recipient": {
    "agent_id": "agent-worker-042",
    "agent_type": "specialist",
    "skill": "schedule-optimization"
  },
  "message_type": "task_request" | "task_response" | "status_update" | "error" | "escalation",
  "correlation_id": "uuid-v4",
  "parent_message_id": "uuid-v4 or null",
  "priority": "critical" | "high" | "normal" | "low",
  "payload": {
    // Message-specific data
  },
  "metadata": {
    "timeout_seconds": 600,
    "retry_count": 0,
    "max_retries": 3
  }
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | UUID | Yes | Unique identifier for this message |
| `timestamp` | ISO 8601 | Yes | When message was created |
| `sender` | Object | Yes | Sending agent information |
| `recipient` | Object | Yes | Receiving agent information |
| `message_type` | Enum | Yes | Type of message (see types below) |
| `correlation_id` | UUID | Yes | Links related messages in a workflow |
| `parent_message_id` | UUID | No | References prior message if continuing thread |
| `priority` | Enum | Yes | Message urgency |
| `payload` | Object | Yes | Message-specific data |
| `metadata` | Object | No | Optional control information |

---

### B. Message Types

#### 1. Task Request

**Purpose:** Request another agent to perform work.

```json
{
  "message_type": "task_request",
  "payload": {
    "task_description": "Generate schedule for Q2 2025",
    "skill_required": "schedule-optimization",
    "action": "generate",
    "parameters": {
      "start_date": "2025-04-01",
      "end_date": "2025-06-30",
      "residents": ["PGY1-01", "PGY2-03"],
      "constraints": ["ACGME", "institutional"]
    },
    "expected_output": {
      "type": "schedule_object",
      "format": "json",
      "schema_version": "2.0"
    },
    "success_criteria": [
      "ACGME compliance validated",
      "All blocks assigned",
      "No double-bookings"
    ]
  },
  "metadata": {
    "timeout_seconds": 600,
    "retry_count": 0,
    "max_retries": 3,
    "cancellable": true
  }
}
```

**Required Fields:**
- `task_description`: Human-readable description
- `skill_required`: Which skill should handle this (or null for general)
- `action`: Specific action to perform
- `parameters`: Input data for the task
- `expected_output`: What format the response should use
- `success_criteria`: Conditions that define success

---

#### 2. Task Response

**Purpose:** Return results from completed task.

```json
{
  "message_type": "task_response",
  "parent_message_id": "original-request-id",
  "payload": {
    "status": "success" | "partial_success" | "failure",
    "result": {
      "schedule": {
        "assignments": [...],
        "start_date": "2025-04-01",
        "end_date": "2025-06-30"
      },
      "metrics": {
        "total_blocks": 182,
        "assigned_blocks": 182,
        "coverage_percentage": 100.0
      }
    },
    "warnings": [
      {
        "code": "HIGH_UTILIZATION",
        "message": "Resident PGY2-03 at 82% utilization",
        "severity": "warning",
        "impact": "May violate resilience threshold"
      }
    ],
    "errors": [],
    "execution_metadata": {
      "start_time": "2025-12-26T14:30:00Z",
      "end_time": "2025-12-26T14:32:15Z",
      "duration_seconds": 135,
      "skill_used": "schedule-optimization",
      "version": "2.1.0"
    }
  }
}
```

**Status Values:**
- `success`: Task completed successfully, all criteria met
- `partial_success`: Task completed with warnings, some criteria not met
- `failure`: Task failed, no usable result

---

#### 3. Status Update

**Purpose:** Provide progress updates for long-running tasks.

```json
{
  "message_type": "status_update",
  "parent_message_id": "original-request-id",
  "payload": {
    "progress_percentage": 45,
    "current_phase": "constraint_solving",
    "phases": [
      {"name": "initialization", "status": "complete"},
      {"name": "constraint_solving", "status": "in_progress"},
      {"name": "validation", "status": "pending"},
      {"name": "finalization", "status": "pending"}
    ],
    "estimated_completion": "2025-12-26T14:35:00Z",
    "message": "Solving constraints for Week 3 of 13"
  }
}
```

**Use For:**
- Tasks taking > 30 seconds
- Tasks with multiple phases
- When user/parent agent needs visibility

**Update Frequency:**
- Every 30 seconds for tasks < 5 minutes
- Every 2 minutes for tasks > 5 minutes
- On phase transitions

---

#### 4. Error Message

**Purpose:** Report errors that occurred during task execution.

```json
{
  "message_type": "error",
  "parent_message_id": "original-request-id",
  "payload": {
    "error_code": "CONSTRAINT_CONFLICT",
    "error_message": "Cannot satisfy constraints: ACGME 80-hour rule violated",
    "error_details": {
      "constraint": "ACGME_80_HOUR_RULE",
      "affected_residents": ["PGY1-01"],
      "week": 3,
      "calculated_hours": 85.5,
      "limit": 80.0
    },
    "severity": "error" | "warning" | "info",
    "recoverable": true | false,
    "recovery_suggestions": [
      "Reduce assignments in Week 3",
      "Redistribute hours to other residents",
      "Request waiver (requires human approval)"
    ],
    "stack_trace": "..." // Only in development, sanitized in production
  }
}
```

**Error Severity Levels:**
- `critical`: System failure, immediate escalation required
- `error`: Task cannot complete, requires intervention
- `warning`: Task completed with issues, review recommended
- `info`: Notable event, no action required

---

#### 5. Escalation Message

**Purpose:** Request human intervention when agent cannot proceed autonomously.

```json
{
  "message_type": "escalation",
  "parent_message_id": "original-request-id",
  "payload": {
    "escalation_reason": "ACGME_VIOLATION_UNRESOLVABLE",
    "urgency": "high",
    "context": {
      "task": "Generate Q2 2025 schedule",
      "issue": "Cannot generate schedule without violating ACGME 80-hour rule",
      "attempts": 3,
      "last_error": "All permutations violate work hour limits"
    },
    "blocking": true,
    "options": [
      {
        "option_id": 1,
        "description": "Reduce resident assignments (will leave gaps)",
        "impact": "Some blocks will be uncovered",
        "recommendation": "Not recommended - patient safety risk"
      },
      {
        "option_id": 2,
        "description": "Request additional residents or faculty",
        "impact": "Requires institutional approval",
        "recommendation": "Recommended - maintains compliance and coverage"
      },
      {
        "option_id": 3,
        "description": "Request ACGME waiver",
        "impact": "Regulatory review required, low approval probability",
        "recommendation": "Last resort only"
      }
    ],
    "human_decision_required": true,
    "timeout": "2025-12-26T18:00:00Z"
  }
}
```

**Escalation Triggers:**
- Constitution rule violation
- Unresolvable constraint conflict
- Safety-critical decision needed
- Ambiguous requirements
- Multiple valid but conflicting solutions

---

## III. COMMUNICATION PATTERNS

### A. Request-Response (Synchronous)

**Pattern:** Sender waits for response before continuing.

```
Agent A                    Agent B
   |                          |
   |--- Task Request -------->|
   |                          |
   |                          | (processing)
   |                          |
   |<--- Task Response -------|
   |                          |
   (continues)                |
```

**Use For:**
- Short tasks (< 30 seconds)
- Dependent workflows (need result to proceed)
- Validation checks

**Implementation:**
```python
# Sender
response = await send_and_wait(
    recipient="agent-worker-042",
    message_type="task_request",
    payload={...},
    timeout_seconds=30
)

if response.payload.status == "success":
    continue_work(response.payload.result)
else:
    handle_error(response.payload.errors)
```

---

### B. Fire-and-Forget (Asynchronous)

**Pattern:** Sender continues immediately, doesn't wait for response.

```
Agent A                    Agent B
   |                          |
   |--- Task Request -------->|
   |                          |
   (continues)                | (processing)
   |                          |
   |                          |
```

**Use For:**
- Long-running tasks (> 30 seconds)
- Non-blocking operations
- Parallel task execution

**Implementation:**
```python
# Sender
task_id = await send_async(
    recipient="agent-worker-042",
    message_type="task_request",
    payload={...}
)

# Store task_id for later retrieval
register_pending_task(task_id)

# Continue other work
continue_work()

# Later, check for completion
if task_completed(task_id):
    result = get_task_result(task_id)
```

---

### C. Publish-Subscribe (Broadcast)

**Pattern:** One sender, multiple recipients.

```
Agent A (Publisher)
   |
   |--- Event: "schedule_generated" --->|
   |                                     |
   |                                     v
   |                              Agent B (Subscriber)
   |                              - Updates dashboard
   |
   |--- Event: "schedule_generated" --->|
   |                                     |
   |                                     v
   |                              Agent C (Subscriber)
   |                              - Sends notifications
   |
   |--- Event: "schedule_generated" --->|
                                         |
                                         v
                                  Agent D (Subscriber)
                                  - Logs audit event
```

**Use For:**
- Event notifications
- System-wide alerts
- Audit logging
- Dashboard updates

**Event Format:**
```json
{
  "event_type": "schedule_generated",
  "timestamp": "2025-12-26T14:32:15Z",
  "source_agent": "agent-scheduler-001",
  "payload": {
    "schedule_id": "uuid-v4",
    "period": "Q2-2025",
    "metrics": {...}
  }
}
```

---

### D. Pipeline (Sequential Chain)

**Pattern:** Output of one agent becomes input to next.

```
Agent A          Agent B          Agent C          Agent D
   |                |                |                |
   |--> Task ------>|                |                |
   |                |                |                |
   |                |--> Task ------>|                |
   |                |                |                |
   |                |                |--> Task ------>|
   |                |                |                |
   |<----------- Final Result --------------------- <|
```

**Use For:**
- Multi-stage workflows
- Data transformation pipelines
- Sequential validation

**Example - Schedule Generation Pipeline:**
```
1. safe-schedule-generation (backup database)
   ↓
2. schedule-optimization (generate schedule)
   ↓
3. acgme-compliance (validate compliance)
   ↓
4. schedule-verification (human checklist)
   ↓
5. Result returned to requester
```

**Implementation:**
```python
async def pipeline_execute(stages, initial_input):
    data = initial_input

    for stage in stages:
        response = await send_and_wait(
            recipient=stage.agent_id,
            message_type="task_request",
            payload={
                "action": stage.action,
                "input": data
            }
        )

        if response.payload.status != "success":
            # Rollback previous stages if needed
            await rollback_pipeline(stages[:stages.index(stage)])
            return error(response.payload.errors)

        # Output becomes next input
        data = response.payload.result

    return success(data)
```

---

### E. Scatter-Gather (Parallel Fan-Out)

**Pattern:** Distribute work to multiple agents, then collect results.

```
                    Agent A (Orchestrator)
                         |
                         |--- Task 1 ----> Agent B
                         |                    |
                         |--- Task 2 ----> Agent C
                         |                    |
                         |--- Task 3 ----> Agent D
                         |                    |
                         |                    |
    Results Collected <-----------------------|
```

**Use For:**
- Independent parallel tasks
- Comprehensive analysis (multiple perspectives)
- Performance optimization

**Example - Comprehensive Code Review:**
```
Orchestrator
├─> code-review (general quality)
├─> security-audit (security focus)
├─> test-writer (coverage analysis)
└─> lint-monorepo (style check)
    ↓
  Merge all results
```

**Implementation:**
```python
async def scatter_gather(tasks):
    # Send all tasks in parallel
    pending = [
        send_async(
            recipient=task.agent_id,
            message_type="task_request",
            payload=task.payload
        )
        for task in tasks
    ]

    # Wait for all to complete (or timeout)
    results = await gather_with_timeout(
        pending,
        timeout_seconds=300
    )

    # Synthesize results
    return synthesize_results(results)
```

---

## IV. HANDOFF PROCEDURES

### A. When to Hand Off

**Hand Off Work When:**

1. **Specialization Required**: Task needs domain expertise
2. **Context Limits**: Current agent reaching context window limit
3. **Permission Boundaries**: Task requires different access level
4. **Load Balancing**: Current agent overloaded
5. **Failure Recovery**: Current approach not working, try different agent

**Do NOT Hand Off When:**
- Current agent has sufficient capability
- Handoff overhead > task completion time
- Context critical to task success (would lose important information)

---

### B. Handoff Message Format

```json
{
  "message_type": "handoff_request",
  "payload": {
    "reason": "specialization_required",
    "context": {
      "original_task": "Debug schedule generation failure",
      "work_completed": [
        "Reviewed error logs",
        "Identified constraint conflict",
        "Attempted manual resolution (failed)"
      ],
      "current_state": {
        "schedule_id": "uuid-v4",
        "failed_constraints": ["ACGME_80_HOUR"],
        "error_logs": "..."
      },
      "remaining_work": [
        "Analyze constraint solver behavior",
        "Adjust constraint priorities",
        "Re-run generation with modified constraints"
      ]
    },
    "required_skill": "schedule-optimization",
    "priority": "high",
    "deadline": "2025-12-26T18:00:00Z"
  }
}
```

**Required Context Transfer:**
- What work has been completed
- Current state of the system
- What still needs to be done
- Any important findings or decisions made
- Relevant file paths, data, or resources

---

### C. Handoff Acknowledgment

```json
{
  "message_type": "handoff_acknowledgment",
  "parent_message_id": "handoff-request-id",
  "payload": {
    "accepted": true | false,
    "agent_id": "agent-specialist-007",
    "skill": "schedule-optimization",
    "context_received": true,
    "context_complete": true | false,
    "missing_context": ["error logs from last 24 hours"],
    "estimated_completion": "2025-12-26T15:30:00Z",
    "status": "starting" | "declined"
  }
}
```

**If Declined:**
```json
{
  "accepted": false,
  "decline_reason": "Missing required database connection",
  "suggestions": [
    "Ensure database container is running",
    "Provide connection credentials",
    "Or hand off to agent with database access"
  ]
}
```

---

### D. Handoff Best Practices

**DO:**
- Provide complete context (all relevant information)
- Explain reasoning for handoff
- Include work already completed (avoid duplication)
- Set clear expectations and deadlines
- Confirm handoff accepted before releasing task

**DON'T:**
- Hand off without explanation
- Lose important context in transfer
- Hand off repeatedly (agent ping-pong)
- Skip acknowledgment confirmation
- Hand off as excuse to avoid difficult work

---

## V. ESCALATION PROTOCOLS

### A. Escalation Levels

| Level | Recipient | Response Time | Examples |
|-------|-----------|---------------|----------|
| **L0 - Self-Resolution** | Same agent | Immediate | Retry with different parameters, use fallback |
| **L1 - Peer Agent** | Specialist agent | < 5 minutes | Hand off to domain expert |
| **L2 - Orchestrator** | Coordinating agent | < 15 minutes | Multi-agent coordination needed |
| **L3 - Human (Info)** | Developer/Admin | < 4 hours | Non-blocking issue, FYI |
| **L4 - Human (Action)** | Developer/Admin | < 1 hour | Blocking issue, decision needed |
| **L5 - Human (Urgent)** | On-call engineer | < 15 minutes | Production outage, data loss risk |

---

### B. Escalation Decision Tree

```
Issue Detected
    |
    ├─ Can I resolve with retry/fallback? ──YES──> L0: Self-Resolve
    |                                       |
    |                                       NO
    |                                       |
    ├─ Is specialist agent available? ──YES──> L1: Hand Off to Peer
    |                                   |
    |                                   NO
    |                                   |
    ├─ Do multiple agents need to coordinate? ──YES──> L2: Escalate to Orchestrator
    |                                              |
    |                                              NO
    |                                              |
    ├─ Is this blocking critical work? ──NO──> L3: Notify Human (Info)
    |                                   |
    |                                   YES
    |                                   |
    ├─ Is production affected? ──NO──> L4: Escalate to Human (Action)
    |                          |
    |                          YES
    |                          |
    └─────────────────────────────> L5: Escalate to Human (Urgent)
```

---

### C. Escalation Message Content

**L3 - Informational Notification:**
```json
{
  "message_type": "escalation",
  "payload": {
    "level": "L3_HUMAN_INFO",
    "urgency": "low",
    "blocking": false,
    "summary": "High utilization detected in Q2 schedule",
    "details": {
      "metric": "average_utilization",
      "value": 82,
      "threshold": 80,
      "affected": ["PGY2-03", "PGY3-01"]
    },
    "recommendation": "Review schedule for load balancing opportunities",
    "action_required": false,
    "can_proceed": true
  }
}
```

**L4 - Action Required:**
```json
{
  "message_type": "escalation",
  "payload": {
    "level": "L4_HUMAN_ACTION",
    "urgency": "high",
    "blocking": true,
    "summary": "Cannot generate compliant schedule with current constraints",
    "details": {
      "constraint": "ACGME_80_HOUR_RULE",
      "conflict": "Insufficient residents to cover all shifts",
      "gap": "Need 2 additional residents or reduce coverage"
    },
    "options": [
      {"id": 1, "description": "Hire additional residents", "impact": "Long-term solution"},
      {"id": 2, "description": "Reduce clinic hours", "impact": "Patient access affected"},
      {"id": 3, "description": "Increase faculty coverage", "impact": "Budget increase"}
    ],
    "recommendation": "Option 3: Increase faculty coverage for next quarter",
    "action_required": true,
    "deadline": "2025-12-27T12:00:00Z",
    "can_proceed": false
  }
}
```

**L5 - Urgent Production Issue:**
```json
{
  "message_type": "escalation",
  "payload": {
    "level": "L5_HUMAN_URGENT",
    "urgency": "critical",
    "blocking": true,
    "summary": "Database connection pool exhausted - production impact",
    "details": {
      "error": "Cannot acquire database connection",
      "impact": "All schedule operations failing",
      "affected_users": 47,
      "started_at": "2025-12-26T14:45:00Z"
    },
    "immediate_actions_taken": [
      "Enabled connection pool overflow",
      "Rejected new non-critical requests",
      "Activated fallback read-only mode"
    ],
    "needs_human_action": [
      "Approve scaling database connections to 200 (from 100)",
      "Investigate long-running queries",
      "Consider emergency restart of backend service"
    ],
    "action_required": true,
    "deadline": "IMMEDIATE",
    "can_proceed": false,
    "severity": "CRITICAL"
  }
}
```

---

### D. Escalation Response

**Human Response Format:**
```json
{
  "message_type": "escalation_response",
  "parent_message_id": "escalation-message-id",
  "payload": {
    "decision": "approved" | "denied" | "modified",
    "selected_option": 3,  // If options provided
    "instructions": "Scale database connections to 150 (not 200). Monitor for 30 minutes.",
    "authorization": {
      "authorized_by": "admin-user-id",
      "timestamp": "2025-12-26T14:50:00Z",
      "authority_level": "senior_engineer"
    },
    "follow_up_required": true,
    "follow_up_deadline": "2025-12-26T15:20:00Z"
  }
}
```

---

## VI. ERROR HANDLING IN COMMUNICATION

### A. Message Delivery Failures

**Scenarios:**
1. Recipient agent not available
2. Message timeout (no response)
3. Network partition
4. Message malformed

**Handling:**
```python
async def send_with_retry(message, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await send_message(message)
            return response
        except AgentUnavailableError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                # Escalate or use fallback
                return await fallback_handler(message)
        except TimeoutError:
            # Try alternative agent if available
            alternative = find_alternative_agent(message.recipient.skill)
            if alternative:
                message.recipient = alternative
                continue
            else:
                raise
```

---

### B. Partial Failures

**Scenario:** Some parallel tasks succeed, others fail.

**Handling:**
```python
async def handle_partial_failure(results):
    successes = [r for r in results if r.status == "success"]
    failures = [r for r in results if r.status == "failure"]

    if len(failures) == 0:
        return success(merge_results(successes))

    if len(successes) == 0:
        return failure(merge_errors(failures))

    # Partial success - decide based on criticality
    if all(f.critical for f in failures):
        # Critical failures - must abort
        return failure(merge_errors(failures))
    else:
        # Non-critical failures - can proceed with warnings
        return partial_success(
            result=merge_results(successes),
            warnings=merge_errors(failures)
        )
```

---

### C. Cascading Failures

**Prevention:**
1. **Circuit Breaker**: Stop sending to failing agent
2. **Bulkhead**: Isolate failures to prevent spread
3. **Timeout**: Don't wait indefinitely
4. **Fallback**: Have backup agents or degraded mode

**Circuit Breaker Implementation:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.opened_at = None
        self.timeout = timeout

    async def call(self, func):
        if self.state == "OPEN":
            if time.time() - self.opened_at > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = await func()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.opened_at = time.time()
            raise
```

---

## VII. COORDINATION PATTERNS

### A. Leader-Follower

**Pattern:** One agent coordinates, others execute.

**Use For:**
- Complex workflows requiring centralized decision-making
- Resource allocation
- Conflict resolution

**Example:**
```
Leader (Orchestrator)
    |
    ├─ Assigns Task 1 to Worker A
    ├─ Assigns Task 2 to Worker B
    ├─ Assigns Task 3 to Worker C
    |
    └─ Monitors progress, reallocates if needed
```

---

### B. Peer-to-Peer

**Pattern:** Agents communicate directly without central coordinator.

**Use For:**
- Simple task delegation
- Specialized skill requests
- Low-latency communication

**Example:**
```
Agent A <──> Agent B
   |            |
   └────────> Agent C
```

---

### C. Consensus

**Pattern:** Multiple agents must agree before proceeding.

**Use For:**
- Safety-critical decisions
- Conflict resolution
- Multi-perspective validation

**Example - ACGME Compliance Check:**
```
┌─ acgme-compliance (regulatory check)
├─ schedule-optimization (feasibility check)
├─ resilience-framework (safety check)
└─ schedule-verification (human checklist)
    ↓
  All must approve before schedule is finalized
```

**Implementation:**
```python
async def consensus_decision(agents, decision_payload):
    votes = await gather_all([
        send_and_wait(
            recipient=agent,
            message_type="consensus_request",
            payload=decision_payload
        )
        for agent in agents
    ])

    approvals = [v for v in votes if v.payload.vote == "approve"]
    rejections = [v for v in votes if v.payload.vote == "reject"]

    # Require unanimous approval for safety-critical decisions
    if len(rejections) > 0:
        return rejected(reasons=[v.payload.reason for v in rejections])
    else:
        return approved()
```

---

## VIII. BEST PRACTICES

### A. Communication Efficiency

**DO:**
- Use structured formats (JSON, not prose)
- Include correlation IDs for tracing
- Set appropriate timeouts
- Batch related messages when possible
- Use compression for large payloads

**DON'T:**
- Send unbounded payloads (set max size)
- Poll excessively (use status updates instead)
- Ignore message priority
- Create message loops (A→B→A→B...)

---

### B. Context Management

**DO:**
- Include sufficient context for agent to work independently
- Reference shared resources (files, databases) rather than copying large data
- Version message schemas
- Sanitize sensitive data before logging

**DON'T:**
- Send entire codebase in message
- Include secrets in messages
- Assume recipient has prior context
- Send PII/PHI in messages (use references)

---

### C. Error Reporting

**DO:**
- Use structured error codes
- Include recovery suggestions
- Log errors with correlation IDs
- Escalate when unable to recover

**DON'T:**
- Leak sensitive data in error messages
- Fail silently
- Retry indefinitely
- Suppress errors

---

## IX. MONITORING & OBSERVABILITY

### A. Communication Metrics

**Track:**
- Message delivery rate
- Average response time by message type
- Error rate by agent pair
- Escalation frequency
- Timeout rate

**Alerts:**
- Delivery rate < 95%
- Response time > 2x normal
- Error rate > 5%
- Escalation spike (> 3x baseline)

---

### B. Distributed Tracing

**Use Correlation IDs:**
```
User Request
  └─ correlation_id: abc123
      |
      ├─ Agent A (message_id: msg-001, correlation_id: abc123)
      |   |
      |   └─ Agent B (message_id: msg-002, correlation_id: abc123, parent: msg-001)
      |       |
      |       └─ Agent C (message_id: msg-003, correlation_id: abc123, parent: msg-002)
      |
      └─ Final Response (correlation_id: abc123)
```

**Tracing Query:**
```sql
SELECT * FROM agent_messages
WHERE correlation_id = 'abc123'
ORDER BY timestamp ASC;
```

---

### C. Audit Trail

**Log Every Communication:**
```json
{
  "timestamp": "2025-12-26T14:30:00Z",
  "message_id": "uuid-v4",
  "correlation_id": "uuid-v4",
  "sender_agent": "agent-main-001",
  "recipient_agent": "agent-worker-042",
  "message_type": "task_request",
  "payload_summary": "Generate Q2 2025 schedule",
  "status": "sent" | "delivered" | "failed",
  "response_time_ms": 135000
}
```

**Retention:**
- INFO level: 30 days
- WARNING level: 90 days
- ERROR level: 1 year
- CRITICAL level: Indefinite

---

## X. SECURITY CONSIDERATIONS

### A. Authentication

**Agent Identity:**
- Every agent has unique ID
- Messages signed with agent credentials
- Verify sender identity before processing

**Example:**
```json
{
  "sender": {
    "agent_id": "agent-main-001",
    "signature": "base64-encoded-signature",
    "public_key_id": "key-001"
  }
}
```

---

### B. Authorization

**Permission Checks:**
- Verify agent authorized to request action
- Skill-based access control
- Rate limiting per agent

**Example:**
```python
def authorize_message(message):
    sender = message.sender
    action = message.payload.action

    # Check skill permissions
    if not agent_has_skill(sender.agent_id, message.recipient.skill):
        raise UnauthorizedError(f"{sender.agent_id} lacks {message.recipient.skill} skill")

    # Check action permissions
    if action in RESTRICTED_ACTIONS:
        if not agent_has_permission(sender.agent_id, action):
            raise ForbiddenError(f"{sender.agent_id} cannot perform {action}")

    # Rate limiting
    if exceeds_rate_limit(sender.agent_id):
        raise RateLimitError(f"{sender.agent_id} exceeded rate limit")

    return True
```

---

### C. Data Protection

**Sensitive Data Handling:**
- Never include PHI/PII in messages
- Use references instead of actual data
- Encrypt messages in transit
- Sanitize logs (no secrets)

**Example:**
```json
{
  "message_type": "task_request",
  "payload": {
    "action": "generate_schedule",
    "resident_ids": ["uuid-1", "uuid-2"],  // IDs only, not names
    "schedule_reference": "s3://schedules/q2-2025.json"  // Reference, not data
  }
}
```

---

## XI. QUICK REFERENCE

### A. Common Message Templates

**1. Request Work from Specialist:**
```json
{
  "message_type": "task_request",
  "recipient": {"skill": "acgme-compliance"},
  "payload": {
    "action": "validate",
    "parameters": {"schedule_id": "uuid"}
  }
}
```

**2. Report Progress:**
```json
{
  "message_type": "status_update",
  "payload": {
    "progress_percentage": 45,
    "message": "Processing week 3 of 13"
  }
}
```

**3. Escalate to Human:**
```json
{
  "message_type": "escalation",
  "payload": {
    "level": "L4_HUMAN_ACTION",
    "summary": "Decision needed: cannot resolve constraint conflict",
    "options": [...]
  }
}
```

---

**END OF AGENT COMMUNICATION PROTOCOLS**

*These protocols ensure coordinated, reliable, and secure agent collaboration. Follow them to maintain system integrity and traceability.*
