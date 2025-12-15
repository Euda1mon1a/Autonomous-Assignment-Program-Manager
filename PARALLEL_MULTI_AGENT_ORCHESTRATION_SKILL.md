***REMOVED*** Skill: Parallel Multi-Agent Task Orchestration for Software Development

***REMOVED******REMOVED*** Overview
This skill enables orchestrating multiple AI coding agents (Claude Code instances) in parallel to complete complex software development projects efficiently through strategic task decomposition, strict file ownership, and sequential PR merging.

***REMOVED******REMOVED*** Core Competencies

***REMOVED******REMOVED******REMOVED*** 1. Strategic Task Decomposition
- Break down complex projects into N parallel workstreams (typically 3-5)
- Assign non-overlapping file territories to prevent merge conflicts
- Ensure each agent has a complete, self-contained task
- Balance workload across agents based on complexity

***REMOVED******REMOVED******REMOVED*** 2. Parallel Execution Management
- Spin up N Claude Code sessions simultaneously
- Paste specialized prompts into each session
- Submit all sessions at once for true parallel execution
- Monitor progress across all sessions
- Track completion status and identify blockers

***REMOVED******REMOVED******REMOVED*** 3. Strict File Ownership Protocol
**Critical Success Factor**: Each agent must have exclusive ownership of specific files

**Ownership Rules:**
- List all files each agent will CREATE or UPDATE
- No two agents touch the same file
- If file access is needed, designate ONE agent as owner
- Document ownership in prompts clearly

**Example Ownership Distribution:**
```
Agent 1 (API): backend/routes/api.py, backend/models/api.py
Agent 2 (UI): frontend/components/Dashboard.tsx, frontend/pages/dashboard.tsx
Agent 3 (Docs): README.md, docs/API.md, CONTRIBUTING.md
Agent 4 (Tests): tests/api.test.ts, tests/ui.test.tsx
Agent 5 (Config): docker-compose.yml, .env.example, Dockerfile
```

***REMOVED******REMOVED******REMOVED*** 4. PR Creation and Sequential Merging
**After all agents complete:**
1. Each agent creates a PR from their branch
2. Merge PRs in strategic order to minimize conflicts:
   - Documentation first (no code conflicts)
   - Foundation/infrastructure next
   - Feature implementations
   - Integration features last

**Merge Order Strategy:**
- Docs → Config → Backend → Frontend → Integration
- Less dependent → More dependent
- Foundational → Feature-specific

***REMOVED******REMOVED******REMOVED*** 5. Prompt Engineering for Parallel Agents

**Essential Prompt Components:**
```markdown
You are [AGENT_NAME]. Your task is to [SPECIFIC_GOAL].

STRICT FILE OWNERSHIP - Only modify files in these paths:
- [file1] (CREATE/UPDATE)
- [file2] (CREATE/UPDATE)
- [file3] (CREATE/UPDATE)

IMPLEMENTATION REQUIREMENTS:
[Detailed specifications]

DO NOT modify any other files.
Commit with prefix: [AGENT_PREFIX]
```

**Key Elements:**
- Clear agent identity and role
- Explicit file ownership list
- CREATE vs UPDATE distinction
- Detailed implementation requirements
- Commit message prefix for tracking
- Strict boundary enforcement

***REMOVED******REMOVED*** Workflow Pattern

***REMOVED******REMOVED******REMOVED*** Phase 1: Planning
1. Analyze project requirements
2. Identify parallelizable workstreams
3. Define file ownership boundaries
4. Create prompt file with all agent prompts
5. Determine merge order

***REMOVED******REMOVED******REMOVED*** Phase 2: Execution
1. Open N Claude Code tabs/sessions
2. Paste prompts simultaneously
3. Submit all sessions (cmd+Return × N)
4. Monitor progress (periodic screenshots)
5. Verify no file conflicts occurring

***REMOVED******REMOVED******REMOVED*** Phase 3: Integration
1. Wait for all agents to complete
2. Review all PRs for completeness
3. Merge PRs in predetermined order
4. Verify each merge completes cleanly
5. Confirm final integration works

***REMOVED******REMOVED*** Success Metrics

***REMOVED******REMOVED******REMOVED*** Efficiency Gains
- **Time Reduction**: N agents working in parallel = ~N× speedup
- **Example**: 5 agents complete 5 tasks in parallel vs sequential
  - Sequential: 5 × 20min = 100min
  - Parallel: max(20min) = ~25min (with overhead)
  - Speedup: 4× faster

***REMOVED******REMOVED******REMOVED*** Quality Indicators
- Zero merge conflicts (from strict file ownership)
- All PRs merge cleanly
- Each agent stays within territory
- Complete feature implementation
- Comprehensive commit history

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Feature Decomposition
**Use Case**: Large application with multiple features
```
Agent 1: Authentication system
Agent 2: Dashboard UI
Agent 3: Data export
Agent 4: API documentation
Agent 5: Deployment config
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Layer-Based Distribution
**Use Case**: Full-stack application
```
Agent 1: Database models + migrations
Agent 2: Backend API routes
Agent 3: Frontend components
Agent 4: Frontend pages
Agent 5: Testing suite
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Enhancement Rounds
**Use Case**: Adding polish to existing app
```
Agent 1: Performance optimization
Agent 2: Accessibility improvements
Agent 3: Error handling
Agent 4: Loading states
Agent 5: Form validation
```

***REMOVED******REMOVED*** Anti-Patterns to Avoid

***REMOVED******REMOVED******REMOVED*** ❌ Shared File Access
**Problem**: Two agents modifying same file
**Result**: Merge conflicts, wasted work
**Solution**: Assign each file to exactly ONE agent

***REMOVED******REMOVED******REMOVED*** ❌ Unclear Boundaries
**Problem**: Vague task definitions, overlapping responsibilities
**Result**: Duplicate work, conflicts
**Solution**: Explicit file lists and clear scope

***REMOVED******REMOVED******REMOVED*** ❌ Sequential Bottlenecks
**Problem**: Agent dependencies (Agent B needs Agent A's output)
**Result**: Parallel execution breaks down
**Solution**: Ensure true parallelism - no inter-agent dependencies

***REMOVED******REMOVED******REMOVED*** ❌ Wrong Merge Order
**Problem**: Merging dependent PR before foundation
**Result**: Conflicts, failed builds
**Solution**: Plan merge order upfront (foundation → features)

***REMOVED******REMOVED*** Advanced Techniques

***REMOVED******REMOVED******REMOVED*** Technique 1: Round-Based Iteration
**Use**: Large projects requiring multiple passes
```
Round 1: Core features (Agents 1-5)
Round 2: Enhancements (Agents 1-5)
Round 3: Polish (Agents 1-5)
Round 4: Production ready (Agents 1-5)
```

***REMOVED******REMOVED******REMOVED*** Technique 2: Commit Prefix Tracking
**Use**: Identifying which agent made which changes
```
[Opus-API] Add authentication endpoints
[Opus-UI] Create dashboard components
[Opus-Docs] Update API documentation
[Opus-Tests] Add E2E test coverage
[Opus-Config] Add Docker configuration
```

***REMOVED******REMOVED******REMOVED*** Technique 3: Territory Expansion
**Use**: Starting narrow, expanding scope in later rounds
```
Round 1: 3 agents, core features
Round 2: 5 agents, more features
Round 3: 5 agents, polish + docs
```

***REMOVED******REMOVED*** Tool Integration

***REMOVED******REMOVED******REMOVED*** Browser Automation
- Open multiple Claude Code tabs programmatically
- Paste prompts via browser automation
- Monitor progress with screenshots
- Navigate GitHub for PR creation/merging

***REMOVED******REMOVED******REMOVED*** Status Tracking
```markdown
***REMOVED******REMOVED*** Round N Status
- Terminal 1 (Agent-Name): ✅ Completed | 🔄 Running | ⏳ Pending
- Terminal 2 (Agent-Name): Status
- Terminal 3 (Agent-Name): Status
- Terminal 4 (Agent-Name): Status
- Terminal 5 (Agent-Name): Status
```

***REMOVED******REMOVED******REMOVED*** PR Management
```markdown
***REMOVED******REMOVED*** PR Merge Order
1. PR ***REMOVED***X (Agent-Name) - Foundation
2. PR ***REMOVED***Y (Agent-Name) - Core feature
3. PR ***REMOVED***Z (Agent-Name) - Integration
4. PR ***REMOVED***W (Agent-Name) - Polish
5. PR ***REMOVED***V (Agent-Name) - Deployment
```

***REMOVED******REMOVED*** Real-World Example: Residency Scheduler (6 Rounds)

***REMOVED******REMOVED******REMOVED*** Round 1: Foundation (3 agents)
- Agent 1: Database models
- Agent 2: API routes
- Agent 3: Frontend setup

***REMOVED******REMOVED******REMOVED*** Round 2: Features (3 agents)
- Agent 1: People management
- Agent 2: Schedule UI
- Agent 3: Authentication

***REMOVED******REMOVED******REMOVED*** Round 3: Core Features (5 agents)
- Agent 1: Absences
- Agent 2: Dashboard
- Agent 3: Navigation
- Agent 4: Testing
- Agent 5: Auth routes

***REMOVED******REMOVED******REMOVED*** Round 4: Backend (5 agents)
- Agent 1: Fix tests
- Agent 2: Auth context
- Agent 3: Route protection
- Agent 4: Error handling
- Agent 5: Settings API

***REMOVED******REMOVED******REMOVED*** Round 5: Polish (5 agents)
- Agent 1: Form validation
- Agent 2: Loading states
- Agent 3: Accessibility
- Agent 4: Performance
- Agent 5: E2E tests

***REMOVED******REMOVED******REMOVED*** Round 6: Production (5 agents)
- Agent 1: Docker config
- Agent 2: API docs
- Agent 3: Error messages
- Agent 4: Data export
- Agent 5: README

**Results**:
- 41 PRs merged
- 0 merge conflicts
- 100% feature completion
- Production-ready application

***REMOVED******REMOVED*** Key Principles

1. **Parallelism Over Sequence**: When possible, run in parallel
2. **Strict Boundaries**: Clear file ownership prevents conflicts
3. **Strategic Merging**: Order matters for clean integration
4. **Clear Communication**: Explicit prompts with exact requirements
5. **Monitoring**: Track progress to identify issues early
6. **Territory Respect**: Agents never cross boundaries
7. **Round-Based**: Iterate in phases for large projects

***REMOVED******REMOVED*** When to Use This Skill

**Ideal Scenarios:**
✅ Large projects with clear component boundaries
✅ Multiple independent features to build
✅ Time-sensitive projects requiring fast completion
✅ Well-defined requirements and specifications
✅ Projects with minimal inter-component dependencies

**Not Recommended:**
❌ Small projects (overhead not worth it)
❌ Highly interdependent components
❌ Unclear requirements
❌ Exploratory/prototype work
❌ Single-file changes

***REMOVED******REMOVED*** Conclusion

Parallel Multi-Agent Task Orchestration transforms software development by enabling true concurrent execution through strategic task decomposition and strict boundary enforcement. When applied correctly, this skill can reduce development time by N× while maintaining zero merge conflicts and high code quality.

The key to success is planning: define clear territories, ensure no overlap, and execute in parallel. The results speak for themselves - complex applications built faster, cleaner, and with better organization.
