"""
Flame Graph Generator

Generates flame graphs for visualizing profiling data. Uses py-spy for sampling
profiling or converts cProfile data to flame graph format.

Requirements:
    pip install py-spy  # Requires root/sudo on Linux

Usage:
    # Using py-spy (recommended for production-like profiling)
    sudo python -m profiling.flame_graph_generator --target schedule --method pyspy

    # Using cProfile data
    python -m profiling.flame_graph_generator --pstats profiling_results/schedule_generation.pstats

    # Profile running process
    sudo py-spy record -o flame_graph.svg --pid <PID>
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_from_pyspy(
    target_script: str,
    output_file: str = "flamegraph.svg",
    duration: int = 30,
    rate: int = 100,
):
    """
    Generate flame graph using py-spy sampling profiler.

    Args:
        target_script: Python script to profile
        output_file: Output SVG file path
        duration: Recording duration in seconds
        rate: Sampling rate (samples per second)
    """
    print(f"{'=' * 80}")
    print("FLAME GRAPH GENERATION (py-spy)")
    print(f"{'=' * 80}")
    print(f"Target: {target_script}")
    print(f"Duration: {duration}s")
    print(f"Rate: {rate} samples/sec")
    print(f"Output: {output_file}")
    print()

    try:
        # Check if py-spy is installed
        subprocess.run(["py-spy", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: py-spy not found. Install with:")
        print("  pip install py-spy")
        print("\nNote: py-spy requires root/sudo on Linux:")
        print("  sudo env PATH=$PATH python -m profiling.flame_graph_generator ...")
        return

    cmd = [
        "py-spy",
        "record",
        "-o",
        output_file,
        "--format",
        "speedscope",  # or "flamegraph"
        "--rate",
        str(rate),
        "--duration",
        str(duration),
        "--",
        sys.executable,
        target_script,
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Flame graph saved to: {output_file}")
        print("  Open in browser to visualize")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: py-spy failed: {e}")
        print("\nTry running with sudo:")
        print(f"  sudo env PATH=$PATH {' '.join(cmd)}")


def convert_pstats_to_flamegraph(
    pstats_file: Path, output_file: str = "flamegraph.svg"
):
    """
    Convert cProfile .pstats file to flame graph format.

    This is a simplified version - for production use, consider using
    tools like flameprof or gprof2dot + dot.
    """
    print(f"{'=' * 80}")
    print("FLAME GRAPH GENERATION (from pstats)")
    print(f"{'=' * 80}")
    print(f"Input: {pstats_file}")
    print(f"Output: {output_file}")
    print()

    try:
        import pstats

        stats = pstats.Stats(str(pstats_file))

        # For now, just print top functions as a guide
        print("Top functions (use gprof2dot for actual flame graph):")
        print("-" * 80)
        stats.strip_dirs()
        stats.sort_stats("cumulative")
        stats.print_stats(30)

        print("\n" + "=" * 80)
        print("To generate actual flame graph from pstats:")
        print("=" * 80)
        print("1. Install gprof2dot and graphviz:")
        print("   pip install gprof2dot")
        print("   apt-get install graphviz  # or brew install graphviz")
        print()
        print("2. Generate flame graph:")
        print(f"   gprof2dot -f pstats {pstats_file} | dot -Tsvg -o {output_file}")
        print()

    except Exception as e:
        print(f"ERROR: Failed to process pstats file: {e}")


def profile_and_generate(
    target: str = "schedule",
    method: str = "pyspy",
    duration: int = 30,
):
    """
    Profile a target operation and generate flame graph.

    Args:
        target: What to profile (schedule, validation, queries)
        method: Profiling method (pyspy or cprofile)
        duration: Duration for py-spy profiling
    """
    # Map targets to profiling scripts
    target_scripts = {
        "schedule": "profiling/profile_scheduler.py",
        "validation": "profiling/profile_api_endpoints.py",
        "queries": "profiling/profile_queries.py",
        "background": "profiling/profile_background_tasks.py",
    }

    if target not in target_scripts:
        print(f"ERROR: Unknown target '{target}'")
        print(f"Available targets: {', '.join(target_scripts.keys())}")
        return

    script_path = Path(__file__).parent / target_scripts[target]

    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return

    output_file = f"flamegraph_{target}_{method}.svg"

    if method == "pyspy":
        generate_from_pyspy(
            target_script=str(script_path),
            output_file=output_file,
            duration=duration,
            rate=100,
        )
    else:
        # Run with cProfile
        import cProfile

        print(f"Profiling {target} with cProfile...")

        pstats_file = Path(f"profile_{target}.pstats")

        cProfile.run(
            f"exec(open('{script_path}').read())",
            str(pstats_file),
        )

        convert_pstats_to_flamegraph(pstats_file, output_file)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate flame graphs for performance analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile schedule generation with py-spy (requires sudo)
  sudo python -m profiling.flame_graph_generator --target schedule --method pyspy

  # Convert existing pstats file to flame graph
  python -m profiling.flame_graph_generator --pstats results/schedule_generation.pstats

  # Profile running server (get PID with ps aux | grep uvicorn)
  sudo py-spy record -o server_flame.svg --pid <PID> --duration 60
        """,
    )

    parser.add_argument(
        "--target",
        type=str,
        choices=["schedule", "validation", "queries", "background"],
        help="Target operation to profile",
    )

    parser.add_argument(
        "--method",
        type=str,
        default="pyspy",
        choices=["pyspy", "cprofile"],
        help="Profiling method",
    )

    parser.add_argument(
        "--pstats",
        type=Path,
        help="Convert existing .pstats file to flame graph",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Duration for py-spy profiling (seconds)",
    )

    args = parser.parse_args()

    if args.pstats:
        # Convert pstats file
        convert_pstats_to_flamegraph(args.pstats)
    elif args.target:
        # Profile and generate
        profile_and_generate(
            target=args.target,
            method=args.method,
            duration=args.duration,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
