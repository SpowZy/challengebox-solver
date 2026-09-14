#!/usr/bin/env python
"""ChallengeBox solver: one problem JSON in, one solution file out, inside the deadline.

    python solve.py samples/<id>.json -o runs/out.py

Exit codes
    0  a solution was written and it agreed with the reference on every generated input
    1  a solution was written but some check did not pass or could not be run
    2  the problem file could not be read
    3  no solution could be produced at all

The distinction between 0 and 1 matters more than it looks. The scoring rule is binary and
hidden, so this tool never claims a solution is correct. It reports what was checked and
what that check said. A file that was written without full verification still scores whatever
it scores; a file that was never written scores zero for certain. That asymmetry is why the
emit phase owns a reserve that no other phase may spend.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solver.analyse import analyse, Analysis            # noqa: E402
from solver.budget import Budget                         # noqa: E402
from solver.generate import generate_wave                # noqa: E402
from solver.provider import build_provider, ProviderError  # noqa: E402
from solver.verify import verify                         # noqa: E402

# A reference that answered on only a handful of generated inputs has not
# verified much, and the status word should not pretend otherwise.
THIN_EVIDENCE_CASES = 4


def log(msg: str, budget: Budget | None = None) -> None:
    stamp = f"[{budget.elapsed_s:6.1f}s] " if budget else ""
    print(f"{stamp}{msg}", file=sys.stderr, flush=True)


def default_output(problem: dict, out: str | None) -> str:
    if out:
        return out
    ext = ".rs" if problem.get("language") == "rust" else ".py"
    return os.path.join("runs", f"{problem.get('problem_id','solution')[:12]}{ext}")


def solve(path: str, out_path: str | None, *, model: str, provider_kind: str,
          deadline_scale: float, n_candidates: int, run_dir: str | None) -> int:
    try:
        with open(path, encoding="utf-8") as fh:
            problem = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        log(f"cannot read problem: {exc}")
        return 2

    pid = problem.get("problem_id", "unknown")
    language = problem.get("language", "python")
    budget = Budget(deadline_s=float(problem.get("deadline_s", 300.0)), scale=deadline_scale)
    out_path = default_output(problem, out_path)
    run_dir = run_dir or os.path.join("runs", pid[:12])
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)

    log(f"{pid[:12]} | {language} | entry={problem.get('entrypoint')} | "
        f"budget {budget.total_s:.0f}s (reserve {budget.emit_reserve_s:.0f}s)", budget)

    try:
        provider = build_provider(provider_kind, model=model)
    except ProviderError as exc:
        log(f"provider unavailable: {exc}")
        return 3

    report: dict = {
        "problem_id": pid,
        "language": language,
        "entrypoint": problem.get("entrypoint"),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "no_candidate",
        "gates": {},
        "events": [],
    }

    def event(name: str, **kw) -> None:
        report["events"].append({"t": round(budget.elapsed_s, 2), "event": name, **kw})

    # ---- one parallel wave, analysis included ----------------------------------
    # Almost the whole budget belongs to the model calls, so everything that needs a model
    # starts at once: the trap pass, the reference, the input generator and the candidates.
    # The trap pass does not run first. It is usually the slowest call of the ten, and
    # waiting for it would cost more of the 300 s than its output is worth, so the `traps`
    # framing carries the static checklist instead and the analysed traps go to the report.
    # Measured across the ten recorded runs: local verification takes 17.1 s at the
    # median and 23.4 s at its slowest, Rust compiles included. The earlier reserves
    # were set before that measurement and were nearly twice what the phase ever
    # needed, which mattered because the trap pass is the long pole of the wave and
    # was being cut at its cap. These are the measured maximum, roughly doubled.
    verify_reserve_s = 45.0 if language == "rust" else 30.0
    call_timeout = max(budget.spendable_s - verify_reserve_s, 30.0)

    budget.start("generate")
    log(f"wave: analysis + oracle + generator + {n_candidates} framings "
        f"(timeout {call_timeout:.0f}s each)", budget)
    analysis: Analysis | None = None
    wave = None
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        fa = pool.submit(analyse, problem, provider, timeout_s=call_timeout)
        fw = pool.submit(generate_wave, problem, None, provider,
                         timeout_s=call_timeout, n_candidates=n_candidates)
        try:
            wave = fw.result()
        except Exception as exc:  # noqa: BLE001
            log(f"generation failed: {exc}", budget)
        try:
            analysis = fa.result()
        except Exception as exc:  # noqa: BLE001
            log(f"analysis failed: {exc}", budget)
    budget.end("generate")
    n_traps = len(analysis.traps) if analysis else 0
    log(f"analysis: {n_traps} traps", budget)
    event("analyse", traps=n_traps)

    n_ok = sum(1 for c in wave.candidates if c.ok) if wave else 0
    log(f"wave done: {n_ok} candidates, "
        f"oracle={'ok' if wave and wave.oracle and wave.oracle.ok else 'missing'}", budget)
    event("wave", candidates=n_ok, oracle=bool(wave and wave.oracle and wave.oracle.ok))

    if analysis:
        report["analysis"] = analysis.to_dict()
        with open(os.path.join(run_dir, "analysis.json"), "w", encoding="utf-8") as fh:
            json.dump(analysis.to_dict(), fh, indent=1, ensure_ascii=False)
        # `to_dict` drops the raw reply because it is large and redundant when the analysis
        # parsed. When it did not, the raw reply is the only thing that explains why.
        if analysis.raw and not analysis.traps:
            with open(os.path.join(run_dir, "analysis-raw.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(analysis.raw)

    if wave is None or not wave.usable:
        log("no usable candidate was produced", budget)
        report["status"] = "no_candidate"
        _write_report(run_dir, report, budget)
        return 3

    # Keep every artefact: the run is the evidence, and an unkept candidate cannot be audited.
    cand_dir = os.path.join(run_dir, "candidates")
    os.makedirs(cand_dir, exist_ok=True)
    ext = ".rs" if language == "rust" else ".py"
    for art in wave.candidates:
        if art.ok:
            with open(os.path.join(cand_dir, f"{art.framing}{ext}"), "w", encoding="utf-8") as fh:
                fh.write(art.source)
    if wave.oracle and wave.oracle.ok:
        with open(os.path.join(cand_dir, "oracle.py"), "w", encoding="utf-8") as fh:
            fh.write(wave.oracle.source)
    if wave.inputgen and wave.inputgen.ok:
        with open(os.path.join(cand_dir, "inputgen.py"), "w", encoding="utf-8") as fh:
            fh.write(wave.inputgen.source)

    # ---- local verification: execution only, no model calls --------------------
    budget.start("verify")
    log("verifying locally (no model calls)", budget)
    verification = verify(wave, problem, analysis, budget)
    budget.end("verify")

    best = verification.best()
    log(f"cases={verification.cases} "
        f"oracle={verification.oracle_answers}/{verification.cases} answered "
        f"clusters={len(verification.clusters)} divergence={verification.framing_divergence}",
        budget)
    for rep in sorted(verification.reports, key=lambda r: r.rank, reverse=True):
        log(f"  {rep.framing:<12} agree={rep.agree_oracle:<3} disagree={rep.disagree_oracle:<3} "
            f"crash={rep.crashed} timeout={rep.timed_out} fp={rep.behaviour or '-'}", budget)

    report["verification"] = {
        "cases": verification.cases,
        "oracle_ok": verification.oracle_ok,
        "oracle_answers": verification.oracle_answers,
        "oracle_unanswered": verification.oracle_unanswered,
        "oracle_error": verification.oracle_error,
        "generator_error": verification.generator_error,
        "clusters": verification.clusters,
        "framing_divergence": verification.framing_divergence,
        "ambiguity_note": verification.ambiguity_note,
        "notes": verification.notes,
        "candidates": [
            {
                "framing": r.framing, "compiled": r.compiled,
                "compile_error": r.compile_error,
                "agree": r.agree_oracle, "disagree": r.disagree_oracle,
                "crashed": r.crashed, "timed_out": r.timed_out,
                "behaviour": r.behaviour, "gates": r.gates,
                "first_disagreement": r.first_disagreement,
                "max_duration_s": round(r.max_duration_s, 4),
            }
            for r in sorted(verification.reports, key=lambda r: r.rank, reverse=True)
        ],
    }

    # ---- emit: the reserve exists so this always happens ------------------------
    budget.start("emit")
    chosen = None
    if best is not None:
        chosen = next((a for a in wave.candidates if a.framing == best.framing), None)
    if chosen is None:
        chosen = next((a for a in wave.candidates if a.ok), None)
    if chosen is None:
        report["status"] = "no_candidate"
        _write_report(run_dir, report, budget)
        return 3

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(chosen.source)
    budget.end("emit")

    verified = bool(best and best.compiled and best.disagree_oracle == 0
                    and best.agree_oracle > 0 and best.crashed == 0 and best.timed_out == 0)
    # Agreement on one input and agreement on eighteen are different claims, and one
    # word cannot carry both. A row where the reference could only answer a handful of
    # cases says so in the status, so the summary count does not quietly add it to the
    # rows that cleared eighteen.
    if verified and verification.oracle_answers < THIN_EVIDENCE_CASES:
        report["status"] = "verified_on_thin_evidence"
    else:
        report["status"] = "verified_against_reference" if verified else "emitted_unverified"
    report["final_candidate"] = chosen.framing
    report["gates"] = best.gates if best else {}
    report["output_path"] = out_path
    report["budget"] = budget.snapshot()
    report["model_usage"] = provider.usage()
    _write_report(run_dir, report, budget)

    log(f"wrote {out_path} from framing '{chosen.framing}' -> {report['status']}", budget)
    if verification.ambiguity_note:
        log(f"AMBIGUITY: {verification.ambiguity_note}", budget)
    return 0 if verified else 1


def _write_report(run_dir: str, report: dict, budget: Budget) -> None:
    report.setdefault("budget", budget.snapshot())
    with open(os.path.join(run_dir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False, default=str)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Solve one ChallengeBox problem.")
    ap.add_argument("problem", help="path to the problem JSON")
    ap.add_argument("-o", "--output", default=None, help="where to write the solution")
    ap.add_argument("--model", default="haiku",
                    help="model alias passed to the CLI (default: haiku, measured fastest)")
    ap.add_argument("--provider", default="claude-cli",
                    choices=["claude-cli", "openai-compatible", "openrouter"])
    ap.add_argument("--deadline-scale", type=float, default=1.0,
                    help="shrink the budget to exercise the emit-under-pressure path")
    ap.add_argument("--candidates", type=int, default=7, help="how many framings to run")
    ap.add_argument("--run-dir", default=None, help="where artefacts and the report land")
    args = ap.parse_args(argv)

    return solve(args.problem, args.output, model=args.model, provider_kind=args.provider,
                 deadline_scale=args.deadline_scale, n_candidates=args.candidates,
                 run_dir=args.run_dir)


if __name__ == "__main__":
    sys.exit(main())
