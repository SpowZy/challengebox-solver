# ChallengeBox, an AI Challenge Problem Solver

A system that takes a problem JSON and writes a solution file before the deadline, for
statements with no public examples and deliberate traps in the wording.

```bash
python solve.py samples/<id>.json -o out.py     # one problem
python bench.py samples/ -o runs/bench          # all ten, writes RESULTS.md
python traps_report.py runs/bench -o TRAPS.md   # the trap analysis, from those runs
python replay.py runs/bench                     # re-verify recorded runs, no model calls
python compliance.py runs/bench                 # every solution against the stated rules
python figures.py runs/bench                    # every measured figure the docs quote
python tests.py                                 # the deterministic tests
```

No API key is required: the model provider is the local `claude` CLI by default. An
OpenAI-compatible endpoint can be selected with `--provider openai-compatible` without
touching the source.

Requires Python 3.11+ and, for the Rust problems, `rustc` on PATH.

## Read these in order

1. **[RESULTS.md](RESULTS.md)**: what happened when the system was actually run on all ten
   samples. Every number comes from an execution recorded under `runs/`.
2. **[ARCHITECTURE.md](ARCHITECTURE.md)**: how it works and why, with the three questions
   from the assignment answered directly.
3. **[TRAPS.md](TRAPS.md)**: the traps found in each statement, quoted, and where different
   readings of the same statement produced different behaviour.

## The one idea

The assignment says the problems hide traps and that a single "write the code" prompt will
usually fail. The failure that matters is not that a model cannot code. It is that a model
codes **the problem it expected instead of the problem on the page**: real Unicode
segmentation instead of the six rules given, exclusive ranges instead of inclusive, byte
offsets instead of UTF-16 code units.

The standard defence against a bad generation is to sample many and take the majority. That
defence does not apply here. Sampling one prompt seven times varies the seed, not the
reading, so a misread clause is misread by all seven at once and the majority is unanimously
wrong at exactly the moment it looks most confident.

So this system generates seven candidates from **seven different reading strategies**:
literal clause-by-clause, adversarial, restate-then-implement, edge-cases-first,
complexity-first, trap-checklist, and one plain control. It does not vote. It runs
them all against an independently generated reference implementation on generated inputs,
and where candidates from different readings disagree, it reports the disagreement with the
input that caused it instead of averaging it away.

It fires often. Across the ten samples, **8 of 10** statements produced a divergence between
readings, and **9 of 10** solutions agreed with an independently generated reference on every
input it could answer. The single "write the code" prompt, running alongside the other six on
every problem, reached 5 of 10 on its own.

On the first sample the sequence ran end to end: the trap pass quoted a magnitude clause
before any code existed, then six candidates and the reference agreed on all 18 generated
inputs while the complexity-first reading disagreed on 10, first splitting on an input whose
credit cap was 10^30, the same clause the trap pass had flagged.

## Layout

```
solve.py            one problem in, one solution file out
bench.py            runs every sample, writes RESULTS.md
replay.py           re-runs verification over recorded artefacts, without spending anything
report_only.py      rebuilds RESULTS.md from recorded runs
compliance.py       checks every emitted solution against the assignment's own rules
figures.py          re-derives every number the documents quote, from those runs
traps_report.py     builds TRAPS.md from recorded runs
tests.py            deterministic tests: no model calls, no network
solver/
  analyse.py        the fixed trap checklist and the pass that applies it
  generate.py       the seven framings, the reference, the input generator
  signature.py      parses the entrypoint signature out of the statement, so nothing guesses it
  verify.py         differential execution, behavioural clustering, ranking
  budget.py         monotonic clock with an emit reserve nothing else may spend
  provider.py       model access behind an interface; claude CLI or any OpenAI-compatible host
  sandbox/          isolated execution for Python and Rust, including the overflow-checked build
runs/               every artefact from every run: candidates, reference, report, analysis
```

`runs/` is committed on purpose. The candidates, the reference, the generated inputs and the
reports are what make `RESULTS.md` checkable rather than merely asserted, and `replay.py`
re-derives every verification number from them in seconds without a single model call.
