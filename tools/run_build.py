"""Run formatter, linter, and tests while reporting per-step status."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYLINTHOME = PROJECT_ROOT / ".pylint.d"
PYLINTHOME.mkdir(exist_ok=True)

Step = tuple[str, list[str], dict[str, str]]


def _steps() -> list[Step]:
    base_env = {}
    return [
        ("test", ["pytest"], base_env),
        (
            "lint",
            ["pylint", "src", "tests"],
            {"PYLINTHOME": str(PYLINTHOME)},
        ),
        ("format", ["black", "src", "tests"], base_env),
    ]


def run() -> int:
    steps = _steps()
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
    sys.exit(run())
