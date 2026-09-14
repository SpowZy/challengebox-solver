#!/usr/bin/env python
"""Print every measured figure that ARCHITECTURE.md and README.md quote.

    python figures.py runs/bench

The documents claim that nothing in them is estimated. This is how that claim is checkable:
each number below is re-derived from the recorded runs, so a reader can compare the prose
against the data without reading any of the code. If a figure in the prose does not appear
here, it does not have a run behind it.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys


def load_reports(run_dir: str) -> list[dict]:
    reports = []
    for path in sorted(glob.glob(os.path.join(run_dir, "*", "report.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                rep = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        rep["_short"] = os.path.basename(os.path.dirname(path))
        reports.append(rep)
    return reports


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default="runs/bench")
    args = ap.parse_args(argv)

    reports = load_reports(args.run_dir)
    if not reports:
        print(f"no runs under {args.run_dir}", file=sys.stderr)
        return 1

    print(f"# Measured figures, from {len(reports)} recorded runs under {args.run_dir}\n")

    # ---- wall clock -------------------------------------------------------------
    elapsed = [(r.get("budget") or {}).get("elapsed_s", 0.0) for r in reports]
    deadlines = [(r.get("budget") or {}).get("total_s", 300.0) for r in reports]
    print("## Wall clock against the 300 s deadline")
    print(f"  slowest problem          {max(elapsed):6.1f}s")
    print(f"  fastest problem          {min(elapsed):6.1f}s")
    print(f"  median                   {statistics.median(elapsed):6.1f}s")
    print(f"  inside the deadline      {sum(1 for e, d in zip(elapsed, deadlines) if e <= d)}"
          f"/{len(elapsed)}")
    print()

    # ---- model calls ------------------------------------------------------------
    per_call, waves, analyses = [], [], []
    calls_total = failed_total = 0
    for r in reports:
        usage = r.get("model_usage") or {}
        calls_total += usage.get("calls", 0)
        failed_total += usage.get("failed", 0)
        detail = usage.get("detail") or []
        lat = [d.get("latency_s", 0.0) for d in detail if d.get("ok")]
        per_call += lat
        if lat:
            waves.append(max(lat))          # the wave ends when its slowest call returns
        analyses += [d.get("latency_s", 0.0) for d in detail
                     if d.get("role") == "analyse" and d.get("ok")]
    print("## Model calls")
    print(f"  calls issued             {calls_total} ({failed_total} failed)")
    print(f"  calls per problem        {calls_total / len(reports):.1f}")
    if per_call:
        print(f"  one call, median         {statistics.median(per_call):6.1f}s")
        print(f"  one call, slowest        {max(per_call):6.1f}s")
    if waves:
        print(f"  whole wave, median       {statistics.median(waves):6.1f}s   "
              f"(nine concurrent calls; the wave ends with its slowest)")
        print(f"  whole wave, slowest      {max(waves):6.1f}s")
    if analyses:
        print(f"  trap pass, median        {statistics.median(analyses):6.1f}s")
    print()

    # ---- local verification -----------------------------------------------------
    verify_s = []
    for r in reports:
        phases = (r.get("budget") or {}).get("phases") or {}
        spent = phases.get("verify", {})
        if isinstance(spent, dict) and spent.get("elapsed_s"):
            verify_s.append(spent["elapsed_s"])
    generate_s = []
    for r in reports:
        phases = (r.get("budget") or {}).get("phases") or {}
        g = phases.get("generate", {})
        if isinstance(g, dict) and g.get("elapsed_s"):
            generate_s.append(g["elapsed_s"])
    if generate_s:
        print("## The parallel wave, wall clock")
        print(f"  median                   {statistics.median(generate_s):6.1f}s")
        print(f"  slowest                  {max(generate_s):6.1f}s")
        print()
    if verify_s:
        print("## Local verification (no model calls)")
        print(f"  median                   {statistics.median(verify_s):6.1f}s")
        print(f"  slowest                  {max(verify_s):6.1f}s")
        print()

    # ---- what the checks found --------------------------------------------------
    traps = [len((r.get("analysis") or {}).get("traps") or []) for r in reports]
    div = sum(1 for r in reports if (r.get("verification") or {}).get("framing_divergence"))
    statuses: dict[str, int] = {}
    for r in reports:
        statuses[r.get("status", "?")] = statuses.get(r.get("status", "?"), 0) + 1
    print("## What the checks found")
    print(f"  clauses quoted as traps  {sum(traps)} across {len(reports)} statements")
    print(f"  statements with 0 traps  {sum(1 for t in traps if t == 0)}")
    print(f"  readings diverged on     {div}/{len(reports)} statements")
    for name, n in sorted(statuses.items(), key=lambda kv: -kv[1]):
        print(f"  status {name:30s} {n}")
    print()

    # ---- reference coverage -----------------------------------------------------
    print("## Reference coverage, per problem")
    for r in sorted(reports, key=lambda x: x["_short"]):
        v = r.get("verification") or {}
        answered = v.get("oracle_answers")
        cases = v.get("cases", 0)
        cov = "not recorded" if answered is None else f"{answered}/{cases}"
        print(f"  {r['_short']}  {r.get('language','?'):6s} reference answered {cov:>13s}"
              f"   status {r.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
