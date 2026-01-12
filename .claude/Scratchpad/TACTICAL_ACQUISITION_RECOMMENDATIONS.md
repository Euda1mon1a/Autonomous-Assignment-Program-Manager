# Tactical Acquisition Advisory: Upgrading the Parallel Agent Infrastructure (PAI)

**Date:** 2026-01-11
**Objective:** Evolve the custom "Antigravity PAI" by tactically acquiring robust architectural patterns from leading open-source agent frameworks.

## Executive Summary

The current Antigravity setup is an advanced custom **Parallel Agent Infrastructure (PAI)** that exceeds "standard" usage. However, it relies on monolithic memory files (`ORCHESTRATOR_ADVISOR_NOTES.md`) and informal delegation protocols. To scale further, we recommend adopting specific patterns from **LangGraph**, **MemGPT**, and **OpenDevin**.

---

## 1. Upgrade from "Monolithic Memory" to "Tiered Memory" (MemGPT Pattern)

### The Current Bottleneck
`ORCHESTRATOR_ADVISOR_NOTES.md` is ~88KB and growing. Reading the entire history into the context window for every session is becoming token-expensive and inefficient (the "Goldfish Memory" vs "Context Overflow" trade-off).

### The Tactical Acquisition
Adopt **MemGPT's Tiered Memory Architecture**:

1.  **Core Memory (RAM)**:
    *   **File:** `.claude/memory/CORE_USER_PROFILE.md` (Small, < 2KB).
    *   **Content:** User preferences ("General of Armies"), Critical Rules ("No hallucinations"), Active Projects list.
    *   **Action:** Always read at startup.

2.  **Recall Memory (Journal)**:
    *   **File:** `.claude/memory/RECALL_JOURNAL.md` (Medium, < 10KB).
    *   **Content:** Summary of the *last 5 sessions* and *pending tasks*.
    *   **Action:** Updated by the agent at the end of every session.

3.  **Archival Memory (Disk)**:
    *   **Location:** `.claude/memory/archive/session_logs/`.
    *   **Content:** Full logs of past sessions (Session 001 - 092).
    *   **Action:** **Searchable on demand** via Vector Search (RAG) or Grep, but *not* loaded into context by default.

**Immediate Action:** Split `ORCHESTRATOR_ADVISOR_NOTES.md` into `CORE_PROFILE.md` and `ARCHIVED_NOTES/`.

---

## 2. Upgrade from "Delegation" to "State Machines" (LangGraph Pattern)

### The Current Bottleneck
Delegation is currently "conversational." The Orchestrator "asks" a subagent to do work, but if the subagent acts strangely or fails to verify, there is no rigid guardrail preventing the Orchestrator from accepting the bad result.

### The Tactical Acquisition
Adopt **LangGraph's Supervisor/State Machine Pattern**:

*   **Define Rigid States:** instead of "Look at this," define a `MISSION_GRAPH`:
    *   `STATE: PLAN` → (only transitions to) → `STATE: EXECUTE`
    *   `STATE: EXECUTE` → (only transitions to) → `STATE: VERIFY`
    *   `STATE: VERIFY` → (IF FAIL) → `STATE: REPAIR`
    *   `STATE: VERIFY` → (IF PASS) → `STATE: MERGE`

*   **Enforcement:** The Orchestrator *refuses* to merge code until the `VERIFY` agent explicitly returns a `status: "PASS"` JSON payload.

**Immediate Action:** Define a "Mission Protocol" file that explicitly maps these valid state transitions for complex tasks like Refactoring or PR Creation.

---

## 3. Upgrade from "Host Browser" to "Sandboxed Browser" (OpenDevin Pattern)

### The Current Bottleneck
The **ASTRONAUT** agent runs on the host machine. While powerful, it carries significant risk:
*   **Data Loss:** Accidental clicks on "Delete" buttons in Admin panels.
*   **Environment Damage:** Access to local file system via browser uploads.

### The Tactical Acquisition
Adopt **OpenDevin's Sandboxed Browser**:

*   **Pattern:** Run the browser (and the agent controlling it) inside a **Docker Container**.
*   **Benefit:** "God Mode" permissions. You can let the agent click *anything* to test it. If it deletes the database, you just restart the container.
*   **Isolation:** The agent cannot touch your actual `.env` files or local documents.

**Immediate Action:** Investigate wrapping the `browser` tool or the ASTRONAUT subagent in a containerized environment for high-risk regression testing.

---

## Summary of Recommendations

| Feature    | Current Antigravity       | Proposed Upgrade                     | Source        |
| :--------- | :------------------------ | :----------------------------------- | :------------ |
| **Memory** | Monolithic Markdown File  | **Tiered Memory** (Core vs. Archive) | **MemGPT**    |
| **Flow**   | Conversational Delegation | **State Graph** (Strict transitions) | **LangGraph** |
| **Safety** | Host-based Execution      | **Sandboxed Environment**            | **OpenDevin** |
