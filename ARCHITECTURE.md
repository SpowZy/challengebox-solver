# ChallengeBox solver, architecture

    python solve.py samples/<id>.json -o out.py     # one problem
    python bench.py samples/ -o runs/bench          # all of them, writes RESULTS.md

Exit codes: `0` a solution was written and agreed with an independent reference on every
generated input, `1` a solution was written but some check did not pass or could not run,
`2` the problem file was unreadable, `3` nothing could be produced.

Every figure in this document and in `RESULTS.md` comes from a run recorded under `runs/`.
Nothing here is estimated.

---

## The problem this is actually solving

Ten statements, no public examples, 300 seconds each, binary scoring. The README says the
problems "hide traps, such as huge numeric bounds, structures that cannot be fully built in
memory, or small wording details that change the answer", and that "a single write the code
prompt will usually fail".

Reading the samples confirms the shape. In `4e49a099` the grapheme rules are **not** UAX#29:
six numbered rules are given and the statement says "rule order is authoritative", so a
solution that reaches for a real Unicode segmentation library is wrong by construction.
Indices resolve negatives *then* clamp, in that order. Offsets are UTF-16 code units, not
bytes and not code points.

So the failure mode to engineer against is not "the model cannot code". It is **the model
codes the problem it expected instead of the problem on the page**.

That distinction decides the whole design, because the standard toolkit does not address it.

## Why sampling more candidates does not help here

The published state of the art for this task is roughly: sample N candidates in parallel,
cluster them by behaviour, pick the medoid, repair on failure. It works. On LiveCodeBench
with Qwen2.5-Coder-7B, S\* takes 29.4% zero-shot to 54.4%
([2502.14382](https://arxiv.org/abs/2502.14382)), and behavioural clustering drops the error
rate from about 65% to 2% ([2506.11021](https://arxiv.org/abs/2506.11021)).

The same paper says what the remaining 2% is: *the residual errors come from misinterpreting
the statement, not from generation noise*.

That is the whole difficulty. **Agreement between candidates measures sampling noise, and is
structurally blind to a shared misreading.** Sample one prompt seven times and seven
candidates inherit the same wrong reading; the cluster is unanimous, the medoid is confident,
and the confidence peaks exactly where it is wrong. AlgoBench measures the size of this
effect directly: on trap variants, Claude Haiku 4.5 falls from 86.5% to 55.8% with a TrapRate
of 22.7%, and newer models still lose a third
([2607.00062](https://arxiv.org/abs/2607.00062)).

So this system samples seven candidates and **does not vote**.

---

## 1. How traps are found and handled

Two mechanisms, one static and one measured.

**A trap pass runs before any code exists.** It applies a fixed eleven-point checklist:
magnitude past 2^53, materialisability, which unit each index counts, terms redefined against
their standard meaning, inclusive versus exclusive, negative-index resolution order, tie
ordering, degenerate input, numbered-rule precedence, exact output shape, and cost at the
stated maximum. The checklist is fixed rather than generated, and every item is phrased as a
question so the answer has to be looked up in the statement instead of assumed. Output is
structured: each trap must quote the clause that creates it, or it is not reported.
See `solver/analyse.py`.

It quoted six clauses on every one of the ten statements, sixty in total. On `1ba0d34f` two of
the six were magnitude traps, *"run counts are at most `10^18`"* and *"cost = min(2\*\*old_level,
spin_limit) where level_cap <= 60"*, and that is the clause the verification pass then caught a
candidate on, which is the sequence this design is built to produce.

**Seven candidates are written from seven different readings.** Not seven samples of one
prompt, but seven prompts that instruct a different reading strategy: implement literally clause
by clause; assume the obvious reading is wrong and find where; restate the specification
first and implement the restatement; enumerate the degenerate cases first; derive the
required complexity first; work through the trap checklist; and one plain control. All seven
run concurrently, so the variation costs nothing in wall clock.

This is metamorphic *prompt* testing rather than metamorphic input testing: varying the
reading of the statement rather than the seed. It is the one published defence against shared
misinterpretation ([2406.06864](https://arxiv.org/abs/2406.06864): 75% detection of erroneous
programs, 8.6% false positives). That paper is from 2024 and its numbers are not transposable
to 2026 models; the mechanism is what carries over, not the percentages.

## 2. How a solution is verified without public examples

Three artefacts are generated **independently of each other**, in the same parallel wave:

* an **oracle**, deliberately slow and literal, prompted for fidelity to the wording and
  explicitly away from cleverness, always in Python even for the Rust problems so it can be
  compared against a Rust candidate through stdin and stdout;
* an **input generator**, a Python `gen(rng, scale)` producing valid inputs at three
  magnitudes, so every generated input respects the statement's constraints (an invalid input
  makes two implementations disagree for reasons that mean nothing). Unlike the two
  implementations, this one is not an independent opinion: it is told the exact signature
  parsed from the statement, and an input whose arity does not match it is rejected as a
  generator error before anything downstream runs. See *What running it changed* below for
  what that costs when it is missing;
* the **seven candidates** above.

Then the whole remaining budget is spent executing, with **no further model calls**. That is
a deliberate choice with evidence behind it: across 18 published configurations,
the best execution-based selector beats majority voting on output patterns by 19 to 52
percentage points ([2605.08680](https://arxiv.org/abs/2605.08680), the figure is in its
abstract). Selection by running the code is measured against selection by inspecting it, and
running it wins, so this system never asks a model to grade code.

Each candidate is run against every generated input and compared to the oracle. Comparison is
structural for Python return values, with tuples and lists normalised to the same form since
JSON has no tuple; for Rust it is token-for-token on stdout, matching the statement's own rule
that output is compared by splitting on ASCII whitespace. The per-candidate result is a
fingerprint string over all cases (`=` agreed, `!` disagreed, `X` crashed, `T` timed out),
and identical fingerprints are one behavioural cluster.

**The stated shape is checked separately from the answer.** The assignment fixes what a
solution must look like as well as what it must compute: Python defines the named entrypoint,
standard library only, no I/O; Rust is one program with `fn main`, standard library only. A
solution that breaks that shape scores zero however correct its logic is, and none of those
properties needs a model to check. `compliance.py` walks the Python AST rather than matching
text, since a comment mentioning `print` is not a call to it, and reads the `use` declarations
on the Rust side. All ten emitted solutions pass:

    python compliance.py runs/bench    ->  10/10 emitted solutions obey every stated constraint

**Rust gets a second build.** The timing build uses `overflow-checks=off`, matching what a
judge is assumed to compile; a second build with checks on is run on the largest input.
Release Rust wraps signed integers silently, so a solution that overflows `i64` at maximum
scale returns a wrong answer with no crash and no warning. Verified here directly:
`i64::MAX + 1` printed `-9223372036854775808` without checks and panicked with them.
This gate proves the arithmetic did not wrap; it does not prove the answer is right at that
scale, because the oracle cannot produce an expected value for a maximum-size input.

**When clusters disagree, the disagreement is reported, not resolved by majority.** If
candidates written from different readings behave differently on the same input, the
difference is about what the problem means, not about who typed it wrong. `RESULTS.md`
records the input, both answers, and which framings fell on each side. On `1ba0d34f` this
fired: six candidates and the reference agreed on all 18 inputs while the complexity-first
framing disagreed on 10, and the first input they split on carried a credit cap of 10^30,
the same magnitude clause the trap pass had quoted before any code existed. Eight of the ten
statements produced a divergence like this.

## 3. What happens when time runs out

The budget is monotonic and carved before anything starts, and the emit phase holds a reserve
that no other phase may spend. `solver/budget.py`.

**Enforcement is global rather than per phase, and that is a decision worth stating.** The
budget does allocate a share to each phase, but those shares are used for reporting; what
actually stops work is the global check `spendable_s <= 3 s`, asked before every unit of work:
before each generated input during the reference pass, before each input for each candidate,
and before each compile. The wave is the reason. Nine model calls run as one indivisible
parallel burst, so cutting it at a phase allocation would discard every candidate still in
flight and leave nothing to emit, which is the opposite of what the reserve exists for. Its
timeout is therefore derived from the global clock: everything spendable, minus what
verification is expected to need. The only hard floor anywhere in the system is the emit
reserve.

The ordering follows from the scoring rule: a missing file scores zero for certain, an
unverified file scores whatever it scores. So the reserve is inviolable, verification is
interruptible at any point (a partially verified candidate still ranks), and the ranking
degrades gracefully: compiles, then agrees with the reference, then does not crash, then
agrees on more inputs, then is faster. The best available candidate is written even when
nothing passed every gate, and the status field says which case it was.

Measured across the ten recorded runs: the whole problem finishes in 173 s at the median and
226 s at its slowest, against a 300 s deadline, ten times out of ten. The wave takes 160 s at
the median and local verification 17 s. Every one of those numbers is reproduced by
`python figures.py runs/bench`. `--deadline-scale` shrinks the budget to exercise the
degradation path without editing the samples.

**Where the degradation stops, stated rather than glossed.** Graceful degradation has a
floor, and it is worth being exact about it. Run at `--deadline-scale 0.12`, a 36 s budget, and
the tool produces nothing and exits 3, because one generation through this provider costs
106 s at the median and no candidate exists to rank. That is a physical limit of the
provider, not a bug in the ranking, and emitting a stub to avoid an empty directory would be
theatre: the scoring rule gives zero for a wrong answer and zero for a missing file alike, so
a placeholder buys nothing and hides the failure.

Between those extremes the degradation is real, and it was measured rather than asserted. The
same problem at `--deadline-scale 0.60`, a 180 s budget, still finished in 142 s with a
solution that agreed with the reference on all 18 generated inputs, and still reported the
divergence between readings. Both endpoints are reproducible in one command each:

    python solve.py samples/<id>.json --deadline-scale 0.12   # 36 s  -> exit 3, nothing emitted
    python solve.py samples/<id>.json --deadline-scale 0.60   # 180 s -> exit 0, verified

Candidates that return are ranked and the best is emitted even if verification was cut
short mid-pass, and `RESULTS.md` records how many of the seven actually returned.

---

## What running it changed

Both published forks of this assignment stop at an architecture document. One of them says so
in its own words: the benchmark was never executed because no API key was configured. This
system was run, and running it found three defects that reading it does not reveal. They are
listed here because each one silently corrupted a result while every test still passed.

**1. The input generator is a fixture, not a second opinion.** The oracle, the seven
candidates and the generator were all prompted independently from the same statement. That is
correct for the implementations, whose disagreement is the signal this system exists to
produce. It is wrong for the generator: on `2beff58f` the generator represented an index entry
as a positional tuple while the reference and six of the seven candidates represented it as a
mapping, and on `6eca8a91` the generator returned five arguments for a function the statement
declares with four. In both cases the reference then failed on every input and the run reported
`0 of 7 candidates agreed`, which blames the candidates for the fixture's error.

The fix is not a better prompt. The statement names the function and its parameters verbatim
in its first line, so the signature is parsed with a regular expression and handed to the
reference, the candidates and the generator alike. A generated input whose arity does not match
is then a detectable generator error, reported as one, instead of a mystery downstream.
`solver/signature.py`, and the payload check in `build_cases`.

**2. A tuple of arguments is a list of arguments.** `build_cases` wrapped any non-list return
in a single-element list, so a generator returning a 3-tuple for a three-parameter function
produced a one-argument call. `normalise()` had always treated tuples and lists as the same
thing when comparing answers; this path did not, and the inconsistency stayed invisible until
the two met on one problem.

**3. The benchmark was not reproducible, and that was the worst of the three.** Input seeds came
from `hash((scale, i))`. Python salts string hashing per process, so every run drew a different
set of inputs. Two replays of the *same stored artefacts* gave 7 of 7 candidates agreeing and
then 0 of 7, with no model call in between. A results table that moves when you rerun it is not
evidence of anything. Seeds now come from `zlib.crc32`, and a test asserts the seed list is
identical across two separate interpreter processes.

None of the three is exotic. All three are the kind of defect that only appears when the thing
runs end to end on real output, which is the argument for running it.

## One finding the fix does not answer

Fixing the generator on `2beff58f` stopped a fixture bug from destroying a run. It did not
settle what that run was pointing at, and the distinction is worth keeping separate.

The statement writes, of the index it operates on:

> An entry has `namespace`, `name`, `version`, and nonempty opaque `hash`.

It names the fields. It never says what holds them. In the same statement the *output* is
pinned down exactly, as a tuple: *return one tuple per reference*, `(status, namespace,
location, hash)`. So the statement uses positional notation where it constrains the answer,
and field-name prose where it describes the input.

Seven implementations were written from that sentence and they split six to one:

    literal, restate, traps, edgefirst, complexity, oracle    entry['namespace']
    plain                                                     namespace, name, version, h = entry

Both are defensible readings of the same sentence, and this is not a difference of skill. It
is the failure mode the assignment describes as *small wording details that change the answer*,
sitting in the input format rather than in the algorithm, where no amount of local verification
can settle it: whichever container the hidden tests pass, the other six or the other one crash
immediately on the first access, and everything downstream of that is noise.

Nothing here resolves it, and inventing a resolution would be the wrong move. What the system
does is notice it, name the clause, and put both readings in front of a human with the line
that produced them. A majority vote would have reported six to one as consensus and thrown
away the only candidate that would have survived if the tests use tuples.

## Replaying a run without spending anything

Every artefact a run generates is kept under `runs/<id>/candidates/`. `replay.py` rebuilds the
wave from those files and re-runs verification against them with no model calls:

    python replay.py runs/bench

The model output is held fixed and only the harness moves, so a change to the checking logic is
measurable on its own, in seconds, at no cost. All three defects above were found this way, and
the before-and-after is recorded rather than asserted: `runs/RESULTS-v1-before-harness-fixes.md`
is the table produced before the fixes, kept on purpose.

---

## Cost

The provider is an interface, not a vendor. Two implementations ship: the local `claude` CLI
in print mode, and any OpenAI-compatible endpoint. The CLI path needs no API key, which is
why this system could be benchmarked rather than only described.

**Why the benchmark runs on the small model.** Every recorded run uses the `haiku` alias, and
that is deliberate rather than a cost dodge. What is being measured here is the harness, not
the model: nine concurrent calls, a reference, an input generator, differential execution and
a ranking. A larger model would raise the agreement numbers and tell you nothing about whether
the checking works, whereas a model that AlgoBench measures losing thirty points on trap
variants ([2607.00062](https://arxiv.org/abs/2607.00062)) puts the harness under exactly the
pressure it was built for. Swapping the alias is one flag, and none of the mechanisms above
change with it.

Cost control is structural rather than a cap bolted on afterwards. The expensive resource is
serialised model calls, and the design has exactly one wave of them: nine concurrent calls,
then everything else is local execution. Measured over 100 calls across the ten runs, none of
which failed: a single call costs 106 s at the median, and the whole wave of nine concurrent
calls costs 160 s: the wave ends when its slowest call returns, so eight extra generations
cost about half again as much as one, not nine times. Repair is deliberately absent from the
hot path: the
published gain collapses after two rounds and assertion-level logic errors are only repaired
about 45% of the time ([2604.10508](https://arxiv.org/abs/2604.10508)), which is to say
repair fixes crashes, not misreadings, and misreadings are this benchmark's failure mode.

## What was considered and rejected, with reasons

| Rejected | Why |
|---|---|
| Majority vote over candidates | Blind to shared misreading, the dominant failure here; 19 to 52 points below execution-based selection ([2605.08680](https://arxiv.org/abs/2605.08680)) |
| LLM-as-judge selection | It cannot see what it did not run, and execution-grounded selection is measured ahead of pattern-based selection by 19 to 52 points ([2605.08680](https://arxiv.org/abs/2605.08680)) |
| Model-written tests as ground truth | Directly generated tests score under 10% verifier accuracy, on a benchmark of 1,840 problems ([2507.06920](https://arxiv.org/abs/2507.06920); both figures are in the body, not the abstract) |
| Multi-agent debate | 2.1 to 3.4 times the tokens for equal or worse accuracy; consensus collapse discards correct answers already in the pool ([2605.00914](https://arxiv.org/abs/2605.00914)) |
| Forced chain-of-thought | 46.0% → 36.8% on 315 Codeforces problems ([2606.05228](https://arxiv.org/abs/2606.05228)) |
| Formal verification | 5.29% end to end ([2605.08553](https://arxiv.org/abs/2605.08553)) |
| N = 64 generation | The pattern works but the wall clock does not fit 300 s |

## Limitations, stated plainly

* **The hidden tests are not available.** `RESULTS.md` measures local gates. A row saying a
  candidate agreed with the reference on 18 inputs is not a claim of a point.
* **Shared misreading is reduced, not eliminated.** The oracle and a candidate can still read
  the same sentence the same wrong way. Varying the framing raises the chance that at least
  one reading differs; it does not guarantee it.
* **Large-scale correctness is inferred, not verified.** Agreement holds at small and medium
  magnitude; at maximum size only timing and overflow are measured, because no reference can
  produce the expected answer there.
* **Agreement on two inputs and agreement on eighteen are different claims.** The reference is
  deliberately slow, so it sometimes cannot answer within its per-case timeout, and those cases
  are dropped. `RESULTS.md` therefore carries a *Ref answered* column: a row where the
  reference answered three of eighteen inputs is a weaker result than the same row at eighteen,
  and the table says which one it is instead of collapsing both into "verified".
* **Judge time limits are unknown.** A solution finishing in 4 s locally may fail a 2 s judge.
* **Model latency varies.** The wave is capped so a slow call is abandoned rather than
  allowed to eat the deadline, which means a run can proceed with five candidates instead of
  seven. `RESULTS.md` records how many actually returned.
