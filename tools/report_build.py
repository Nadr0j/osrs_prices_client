from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.table import Table


def main() -> None:
    console = Console()
    data = json.loads(sys.stdin.read() or "[]")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Step")
    table.add_column("Status")

    for entry in data:
        step = entry.get("step", "unknown")
        ok = entry.get("ok", False)
        status = "✅ success" if ok else "❌ failed"
        table.add_row(step, status)

    console.print(table)


if __name__ == "__main__":
    main()
