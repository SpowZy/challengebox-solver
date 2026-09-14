#!/usr/bin/env python
"""Rebuild RESULTS.md from runs already on disk, without re-running anything.

    python report_only.py runs/bench -o runs/bench/RESULTS.md

The benchmark writes `rows.json` as it goes, and every run leaves a `report.json`. Reporting
is therefore separable from execution: the table can be regenerated after a change to its
wording without spending the budget again, and the numbers still come from the same recorded
runs rather than from anything retyped.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import write_results  # noqa: E402


def rows_from_disk(run_dir: str, *, ignore_rows: bool = False) -> list[dict]:
    """Rebuild the table rows. `ignore_rows` rebuilds purely from each run's report.json,
    which is what you want after changing what the table reports: a `rows.json` written by an
    earlier version of this script does not carry fields the new table needs."""
    rows_path = os.path.join(run_dir, "rows.json")
    rows: list[dict] = []
    if os.path.exists(rows_path) and not ignore_rows:
        try:
            with open(rows_path, encoding="utf-8") as fh:
                rows = json.load(fh)
        except json.JSONDecodeError:
            rows = []

    # rows.json is written after each problem, so a run interrupted mid-problem still has a
    # report.json the table should include. Fill any gap from the reports themselves.
    known = {r.get("short") for r in rows}
    for report_path in sorted(glob.glob(os.path.join(run_dir, "*", "report.json"))):
        short = os.path.basename(os.path.dirname(report_path))
        if short in known:
            continue
        try:
            with open(report_path, encoding="utf-8") as fh:
                rep = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        ver = rep.get("verification") or {}
        cands = ver.get("candidates") or []
        rows.append({
            "problem_id": rep.get("problem_id", short),
            "short": short,
            "language": rep.get("language"),
            "entrypoint": rep.get("entrypoint"),
            "deadline_s": (rep.get("budget") or {}).get("deadline_s", 300.0),
            "exit_code": None,
            "elapsed_s": round((rep.get("budget") or {}).get("elapsed_s", 0.0), 1),
            "within_deadline": True,
            "solution_written": bool(rep.get("output_path")),
            "status": rep.get("status"),
            "final_candidate": rep.get("final_candidate"),
            "traps": len((rep.get("analysis") or {}).get("traps") or []),
            "cases": ver.get("cases", 0),
            "oracle_ok": ver.get("oracle_ok"),
            "oracle_answers": ver.get("oracle_answers"),
            "generator_error": ver.get("generator_error"),
            "notes": ver.get("notes") or [],
            "clusters": ver.get("clusters") or {},
            "candidates_total": len(cands),
            "candidates_agreeing": sum(
                1 for c in cands if c.get("disagree") == 0 and c.get("agree", 0) > 0),
            "framing_divergence": ver.get("framing_divergence"),
            "ambiguity_note": ver.get("ambiguity_note", ""),
            "_candidates": [
                {"framing": c.get("framing"), "agree": c.get("agree", 0),
                 "disagree": c.get("disagree", 0), "compiled": c.get("compiled")}
                for c in cands
            ],
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default="runs/bench")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--ignore-rows", action="store_true",
                    help="rebuild from each report.json instead of a stale rows.json")
    args = ap.parse_args(argv)

    rows = rows_from_disk(args.run_dir, ignore_rows=args.ignore_rows)
    if not rows:
        print(f"no runs found under {args.run_dir}", file=sys.stderr)
        return 1
    path = write_results(rows, args.run_dir, args.model)
    if args.out and os.path.abspath(args.out) != os.path.abspath(path):
        with open(path, encoding="utf-8") as src, open(args.out, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        path = args.out
    print(f"wrote {path} from {len(rows)} runs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
