#!/usr/bin/env python3
"""Append each subagent request's `subagent_type` to a file beside this script.

Reads one hook event as JSON on stdin. Exits 0 on every path, including every
failure, and writes nothing to stdout. See `evals/README.md` for what this is
for, why it is shaped this way, and what its output is used for.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROSTER = Path(__file__).resolve().parent / "dispatched.txt"

SUBAGENT_KEY = "subagent_type"


def main() -> int:
    try:
        event = json.load(sys.stdin)
        requested = (event.get("tool_input") or {}).get(SUBAGENT_KEY)
        if isinstance(requested, str) and requested:
            with ROSTER.open("a", encoding="utf-8") as handle:
                handle.write(f"{requested}\n")
    except Exception:  # noqa: BLE001 -- never fail; see evals/README.md
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
