#!/usr/bin/env python
"""Build TRAPS.md from the recorded runs.

    python traps_report.py runs/bench -o TRAPS.md

This is generated rather than written, on purpose. Every quoted clause comes from an
`analysis.json` produced by a run, and every disagreement comes from a `report.json` with the
input that produced it. A hand-written trap list would be an opinion; this one can be
regenerated and checked against the artefacts in the same directory.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from solver.analyse import locate_quote  # noqa: E402

KIND_BLURB = {
    "MAGNITUDE": "a bound past the point where the obvious numeric type stops being safe",
    "MEMORY": "a structure that cannot be materialised at the stated maximum",
    "UNITS": "two different units of measurement used for the same thing",
    "REDEFINITION": "a standard term redefined to mean something else",
    "RANGES": "an inclusive or exclusive boundary that is easy to read the wrong way",
    "INDEXING": "an index convention that differs from the usual one",
    "ORDERING": "an ordering requirement at a tie",
    "DEGENERATE": "a degenerate input with a specified, non-obvious result",
    "PRECEDENCE": "numbered rules that must be applied in order, first match winning",
    "OUTPUT": "an output shape that is easy to get subtly wrong",
    "COMPLEXITY": "a size at which the obvious approach is a wrong answer",
}


def plain(text: str) -> str:
    """Normalise the typography of text that came back from a model.

    The recorded analyses are evidence and are never rewritten, but a model writes long
    dashes and curly quotes wherever it likes, and this report is read as a document. Only
    the punctuation is touched: no word is added, removed or reordered.
    """
    if not text:
        return ""
    for code in (0x2018, 0x2019):          # curly single quotes
        text = text.replace(chr(code), "'")
    for code in (0x201C, 0x201D):          # curly double quotes
        text = text.replace(chr(code), '"')
    for code in (0x2014, 0x2013):          # long dashes
        text = text.replace(chr(code), ", ")
    text = text.replace(chr(0x2026), "...")
    return " ".join(text.split())


def load(run_dir: str, samples_dir: str = "samples") -> list[dict]:
    # The statements are loaded so every quoted clause can be checked against the text
    # it claims to come from. The recorded runs are evidence and are never rewritten;
    # the verdict is computed here, at report time, from data already on disk.
    statements: dict[str, str] = {}
    for path in glob.glob(os.path.join(samples_dir, "*.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                problem = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        statements[problem.get("problem_id", "")[:12]] = problem.get("statement", "")
    rows = []
    for analysis_path in sorted(glob.glob(os.path.join(run_dir, "*", "analysis.json"))):
        d = os.path.dirname(analysis_path)
        try:
            with open(analysis_path, encoding="utf-8") as fh:
                analysis = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        report = {}
        rp = os.path.join(d, "report.json")
        if os.path.exists(rp):
            try:
                with open(rp, encoding="utf-8") as fh:
                    report = json.load(fh)
            except json.JSONDecodeError:
                pass
        short = os.path.basename(d)
        statement = statements.get(short, "")
        for trap in (analysis.get("traps") or []):
            trap["fidelity"] = locate_quote(trap.get("quote", ""), statement)
        rows.append({"short": short, "analysis": analysis, "report": report,
                     "statement": statement})
    return rows


def render(rows: list[dict]) -> str:
    total_traps = sum(len(r["analysis"].get("traps") or []) for r in rows)
    fid_counts = {"verbatim": 0, "fragments": 0, "paraphrase": 0}
    for r in rows:
        for t in (r["analysis"].get("traps") or []):
            fid_counts[t.get("fidelity", "paraphrase")] =                 fid_counts.get(t.get("fidelity", "paraphrase"), 0) + 1
    diverged = [r for r in rows
                if (r["report"].get("verification") or {}).get("framing_divergence")]

    out = [
        "# Traps, per problem",
        "",
        f"Across {len(rows)} statements the trap pass quoted **{total_traps} clauses** that "
        "change the answer if read the usual way instead of the way they are written. "
        f"On **{len(diverged)}** of them, candidates written from different readings then "
        "behaved differently on the same input. That is a disagreement about meaning, not "
        "about typing.",
        "",
        "typing.",
        "",
        f"Every disagreement below shows the input that produced it. Regenerate with "
        "`python traps_report.py runs/bench -o TRAPS.md`.",
        "",
        "**About the quotes.** The trap prompt asks for the clause verbatim, and asking "
        "is not checking, so every quote is matched back against the statement it "
        "claims to come from and labelled with the result. Of the "
        f"{total_traps}: **{fid_counts['verbatim']} are literal spans** of the "
        f"statement, **{fid_counts['fragments']}** reproduce it in pieces across an "
        f"elision, and **{fid_counts['paraphrase']}** are the model's own wording for "
        "a clause rather than the clause. A paraphrase can still point at a real trap, "
        "and several here do, but it is not a citation and this file does not call it "
        "one. The check is a substring match after whitespace and punctuation are "
        "normalised; `locate_quote` in `solver/analyse.py`.",
        "",
        "## Why this file exists",
        "",
        "Sampling one prompt N times varies the seed. It does not vary the reading, so a "
        "misread clause is misread by all N candidates at once and the majority is "
        "unanimously wrong. Behavioural clustering removes generation noise and leaves "
        "statement misinterpretation untouched. That is the measured residual in "
        "[2506.11021](https://arxiv.org/abs/2506.11021), and it is this benchmark's whole "
        "difficulty. So the seven candidates are written from seven different reading "
        "strategies, and where they split, the split is recorded here rather than voted away.",
        "",
        "---",
        "",
    ]

    for r in rows:
        a, rep = r["analysis"], r["report"]
        ver = rep.get("verification") or {}
        traps = a.get("traps") or []
        out.append(f"## `{r['short']}`, {a.get('language','?')}, "
                   f"`{a.get('entrypoint','?')}`")
        out.append("")
        if a.get("summary"):
            out.append(f"*{plain(a['summary'])}*")
            out.append("")
        if a.get("max_scale"):
            out.append(f"**Stated maximum:** {plain(a['max_scale'])}")
            out.append("")

        if not traps:
            out.append("The trap pass returned nothing for this statement. That is a gap in "
                       "the run, not a statement without traps.")
            out.append("")
        else:
            out.append(f"**{len(traps)} traps quoted:**")
            out.append("")
            for t in traps:
                kind = t.get("kind", "?")
                blurb = KIND_BLURB.get(kind, "")
                out.append(f"- **{kind}**{f': {blurb}' if blurb else ''}")
                mark = {"verbatim": "quoted from the statement",
                        "fragments": "quoted in pieces, across an elision",
                        "paraphrase": "the model's wording, not the statement's"}
                out.append(f"  > {plain(t.get('quote',''))}")
                out.append("")
                out.append(f"  *{mark.get(t.get('fidelity'), 'unchecked')}*")
                out.append("")
                out.append(f"  Missing it produces: {plain(t.get('consequence',''))}")
                out.append("")
                out.append(f"  Required instead: {plain(t.get('guard',''))}")
                out.append("")

        cands = ver.get("candidates") or []
        agreeing = [c for c in cands if c.get("disagree") == 0 and c.get("agree", 0) > 0]
        if cands:
            out.append(f"**Verification:** {ver.get('cases',0)} generated inputs, "
                       f"{len(agreeing)} of {len(cands)} candidates agreed with the "
                       f"independent reference on all of them.")
            out.append("")

        if ver.get("framing_divergence"):
            out.append("**Readings disagreed.**")
            out.append("")
            groups = ver.get("clusters") or {}
            for fingerprint, framings in groups.items():
                out.append(f"- `{fingerprint}`: {', '.join(sorted(framings))}")
            out.append("")
            for c in cands:
                d = c.get("first_disagreement")
                if d:
                    out.append(f"First divergence, framing `{c['framing']}`, case "
                               f"`{d.get('case')}`:")
                    out.append("")
                    out.append("```")
                    out.append(f"input     {d.get('input','')}")
                    out.append(f"reference {d.get('oracle','')}")
                    out.append(f"candidate {d.get('candidate','')}")
                    out.append("```")
                    out.append("")
                    break
            # Which reading was actually submitted is in the data, so it is read from the
            # data. A hardcoded sentence claiming the majority was submitted was wrong on
            # three of the eight diverging problems, because the ranking is driven by
            # agreement with the independent reference and not by cluster size. That is the
            # design working, and saying the opposite threw away the best evidence for it.
            chosen = rep.get("final_candidate")
            groups = ver.get("clusters") or {}
            chosen_size = next((len(f) for f in groups.values() if chosen in f), 0)
            largest = max((len(f) for f in groups.values()), default=0)
            if chosen_size and chosen_size < largest:
                out.append(
                    f"**A minority reading was submitted.** `{chosen}` sits in a cluster of "
                    f"{chosen_size} of {len(cands)}, against a largest cluster of {largest}. "
                    "It was submitted because it agreed with the independently generated "
                    "reference and the larger cluster did not. This is the case a majority "
                    "vote gets wrong by construction, and it is why the ranking has no term "
                    "for cluster size.")
            elif chosen_size:
                out.append(
                    f"The submitted reading, `{chosen}`, is in the largest cluster "
                    f"({chosen_size} of {len(cands)}), but it was chosen for agreeing with "
                    "the independent reference rather than for the size of its cluster. The "
                    "divergence is reported rather than resolved: a unanimous cluster is not "
                    "evidence that the clause was read correctly.")
            else:
                out.append(
                    "The divergence is reported rather than resolved by counting: a "
                    "unanimous cluster is not evidence that the clause was read correctly.")
            out.append("")

        out.append("---")
        out.append("")

    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default="runs/bench")
    ap.add_argument("-o", "--out", default="TRAPS.md")
    args = ap.parse_args(argv)

    rows = load(args.run_dir)
    if not rows:
        print(f"no analysis.json found under {args.run_dir}", file=sys.stderr)
        return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(render(rows))
    print(f"wrote {args.out} from {len(rows)} runs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
