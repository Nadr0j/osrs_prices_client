"""Run formatter, linter, and tests while reporting per-step status."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYLINTHOME = PROJECT_ROOT / ".pylint.d"
PYLINTHOME.mkdir(exist_ok=True)

Step = tuple[str, list[str], dict[str, str]]


def _steps(black_check: bool = False) -> list[Step]:
    base_env: dict[str, str] = {}
    format_cmd = ["black", "src", "tests"]
    if black_check:
        format_cmd.insert(1, "--check")

    return [
        ("test", ["pytest"], base_env),
        (
            "lint",
            ["pylint", "src", "tests"],
            {"PYLINTHOME": str(PYLINTHOME)},
        ),
        ("format", format_cmd, base_env),
    ]


def run(black_check: bool = False) -> int:
    steps = _steps(black_check=black_check)
    results: list[tuple[str, str]] = []
    base_env = os.environ.copy()
    aborted = False
    exit_code = 0

    for name, cmd, extra_env in steps:
        if aborted:
            results.append((name, "SKIPPED"))
            continue

        full_env = base_env.copy()
        full_env.update(extra_env)

        print(f"→ Running {name}: {' '.join(cmd)}", flush=True)
        completed = subprocess.run(cmd, cwd=PROJECT_ROOT, env=full_env, check=False)
        if completed.returncode == 0:
            results.append((name, "OK"))
        else:
            results.append((name, f"FAILED ({completed.returncode})"))
            exit_code = completed.returncode
            aborted = True

    print("\nBuild summary:")
    for name, status in results:
        print(f"- {name}: {status}")

    if exit_code == 0:
        print("\nAll checks passed ✨")
    else:
        print("\nBuild failed ❌")

    return exit_code


if __name__ == "__main__":
    sys.exit(run(black_check="--check" in sys.argv))
