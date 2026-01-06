# MCP Armory

> **Specialized Tool Storage for Advanced Analysis**

The armory contains 50+ exotic MCP tools organized by scientific domain. These tools are **not loaded by default** to reduce cognitive clutter and API surface area. Activate them on-demand when deep analysis is required.

---

## Purpose

The core MCP toolset (~34 tools) handles 95% of scheduling operations:
- Schedule validation and conflict detection
- Swap analysis and execution
- Basic resilience monitoring (N-1/N-2, defense levels)
- Deployment and background tasks

The **armory** contains specialized tools for:
- Deep scientific analysis (physics, biology analogies)
- Advanced optimization (game theory, operations research)
- Detailed fatigue modeling (component-level FRMS)
- Research-grade resilience metrics

**Philosophy:** Keep the everyday toolkit lean. Reach into the armory when you need a specialized instrument.

---

## Activation Methods

### Method 1: Environment Variable

```bash
# Activate specific domains
export ARMORY_DOMAINS="physics,biology"

# Activate all armory tools
export ARMORY_DOMAINS="all"

# Deactivate (default)
unset ARMORY_DOMAINS
```

### Method 2: Skill-Based Activation

```
/armory physics          # Load physics domain tools
/armory biology          # Load biology domain tools
/armory all              # Load entire armory
/armory status           # Show loaded domains
```

### Method 3: Programmatic (Python)

```python
from scheduler_mcp.armory import load_domain, unload_domain

load_domain("physics")
load_domain("operations_research")
# ... do analysis ...
unload_domain("physics")
```

---

## Domain Index

| Domain | Tools | Description |
|--------|-------|-------------|
| [physics/](physics/) | 12 | Thermodynamics, Hopfield networks, time crystals |
| [biology/](biology/) | 14 | Epidemiology, immune systems, gene regulation |
| [operations_research/](operations_research/) | 10 | Queuing theory, game theory, signal processing |
| [resilience_advanced/](resilience_advanced/) | 8 | Homeostasis, cognitive load, stigmergy |
| [fatigue_detailed/](fatigue_detailed/) | 6 | Low-level FRMS components |

**Total:** ~50 specialized tools

---

## When to Use Armory vs Core Tools

### Use Core Tools When:
- Validating daily schedules
- Processing swap requests
- Monitoring basic compliance (ACGME hours)
- Running routine resilience checks
- Deploying or rolling back

### Use Armory Tools When:
- Investigating complex system instabilities
- Performing root cause analysis on burnout patterns
- Optimizing long-term scheduling strategies
- Generating research-grade metrics for reporting
- Building predictive models for workforce planning

---

## Tool Migration Path

Tools graduate from armory to core based on:
1. **Usage frequency** - If used daily, promote to core
2. **Proven value** - Validated against real scheduling outcomes
3. **Stability** - API and implementation mature

Tools may also be **retired** if:
- Never used in 6+ months
- Superseded by better approaches
- Too complex for practical value

---

## Contributing New Tools

1. Identify the appropriate domain
2. Create tool module in domain directory
3. Add to domain README.md
4. Test with `pytest mcp-server/tests/armory/`
5. Document activation requirements

See individual domain READMEs for tool specifications.

---

## Architecture Note

Armory tools share the same MCP infrastructure as core tools:
- Same authentication/authorization
- Same database connections
- Same response formats
- Same error handling

The only difference is **loading behavior** - armory tools require explicit activation.
