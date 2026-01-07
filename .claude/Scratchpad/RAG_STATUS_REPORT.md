# RAG Status Report
**Generated:** 2026-01-06 | **Report Type:** Quarterly Health Assessment | **Status:** HEALTHY

---

## Executive Summary

The Retrieval Augmented Generation (RAG) system is a searchable knowledge base that captures institutional knowledge about how this program works. Think of it as an intelligent filing system: when an AI agent needs to answer a question about scheduling rules, ACGME compliance, how swaps work, or how decisions are made, it queries RAG to pull relevant documents rather than making things up.

**Current Status:** The knowledge base is **healthy and well-populated** with 148 documents across 12 subject areas. It contains the core institutional knowledge needed to run the scheduler, including ACGME compliance rules, scheduling policies, how swaps and conflicts are handled, and organizational procedures. All documents are properly indexed and searchable.

---

## Document Inventory

The knowledge base is organized into these subject areas:

### 1. **ACGME Rules** (7 documents)
**What:** Federal compliance regulations for medical residency training.
- 80-hour weekly work limit
- 1-in-7 call requirements
- Supervision ratios and faculty oversight
- Rest periods and consecutive duty limits
- Moonlighting restrictions

**Why It Matters:** The scheduler must enforce these rules automatically. Violations create liability and affect resident wellbeing.

**Example Queries:**
- "What is the 80-hour work limit?"
- "How many consecutive hours can a resident work?"
- "What supervision ratios are required?"

---

### 2. **Scheduling Policy** (9 documents)
**What:** Internal institutional policies for how schedules are built and managed.
- How rotations are structured and assigned
- Block scheduling conventions
- Call assignment distribution
- Clinic day allocation
- Absence handling procedures
- Block 0 (schedule initialization) procedures

**Why It Matters:** These define what "good" looks like operationally—policies that balance ACGME compliance with clinical needs.

**Example Queries:**
- "How should call be distributed fairly?"
- "What's the Block 0 procedure?"
- "How are absences handled in schedules?"

---

### 3. **Swap System** (8 documents)
**What:** Procedures for residents requesting to exchange assignments.
- How swap requests are submitted and approved
- Validation rules (both must still comply with rules)
- Role-based approval workflows
- Edge cases (partial swaps, cascading swaps)
- Audit trail requirements

**Why It Matters:** Swaps happen frequently. The system must make them fast and safe, ensuring no ACGME violations sneak in.

**Example Queries:**
- "What happens when a resident requests a swap?"
- "Who approves swaps?"
- "Can swaps violate ACGME rules?"

---

### 4. **Resilience Concepts** (13 documents)
**What:** Patterns from other critical industries (nuclear safety, aviation, power grids) adapted for scheduling.
- Defense-in-depth: Multiple layers of protection
- Contingency analysis: What if a key faculty member is sick?
- Load shedding: How to gracefully reduce when understaffed
- Circuit breakers: How to fail safely without cascade failures
- Cascade failure simulation: Modeling worst-case scenarios

**Why It Matters:** Medical scheduling is safety-critical. These patterns help us prevent "one bad thing causes collapse."

**Example Queries:**
- "What happens if one faculty member can't work?"
- "How do we handle an unexpected absence?"
- "How do we detect system overload?"

---

### 5. **Delegation Patterns** (37 documents)
**What:** How decisions are made and responsibility is distributed in the organization.
- Auftragstaktik doctrine: Mission-type orders (tell people the "why," not the "how")
- Decision rights: Who decides what
- Agent spawning patterns: How AI agents coordinate with each other
- Escalation procedures: When to ask for help
- Authority chains: Who reports to whom

**Why It Matters:** This program uses a sophisticated delegation model. New operators need to understand how to make decisions without asking permission for everything.

**Example Queries:**
- "Who can approve schedule changes?"
- "When should I escalate a decision?"
- "How do AI agents work together?"

---

### 6. **Agent Specifications** (13 documents)
**What:** Detailed identity cards for each AI agent in the system.
- Role and responsibilities
- Standing orders (what they can do without asking)
- Chain of command
- When to spawn them
- Their areas of expertise

**Why It Matters:** This program uses multiple specialized AI agents. Each has different authority and knows different things. These cards explain who does what.

**Example Queries:**
- "What can the Historian agent do?"
- "When should I spawn the Security Auditor?"
- "Who reviews code changes?"

---

### 7. **Military-Specific Guidance** (10 documents)
**What:** Unique considerations for military medical residency training.
- OPSEC/PERSEC requirements (protecting sensitive information)
- Deployment and TDY (temporary duty) considerations
- Multi-tier functionality (MTF) military compliance framework
- DRRS (Defense Readiness Reporting System) alignment
- Iron Dome regulatory protection

**Why It Matters:** This is a military program. Different rules and sensitivities apply compared to civilian medical training.

**Example Queries:**
- "What data cannot be logged or stored?"
- "How do deployments affect schedules?"
- "How do we report readiness?"

---

### 8. **Exotic Concepts** (19 documents)
**What:** Advanced scheduling and system design concepts.
- Tensegrity solver: A scheduling algorithm that works like architectural tensegrity (cables and rods in tension/compression)
- Constraint programming: Mathematical approach to solving hard scheduling problems
- Graph algorithms: Finding optimal assignments using network theory
- Pareto optimization: Trading off competing goals (fairness vs. coverage)
- Stigmergy: Agents leaving signals for each other (like ants with pheromones)

**Why It Matters:** These explain the "secret sauce" of how the scheduler works—the algorithms and mathematical concepts that make it smart.

**Example Queries:**
- "How does the tensegrity solver work?"
- "What is Pareto optimization?"
- "How do constraints get satisfied?"

---

### 9. **Session Learnings** (11 documents)
**What:** Summaries of issues discovered and fixed in previous work sessions.
- Bugs that were found and root causes
- Why certain architectural decisions were made
- Common pitfalls and how to avoid them
- Performance improvements and their impact
- Test failures and how they were resolved

**Why It Matters:** This captures institutional memory. "We tried that before and it failed because..."—this knowledge prevents repeating mistakes.

**Example Queries:**
- "What's the CCW token bug?"
- "Why can't we modify certain files?"
- "What issues have been found with block 0?"

---

### 10. **Session Protocols** (3 documents)
**What:** Standard procedures for starting and ending work sessions.
- Session initialization (loading context)
- Handoff procedures (passing work to another agent)
- Session closure and documentation requirements

**Why It Matters:** This ensures consistency and continuity. New sessions load the right context, work is properly documented, and nothing falls through cracks.

**Example Queries:**
- "How should a session start?"
- "What goes in a session handoff?"
- "How do we close out work?"

---

### 11. **User Guide & FAQ** (16 documents)
**What:** Instructions for human operators of the system.
- How to generate schedules
- How to handle emergency coverage requests
- How to approve/reject swaps
- How to investigate schedule conflicts
- Troubleshooting common issues

**Why It Matters:** The Program Director and Coordinator need to know how to use the system day-to-day.

**Example Queries:**
- "How do I generate a schedule?"
- "What do I do if someone calls in sick?"
- "How do I see why a schedule failed?"

---

### 12. **README & Overview** (2 documents)
**What:** High-level explanations of the overall system.
- What the scheduler does and why
- System architecture overview
- How to get started

**Why It Matters:** Orientation documents for new users.

**Example Queries:**
- "What does this system do?"
- "How do all the pieces fit together?"

---

## Coverage Assessment

### Well-Covered Areas (Confident)
✅ **ACGME Compliance** - Comprehensive coverage of federal rules
✅ **Swap Procedures** - Full lifecycle documented
✅ **Delegation Model** - Extensive patterns documented
✅ **AI Agent Roles** - All agents documented
✅ **Resilience Patterns** - Good coverage of failure scenarios
✅ **Military Requirements** - OPSEC/PERSEC and reporting covered

### Good Coverage (Generally Sufficient)
✓ **Scheduling Policies** - Core policies documented
✓ **Algorithm Concepts** - Tensegrity and constraint programming explained
✓ **Session Procedures** - Standard protocols documented

### Emerging Gaps (Worth Adding)
⚠ **Detailed Troubleshooting** - More "how to debug common errors" content
⚠ **Integration Guides** - How different components interact (less detail needed)
⚠ **Performance Tuning** - How to optimize schedules for speed vs. quality
⚠ **Historical Data** - Tracking what has been tried and succeeded/failed

### Not Covered (Out of Scope)
❌ **API Reference** - This lives in code comments and Swagger docs, not RAG
❌ **DevOps** - Infrastructure setup (Docker, Kubernetes) not in RAG
❌ **Database Schema** - Code-level implementation details

---

## Usage Guidance for Operators

### When to Query RAG
**Use RAG when:**
- You're asking a procedural question ("How does X work?")
- You're trying to understand a policy ("What's the rule about Y?")
- You're troubleshooting and want historical context ("Has this failed before?")
- You need to understand decision-making authority ("Who can approve Z?")

### When to Read Files Directly
**Read code/files when:**
- You need to understand implementation details
- You're developing a feature
- You need the exact data schema
- You need to see actual code examples

### Who Should Use RAG
- **Program Directors** - Query for policies and procedures
- **AI Agents** - Automatically query for context before making decisions
- **New Team Members** - Onboarding: "How does this place work?"
- **Coordinators** - Check procedures before taking actions

---

## Technical Details

**Embedding Model:** all-MiniLM-L6-v2
A lightweight, efficient semantic search model. Converts text to 384-dimensional vectors, enabling "fuzzy" searches that understand meaning rather than just keyword matching.

**Vector Index Status:** Ready
All 148 documents are indexed and searchable. Index is in memory, searchable in <100ms.

**Index Health:** No issues detected. All documents properly vectorized.

---

## Recommendations

### High Priority (Next Session)
1. **Add Troubleshooting Guide** - "What does this error mean and how do I fix it?" Common issues:
   - Schedule generation timeouts
   - Constraint conflicts
   - Swap validation failures
   - Report generation errors

2. **Expand Session Learnings** - Capture this session's discoveries. What was tried? What worked? What failed?

### Medium Priority (Next 2-4 Weeks)
3. **Performance Tuning Guide** - How to trade off schedule generation speed vs. fairness/quality

4. **Integration Map** - Visual/textual guide to how components interact:
   - Schedule generator → Validator → Database
   - Swap request → Validator → Approval → Scheduler update
   - Conflict detector → Resolution suggestions

5. **Historical Decisions Archive** - Why were certain architectural choices made? (This helps future developers understand design rationale)

### Low Priority (Optional)
6. **Advanced Concepts Deep-Dives** - Expanded explanations of Tensegrity, Stigmergy, etc. for developers

7. **Operator Runbooks** - Step-by-step guides for 10 most common tasks

---

## Summary

The RAG system is **functioning well** and contains the institutional knowledge needed to run the scheduler effectively. The knowledge base emphasizes decision-making procedures, compliance rules, and system resilience—reflecting the program's priorities.

**Recommendations:** Focus on adding troubleshooting guides and capturing lessons learned from ongoing sessions. These will make the system more immediately useful for operators facing novel problems.

For questions about specific topics, query RAG directly. For implementation details, read the code.

---

*Historian Report | Residency Scheduler Project*
*RAG System Version: 1.0 (healthy, 148 docs, 12 categories)*
