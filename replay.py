#!/usr/bin/env python
"""Re-run verification over artefacts already on disk, with no model calls.

    python replay.py runs/bench

Every generated artefact from a run is kept under `runs/<id>/candidates/`, so the entire
verification stage can be replayed against the exact same inputs it saw the first time. That
makes a change to the checking logic measurable on its own: the model output is held fixed and
only the harness moves. It is also the cheapest possible regression test for this stage, since
it costs no tokens and finishes in seconds.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solver.budget import Budget                      # noqa: E402
from solver.generate import Artifact, Wave            # noqa: E402
from solver.verify import verify                      # noqa: E402

ROLE_BY_NAME = {"oracle": "oracle", "inputgen": "inputgen"}


def load_wave(run_dir: str, language: str) -> Wave:
    wave = Wave()
    cdir = os.path.join(run_dir, "candidates")
    for path in sorted(glob.glob(os.path.join(cdir, "*"))):
        name = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        if name == "oracle":
            wave.oracle = Artifact(role="oracle", framing="literal-reference",
                                   language="python", source=source)
        elif name == "inputgen":
            wave.inputgen = Artifact(role="inputgen", framing="generator",
                                     language="python", source=source)
        else:
            wave.candidates.append(Artifact(role="candidate", framing=name,
                                            language=language, source=source))
    return wave


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default="runs/bench")
    ap.add_argument("--samples", default="samples")
    ap.add_argument("-o", "--out", default=None, help="write the replayed rows as JSON")
    args = ap.parse_args(argv)

    rows = []
    for report_path in sorted(glob.glob(os.path.join(args.run_dir, "*", "report.json"))):
        rdir = os.path.dirname(report_path)
        short = os.path.basename(rdir)
        with open(report_path, encoding="utf-8") as fh:
            rep = json.load(fh)
        matches = glob.glob(os.path.join(args.samples, f"{short}*.json"))
        if not matches:
            continue
        with open(matches[0], encoding="utf-8") as fh:
            problem = json.load(fh)

        wave = load_wave(rdir, problem.get("language", "python"))
        if not wave.candidates:
            continue
        budget = Budget(deadline_s=float(problem.get("deadline_s", 300.0)))
        budget.start("verify")
        t0 = time.monotonic()
        v = verify(wave, problem, None, budget)
        agreeing = sum(1 for r in v.reports
                       if r.disagree_oracle == 0 and r.agree_oracle > 0)
        before = rep.get("verification") or {}
        was = sum(1 for c in (before.get("candidates") or [])
                  if c.get("disagree") == 0 and c.get("agree", 0) > 0)
        rows.append({
            "short": short, "language": problem.get("language"),
            "cases": v.cases, "oracle_answers": v.oracle_answers,
            "agreeing_before": was, "agreeing_after": agreeing,
            "total": len(v.reports), "divergence": v.framing_divergence,
            "generator_error": v.generator_error,
            "notes": v.notes, "replay_s": round(time.monotonic() - t0, 1),
        })
        print(f"{short} {problem.get('language'):6s} cases={v.cases:2d} "
              f"oracle_answered={v.oracle_answers:2d} "
              f"agreeing {was}/{len(v.reports)} -> {agreeing}/{len(v.reports)} "
              f"({rows[-1]['replay_s']}s)", flush=True)
        if v.generator_error:
            print(f"    generator: {v.generator_error}")
        for n in v.notes:
            if n != v.generator_error:
                print(f"    note: {n}")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=1, ensure_ascii=False)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
