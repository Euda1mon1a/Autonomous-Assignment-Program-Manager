# Roadmap: Foam Topology Scheduler (Natural Swaps)

**Date:** February 25, 2026
**Target:** Implement Phase 1 & 2 of the Foam Topology Scheduler based on the Penn Engineering Foam Bubble Research paradigm.
**Objective:** Deliver "Natural Swap" recommendations to the frontend, drastically reducing the cognitive load required for coordinators to manually fix broken schedules or accommodate ad-hoc requests.

---

## 1. Core Concept & Value Proposition

When a scheduling conflict occurs or a resident needs a sudden change, human coordinators struggle to find valid trades because they cannot visualize the high-dimensional constraint space.

The **Foam Topology Scheduler** maps assignments as "bubbles" and constraints as the "films" between them. When a constraint is near its limit, the film area shrinks. When it reaches zero, a "T1 Event" occurs—this is a mathematical guarantee that a swap is topologically natural and safe.

By implementing this, we give coordinators a "Suggested Swaps" button that instantly provides 3-5 mathematically verified, low-friction shift trades.

---

## 2. Implementation Roadmap

### Phase 1: Foundational Physics Engine (Backend)
**Goal:** Build the core mathematics to represent a schedule as a foam structure.

*   **Task 1.1: Core Data Structures**
    *   Implement `FoamCell` (Bubble): Represents an assignment (Resident + Time Block).
    *   Implement `FoamFilm` (Interface): Represents the shared constraint boundary between two cells.
    *   Implement `T1Event` (Swap): Represents the topological rearrangement (the actual swap).
    *   *Location:* `backend/app/resilience/exotic/foam_topology.py`
*   **Task 1.2: State Conversion Engine**
    *   Write the adapter that takes the current `Schedule` object and converts it into a `FoamStructure`.
    *   Map `Assignments` to `FoamCells`.
    *   Map `Constraints` (e.g., duty hours, required rotations) to `FoamFilms`. Calculate initial film "area" based on the remaining slack in the constraint.
*   **Task 1.3: Pressure & Diffusion Calculation**
    *   Calculate internal cell pressure based on resident workload/fatigue.
    *   Implement basic diffusion: simulated flow of workload pressure across films to equalize stress.

### Phase 2: Natural Swap Detection (Backend)
**Goal:** Identify T1 events and expose them via an API.

*   **Task 2.1: T1 Event Detection Algorithm**
    *   Implement logic to scan the `FoamStructure` for films whose area is below the `t1_threshold`.
    *   Validate that a swap (T1 event) between the adjacent cells lowers the overall local energy (reduces constraint pressure).
*   **Task 2.2: Safety Validation Layer**
    *   Ensure that proposed T1 swaps do not violate hard ACGME constraints (e.g., breaking minimum time off between shifts).
*   **Task 2.3: API Endpoint Creation**
    *   Create `GET /api/v1/schedules/{schedule_id}/natural-swaps`
    *   Return a ranked list of `SwapRecommendation` objects, sorted by their "Naturalness Score" (how close the film area is to 0).

### Phase 3: Frontend Integration & Visualization (Frontend)
**Goal:** Surface the recommendations to the user in an actionable UI.

*   **Task 3.1: Natural Swap UI Component**
    *   Create a React component (`NaturalSwapPanel.tsx`) to display the ranked list of suggested trades.
    *   Include metrics for each suggestion: "Energy Improvement" and "Naturalness".
*   **Task 3.2: Integration with Coordinator Dashboard**
    *   Embed the swap panel into the main schedule management view. When a coordinator clicks on an assignment, instantly query the API for natural swaps involving that cell.
*   **Task 3.3 (Optional/Stretch): 3D Foam Visualization**
    *   Implement `FoamTopologyViewer.tsx` using Three.js to visually render the bubbles and films, allowing the user to literally *see* the pressure points in the schedule.

### Phase 4: MCP Tool Integration (Agentic Capabilities)
**Goal:** Allow autonomous agents to utilize foam topology to self-heal schedules.

*   **Task 4.1: Create MCP Tools**
    *   Implement `analyze_foam_structure`: Allows agents to query the health/pressure of the schedule.
    *   Implement `detect_natural_swaps`: Allows agents to request safe swaps.
    *   *Location:* `mcp-server/src/scheduler_mcp/tools/resilience/`
*   **Task 4.2: Update Agent Prompts**
    *   Instruct the scheduling and coordinator agents to utilize the foam topology tools when resolving conflicts, rather than attempting brute-force trial and error.

---

## 3. Technical Considerations & Risks

*   **Performance:** Converting a full 12-month schedule into a graph of cells and films could be computationally heavy. *Mitigation:* We should limit the foam analysis window to a rolling 4-to-8 week block around the target date.
*   **Constraint Mapping:** Translating complex business rules (like "Resident must do 2 weeks of nights in a 6 month period") into a geometric "film area" requires careful mathematical design. *Mitigation:* Start with simple, easily quantifiable constraints (e.g., weekly hours, shift gaps) before tackling complex longitudinal rules.
*   **UI Clutter:** We must ensure the "Naturalness Score" is translated into plain English for the end-user (e.g., "Highly Recommended", "Minimal Disruption").

---

## 4. Success Criteria

1.  **Backend:** The `FoamTopologyScheduler` can take a valid schedule, convert it to a foam structure, and return at least 1 valid swap candidate in under 500ms.
2.  **Accuracy:** 100% of suggested T1 swaps must pass standard ACGME hard-constraint validation.
3.  **Frontend:** The coordinator can execute a natural swap with 2 clicks or fewer from the main dashboard.
