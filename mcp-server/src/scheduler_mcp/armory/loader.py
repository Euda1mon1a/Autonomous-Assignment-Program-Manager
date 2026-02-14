"""
Armory Loader - Conditional loading of specialized MCP tools.

The armory contains ~50 exotic MCP tools organized by scientific domain.
These tools are not loaded by default to reduce cognitive clutter.

Activation Methods:
1. Environment variable: ARMORY_DOMAINS="physics,biology" or "all"
2. Programmatic: load_domain("physics")

Domains:
- physics: Thermodynamics, Hopfield networks, time crystals (12 tools)
- biology: Epidemiology, immune system, gene regulation (14 tools)
- operations_research: Queuing theory, game theory, Six Sigma (10 tools)
- resilience_advanced: Homeostasis, cognitive load, stigmergy (8 tools)
- fatigue_detailed: Low-level FRMS components (6 tools)
"""

import logging
import os
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Track which domains are loaded
_loaded_domains: Set[str] = set()

# Domain definitions - maps domain name to list of tool function names
DOMAIN_TOOLS: Dict[str, List[str]] = {
    "physics": [
        # Thermodynamics
        "calculate_schedule_entropy_tool",
        "get_entropy_monitor_state_tool",
        "analyze_phase_transitions_tool",
        "optimize_free_energy_tool",
        # Hopfield
        "calculate_hopfield_energy_tool",
        "find_nearby_attractors_tool",
        "measure_basin_depth_tool",
        "detect_spurious_attractors_tool",
        "analyze_energy_landscape_tool",
        # Time Crystal
        "analyze_schedule_periodicity_tool",
        "calculate_time_crystal_objective_tool",
        "get_checkpoint_status_tool",
        "get_time_crystal_health_tool",
    ],
    "biology": [
        # Epidemiology
        "calculate_burnout_rt_tool",
        "simulate_burnout_spread_tool",
        "simulate_burnout_contagion_tool",
        # Immune System
        "assess_immune_response_tool",
        "check_memory_cells_tool",
        "analyze_antibody_response_tool",
        # Gene Regulation
        "analyze_transcription_triggers_tool",
        # Materials Science
        "assess_creep_fatigue_tool",
        "calculate_recovery_distance_tool",
    ],
    "operations_research": [
        # Queuing Theory
        "optimize_erlang_coverage_tool",
        "calculate_erlang_metrics_tool",
        # Game Theory
        "calculate_shapley_workload_tool",
        # Signal Processing
        "detect_schedule_changepoints_tool",
        "detect_critical_slowing_down_tool",
        # Six Sigma
        "calculate_process_capability_tool",
        "calculate_equity_metrics_tool",
        "generate_lorenz_curve_tool",
    ],
    "resilience_advanced": [
        # Homeostasis
        "analyze_homeostasis_tool",
        "analyze_le_chatelier_tool",
        # Cognitive Load
        "assess_cognitive_load_tool",
        # Stigmergy
        "get_behavioral_patterns_tool",
        "analyze_stigmergy_tool",
        # Blast Radius
        "calculate_blast_radius_tool",
        "analyze_hub_centrality_tool",
    ],
    "fatigue_detailed": [
        # Core Components
        "get_fatigue_score_tool",
        "analyze_sleep_debt_tool",
        "evaluate_fatigue_hazard_tool",
        # Fire Danger
        "calculate_fire_danger_index_tool",
        "calculate_batch_fire_danger_tool",
        # Early Warning
        "detect_burnout_precursors_tool",
        "predict_burnout_magnitude_tool",
        "run_spc_analysis_tool",
        "calculate_workload_process_capability_tool",
    ],
}

# All armory tool names (for quick lookup)
ALL_ARMORY_TOOLS: Set[str] = set()
for tools in DOMAIN_TOOLS.values():
    ALL_ARMORY_TOOLS.update(tools)


def get_enabled_domains() -> List[str]:
    """Get list of domains enabled via environment variable."""
    env_value = os.environ.get("ARMORY_DOMAINS", "").strip()
    if not env_value:
        return []
    if env_value.lower() == "all":
        return list(DOMAIN_TOOLS.keys())
    return [d.strip() for d in env_value.split(",") if d.strip() in DOMAIN_TOOLS]


def is_armory_tool(tool_name: str) -> bool:
    """Check if a tool name is an armory tool."""
    return tool_name in ALL_ARMORY_TOOLS


def should_load_tool(tool_name: str) -> bool:
    """
    Determine if a tool should be loaded.

    Returns True if:
    - Tool is NOT an armory tool (always load core tools)
    - Tool IS an armory tool AND its domain is enabled
    """
    if tool_name not in ALL_ARMORY_TOOLS:
        return True  # Core tool, always load

    enabled = get_enabled_domains()
    for domain, tools in DOMAIN_TOOLS.items():
        if tool_name in tools and domain in enabled:
            return True
    return False


def get_armory_tools_for_domain(domain: str) -> List[str]:
    """Get list of tool names for a specific domain."""
    return DOMAIN_TOOLS.get(domain, [])


def load_domain(domain: str) -> bool:
    """
    Mark a domain as loaded (for runtime activation).

    Note: This only affects should_load_tool() checks for future registrations.
    Already-registered tools are not affected.
    """
    if domain not in DOMAIN_TOOLS and domain != "all":
        logger.warning(f"Unknown armory domain: {domain}")
        return False

    if domain == "all":
        _loaded_domains.update(DOMAIN_TOOLS.keys())
    else:
        _loaded_domains.add(domain)

    logger.info(f"Armory domain loaded: {domain}")
    return True


def unload_domain(domain: str) -> bool:
    """Mark a domain as unloaded."""
    if domain == "all":
        _loaded_domains.clear()
    else:
        _loaded_domains.discard(domain)
    return True


def get_loaded_domains() -> List[str]:
    """Get list of currently loaded domains."""
    return list(_loaded_domains | set(get_enabled_domains()))


def get_armory_status() -> Dict:
    """Get current armory status for debugging/display."""
    enabled = get_enabled_domains()
    return {
        "env_enabled_domains": enabled,
        "runtime_loaded_domains": list(_loaded_domains),
        "effective_domains": get_loaded_domains(),
        "total_armory_tools": len(ALL_ARMORY_TOOLS),
        "tools_by_domain": {d: len(t) for d, t in DOMAIN_TOOLS.items()},
    }


# Log armory status on import
_enabled = get_enabled_domains()
if _enabled:
    logger.info(f"Armory domains enabled via env: {_enabled}")
else:
    logger.debug("No armory domains enabled (set ARMORY_DOMAINS to activate)")
