#!/usr/bin/env python3
"""End-to-end solver validation: run CP-SAT on historical blocks, compare to actual schedules.

For each target block, this script:
1. Snapshots the actual coordinator schedule (ground truth)
2. Runs the CP-SAT activity solver with calibrated constraints
3. Reads the solver's output (within the same transaction)
4. Rolls back — DB is never modified
5. Computes 3-tier quality metrics

Safety: The solver uses session.flush() (not commit), so we wrap each run
in a transaction and rollback after reading. The database is never modified.

Usage:
    cd ~/Autonomous-Assignment-Program-Manager
    backend/.venv/bin/python scripts/ml/validate_e2e.py --blocks 6,8,10
    backend/.venv/bin/python scripts/ml/validate_e2e.py --blocks 8 --weight-configs
"""

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# Add backend to path for solver imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import solver and utilities (requires backend on sys.path)
from app.scheduling.activity_solver import CPSATActivitySolver
from app.utils.academic_blocks import get_block_dates

# Penalty weight constants we'll monkey-patch for sensitivity analysis
import app.scheduling.activity_solver as solver_module

# Weight configs for Phase 6b sensitivity analysis
WEIGHT_CONFIGS = {
    "baseline": {
        "ACTIVITY_MIN_SHORTFALL_PENALTY": 10,
        "CLINIC_MIN_SHORTFALL_PENALTY": 25,
        "ACTIVITY_MAX_OVERAGE_PENALTY": 20,
        "CLINIC_MAX_OVERAGE_PENALTY": 40,
        "AT_COVERAGE_SHORTFALL_PENALTY": 50,
    },
    "clinic_heavy": {
        "ACTIVITY_MIN_SHORTFALL_PENALTY": 10,
        "CLINIC_MIN_SHORTFALL_PENALTY": 50,
        "ACTIVITY_MAX_OVERAGE_PENALTY": 20,
        "CLINIC_MAX_OVERAGE_PENALTY": 80,
        "AT_COVERAGE_SHORTFALL_PENALTY": 50,
    },
    "balanced": {
        "ACTIVITY_MIN_SHORTFALL_PENALTY": 25,
        "CLINIC_MIN_SHORTFALL_PENALTY": 25,
        "ACTIVITY_MAX_OVERAGE_PENALTY": 25,
        "CLINIC_MAX_OVERAGE_PENALTY": 25,
        "AT_COVERAGE_SHORTFALL_PENALTY": 25,
    },
    "coverage_dominant": {
        "ACTIVITY_MIN_SHORTFALL_PENALTY": 10,
        "CLINIC_MIN_SHORTFALL_PENALTY": 25,
        "ACTIVITY_MAX_OVERAGE_PENALTY": 20,
        "CLINIC_MAX_OVERAGE_PENALTY": 40,
        "AT_COVERAGE_SHORTFALL_PENALTY": 100,
    },
}

# SQL to snapshot HDAs with activity codes for a date range
SNAPSHOT_SQL = text("""
    SELECT
        hda.person_id::text,
        hda.date,
        hda.time_of_day,
        a.code AS activity_code,
        hda.source,
        p.name AS person_name,
        p.type AS person_type
    FROM half_day_assignments hda
    LEFT JOIN activities a ON hda.activity_id = a.id
    LEFT JOIN people p ON hda.person_id = p.id
    WHERE hda.date >= :start_date AND hda.date <= :end_date
    ORDER BY hda.person_id, hda.date, hda.time_of_day
""")

# SQL to get rotation template assignments for a block
# Split-block residents have two rows: block_half=1 (primary) and block_half=2 (secondary).
# Full-block residents have block_half IS NULL.
BLOCK_ASSIGNMENTS_SQL = text("""
    SELECT
        ba.resident_id::text,
        rt.name AS template_name,
        rt.rotation_type AS template_type,
        ba.block_half
    FROM block_assignments ba
    JOIN rotation_templates rt ON ba.rotation_template_id = rt.id
    WHERE ba.block_number = :block_number AND ba.academic_year = :academic_year
    ORDER BY ba.resident_id, ba.block_half NULLS FIRST
""")

# SQL to unlock manual slots (change source to 'template' and clear activity)
# so the solver will pick them up as candidate slots
UNLOCK_MANUAL_SQL = text("""
    UPDATE half_day_assignments
    SET source = 'template', activity_id = NULL
    WHERE date >= :start_date AND date <= :end_date
      AND source = 'manual'
""")

# SQL to link HDAs to block_assignments (so the solver can resolve rotation templates)
# Without this, _get_active_rotation_template() returns None for all resident slots
# because block_assignment_id is NULL and the assignments table fallback may not have entries.
LINK_BLOCK_ASSIGNMENTS_SQL = text("""
    UPDATE half_day_assignments hda
    SET block_assignment_id = ba.id
    FROM block_assignments ba
    WHERE hda.person_id = ba.resident_id
      AND ba.block_number = :block_number
      AND ba.academic_year = :academic_year
      AND hda.date >= :start_date AND hda.date <= :end_date
      AND hda.block_assignment_id IS NULL
""")

# SQL to get constraint requirements for comparison
REQUIREMENTS_SQL = text("""
    SELECT
        rt.name AS template_name,
        a.code AS activity_code,
        rar.min_halfdays,
        rar.max_halfdays,
        rar.target_halfdays,
        rar.applicable_weeks
    FROM rotation_activity_requirements rar
    JOIN rotation_templates rt ON rar.rotation_template_id = rt.id
    JOIN activities a ON rar.activity_id = a.id
    ORDER BY rt.name, a.code
""")


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--blocks", default="6,8,10",
                   help="Comma-separated block numbers to validate (default: 6,8,10)")
    p.add_argument("--academic-year", type=int, default=2025,
                   help="Academic year (default: 2025)")
    p.add_argument("--output", default="/tmp/e2e_validation_results.json",
                   help="Output JSON path")
    p.add_argument("--weight-configs", action="store_true",
                   help="Run Phase 6b weight sensitivity analysis")
    p.add_argument("--unlock-manual", action="store_true",
                   help="Temporarily unlock manual slots to template source "
                        "so the solver fills them (for true E2E comparison)")
    p.add_argument("--timeout", type=float, default=120.0,
                   help="Solver timeout per block in seconds (default: 120)")
    p.add_argument("--include-faculty", action="store_true", default=True,
                   help="Include faculty slots in solver run (default: True)")
    p.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL",
        "postgresql://scheduler@localhost:5432/residency_scheduler",
    ))
    return p.parse_args()


def snapshot_hdas(session, start_date, end_date):
    """Snapshot all HDAs for a date range. Returns dict keyed by (person_id, date, time_of_day)."""
    rows = session.execute(SNAPSHOT_SQL,
                           {"start_date": start_date, "end_date": end_date}).fetchall()
    result = {}
    for row in rows:
        key = (row.person_id, row.date, row.time_of_day)
        result[key] = {
            "activity_code": row.activity_code,
            "source": row.source,
            "person_name": row.person_name,
            "person_type": row.person_type,
        }
    return result


def get_block_templates(session, block_number, academic_year):
    """Get rotation template assignments for a block.

    Merges block_half=1 (primary) and block_half=2 (secondary) rows
    into a single dict entry per resident.
    """
    rows = session.execute(BLOCK_ASSIGNMENTS_SQL,
                           {"block_number": block_number,
                            "academic_year": academic_year}).fetchall()
    templates = {}
    for row in rows:
        rid = row.resident_id
        bh = row.block_half
        if bh == 2:
            # Secondary rotation — attach to existing entry
            if rid in templates:
                templates[rid]["secondary"] = row.template_name
                templates[rid]["secondary_type"] = row.template_type
        else:
            # Primary (block_half IS NULL or 1)
            templates[rid] = {
                "primary": row.template_name,
                "secondary": None,
                "primary_type": row.template_type,
                "secondary_type": None,
            }
    return templates


def get_requirements(session):
    """Load all rotation activity requirements."""
    rows = session.execute(REQUIREMENTS_SQL).fetchall()
    reqs = defaultdict(dict)
    for row in rows:
        reqs[row.template_name][row.activity_code] = {
            "min": row.min_halfdays,
            "max": row.max_halfdays,
            "target": row.target_halfdays,
            "applicable_weeks": row.applicable_weeks,
        }
    return dict(reqs)


def jensen_shannon_divergence(p_counts, q_counts):
    """Compute Jensen-Shannon divergence between two activity frequency distributions.

    Returns value in [0, 1] where 0 = identical distributions, 1 = completely different.
    """
    all_codes = set(p_counts.keys()) | set(q_counts.keys())
    if not all_codes:
        return 0.0

    p_total = sum(p_counts.values()) or 1
    q_total = sum(q_counts.values()) or 1

    p_dist = {code: p_counts.get(code, 0) / p_total for code in all_codes}
    q_dist = {code: q_counts.get(code, 0) / q_total for code in all_codes}

    # M = average distribution
    m_dist = {code: (p_dist[code] + q_dist[code]) / 2 for code in all_codes}

    def kl_div(a, b):
        total = 0.0
        for code in all_codes:
            if a[code] > 0 and b[code] > 0:
                total += a[code] * math.log2(a[code] / b[code])
        return total

    return (kl_div(p_dist, m_dist) + kl_div(q_dist, m_dist)) / 2


def compute_metrics(ground_truth, solver_output, block_templates, requirements,
                    block_dates, unlock_manual=False):
    """Compute E2E validation metrics.

    Tier 1: Constraint satisfaction rate (outpatient persons only)
    Tier 2: Activity-mix Jaccard similarity per person-block
    Tier 3: Slot-level exact match rate
    New: Jensen-Shannon divergence, gme concentration ratio
    """
    # Block start for week number calculation
    block_start = block_dates.start_date

    # Group by person
    persons_gt = defaultdict(dict)
    persons_sv = defaultdict(dict)
    person_names = {}

    for key, val in ground_truth.items():
        pid, d, tod = key
        persons_gt[pid][(d, tod)] = val["activity_code"]
        person_names[pid] = val["person_name"]

    for key, val in solver_output.items():
        pid, d, tod = key
        persons_sv[pid][(d, tod)] = val["activity_code"]

    all_persons = set(persons_gt.keys()) | set(persons_sv.keys())

    # --- Tier 3: Slot-level match rate ---
    total_slots = 0
    matching_slots = 0
    # Only count solver-modifiable slots (source != preload/manual)
    solver_slots = 0
    solver_matching = 0
    # Solver-filled-only: slots where solver actually assigned an activity
    solver_filled = 0
    solver_filled_matching = 0

    for key in ground_truth:
        gt_code = ground_truth[key]["activity_code"]
        sv_data = solver_output.get(key)
        sv_code = sv_data["activity_code"] if sv_data else None

        total_slots += 1
        if gt_code == sv_code:
            matching_slots += 1

        # Count slots the solver could modify
        # In unlock-manual mode, manual slots were also solver-eligible
        solver_eligible_sources = {"solver", "template"}
        if unlock_manual:
            solver_eligible_sources.add("manual")
        if ground_truth[key]["source"] in solver_eligible_sources:
            solver_slots += 1
            if gt_code == sv_code:
                solver_matching += 1

        # Count slots the solver ACTUALLY filled (non-null in output)
        if sv_code is not None and ground_truth[key]["source"] in solver_eligible_sources:
            solver_filled += 1
            if gt_code == sv_code:
                solver_filled_matching += 1

    slot_match_all = matching_slots / total_slots if total_slots else 0
    slot_match_solver = solver_matching / solver_slots if solver_slots else 0
    slot_match_filled = solver_filled_matching / solver_filled if solver_filled else 0

    # --- Tier 2: Jaccard similarity per person ---
    jaccard_scores = []
    jaccard_filled_scores = []  # Only persons with solver-filled slots
    person_details = []

    for pid in all_persons:
        gt_codes = set(persons_gt.get(pid, {}).values()) - {None}
        sv_codes = set(persons_sv.get(pid, {}).values()) - {None}

        if not gt_codes and not sv_codes:
            continue

        intersection = gt_codes & sv_codes
        union = gt_codes | sv_codes
        jaccard = len(intersection) / len(union) if union else 1.0
        jaccard_scores.append(jaccard)

        # Track filled-only Jaccard (persons who got solver assignments)
        has_solver_output = bool(sv_codes)
        if has_solver_output:
            jaccard_filled_scores.append(jaccard)

        # Activity count comparison
        gt_counts = defaultdict(int)
        sv_counts = defaultdict(int)
        for code in persons_gt.get(pid, {}).values():
            if code:
                gt_counts[code] += 1
        for code in persons_sv.get(pid, {}).values():
            if code:
                sv_counts[code] += 1

        person_details.append({
            "person_id": pid,
            "person_name": person_names.get(pid, "unknown"),
            "jaccard": round(jaccard, 3),
            "gt_activity_set": sorted(gt_codes),
            "sv_activity_set": sorted(sv_codes),
            "gt_counts": dict(gt_counts),
            "sv_counts": dict(sv_counts),
            "template": block_templates.get(pid, {}).get("primary", "N/A"),
        })

    mean_jaccard = sum(jaccard_scores) / len(jaccard_scores) if jaccard_scores else 0
    mean_jaccard_filled = (sum(jaccard_filled_scores) / len(jaccard_filled_scores)
                           if jaccard_filled_scores else 0)

    # --- Tier 1: Constraint satisfaction rate (outpatient only) ---
    # Only check persons on outpatient rotations — the solver's scope.
    # Non-outpatient persons (inpatient, NF, off, education) get zero solver
    # output and would produce guaranteed violations.
    # Also skip preloaded activities (W, LV, lec, FMIT, TDY, etc.) which the
    # solver never assigns. In unlock-manual mode these slots are wiped, so
    # the solver can't reproduce them.
    PRELOADED_CODES = {
        "fmit", "lv", "lv-am", "lv-pm", "w", "w-am", "w-pm", "pc", "pcat",
        "do", "lec", "lec-pm", "adv", "sim", "hafp", "usafp", "bls", "dep",
        "pi", "mm", "hol", "tdy", "ccc", "orient", "off", "off-am", "off-pm",
    }
    satisfaction_checks = 0
    satisfaction_met = 0
    constraint_violations = []
    outpatient_persons_checked = 0
    non_outpatient_skipped = 0
    preloaded_skipped = 0

    for pid in all_persons:
        template_info = block_templates.get(pid, {})
        primary_template = template_info.get("primary")
        primary_type = template_info.get("primary_type", "")
        if not primary_template or primary_template not in requirements:
            continue
        # Only check outpatient rotations (the activity solver's scope)
        if (primary_type or "").lower() != "outpatient":
            non_outpatient_skipped += 1
            continue

        outpatient_persons_checked += 1
        template_reqs = requirements[primary_template]
        sv_counts = defaultdict(int)
        for code in persons_sv.get(pid, {}).values():
            if code:
                sv_counts[code] += 1

        for act_code, req in template_reqs.items():
            # Skip preloaded activities — solver can't assign these
            if unlock_manual and act_code.lower() in PRELOADED_CODES:
                preloaded_skipped += 1
                continue
            satisfaction_checks += 1

            # Filter by applicable_weeks if the requirement is week-scoped
            applicable = req.get("applicable_weeks")
            if applicable:
                actual_count = 0
                for (d, tod), code in persons_sv.get(pid, {}).items():
                    if code == act_code:
                        week_num = ((d - block_start).days // 7) + 1
                        if week_num in applicable:
                            actual_count += 1
            else:
                actual_count = sv_counts.get(act_code, 0)
            req_min = req["min"]
            req_max = req["max"]

            if req_min <= actual_count <= req_max:
                satisfaction_met += 1
            else:
                constraint_violations.append({
                    "person_id": pid,
                    "person_name": person_names.get(pid, "unknown"),
                    "template": primary_template,
                    "activity": act_code,
                    "actual": actual_count,
                    "min": req_min,
                    "max": req_max,
                    "violation": "below_min" if actual_count < req_min else "above_max",
                })

    satisfaction_rate = satisfaction_met / satisfaction_checks if satisfaction_checks else 0

    # --- Jensen-Shannon divergence (outpatient persons only) ---
    gt_outpatient_freq = defaultdict(int)
    sv_outpatient_freq = defaultdict(int)
    for pid in all_persons:
        template_info = block_templates.get(pid, {})
        primary_type = template_info.get("primary_type", "")
        if (primary_type or "").lower() != "outpatient":
            continue
        for code in persons_gt.get(pid, {}).values():
            if code:
                gt_outpatient_freq[code] += 1
        for code in persons_sv.get(pid, {}).values():
            if code:
                sv_outpatient_freq[code] += 1

    js_div_outpatient = jensen_shannon_divergence(
        dict(gt_outpatient_freq), dict(sv_outpatient_freq))

    # --- GME concentration ratio ---
    gme_codes = {"gme", "GME"}
    gme_solver_count = sum(1 for v in solver_output.values()
                           if v["activity_code"] in gme_codes)
    gme_gt_count = sum(1 for v in ground_truth.values()
                       if v["activity_code"] in gme_codes)
    total_solver_filled = sum(1 for v in solver_output.values()
                              if v["activity_code"] is not None)

    # --- Activity frequency comparison ---
    gt_freq = defaultdict(int)
    sv_freq = defaultdict(int)
    for val in ground_truth.values():
        if val["activity_code"]:
            gt_freq[val["activity_code"]] += 1
    for val in solver_output.values():
        if val["activity_code"]:
            sv_freq[val["activity_code"]] += 1

    all_codes = sorted(set(gt_freq.keys()) | set(sv_freq.keys()))
    freq_comparison = {
        code: {"ground_truth": gt_freq.get(code, 0),
               "solver": sv_freq.get(code, 0),
               "delta": sv_freq.get(code, 0) - gt_freq.get(code, 0)}
        for code in all_codes
    }

    return {
        "tier1_constraint_satisfaction": {
            "checks": satisfaction_checks,
            "satisfied": satisfaction_met,
            "rate": round(satisfaction_rate, 4),
            "outpatient_persons_checked": outpatient_persons_checked,
            "non_outpatient_skipped": non_outpatient_skipped,
            "preloaded_skipped": preloaded_skipped,
            "violations_count": len(constraint_violations),
            "violations": constraint_violations[:20],  # Top 20
        },
        "tier2_jaccard_similarity": {
            "mean_jaccard": round(mean_jaccard, 4),
            "mean_jaccard_filled": round(mean_jaccard_filled, 4),
            "n_persons": len(jaccard_scores),
            "n_persons_filled": len(jaccard_filled_scores),
            "min_jaccard": round(min(jaccard_scores), 3) if jaccard_scores else 0,
            "max_jaccard": round(max(jaccard_scores), 3) if jaccard_scores else 0,
            "below_070": sum(1 for j in jaccard_scores if j < 0.70),
            "person_details": sorted(person_details, key=lambda x: x["jaccard"]),
        },
        "tier3_slot_match": {
            "total_slots": total_slots,
            "matching_slots": matching_slots,
            "match_rate_all": round(slot_match_all, 4),
            "solver_slots": solver_slots,
            "solver_matching": solver_matching,
            "match_rate_solver_only": round(slot_match_solver, 4),
            "solver_filled": solver_filled,
            "solver_filled_matching": solver_filled_matching,
            "match_rate_filled_only": round(slot_match_filled, 4),
        },
        "activity_frequency": freq_comparison,
        "js_divergence_outpatient": round(js_div_outpatient, 4),
        "gme_concentration": {
            "solver_gme": gme_solver_count,
            "gt_gme": gme_gt_count,
            "total_slots": len(ground_truth),
            "solver_total_filled": total_solver_filled,
            "solver_gme_ratio": round(
                gme_solver_count / len(ground_truth), 4
            ) if ground_truth else 0,
            "gt_gme_ratio": round(
                gme_gt_count / len(ground_truth), 4
            ) if ground_truth else 0,
        },
    }


def set_weight_config(config_name):
    """Monkey-patch solver penalty weights for sensitivity analysis."""
    config = WEIGHT_CONFIGS[config_name]
    saved = {}
    for key, value in config.items():
        saved[key] = getattr(solver_module, key)
        setattr(solver_module, key, value)
    return saved


def restore_weights(saved):
    """Restore original penalty weights."""
    for key, value in saved.items():
        setattr(solver_module, key, value)


def run_validation(session, block_number, academic_year, timeout,
                   include_faculty, requirements, unlock_manual=False):
    """Run solver on one block and compute metrics. Rolls back after."""
    block_dates = get_block_dates(block_number, academic_year)
    start_date = block_dates.start_date
    end_date = block_dates.end_date

    print(f"\n{'='*60}")
    print(f"  Block {block_number}: {start_date} to {end_date} "
          f"({block_dates.duration_days} days)")
    if unlock_manual:
        print(f"  MODE: unlock-manual (solver fills all non-preload slots)")
    print(f"{'='*60}")

    # Step 1: Snapshot ground truth (BEFORE any unlocking)
    print("  Snapshotting ground truth...")
    ground_truth = snapshot_hdas(session, start_date, end_date)
    print(f"    {len(ground_truth)} total HDA slots")

    source_counts = defaultdict(int)
    for v in ground_truth.values():
        source_counts[v["source"]] += 1
    for src, cnt in sorted(source_counts.items()):
        print(f"    source={src}: {cnt}")

    # Get block templates
    block_templates = get_block_templates(session, block_number, academic_year)
    print(f"    {len(block_templates)} residents with block assignments")

    # Step 1b: If unlock-manual, change manual slots to template source
    unlocked_count = 0
    if unlock_manual:
        result_proxy = session.execute(
            UNLOCK_MANUAL_SQL,
            {"start_date": start_date, "end_date": end_date},
        )
        unlocked_count = result_proxy.rowcount
        # Link HDAs to block_assignments so solver can resolve rotation templates
        link_result = session.execute(
            LINK_BLOCK_ASSIGNMENTS_SQL,
            {"block_number": block_number, "academic_year": academic_year,
             "start_date": start_date, "end_date": end_date},
        )
        linked_count = link_result.rowcount
        session.flush()
        print(f"  Unlocked {unlocked_count} manual slots → template source")
        if linked_count:
            print(f"  Linked {linked_count} HDAs to block_assignments")

    # Step 2: Run solver
    print(f"  Running CP-SAT solver (timeout={timeout}s)...")
    t0 = time.time()
    solver = CPSATActivitySolver(session, timeout_seconds=timeout)
    result = solver.solve(
        block_number, academic_year,
        include_faculty_slots=include_faculty,
        force_faculty_override=include_faculty,
    )
    elapsed = time.time() - t0
    print(f"    Status: {result.get('status', 'unknown')}")
    print(f"    Assignments updated: {result.get('assignments_updated', 0)}")
    print(f"    Runtime: {elapsed:.1f}s")

    # Step 3: Read solver output (flushed but not committed)
    print("  Reading solver output...")
    solver_output = snapshot_hdas(session, start_date, end_date)

    # Step 4: Rollback — DB untouched (undoes both unlock AND solver changes)
    session.rollback()
    print("  Rolled back — DB unchanged")

    # Step 5: Compute metrics
    print("  Computing metrics...")
    metrics = compute_metrics(ground_truth, solver_output, block_templates,
                              requirements, block_dates,
                              unlock_manual=unlock_manual)

    # Print summary
    t1 = metrics["tier1_constraint_satisfaction"]
    t2 = metrics["tier2_jaccard_similarity"]
    t3 = metrics["tier3_slot_match"]
    gme = metrics["gme_concentration"]

    print(f"\n  RESULTS:")
    print(f"    Tier 1 — Constraint satisfaction (outpatient): "
          f"{t1['satisfied']}/{t1['checks']} = {t1['rate']:.1%} "
          f"({t1['outpatient_persons_checked']} outpatient, "
          f"{t1['non_outpatient_skipped']} non-outpatient skipped"
          f"{', ' + str(t1.get('preloaded_skipped', 0)) + ' preloaded skipped' if t1.get('preloaded_skipped') else ''})")
    print(f"    Tier 2 — Mean Jaccard (all):       {t2['mean_jaccard']:.3f} "
          f"(n={t2['n_persons']}, {t2['below_070']} below 0.70)")
    print(f"    Tier 2 — Mean Jaccard (filled):    {t2['mean_jaccard_filled']:.3f} "
          f"(n={t2['n_persons_filled']})")
    print(f"    Tier 3 — Slot match (all):         {t3['match_rate_all']:.1%} "
          f"({t3['matching_slots']}/{t3['total_slots']})")
    print(f"    Tier 3 — Slot match (solver-only):  {t3['match_rate_solver_only']:.1%} "
          f"({t3['solver_matching']}/{t3['solver_slots']})")
    if t3['solver_filled'] > 0:
        print(f"    Tier 3 — Slot match (filled-only): {t3['match_rate_filled_only']:.1%} "
              f"({t3['solver_filled_matching']}/{t3['solver_filled']})")
    print(f"    JS Divergence (outpatient):        {metrics['js_divergence_outpatient']:.4f}")
    print(f"    GME concentration:                 {gme['solver_gme_ratio']:.1%} "
          f"({gme['solver_gme']}/{gme['solver_total_filled']} solver, "
          f"vs {gme['gt_gme_ratio']:.1%} ground truth)")

    if t1["violations_count"] > 0:
        print(f"\n  Top constraint violations ({t1['violations_count']} total):")
        for v in t1["violations"][:5]:
            print(f"    {v['person_name']}: {v['activity']} on {v['template']} "
                  f"— actual={v['actual']}, bounds=[{v['min']},{v['max']}] "
                  f"({v['violation']})")

    # Worst Jaccard
    if t2["person_details"]:
        print(f"\n  Worst 5 Jaccard scores:")
        for pd in t2["person_details"][:5]:
            print(f"    {pd['person_name']}: {pd['jaccard']:.3f} "
                  f"({pd['template']})")

    return {
        "block_number": block_number,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "solver_status": result.get("status", "unknown"),
        "solver_runtime": round(elapsed, 2),
        "assignments_updated": result.get("assignments_updated", 0),
        "ground_truth_slots": len(ground_truth),
        "source_distribution": dict(source_counts),
        "n_residents": len(block_templates),
        "unlock_manual": unlock_manual,
        "unlocked_count": unlocked_count,
        "metrics": metrics,
    }


def main():
    args = parse_args()
    target_blocks = [int(b.strip()) for b in args.blocks.split(",")]

    print("E2E Solver Validation")
    print(f"  Blocks: {target_blocks}")
    print(f"  Academic year: {args.academic_year}")
    print(f"  DB: {args.db_url}")
    print(f"  Solver timeout: {args.timeout}s")
    print(f"  Weight configs: {args.weight_configs}")
    print(f"  Unlock manual: {args.unlock_manual}")

    # Create sync engine + session
    engine = create_engine(args.db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()

    # Load requirements once (shared across blocks)
    requirements = get_requirements(session)
    print(f"  Loaded {sum(len(v) for v in requirements.values())} "
          f"requirements across {len(requirements)} templates")

    results = {}

    if args.weight_configs:
        # Phase 6b: Weight sensitivity analysis
        print(f"\n{'#'*60}")
        print(f"  PHASE 6b: WEIGHT SENSITIVITY ANALYSIS")
        print(f"{'#'*60}")

        for config_name, config in WEIGHT_CONFIGS.items():
            print(f"\n  === Config: {config_name} ===")
            for k, v in config.items():
                print(f"    {k} = {v}")

            saved = set_weight_config(config_name)
            try:
                config_results = []
                for block_number in target_blocks:
                    block_result = run_validation(
                        session, block_number, args.academic_year,
                        args.timeout, args.include_faculty, requirements,
                        unlock_manual=args.unlock_manual,
                    )
                    config_results.append(block_result)
                results[config_name] = config_results
            finally:
                restore_weights(saved)

        # Summary comparison
        print(f"\n{'='*60}")
        print("  WEIGHT SENSITIVITY SUMMARY")
        print(f"{'='*60}")
        print(f"  {'Config':<20} {'Satisfaction':>12} {'Jaccard':>10} {'Slot Match':>12}")
        print(f"  {'-'*54}")
        for config_name, config_results in results.items():
            avg_sat = sum(r["metrics"]["tier1_constraint_satisfaction"]["rate"]
                         for r in config_results) / len(config_results)
            avg_jac = sum(r["metrics"]["tier2_jaccard_similarity"]["mean_jaccard"]
                         for r in config_results) / len(config_results)
            avg_slot = sum(r["metrics"]["tier3_slot_match"]["match_rate_solver_only"]
                          for r in config_results) / len(config_results)
            print(f"  {config_name:<20} {avg_sat:>11.1%} {avg_jac:>10.3f} {avg_slot:>11.1%}")

    else:
        # Phase 6: Standard E2E validation
        for block_number in target_blocks:
            block_result = run_validation(
                session, block_number, args.academic_year,
                args.timeout, args.include_faculty, requirements,
                unlock_manual=args.unlock_manual,
            )
            results[f"block_{block_number}"] = block_result

    session.close()
    engine.dispose()

    # Write output
    out_path = Path(args.output)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n  Output: {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
