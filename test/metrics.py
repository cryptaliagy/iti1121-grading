#!/usr/bin/env python3

"""
Baseline performance and code metrics tracking script.

This script captures performance metrics and code statistics to establish a baseline
for the refactoring process. It should be run before and after major changes to track
improvements.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[str, float]:
    """Run a command and return output and execution time."""
    print(f"Running: {description}...")
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent,
        )
        elapsed = time.time() - start
        return result.stdout, elapsed
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        print(f"  ⚠️  Command failed: {e}")
        return e.stdout + e.stderr, elapsed


def get_code_metrics():
    """Gather code metrics."""
    metrics = {}

    # Count lines of code
    print("\n📊 Code Metrics")
    print("=" * 60)

    # Count Python files
    src_files = list(Path("src").rglob("*.py"))
    test_files = list(Path("test").rglob("*.py"))

    metrics["source_files"] = len(src_files)
    metrics["test_files"] = len(test_files)

    # Count lines in source files
    source_lines = 0
    for f in src_files:
        source_lines += len(f.read_text().splitlines())

    test_lines = 0
    for f in test_files:
        test_lines += len(f.read_text().splitlines())

    metrics["source_lines"] = source_lines
    metrics["test_lines"] = test_lines

    print(f"  Source files: {metrics['source_files']}")
    print(f"  Test files: {metrics['test_files']}")
    print(f"  Source lines: {metrics['source_lines']:,}")
    print(f"  Test lines: {metrics['test_lines']:,}")
    print(f"  Test/Source ratio: {metrics['test_lines'] / metrics['source_lines']:.2f}")

    return metrics


def get_test_coverage():
    """Run tests and get coverage metrics."""
    print("\n🧪 Test Coverage")
    print("=" * 60)

    output, elapsed = run_command(
        [sys.executable, "-m", "pytest", "test/", "--cov=src/grader", "--cov-report=term"],
        "Test suite with coverage",
    )

    # Extract coverage percentage from output
    coverage_pct = 0
    for line in output.splitlines():
        if "TOTAL" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "TOTAL":
                    try:
                        # Coverage percentage is typically the last column
                        coverage_pct = int(parts[-1].rstrip("%"))
                    except (ValueError, IndexError):
                        pass

    print(f"  Test execution time: {elapsed:.2f}s")
    print(f"  Coverage: {coverage_pct}%")

    return {"coverage": coverage_pct, "test_time": elapsed}


def get_linter_metrics():
    """Run linters and collect metrics."""
    print("\n🔍 Code Quality Checks")
    print("=" * 60)

    metrics = {}

    # Run ruff
    output, elapsed = run_command(
        [sys.executable, "-m", "ruff", "check", "."],
        "Ruff linter",
    )
    ruff_issues = len([line for line in output.splitlines() if line.strip() and not line.startswith("All")])
    print(f"  ✓ Ruff: {ruff_issues} issues ({elapsed:.2f}s)")
    metrics["ruff_issues"] = ruff_issues

    # Run mypy
    output, elapsed = run_command(
        [sys.executable, "-m", "mypy", "src/"],
        "Mypy type checker",
    )
    mypy_errors = len([line for line in output.splitlines() if "error:" in line])
    print(f"  ✓ Mypy: {mypy_errors} errors ({elapsed:.2f}s)")
    metrics["mypy_errors"] = mypy_errors

    # Run bandit
    output, elapsed = run_command(
        [sys.executable, "-m", "bandit", "-c", "pyproject.toml", "-r", "src/", "-q"],
        "Bandit security scanner",
    )
    bandit_issues = len([line for line in output.splitlines() if "Issue:" in line])
    print(f"  ✓ Bandit: {bandit_issues} security issues ({elapsed:.2f}s)")
    metrics["bandit_issues"] = bandit_issues

    return metrics


def main():
    """Run all metrics collection."""
    print("\n" + "=" * 60)
    print("📈 Baseline Performance & Code Metrics")
    print("=" * 60)

    all_metrics = {}

    # Gather metrics
    all_metrics["code"] = get_code_metrics()
    all_metrics["coverage"] = get_test_coverage()
    all_metrics["quality"] = get_linter_metrics()

    # Print summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    print(f"  Coverage: {all_metrics['coverage']['coverage']}%")
    print(f"  Test time: {all_metrics['coverage']['test_time']:.2f}s")
    print(f"  Ruff issues: {all_metrics['quality']['ruff_issues']}")
    print(f"  Mypy errors: {all_metrics['quality']['mypy_errors']}")
    print(f"  Bandit issues: {all_metrics['quality']['bandit_issues']}")
    print(f"  Source files: {all_metrics['code']['source_files']}")
    print(f"  Test files: {all_metrics['code']['test_files']}")
    print(f"  Test/Source ratio: {all_metrics['code']['test_lines'] / all_metrics['code']['source_lines']:.2f}")

    print("\n✅ Baseline metrics collected!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
