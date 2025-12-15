# GraphQL Layer – Risk/Benefit Analysis for Future Consideration

> **Status**: Future consideration only. Not for immediate implementation.
>
> **Rationale**: The project serves diverse users—from power users to technically adept Gen Z developers to career professionals comfortable with Excel. Any API evolution must account for this spectrum.

## Summary Recommendation

For this project, a GraphQL layer is **optional, not foundational**. It can add real value once we have multiple consumers (web UI, agents, dashboards) and more complex read patterns, but it also introduces non-trivial complexity in operations and performance.

**Short term:** keep the core API as well-structured REST/JSON.
**Medium term:** consider adding GraphQL as a thin read/write façade if and when we feel pain around endpoint proliferation or diverse client needs.

---

## Potential Benefits

### 1. Single, self-describing contract for all clients

- GraphQL exposes a strongly-typed schema that frontends, scripts, and AI agents can introspect.
- This is particularly valuable for a "vibe-coded scheduler" where different tools (web UI, CLI, agents) may want different slices of the same domain graph: programs → blocks → rotations → assignments → residents → absences.
- Schema introspection lets tools discover available queries and mutations (`generateSchedule`, `simulateScheduleChanges`, `exportScheduleToExcel`) without hard-coding every endpoint shape.

### 2. Flexible, efficient data fetching for rich UIs

- A future admin UI or chief-resident dashboard may need highly customized views:
  - Example: "for Program X, show Blocks 3–5 with FM Inpatient coverage, duty-hour violations, and load scores, but only for PGY1s."
- GraphQL lets the frontend specify exactly which fields and relationships it needs in one request, instead of us designing a new REST endpoint (or multiple endpoints) for every variant.
- This reduces "REST sprawl" where we accumulate many slightly different endpoints over time.

### 3. Better fit for agents and automation clients

- AI agents interacting with the scheduler benefit from a graph-style API: they can query deeply nested structures and request only the fields needed for reasoning.
- This aligns with the project's long-term goal of having agents autonomously:
  - generate schedules,
  - simulate changes in response to deployments/leave,
  - and inspect fairness/coverage metrics.
- GraphQL's type system gives agents reliable structure (e.g., `Schedule`, `Assignment`, `FairnessSummary`) instead of ad hoc JSON blobs.

### 4. Easier evolution of the data model

- As the scheduling engine grows (more rules, new views like wellness scores or educational metrics), GraphQL supports:
  - adding fields without breaking existing queries,
  - deprecating fields via schema annotations.
- This can reduce upgrade friction as we iterate on the domain model.

---

## Risks and Costs

### 1. Operational and architectural complexity

- Adding GraphQL means:
  - a new server layer (or gateway) to deploy and maintain,
  - learning and enforcing a schema discipline on top of the existing REST/JSON API,
  - additional tooling (schema generation, validation, testing).
- For a project that already has non-trivial complexity (auth, optimization logic, caching, Excel export), this is another moving part that can fail.

### 2. Performance pitfalls in a scheduling/optimization context

- Naive resolvers can lead to N+1 queries and expensive nested fetches, especially with graphs like:
  - `program → schedules → assignments → resident → absences`.
- Without careful batching and caching, GraphQL can become a performance bottleneck or amplify underlying inefficiencies.
- The scheduling engine's main cost is the optimization step itself; GraphQL doesn't make that cheaper, and can add overhead on top of it.

### 3. Security, authz, and data leakage risk

- GraphQL's flexibility cuts both ways:
  - If authz is not strictly enforced at the field/type level, a client could query data it shouldn't see (e.g., viewing all absences, load scores, or other sensitive fields).
- We would need a clear authorization strategy:
  - role-based access per operation and sometimes per field,
  - defense against introspecting or calling internal-only operations.

### 4. Limited benefit for the current primary output (Excel)

- The current system's main deliverable is an exported Excel schedule for non-technical users.
- That Excel flow interacts with the backend in a fairly coarse-grained way:
  - "generate schedule," "export schedule to Excel."
- GraphQL does not materially improve this path; Excel consumers don't care about flexible querying.

### 5. Risk of over-investing in infrastructure before it's needed

- Time spent designing, implementing, and tuning a GraphQL layer is time not spent:
  - improving the scheduling algorithm,
  - refining absence/deployment handling,
  - hardening testing and error handling,
  - or simplifying the Excel export pipeline.
- If endpoint and client diversity remain modest, the return on a full GraphQL layer may not justify its complexity.

---

## When GraphQL *Would* Make Sense

Add (or seriously consider) a GraphQL façade when **all** of the following are true:

1. **Multiple heterogeneous clients exist or are planned**
   - Examples:
     - Rich web dashboard for PD/APD/chiefs,
     - separate resident-facing portal with personalized schedule views,
     - AI agents that orchestrate schedule runs and simulations,
     - possibly other institutional systems needing schedule data.

2. **We see real pain around REST proliferation**
   - Symptoms:
     - Many versioned endpoints for similar schedule views,
     - frequent "can you add X to this response" changes,
     - complex custom endpoints for bespoke reporting.

3. **There is a clear plan for performance and authz**
   - Batching and caching in resolvers (e.g., via DataLoader-style patterns).
   - Well-defined role-based restrictions on types, fields, and operations.
   - Monitoring around expensive or abusive queries.

At that point, a *thin* GraphQL layer that maps directly onto existing domain services can provide real leverage without becoming the core of the system.

---

## Recommended Stance for This Project

### Now / near-term

- Keep REST/JSON as the primary interface.
- Design endpoints with clear, stable contracts that could later be mirrored in a GraphQL schema.
- Avoid decisions that would make a future GraphQL layer hard (e.g., extremely ad hoc response shapes).

### Later / when conditions are met

- Introduce a small GraphQL schema focused on:
  - reading complex, nested schedule views,
  - invoking key domain operations (`generateSchedule`, `simulateScheduleChanges`, `exportScheduleToExcel`).
- Treat GraphQL as a façade, not as the source of truth for business logic.
- Incrementally migrate high-value read use cases (dashboards, agent workflows) to GraphQL, while keeping the REST API for simpler integrations and Excel export.

---

## Conclusion

**GraphQL is a useful future option, not an immediate requirement.** It should be adopted only when client diversity and data access patterns are complex enough that the benefits of a typed, queryable graph outweigh the added complexity in deployment, performance tuning, and security.
