# ORCHESTRATOR Spec Handoff: Seamless Subagent Launch

Date: 2026-01-18
Purpose: Explain how a prepared AgentSpec can be handed off for ORCHESTRATOR to launch a subagent seamlessly, plus constraints and recommended workflow.

## Concept (Plain Language)
A tool can prepare a subagent **AgentSpec** (identity + injected RAG + mission + tool access). ORCHESTRATOR can then take over and launch the subagent using that spec without re‑writing the prompt. This is the cleanest bridge between “preparation” and “execution.”

## What Exists Today
- `spawn_agent_tool` **prepares** an AgentSpec but does not execute it.
- Execution requires a `Task()` call, which must be run by the ORCHESTRATOR runtime.
- The spec includes: `full_prompt`, `model`, `max_turns`, `tools_access`, `checkpoint_path`, and `escalation_target`.

## Seamless Handoff Workflow
1) **Preparation (this environment)**
   - Call `spawn_agent_tool` with agent name + mission (+ optional context).
   - Save the returned spec to a scratchpad file.

2) **Handoff (ORCHESTRATOR runtime)**
   - ORCHESTRATOR reads the spec file.
   - ORCHESTRATOR runs `Task()` using the spec as‑is.

3) **Review**
   - The subagent writes results to the specified checkpoint path.
   - ORCHESTRATOR reviews output and synthesizes.

## Constraints to Surface
- **Spawn chain validation:**
  - If `parent_agent` is set and not authorized, spec creation may fail.
  - Because ORCHESTRATOR is not listed in `.claude/agents.yaml`, use a Deputy (ARCHITECT/SYNTHESIZER) as `parent_agent`, or omit `parent_agent`.

- **Model selection:**
  - Model is selected by the agent entry in `.claude/agents.yaml` (opus/sonnet/haiku).
  - No ad‑hoc model overrides unless the registry is updated.

- **Execution boundary:**
  - This environment can **prepare** specs, but cannot execute `Task()`.

## Recommended SOP
- **Default:**
  - Prepare spec here → ORCHESTRATOR reads + launches.
- **If spawn chain blocks ORCHESTRATOR:**
  - Use `parent_agent=SYNTHESIZER` or `ARCHITECT` for spec generation.
- **If RAG is down:**
  - Use local doc pointers in the mission context; avoid RAG‑dependent instructions.

## Example Handoff Artifact (Human‑Readable)
```
Spec File: .claude/Scratchpad/AGENT_SPEC_SCHEDULER_20260118.md
- agent_name: SCHEDULER
- model: haiku
- max_turns: 5
- full_prompt: [identity + injected RAG + mission]
- checkpoint_path: .claude/Scratchpad/AGENT_SCHEDULER_20260118_153000.md
```

## Suggested Improvements
1) **Add ORCHESTRATOR to `.claude/agents.yaml`**
   - Makes spawn chain validation explicit and reduces confusion.

2) **Create a “Spec Queue” directory**
   - Standard place for prepared specs: `.claude/Scratchpad/specs/`.

3) **Add a tiny launcher helper**
   - A script or note that ORCHESTRATOR can run: `Task(prompt=spec.full_prompt, ...)`.

4) **Document exceptions**
   - Explicitly list USASOC/user overrides + built‑in subagent types as exceptions.

## Bottom Line
Prepared AgentSpecs allow a clean split between preparation and execution. With a consistent handoff folder and a documented launch step, ORCHESTRATOR can take over seamlessly and run the subagent without re‑authoring the prompt.
