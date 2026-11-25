#!/usr/bin/env python3
"""Verify released FinitePGroupLab Lean modules incrementally by target.

Avoids uncurated umbrella/full-lab builds: reads ``releases/results.json`` and
checks each released Lean module explicitly via ``lake build <Module>``, or
verifies ``FinitePGroupLab.lean`` when no theorem modules are released yet.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def lean_module_name(lean_file: str) -> str:
    if not lean_file.endswith(".lean"):
        raise ValueError(f"Expected .lean path, got: {lean_file}")
    return lean_file.removesuffix(".lean").replace("/", ".")


def planned_commands(manifest_path: Path, lake_cmd: str = "lake") -> list[list[str]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = data.get("results") or []
    modules: list[str] = []
    for item in results:
        lean_file = item.get("lean_file")
        if isinstance(lean_file, str) and lean_file.strip():
            mod = lean_module_name(lean_file.strip())
            if mod not in modules:
                modules.append(mod)
    if not modules:
        return [[lake_cmd, "env", "lean", "FinitePGroupLab.lean"]]
    cmds = [[lake_cmd, "build", mod] for mod in modules]
    cmds.append([lake_cmd, "env", "lean", "FinitePGroupLab.lean"])
    return cmds


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elan", action="store_true", help="Use ~/.elan/bin/lake (for GitHub Actions).")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without running Lake.")
    args = parser.parse_args()

    lake_cmd = str(Path.home() / ".elan" / "bin" / "lake") if args.elan else "lake"
    cmds = planned_commands(ROOT / "releases" / "results.json", lake_cmd=lake_cmd)
    for cmd in cmds:
        print("RUN:", " ".join(cmd))
        if not args.dry_run:
            proc = subprocess.run(cmd, cwd=ROOT)
            if proc.returncode != 0:
                return proc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
