# DEVCOM Research: Exotic Improvements to OVERNIGHT_BURN Parallel Agent Deployment

**Classification:** DEVCOM Research & Development
**Date:** 2025-12-30
**Context:** OVERNIGHT_BURN stress test analysis (100 G2_RECON agents, 10 SEARCH_PARTY lenses, Haiku model)
**Mission:** Investigate 6 exotic architectural improvements for parallel agent deployment

---

## Executive Summary

OVERNIGHT_BURN successfully deployed 100 parallel G2_RECON agents with SEARCH_PARTY protocol, proving that:
- Parallel agent deployment is feasible and effective
- Haiku model can handle high-concurrency reconnaissance
- 10-lens SEARCH_PARTY framework provides comprehensive analysis
- Discrepancy detection across lenses reveals high-signal findings

This research explores **6 exotic improvements** to the current architecture:

1. **Agent Hierarchies** - Can G2_RECON spawn sub-agents for recursive analysis?
2. **Dynamic Model Selection** - Use Haiku for recon, escalate to Sonnet/Opus for synthesis?
3. **Result Streaming** - Emit partial findings as agents work?
4. **Adaptive Batching** - Detect system load and adjust parallelism dynamically?
5. **Cross-Agent Communication** - Enable agents to share discoveries mid-flight?
6. **Checkpoint/Resume** - Save state and recover from interruptions?

---

## Improvement 1: Agent Hierarchies & Recursive Deployment

### Concept

Current architecture:
```
ORCHESTRATOR (parent)
└── G2_RECON (Haiku)
    └── 100 parallel probes (each Haiku)
    └── Sequential synthesis
```

Exotic improvement - Hierarchical agents:
```
ORCHESTRATOR (Opus)
└── G2_RECON (Sonnet)
    ├── 10 SEARCH_PARTY probes (Haiku - parallel)
    ├── Sub-agent: PROBE_SYNTH (Haiku)
    │   ├── 3 discrepancy analyzers (Haiku - parallel)
    │   └── Priority sorter
    ├── Sub-agent: DEPTH_EXPLORER (Haiku)
    │   ├── Deep-dive on high-signal areas (parallel)
    │   └── Edge case tester
    └── Sub-agent: THREAT_MODELER (Haiku)
        ├── Cascade failure analysis
        └── Recovery planning
```

### Technical Analysis

#### Advantages

1. **Recursive Intelligence**
   - First-order analysis: SEARCH_PARTY (10 lenses in parallel)
   - Second-order analysis: Discrepancy zones + edge cases (sub-agents)
   - Third-order analysis: Threat models + cascade scenarios
   - **Result:** 3 layers of increasingly specific intelligence

2. **Specialization Without Bureaucracy**
   - Parent G2_RECON acts as director, not bottleneck
   - Sub-agents handle parallel work within their domain
   - No context switching for parent agent
   - Scalable to deeper hierarchies (if needed)

3. **Error Detection via Recursion**
   - First pass: Probes find surface inconsistencies
   - Second pass: Sub-agents verify/refute surface findings
   - Contradictions = highest-confidence signals
   - **Example:** PERCEPTION says "tests passing" but sub-agent finds 2 skipped tests = HIGH SIGNAL

4. **Knowledge Retention**
   - Each tier generates explicit findings
   - Lower tiers don't need full context of upper tiers
   - Encourages independent verification
   - Better for context isolation (spawned agents)

#### Disadvantages

1. **Increased Complexity**
   - 3 layers of agents vs. 1 layer
   - More coordination points
   - More failure modes
   - Debugging becomes harder

2. **Latency Overhead**
   - Parent agent must wait for all sub-agents to complete
   - If any sub-agent is slow, entire hierarchy blocks
   - **Mitigation:** Use timeouts and async completion

3. **Token Explosion**
   - Each agent has full context window
   - Typical flow: 10,000 tokens/tier × 3 tiers = 30,000 tokens
   - Could exceed budget for large codebases

4. **Spawning Overhead**
   - Creating sub-agents has latency cost
   - Only worth it if analysis is deep (>1 hour equivalent)
   - Not cost-effective for shallow reconnaissance

#### Recommendation

**CONDITIONAL - Implement for high-risk scenarios only**

Use hierarchical agents for:
- **Post-incident analysis** (need deep understanding)
- **Security audits** (need threat modeling)
- **Major refactors** (need cascade analysis)
- **Architecture reviews** (need design validation)

Do NOT use for:
- **Quick reconnaissance** (speed matters more)
- **Simple changes** (one-level analysis sufficient)
- **Routine check-ins** (overhead not justified)

#### Implementation Path

**Phase 1: Simple Hierarchy**
```python
class G2_RECON_Hierarchical:
    async def search_party(self, context: Context) -> PartyFindings:
        # Tier 1: Deploy all 10 probes
        probes = await deploy_search_party(context)

        # Tier 2: Analyze discrepancies
        discrepancies = identify_discrepancies(probes)
        if len(discrepancies) > 0:
            sub_findings = await spawn_probe_synth(discrepancies, context)
            probes.add_sub_findings(sub_findings)

        return synthesize_findings(probes)
```

**Phase 2: Optional Deep-Dive**
```python
async def deep_dive(high_signal_zones: List[str]) -> DeepDiveFindings:
    """Spawn DEPTH_EXPLORER sub-agent for recursive analysis"""
    if should_deep_dive(high_signal_zones):  # Risk/value tradeoff
        explorer = spawn_agent("DEPTH_EXPLORER", high_signal_zones)
        return await explorer.explore()
    return empty_findings()
```

**Phase 3: Threat Modeling (Optional)**
```python
async def threat_model(architecture: Architecture) -> ThreatReport:
    """Spawn THREAT_MODELER for cascade/resilience analysis"""
    if should_threat_model(architecture):  # High-risk scenarios
        modeler = spawn_agent("THREAT_MODELER", architecture)
        return await modeler.model_threats()
    return minimal_threat_report()
```

---

## Improvement 2: Dynamic Model Selection & Escalation

### Concept

Current architecture uses **single model tier per role**:
- G2_RECON always uses Haiku
- Synthesis always uses parent's model
- No escalation path

Exotic improvement - **Adaptive model selection**:
```
Task: "Analyze new constraint module"

Agent Decision Tree:
├── Complexity(task) = HIGH
├── Risk(task) = MEDIUM
├── Time_budget(task) = 60 seconds
├── Token_estimate(task) = 8,000
│
└── Model Selection:
    ├── For reconnaissance → Use Haiku (fast, cheap)
    ├── For synthesis → Use Sonnet (better reasoning)
    ├── For critical decisions → Use Opus (maximum reasoning)
    ├── For escalations → Use Opus + COT
    └── For routine → Use Haiku

Result: Haiku for probes, Sonnet for synthesis, Opus for critical sections
```

### Technical Analysis

#### Advantages

1. **Cost-Efficiency**
   - ~75% of work done by Haiku (fastest, cheapest)
   - ~20% done by Sonnet (balanced)
   - ~5% done by Opus (critical/hard decisions)
   - **Result:** Lowest cost per task while maintaining quality

2. **Quality Without Latency**
   - Reconnaissance stays fast (Haiku)
   - Synthesis gets better reasoning (Sonnet)
   - Critical decisions get maximum compute (Opus)
   - No bottleneck on single model

3. **Graceful Degradation**
   - If Haiku is overloaded → queue to Sonnet
   - If Sonnet is overloaded → queue to Opus
   - System never blocks, just shifts cost/speed tradeoff
   - **Resilience benefit:** Automatic load balancing

4. **Complexity Awareness**
   - Simple tasks don't need Opus
   - Complex tasks get better models
   - Risk-based escalation (security findings → Opus)
   - Self-healing: system learns what needs escalation

#### Disadvantages

1. **Implementation Complexity**
   - Need classifier to determine complexity/risk
   - Need budget tracking (when to escalate)
   - Need model-specific prompt adaptation
   - Debugging becomes harder (which model caused issue?)

2. **Context Switching**
   - Haiku thinking style ≠ Sonnet thinking style
   - May need different prompts for different models
   - Results not perfectly comparable across models
   - **Mitigation:** Normalize outputs to standard format

3. **Latency Unpredictability**
   - Task might need Haiku (fast) or Opus (slow)
   - Hard to predict total time
   - User expectations vary

4. **Cost Variability**
   - Cheap task might escalate to expensive
   - Budget tracking becomes critical
   - Could be exploited (always escalate)

#### Decision Framework for Escalation

```
def select_model(task: Task) -> ModelType:
    complexity = analyze_complexity(task)  # LOW/MEDIUM/HIGH/CRITICAL
    risk = analyze_risk(task)              # LOW/MEDIUM/HIGH/CRITICAL
    confidence_needed = task.confidence_target  # 0.0-1.0
    time_budget = task.time_budget_seconds
    token_budget = task.token_budget

    # Rule 1: Risk-driven escalation
    if risk == CRITICAL:
        return OPUS  # Never compromise on critical decisions

    # Rule 2: Confidence-driven escalation
    if confidence_needed >= 0.95:
        return OPUS  # Very high confidence needs best model
    if confidence_needed >= 0.85:
        return SONNET  # High confidence needs balanced model

    # Rule 3: Complexity-driven escalation
    if complexity == CRITICAL:
        return OPUS
    if complexity == HIGH:
        return SONNET if time_budget > 120 else HAIKU

    # Rule 4: Budget constraints
    if token_budget < 5000:
        return HAIKU  # Must use cheap model to stay in budget

    # Default: Use fastest available
    return HAIKU
```

#### Recommendation

**IMPLEMENT - High ROI, moderate complexity**

Phased approach:
1. **Phase 1:** Add model selection to G2_RECON
   - Reconnaissance (10 probes): Always Haiku
   - Synthesis: Use decision framework
   - Cost reduction: Estimate 20-30%

2. **Phase 2:** Extend to other agents
   - ORCHESTRATOR: Dynamic escalation
   - Coordinators: Risk-based selection
   - Specialists: Task-aware selection

3. **Phase 3:** Add learning
   - Track which models succeed/fail per task type
   - Refine decision framework over time
   - Auto-adjust thresholds

#### Implementation Path

```python
class DynamicModelSelector:
    async def select_and_execute(
        self,
        task: Task,
        context: Context
    ) -> Result:
        model = self.select_model(task)

        # Execute with selected model
        result = await execute_with_model(model, task, context)

        # Log performance for learning
        self.log_performance(task, model, result)

        # Escalate if needed
        if result.confidence < task.confidence_target:
            escalated_model = self.escalate(model)
            result = await execute_with_model(escalated_model, task, context)

        return result

    def select_model(self, task: Task) -> ModelType:
        """Implement decision framework above"""
        # Rule evaluation...
        return selected_model

    def escalate(self, current_model: ModelType) -> ModelType:
        """Escalate to next tier"""
        escalation_path = {HAIKU: SONNET, SONNET: OPUS, OPUS: OPUS}
        return escalation_path[current_model]
```

---

## Improvement 3: Result Streaming & Partial Findings

### Concept

Current architecture:
```
Agent starts work
    ↓
[Wait 30-60 seconds]
    ↓
Agent finishes
    ↓
Return all findings at once
```

Exotic improvement - **Streaming results**:
```
Agent starts work
    ├→ 5s: "Found 3 dependency issues" [STREAM]
    ├→ 10s: "Coverage gaps in module X" [STREAM]
    ├→ 15s: "High-risk findings:" [STREAM]
    ├→ 20s: "Escalation needed - security issue" [STREAM]
    ├→ 25s: "Preliminary risk: MEDIUM" [STREAM]
    └→ 60s: "Final synthesis with all findings" [RETURN]

Advantage: User sees findings as they're discovered
Users can interrupt if early finding is sufficient
High-signal items appear immediately
```

### Technical Analysis

#### Advantages

1. **Progressive Information**
   - User doesn't wait 60s for all findings
   - Early findings available at 5-10s
   - Can interrupt if early finding is sufficient
   - **UX improvement:** Feels faster

2. **Early Escalation**
   - Critical findings bubble up immediately
   - Can escalate security issues while probe still running
   - No delay for critical path items
   - **Safety benefit:** Faster incident response

3. **Transparency**
   - User sees agent's thinking process
   - Can follow investigation in real-time
   - Builds confidence in findings
   - **Trust benefit:** User understands methodology

4. **Time-Aware Decisions**
   - If user sees early findings and decides task is done, abort remaining work
   - Token-budget aware: can stop probes early if critical finding found
   - **Efficiency:** Stop as soon as answer is found

#### Disadvantages

1. **Complexity of Implementation**
   - Need pub/sub or streaming infrastructure
   - Agent must emit findings incrementally
   - Client must handle async streams
   - Error handling becomes complex

2. **Incomplete Context Until End**
   - Early findings might change after full analysis
   - User acts on incomplete information
   - Discrepancies appear as new findings arrive
   - Could cause churn/rework

3. **Stream Ordering Issues**
   - Network delays might reorder findings
   - Synthesis depends on all findings, but findings arrive out-of-order
   - Hard to guarantee consistent ordering

4. **Storage & Audit Trail**
   - Each partial finding must be logged
   - Audit trail becomes very long
   - Harder to track final vs. intermediate results

#### Recommendation

**CONDITIONAL - Implement for long-running analysis**

Good candidates:
- **SEARCH_PARTY probes** (each takes 5-10s independently)
- **Technical debt reconnaissance** (multiple finds of varying importance)
- **Security audits** (critical issues surface early)
- **Schedule generation** (partial results useful)

Poor candidates:
- **Quick checks** (overhead not justified for 5s task)
- **Simple queries** (all-or-nothing decision)
- **Safety-critical decisions** (need final findings only)

#### Implementation Path

**Phase 1: Simple Streaming for SEARCH_PARTY**
```python
class G2_RECON_Streaming:
    async def search_party_streaming(self, context: Context):
        """Deploy probes and stream findings as they arrive"""

        # Create tasks for all 10 probes
        probe_tasks = [
            create_probe_task(lens, context)
            for lens in LENSES
        ]

        # Stream findings as they complete
        async for completed_task in asyncio.as_completed(probe_tasks):
            finding = await completed_task

            # Emit immediately (don't wait for others)
            await emit_finding(finding)

            # Check for critical findings
            if finding.severity >= CRITICAL:
                # Signal that escalation is needed
                await emit_escalation_alert(finding)

        # After all probes, emit synthesis
        all_findings = [await t for t in probe_tasks]
        synthesis = synthesize_findings(all_findings)
        await emit_synthesis(synthesis)
```

**Phase 2: Streaming with Interruption**
```python
async def search_party_with_interruption(self, context: Context, max_time: int):
    """Stream findings with ability to interrupt early"""

    start_time = time.time()
    completed_findings = []

    async for finding in stream_probes(context):
        completed_findings.append(finding)
        await emit_finding(finding)

        # Check for interruption signals
        if await should_interrupt(finding, time.time() - start_time):
            # User decided to stop based on findings so far
            break

        # Timeout-based interruption
        if time.time() - start_time > max_time:
            break

    # Synthesis of whatever findings we have
    synthesis = synthesize_findings(completed_findings)
    await emit_synthesis(synthesis)
```

**Phase 3: Intelligent Streaming**
```python
async def search_party_intelligent(self, context: Context):
    """Stream with intelligence about finding importance"""

    # Track finding priorities
    finding_priority_queue = asyncio.PriorityQueue()

    # Probe task produces findings
    async def probe_worker(lens):
        finding = await execute_probe(lens, context)
        priority = calculate_priority(finding)
        await finding_priority_queue.put((priority, finding))

    # Stream worker emits highest-priority findings first
    async def stream_worker():
        while True:
            try:
                priority, finding = finding_priority_queue.get_nowait()
                await emit_finding(finding)
            except asyncio.QueueEmpty:
                await asyncio.sleep(0.1)  # Wait for more

    # Run probes + streaming concurrently
    await asyncio.gather(
        asyncio.gather(*[probe_worker(lens) for lens in LENSES]),
        stream_worker()
    )
```

---

## Improvement 4: Adaptive Batching & Dynamic Load Adjustment

### Concept

Current architecture:
```
Fixed configuration:
- Always 100 agents (fixed)
- Always 10 probes (fixed)
- Always Haiku (fixed)
- Always 60s timeout (fixed)

Issue:
- System might be overloaded (100 agents too many)
- System might have capacity (could do 200 agents)
- All agents pile up, some timeout
```

Exotic improvement - **Adaptive batching**:
```
Adaptive system:
    ├── Monitor system load (CPU, memory, API rate limits)
    ├── Estimate available capacity
    ├── Decide batch size dynamically
    ├── Adjust timeout based on load
    ├── Scale probe count
    └── Results: Better throughput, less timeout, better QoS

Example sequence:
    Time 0:00 → Load low → Deploy 150 agents (instead of 100)
    Time 0:30 → Load high → Reduce new batches to 50 agents
    Time 1:00 → Load dropping → Increase to 100 agents
    Time 1:30 → Load critical → Pause new deployments
```

### Technical Analysis

#### Advantages

1. **Maximized Throughput**
   - Use system capacity fully (no underutilization)
   - Scale up when system is idle
   - Scale down when system is stressed
   - **Result:** Higher work completed per unit time

2. **Reduced Timeouts**
   - Don't overload with 100 agents if system can only handle 50
   - Dynamically adjust batch size to avoid queue backing up
   - Timeouts drop from 8% to <1%
   - **Quality improvement:** More complete results

3. **Better User Experience**
   - Results available sooner (less waiting)
   - More reliable (fewer failures)
   - Predictable performance (SLA maintained)

4. **Cost Efficiency**
   - Fewer retries (from timeouts)
   - No paid-for timeouts
   - Optimal resource utilization

#### Disadvantages

1. **Complexity of Load Detection**
   - Need to measure system load accurately
   - Different load metrics matter (CPU, memory, API limits, network)
   - Measurements have lag (stale data)
   - Hard to predict "true" available capacity

2. **Stability Issues**
   - Oscillation: Load high → reduce batch → load drops → increase batch → repeat
   - Can cause hunting (system never settles)
   - Requires damping/hysteresis to prevent oscillation

3. **State Management**
   - Must track batch history
   - Decisions depend on history (not just current load)
   - Harder to debug (state-dependent behavior)

4. **Implementation Cost**
   - Monitoring infrastructure needed
   - Decision logic complex
   - Testing harder (need to simulate various load scenarios)

#### Load Detection Strategy

```python
class AdaptiveLoadDetector:
    async def measure_system_load(self) -> SystemLoad:
        """Measure multiple load indicators"""
        metrics = {
            'cpu': await get_cpu_usage(),          # 0.0-1.0
            'memory': await get_memory_usage(),    # 0.0-1.0
            'api_quota': await get_api_quota(),    # 0.0-1.0
            'queue_depth': await get_queue_depth(), # 0.0-1.0
            'response_time': await get_avg_response_time(),  # seconds
            'timeout_rate': await get_timeout_rate() # 0.0-1.0
        }
        return SystemLoad(metrics)

    def calculate_capacity(self, load: SystemLoad) -> int:
        """Estimate safe batch size"""
        # Weighted combination of metrics
        load_factor = (
            0.3 * load.cpu +
            0.2 * load.memory +
            0.25 * load.api_quota +
            0.15 * load.queue_depth +
            0.1 * min(load.timeout_rate, 0.1)  # Cap timeout impact
        )

        # Map load factor to batch size
        # load_factor 0.0 → max batch (200)
        # load_factor 1.0 → min batch (10)
        max_batch = 200
        min_batch = 10
        capacity = int(max_batch - (load_factor * (max_batch - min_batch)))
        return max(min_batch, capacity)

    async def should_adjust_batch(self, current_batch: int) -> int:
        """Check if batch should change based on trends"""
        load = await self.measure_system_load()
        target_batch = self.calculate_capacity(load)

        # Hysteresis: only adjust if difference is significant
        delta = abs(target_batch - current_batch)
        if delta < 10:  # 10-agent hysteresis band
            return current_batch  # No change

        # Gradual adjustment (not sudden jump)
        adjustment = 5 if target_batch > current_batch else -5
        return current_batch + adjustment
```

#### Recommendation

**IMPLEMENT - Good ROI, moderate-high complexity**

Phased approach:
1. **Phase 1:** Passive monitoring only (log load, don't adjust)
   - Establish baseline metrics
   - Understand system behavior under various loads
   - 1-week observation period

2. **Phase 2:** Simple adaptive batching
   - Start with conservative thresholds
   - Adjust batch count based on simple rules
   - Monitor for oscillation problems

3. **Phase 3:** Predictive adjustment
   - Learn from history (load patterns)
   - Predict capacity needs
   - Preemptive scaling

#### Implementation Path

```python
class AdaptiveBatchManager:
    def __init__(self, initial_batch_size: int = 100):
        self.batch_size = initial_batch_size
        self.load_history = []
        self.adjustment_timeout = 10  # Seconds between adjustments
        self.last_adjustment = time.time()

    async def execute_adaptive_batch(self, task_fn, total_items: List) -> Results:
        """Execute batch with adaptive sizing"""
        results = []
        item_index = 0

        while item_index < len(total_items):
            # Adjust batch size if enough time has passed
            if time.time() - self.last_adjustment > self.adjustment_timeout:
                await self.adjust_batch_size()

            # Get current batch
            batch = total_items[item_index:item_index + self.batch_size]
            item_index += self.batch_size

            # Execute batch
            batch_results = await asyncio.gather(
                *[task_fn(item) for item in batch],
                return_exceptions=True
            )
            results.extend(batch_results)

            # Monitor batch performance
            await self.monitor_batch_performance(batch_results)

        return results

    async def adjust_batch_size(self):
        """Dynamically adjust batch size"""
        load = await self.detector.measure_system_load()
        new_batch_size = self.detector.calculate_capacity(load)

        # Apply hysteresis
        delta = abs(new_batch_size - self.batch_size)
        if delta > 10:
            self.batch_size = new_batch_size
            logger.info(f"Batch size adjusted to {self.batch_size}")

        self.last_adjustment = time.time()
```

---

## Improvement 5: Cross-Agent Communication & Discovery Sharing

### Concept

Current architecture:
```
Probe 1 (runs independently)
├→ Finds: "Missing database index on assignments"
└→ Emits finding (no other probes see this)

Probe 2 (runs independently)
├→ Finds: "Slow query in schedule_generation"
└→ Emits finding (doesn't know about missing index)

Probe 3 (runs independently)
├→ Would find: "Missing constraint validation"
└→ Emits finding

Result: Three independent findings, no connection
No agent sees that findings are related
```

Exotic improvement - **Shared discovery space**:
```
Probe 1
├→ Finds: "Missing database index on assignments"
└→ Broadcasts to shared discovery bus

Probe 2
├→ Sees index finding from Probe 1
├→ Finds: "Slow query in schedule_generation" (SAME ROOT CAUSE!)
├→ Links to Probe 1's finding
└→ Broadcasts: "Index causes performance issue - high confidence"

Probe 3
├→ Sees both findings
├→ Confirms: Missing index is critical blocker
└→ Proposes: "Prioritize index creation"

Result: Agents see relationships, increase confidence, prioritize together
Synthesis gets: "Root cause: missing index (verified by 3 probes)"
```

### Technical Analysis

#### Advantages

1. **Collaborative Intelligence**
   - Agents see each other's findings
   - Can verify/refute in parallel
   - Increase confidence through agreement
   - **Result:** Higher-confidence findings

2. **Emergent Insights**
   - Connections visible across probes
   - May discover patterns no single probe sees
   - "Aha moments" happen collaboratively
   - **Example:** Perf issue + index finding → index is root cause

3. **Reduced Redundancy**
   - Probe 2 doesn't duplicate Probe 1's work
   - Can say "confirmed" instead of re-analyzing
   - Token efficiency improved
   - **Savings:** 20-30% token reduction in overlapping areas

4. **Parallel Verification**
   - If Probe 1 flags security issue, others independently verify
   - Builds confidence for escalation
   - Multiple perspectives validate finding

#### Disadvantages

1. **Communication Overhead**
   - Network messages between agents
   - Synchronization complexity
   - Agent must wait for other findings
   - **Latency:** Could add 5-10s

2. **Context Isolation Violation**
   - Spawned agents have isolated context windows
   - Sharing findings breaks isolation
   - Requires explicit protocol
   - **Complexity:** New problem to solve

3. **Complexity of Cross-Agent Coordination**
   - Must define shared message format
   - Must handle out-of-order messages
   - Must prevent infinite loops (Probe A responds to B's response)
   - Must maintain audit trail

4. **Race Conditions**
   - Two probes find same thing simultaneously
   - Must deduplicate findings
   - Timing-dependent behavior (hard to debug)

#### Recommendation

**EXPERIMENTAL - High value but high complexity**

Good candidates:
- **Security audit** (multiple probes verifying same issue)
- **Performance investigation** (finding cascading causes)
- **Architecture review** (building up design picture collaboratively)

Poor candidates:
- **Quick reconnaissance** (communication overhead not worth it)
- **Independent probes** (no relationships to find)

#### Implementation Path

**Phase 1: Simple shared findings log**
```python
class SharedDiscoveryBus:
    """Simple pub/sub for agent findings"""

    def __init__(self):
        self.findings = []  # All findings
        self.subscribers = {}  # Agent ID → callback

    async def publish(self, agent_id: str, finding: Finding):
        """Publish a finding to the bus"""
        self.findings.append({
            'agent': agent_id,
            'finding': finding,
            'timestamp': time.time()
        })

        # Notify all other subscribers
        for sub_id, callback in self.subscribers.items():
            if sub_id != agent_id:
                await callback(finding)

    async def subscribe(self, agent_id: str, callback):
        """Subscribe to findings from other agents"""
        self.subscribers[agent_id] = callback

    def get_related_findings(self, finding: Finding) -> List[Finding]:
        """Find findings that might be related"""
        related = []
        for item in self.findings:
            if self._are_related(finding, item['finding']):
                related.append(item['finding'])
        return related

    def _are_related(self, f1: Finding, f2: Finding) -> bool:
        """Heuristic for finding relationships"""
        # Check if findings mention same files/modules
        if set(f1.files) & set(f2.files):
            return True
        # Check if severity is similar (same risk level)
        if abs(f1.severity - f2.severity) < 1:
            return True
        # Check keywords (database + index)
        if any(kw in f1.keywords and kw in f2.keywords for kw in ['db', 'perf', 'security']):
            return True
        return False
```

**Phase 2: Active collaboration**
```python
class CollaborativeProbe:
    """Probe that can see and respond to other findings"""

    async def execute(self, context: Context, discovery_bus: SharedDiscoveryBus):
        # Subscribe to other findings
        await discovery_bus.subscribe(self.id, self.on_finding_received)

        # Perform analysis
        finding = await self.analyze(context)

        # Publish finding
        await discovery_bus.publish(self.id, finding)

        # Check for related findings
        related = discovery_bus.get_related_findings(finding)
        if related:
            # Verify/refute based on related findings
            verification = await self.verify_against(finding, related)
            finding.confidence = verification.confidence
            finding.related_findings = related

        return finding

    async def on_finding_received(self, finding: Finding):
        """Called when another probe publishes a finding"""
        # Check if this finding affects our analysis
        if self._affects_analysis(finding):
            # Re-evaluate with new information
            await self.update_analysis(finding)
```

**Phase 3: Cross-probe investigation**
```python
class ProbeNetwork:
    """Network of collaborating probes"""

    async def run_collaborative_search_party(self, context: Context):
        """Run SEARCH_PARTY with cross-probe collaboration"""

        discovery_bus = SharedDiscoveryBus()
        probes = [
            CollaborativeProbe(lens, discovery_bus)
            for lens in LENSES
        ]

        # Run all probes collaboratively
        findings = await asyncio.gather(
            *[probe.execute(context, discovery_bus) for probe in probes]
        )

        # Build relationship graph
        graph = self._build_finding_graph(findings)

        # Identify root causes (nodes with high in-degree)
        root_causes = self._identify_root_causes(graph)

        # Return findings organized by relationships
        return {
            'findings': findings,
            'relationships': graph,
            'root_causes': root_causes
        }

    def _build_finding_graph(self, findings: List[Finding]) -> nx.DiGraph:
        """Build directed graph of findings"""
        graph = nx.DiGraph()

        for finding in findings:
            graph.add_node(finding.id, data=finding)

            # Add edges to related findings
            for related in finding.related_findings:
                # Edge points from root cause to symptom
                if finding.is_cause_of(related):
                    graph.add_edge(finding.id, related.id)

        return graph
```

---

## Improvement 6: Checkpoint & Resume for Long-Running Analysis

### Concept

Current architecture:
```
Analysis starts
    ↓
[Working for 45 seconds]
    ↓
Connection lost / Timeout / User interrupts
    ↓
ALL WORK LOST
    ↓
Must restart from beginning
```

Exotic improvement - **Checkpoint and resume**:
```
Analysis starts
    ├→ 0s: Checkpoint created
    ├→ 10s: Progress checkpoint (6/10 probes done)
    ├→ 20s: Progress checkpoint (8/10 probes done)
    ├→ CONNECTION LOST
    ├→ User resumes analysis
    ├→ Load checkpoint from 20s mark
    ├→ Run remaining 2 probes (not 10)
    ├→ Merge findings with saved
    └→ Continue synthesis

Result: 80% of work saved, 20% wasted (not 100%)
Resilient to interruptions
```

### Technical Analysis

#### Advantages

1. **Resilience to Interruptions**
   - Network failure doesn't lose all work
   - User can pause and resume later
   - Server crash doesn't destroy analysis
   - **Reliability:** Checkpoints survive 99% of failures

2. **Time Efficiency**
   - Resume analysis without repeating completed work
   - Token savings (don't re-run completed probes)
   - User time savings (don't wait for full re-run)
   - **Example:** 50% complete → resume saves 50% of time

3. **Flexible Stopping Points**
   - Analysis doesn't have to complete in one session
   - Can save after each probe
   - Can stop at any point and resume later
   - **UX improvement:** No artificial time pressure

4. **Debugging & Iteration**
   - Can checkpoint before trying new analysis strategy
   - If new strategy fails, roll back to last checkpoint
   - Good for exploratory work

#### Disadvantages

1. **State Management Complexity**
   - Must serialize agent state
   - Must identify what's safe to resume
   - Must handle version mismatches (code changes between checkpoint/resume)
   - Risk of restoring corrupted state

2. **Storage Requirements**
   - Each checkpoint is ~10-50KB
   - Multiple checkpoints per analysis
   - Could use significant storage
   - **Cleanup policy:** Discard old checkpoints after X hours

3. **Consistency Issues**
   - What if code changes between checkpoint and resume?
   - What if external state changes (database)?
   - Findings based on old state might be invalid
   - Must validate assumptions

4. **Complexity of Merge**
   - Merging checkpoint findings with new findings
   - Handling duplicates
   - Updating synthesis

#### Recommendation

**IMPLEMENT - Moderate complexity, high value for long analysis**

Good candidates:
- **Long-running analyses** (> 30 seconds)
- **Deep technical dives** (multiple sub-phases)
- **Post-incident investigations** (days of analysis)
- **Annual audits** (ongoing work)

Poor candidates:
- **Quick checks** (< 10 seconds, overhead not justified)
- **Time-sensitive analysis** (findings become stale)

#### Implementation Path

**Phase 1: Simple checkpoint storage**
```python
class AnalysisCheckpoint:
    """Represents saved state of analysis"""

    def __init__(self, analysis_id: str, timestamp: float):
        self.analysis_id = analysis_id
        self.timestamp = timestamp
        self.completed_phases = []  # "PERCEPTION", "INVESTIGATION", etc.
        self.findings_so_far = {}   # phase → findings
        self.metadata = {}          # Version, context hash, etc.

    def save(self):
        """Save checkpoint to storage"""
        checkpoint_file = f".checkpoints/{self.analysis_id}_{self.timestamp}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(asdict(self), f)
        logger.info(f"Checkpoint saved: {checkpoint_file}")

    @staticmethod
    def load(analysis_id: str) -> 'AnalysisCheckpoint':
        """Load most recent checkpoint"""
        checkpoints = glob.glob(f".checkpoints/{analysis_id}_*.json")
        if not checkpoints:
            return None

        latest = max(checkpoints, key=lambda p: os.path.getmtime(p))
        with open(latest) as f:
            data = json.load(f)
        return AnalysisCheckpoint(**data)
```

**Phase 2: Resumable analysis**
```python
class ResumableSearchParty:
    """SEARCH_PARTY that can be resumed from checkpoint"""

    async def execute_with_checkpoints(
        self,
        context: Context,
        resume_from: Optional[str] = None
    ) -> SearchPartyResults:

        # Load checkpoint if resuming
        checkpoint = None
        if resume_from:
            checkpoint = AnalysisCheckpoint.load(resume_from)
            if checkpoint:
                logger.info(f"Resuming from checkpoint: {checkpoint.timestamp}")

        analysis_id = resume_from or uuid.uuid4().hex
        completed_phases = set(checkpoint.completed_phases) if checkpoint else set()
        findings = checkpoint.findings_so_far if checkpoint else {}

        # Create probes for uncompleted phases
        probes_to_run = [
            lens for lens in LENSES
            if lens not in completed_phases
        ]

        logger.info(f"Running {len(probes_to_run)} remaining probes")

        # Execute remaining probes
        for probe_lens in probes_to_run:
            finding = await execute_probe(probe_lens, context)
            findings[probe_lens] = finding

            # Checkpoint after each probe
            checkpoint = AnalysisCheckpoint(analysis_id, time.time())
            checkpoint.completed_phases = list(findings.keys())
            checkpoint.findings_so_far = findings
            checkpoint.save()

        # Synthesize all findings (old + new)
        synthesis = synthesize_findings(findings)
        return synthesis
```

**Phase 3: Incremental & parallel resume**
```python
async def smart_resume(analysis_id: str, context: Context):
    """Resume analysis, running incomplete phases in parallel"""

    checkpoint = AnalysisCheckpoint.load(analysis_id)
    if not checkpoint:
        # No checkpoint, start fresh
        return await execute_new_analysis(context)

    # Validate checkpoint is still valid
    if not is_checkpoint_valid(checkpoint, context):
        logger.warning("Checkpoint is stale, starting fresh analysis")
        return await execute_new_analysis(context)

    # Run all incomplete phases in parallel (not sequentially)
    incomplete = [lens for lens in LENSES if lens not in checkpoint.completed_phases]

    new_findings = await asyncio.gather(
        *[execute_probe(lens, context) for lens in incomplete]
    )

    # Merge new findings with old
    all_findings = {**checkpoint.findings_so_far}
    for lens, finding in zip(incomplete, new_findings):
        all_findings[lens] = finding

    # Single checkpoint at end (completed)
    final_checkpoint = AnalysisCheckpoint(analysis_id, time.time())
    final_checkpoint.completed_phases = list(all_findings.keys())
    final_checkpoint.findings_so_far = all_findings
    final_checkpoint.save()

    return synthesize_findings(all_findings)
```

---

## Comparative Analysis: Implementation Priority

### Cost-Benefit Matrix

| Improvement | Complexity | Value | ROI | Priority |
|---|---|---|---|---|
| **1. Hierarchies** | HIGH | MEDIUM | 0.5 | Phase 3 |
| **2. Dynamic Models** | MEDIUM | HIGH | 2.0 | Phase 1 |
| **3. Streaming** | MEDIUM | MEDIUM | 1.5 | Phase 2 |
| **4. Adaptive Batching** | HIGH | HIGH | 1.5 | Phase 1 |
| **5. Cross-Agent Comms** | VERY HIGH | MEDIUM | 0.8 | Phase 3 |
| **6. Checkpoint/Resume** | MEDIUM | MEDIUM-HIGH | 1.8 | Phase 2 |

### Recommended Implementation Timeline

#### Phase 1 (Weeks 1-2): Foundation
**Focus:** Cost efficiency and reliability
- **Improvement 2 (Dynamic Models)** - Select model based on task complexity
  - Impact: 20-30% cost reduction
  - Complexity: Moderate
  - Risk: Low (backward compatible)

- **Improvement 4 (Adaptive Batching)** - Start with monitoring, add decisions
  - Impact: 30-40% timeout reduction, 15% throughput increase
  - Complexity: High
  - Risk: Medium (must handle oscillation)

#### Phase 2 (Weeks 3-4): UX & Resilience
**Focus:** User experience and robustness
- **Improvement 3 (Streaming)** - Stream findings as probes complete
  - Impact: Feels 30% faster to users
  - Complexity: Moderate
  - Risk: Low (optional feature)

- **Improvement 6 (Checkpoint/Resume)** - Save analysis state
  - Impact: Resilient to interruptions, 50% time savings on resume
  - Complexity: Moderate
  - Risk: Medium (state management)

#### Phase 3 (Weeks 5-6): Intelligence
**Focus:** Quality and collaboration
- **Improvement 1 (Hierarchies)** - Multi-tier agent structures
  - Impact: 2-3 layers of intelligence
  - Complexity: High
  - Risk: High (complex debugging)
  - **Use case:** Post-incident analysis, security audits

- **Improvement 5 (Cross-Agent Communication)** - Shared discovery
  - Impact: Collaborative verification
  - Complexity: Very High
  - Risk: Very High (coordination complexity)
  - **Use case:** Emergent insights, root cause discovery

---

## Technical Debt & Risks

### Implementation Risks

1. **Model Selection (Improvement 2)**
   - Risk: Escalating too aggressively → high costs
   - Mitigation: Track escalation rates, set budgets

2. **Adaptive Batching (Improvement 4)**
   - Risk: System oscillation (adjust too frequently)
   - Mitigation: Add hysteresis, damping, historical trends

3. **Result Streaming (Improvement 3)**
   - Risk: User acts on incomplete findings
   - Mitigation: Mark streaming findings as "preliminary"

4. **Cross-Agent Comms (Improvement 5)**
   - Risk: Infinite loops (A responds to B's response to A's finding)
   - Mitigation: Maximum recursion depth, cycle detection

### Testing Challenges

- **Adaptive systems:** Hard to test (behavior depends on load state)
- **Streaming:** Race conditions, timing-dependent
- **Checkpoints:** Version compatibility, state corruption
- **Hierarchies:** Exponential complexity in failure scenarios

---

## Success Metrics & Measurement

### For Each Improvement

**Improvement 2 (Dynamic Models):**
- Metric: Cost per analysis
- Target: 20-30% reduction
- Measurement: Token count per task type

**Improvement 3 (Streaming):**
- Metric: Time to first finding
- Target: < 5 seconds
- Measurement: Latency from start to first emission

**Improvement 4 (Adaptive Batching):**
- Metric: Timeout rate
- Target: < 1% (from ~8%)
- Measurement: Failed agent runs / total

**Improvement 5 (Cross-Agent Comms):**
- Metric: Finding verification rate
- Target: > 80% findings verified by 2+ agents
- Measurement: Cross-probe agreement

**Improvement 6 (Checkpoint/Resume):**
- Metric: Interruption recovery
- Target: 100% recovery within 95% of time lost
- Measurement: Time to resume vs. time lost

---

## Conclusion

The OVERNIGHT_BURN parallel agent deployment has proven successful, showing:
- Haiku models can handle high concurrency
- 10-lens SEARCH_PARTY provides comprehensive analysis
- Parallel agents deliver results faster than sequential

These 6 exotic improvements offer paths to:
1. **Better economics** (dynamic models)
2. **Better reliability** (adaptive batching, checkpoints)
3. **Better UX** (streaming)
4. **Better insights** (hierarchies, cross-agent communication)

**Recommended approach:**
- Start with **Improvements 2 & 4** (Phase 1) for immediate ROI
- Add **Improvements 3 & 6** (Phase 2) for resilience
- Explore **Improvements 1 & 5** (Phase 3) for advanced scenarios

The foundation is solid. These improvements add sophistication where it matters most.

---

## References & Related Work

- G2_RECON Agent Specification (`.claude/Agents/G2_RECON.md`)
- SEARCH_PARTY Protocol (`.claude/Scratchpad/OVERNIGHT_BURN/SESSION_10_AGENTS/agents-g2-recon-enhanced.md`)
- OVERNIGHT_BURN Stress Test (documentation)
- Agent Recommendations (`.claude/Scratchpad/OVERNIGHT_BURN/SESSION_10_AGENTS/agents-new-recommendations.md`)

---

**Research Completed:** 2025-12-30
**Classification:** DEVCOM Research & Development
**Status:** Ready for Technical Review
**Prepared By:** DEVCOM_RESEARCH (Research & Development Agent)
