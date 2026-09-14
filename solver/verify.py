"""Decide which candidate to submit, using execution only. No model calls happen here.

The whole budget after the generation wave belongs to this module, and it spends it running
code rather than asking anything. That is deliberate: on 18 published configurations,
execution-based selectors beat majority voting on output patterns by 19 to 52 points
(2605.08680), and LLM-as-judge selection underperforms adaptive input synthesis (2502.14382).

Two signals are collected, and they mean different things.

**Agreement** across candidates is evidence about implementation noise. Candidates that were
given the same reading of the statement and produce the same outputs are probably not buggy.

**Divergence across framings** is evidence about the statement. The candidates were written
from deliberately different readings, so when two framings disagree, the disagreement is about
what the problem means, not about who typed it wrong. That is the trap signal, and it is
reported rather than voted away. A majority of candidates sharing a misreading is precisely
the failure mode that clustering cannot see (2506.11021).
"""

from __future__ import annotations

import json
import random
import zlib
from dataclasses import dataclass, field

from .analyse import Analysis
from .generate import Artifact, Wave
from .signature import Signature, parse_signature
from .sandbox import (
    ExecResult,
    call_function,
    compile_rust,
    is_overflow_panic,
    run_binary,
    run_stdin,
    rust_available,
    syntax_ok,
)

ORACLE_TIMEOUT_FACTOR = 3.0   # the reference is deliberately slow; see verify()
SCALES = ("edge", "small", "medium")


# ---- comparison ------------------------------------------------------------------

def normalise(value):
    """Structural form that survives the JSON round trip on both sides.

    A reference returning a tuple and a candidate returning a list are the same answer; JSON
    has no tuple, so both arrive as lists and are compared as such. Floats are rounded to a
    tolerance because a difference in the twelfth decimal is not a disagreement about the
    problem.
    """
    if isinstance(value, (list, tuple)):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {str(k): normalise(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if value == int(value):
            return int(value)
        return round(value, 9)
    return value


def tokens(text: str) -> list[str]:
    """Judge-equivalent tokenisation: split on ASCII whitespace, compare exactly."""
    return text.split()


def same_value(a, b) -> bool:
    return normalise(a) == normalise(b)


def same_output(a: str, b: str) -> bool:
    return tokens(a) == tokens(b)


# ---- input generation ------------------------------------------------------------

@dataclass
class Case:
    scale: str
    seed: int
    payload: object          # args list (python) or stdin string (rust)

    def label(self) -> str:
        return f"{self.scale}#{self.seed}"


def build_cases(inputgen: Artifact | None, language: str, *,
                signature: Signature | None = None,
                per_scale: int = 6, timeout_s: float = 8.0) -> tuple[list[Case], str | None]:
    """Run the generated generator to get valid inputs. Returns (cases, error).

    The generator is a fixture, not a second opinion. When it disagrees with the statement
    about the shape of an input, nothing downstream means anything, and the symptom appears
    far from the cause as "the reference failed on every input". So its output is checked
    against the signature parsed from the statement before any of it is used, and a mismatch
    is reported as the generator error it is.
    """
    if inputgen is None or not inputgen.ok:
        return [], "no input generator was produced"
    ok, err = syntax_ok(inputgen.source)
    if not ok:
        return [], f"input generator does not parse: {err}"

    cases: list[Case] = []
    failures = 0
    arity_errors: list[str] = []
    for scale in SCALES:
        for i in range(per_scale):
            # NOT hash(): Python salts string hashing per process, so hash((scale, i))
            # gave different seeds on every run and the same artefacts scored
            # differently twice in a row. A results table has to be reproducible.
            seed = zlib.crc32(f"{scale}#{i}".encode()) & 0xFFFF
            driver = (
                inputgen.source
                + f"\n\ndef __drive():\n"
                f"    import random\n"
                f"    return gen(random.Random({seed}), {scale!r})\n"
            )
            res = call_function(driver, "__drive", [], timeout_s=timeout_s)
            if not res.ok:
                failures += 1
                continue
            payload = res.value
            if language == "rust":
                if not isinstance(payload, str):
                    failures += 1
                    continue
            else:
                # A tuple of arguments is a list of arguments. `normalise` already treats the
                # two as one thing; collapsing a returned 3-tuple into a single argument here
                # silently produced a one-argument call to a three-parameter function.
                if isinstance(payload, tuple):
                    payload = list(payload)
                elif not isinstance(payload, list):
                    payload = [payload]
                if signature is not None and len(payload) != signature.arity:
                    arity_errors.append(
                        f"{len(payload)} argument(s) for {signature.describe()}")
                    failures += 1
                    continue
            cases.append(Case(scale=scale, seed=seed, payload=payload))

    err = None
    if not cases:
        if arity_errors:
            err = ("input generator does not match the signature in the statement: "
                   f"it returned {arity_errors[0]}")
        else:
            err = f"generator produced no usable input ({failures} failures)"
    elif arity_errors:
        err = (f"{len(arity_errors)} generated input(s) dropped for not matching "
               f"{signature.describe()}")
    return cases, err


# ---- running one artefact --------------------------------------------------------

@dataclass
class Runner:
    """Executes one artefact against cases, hiding the python/rust difference."""

    artifact: Artifact
    entrypoint: str
    language: str
    binary: str | None = None
    compile_error: str | None = None

    def prepare(self, *, timeout_s: float = 60.0, overflow_checks: bool = False) -> bool:
        if self.language != "rust" or self.artifact.role == "oracle":
            ok, err = syntax_ok(self.artifact.source)
            if not ok:
                self.compile_error = err
                return False
            return True
        if not rust_available():
            self.compile_error = "rustc not available"
            return False
        build = compile_rust(self.artifact.source, overflow_checks=overflow_checks,
                             timeout_s=timeout_s)
        if not build.ok:
            self.compile_error = (build.error or "compile failed")[:1500]
            return False
        self.binary = build.binary
        return True

    def run(self, case: Case, *, timeout_s: float) -> ExecResult:
        # The oracle is always Python, even for Rust problems, so it is driven by shape of
        # payload rather than by the problem's declared language.
        if isinstance(case.payload, str):
            if self.binary:
                return run_binary(self.binary, case.payload, timeout_s=timeout_s)
            return run_stdin(self.artifact.source, case.payload, timeout_s=timeout_s)
        return call_function(self.artifact.source, self.entrypoint, list(case.payload),
                             timeout_s=timeout_s)

    @staticmethod
    def answer(res: ExecResult, payload) -> object:
        return res.stdout if isinstance(payload, str) else res.value


# ---- verdicts --------------------------------------------------------------------

@dataclass
class CandidateReport:
    framing: str
    compiled: bool = False
    compile_error: str | None = None
    agree_oracle: int = 0
    disagree_oracle: int = 0
    crashed: int = 0
    timed_out: int = 0
    behaviour: str = ""            # fingerprint over all cases, for clustering
    first_disagreement: dict | None = None
    overflow_clean: bool | None = None
    max_duration_s: float = 0.0

    @property
    def gates(self) -> dict:
        return {
            "compile": self.compiled,
            "no_crash": self.crashed == 0 and self.timed_out == 0,
            "agrees_with_oracle": self.disagree_oracle == 0 and self.agree_oracle > 0,
            "overflow_checked": self.overflow_clean,
        }

    @property
    def rank(self) -> tuple:
        """Higher is better. Sorted on descending."""
        return (
            self.compiled,
            self.disagree_oracle == 0,
            self.crashed == 0 and self.timed_out == 0,
            self.agree_oracle,
            self.overflow_clean is not False,
            -self.max_duration_s,
        )


@dataclass
class Verification:
    cases: int = 0
    oracle_ok: bool = False          # the reference was produced and prepared
    oracle_answers: int = 0          # ... and how many inputs it actually answered on
    oracle_unanswered: int = 0       # cases dropped because the reference could not answer
    oracle_error: str | None = None
    generator_error: str | None = None
    reports: list[CandidateReport] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)
    framing_divergence: bool = False
    ambiguity_note: str = ""
    notes: list[str] = field(default_factory=list)

    def best(self) -> CandidateReport | None:
        if not self.reports:
            return None
        return sorted(self.reports, key=lambda r: r.rank, reverse=True)[0]


def _overflow_check(artifact, entrypoint: str, cases: list[Case], budget,
                    case_timeout_s: float) -> bool | None:
    """Rebuild one Rust candidate with overflow checks on and run it on the largest input.

    Returns True when it completed without an overflow panic, False when it panicked on one,
    and None when the check could not be made at all. None is not a pass: it means unknown,
    and the report prints it as unknown.

    This proves the arithmetic did not wrap at the size tested. It does not prove the answer
    is right at that size, because the reference cannot produce an expected value there.
    """
    largest = max(cases, key=lambda c: len(c.payload) if isinstance(c.payload, str) else 0)
    checked = Runner(artifact=artifact, entrypoint=entrypoint, language="rust")
    if not checked.prepare(timeout_s=min(45.0, max(budget.spendable_s, 5.0)),
                           overflow_checks=True):
        return None
    res = checked.run(largest, timeout_s=case_timeout_s)
    if res.ok:
        return True
    return False if is_overflow_panic(res) else None


def verify(wave: Wave, problem: dict, analysis: Analysis | None, budget, *,
           case_timeout_s: float = 6.0) -> Verification:
    language = problem.get("language", "python")
    entrypoint = problem.get("entrypoint", "main")
    out = Verification()

    # Rust problems are driven through stdin, so there is no argument list to check.
    signature = (None if language == "rust"
                 else parse_signature(problem.get("statement", ""), entrypoint))
    cases, gen_err = build_cases(wave.inputgen, language, signature=signature)
    out.cases = len(cases)
    if gen_err:
        out.generator_error = gen_err
        out.notes.append(gen_err)

    # --- oracle ---
    oracle_runner = None
    if wave.oracle and wave.oracle.ok:
        oracle_runner = Runner(artifact=wave.oracle, entrypoint=entrypoint, language="python")
        if oracle_runner.prepare():
            out.oracle_ok = True
        else:
            out.oracle_error = oracle_runner.compile_error
            oracle_runner = None
    else:
        out.oracle_error = "no oracle produced"

    oracle_timeout_s = case_timeout_s * ORACLE_TIMEOUT_FACTOR
    expected: dict[str, object] = {}
    live_cases: list[Case] = []
    if oracle_runner:
        for c in cases:
            if budget.must_emit_now:
                out.notes.append("oracle pass cut short by the budget")
                break
            # The reference is prompted to be slow and literal, so it needs a longer leash
            # than the candidates. Without it, whether a case is comparable depends on
            # machine load, and the same artefacts score differently on two runs. Measured
            # on the Unicode problem: at 6 s the reference answered 5 or 6 of 18 cases
            # depending on the run, and a candidate's agreement count moved with it.
            res = oracle_runner.run(c, timeout_s=oracle_timeout_s)
            if res.ok:
                expected[c.label()] = Runner.answer(res, c.payload)
                live_cases.append(c)
            else:
                out.oracle_unanswered += 1
        out.oracle_answers = len(live_cases)
        if live_cases and len(live_cases) * 2 < len(cases):
            # Agreement on two inputs and agreement on eighteen are not the same
            # claim, and the per-candidate counters alone do not say which one a
            # row is making.
            out.notes.append(
                f"thin evidence: the reference answered on only "
                f"{len(live_cases)} of {len(cases)} generated inputs, so every "
                f"agreement below rests on that many cases")
        if not live_cases:
            # Which artefact is at fault matters, and the symptom does not say. If the
            # generator already failed its own contract, blaming the reference here would
            # put a wrong cause in the report.
            if out.generator_error:
                out.notes.append(
                    "the reference answered on no input, and the input generator had "
                    "already failed its own check, so the inputs are the suspect")
            else:
                out.notes.append(
                    "the reference failed on every generated input: the reference and the "
                    "generator read the statement's input format differently")

    # --- candidates ---
    for art in wave.candidates:
        if not art.ok:
            continue
        rep = CandidateReport(framing=art.framing)
        runner = Runner(artifact=art, entrypoint=entrypoint, language=language)
        if budget.must_emit_now:
            rep.compile_error = "not evaluated: budget exhausted"
            out.reports.append(rep)
            continue
        if not runner.prepare(timeout_s=min(45.0, max(budget.spendable_s, 5.0))):
            rep.compile_error = runner.compile_error
            out.reports.append(rep)
            continue
        rep.compiled = True

        fingerprint: list[str] = []
        for c in live_cases:
            if budget.must_emit_now:
                out.notes.append("candidate pass cut short by the budget")
                break
            res = runner.run(c, timeout_s=case_timeout_s)
            rep.max_duration_s = max(rep.max_duration_s, res.duration_s)
            if res.timed_out:
                rep.timed_out += 1
                fingerprint.append("T")
                continue
            if not res.ok:
                rep.crashed += 1
                fingerprint.append("X")
                continue
            got = Runner.answer(res, c.payload)
            want = expected[c.label()]
            match = same_output(got, want) if isinstance(c.payload, str) else same_value(got, want)
            if match:
                rep.agree_oracle += 1
                fingerprint.append("=")
            else:
                rep.disagree_oracle += 1
                fingerprint.append("!")
                if rep.first_disagreement is None:
                    rep.first_disagreement = {
                        "case": c.label(),
                        "input": _trim(c.payload),
                        "oracle": _trim(want),
                        "candidate": _trim(got),
                    }
        rep.behaviour = "".join(fingerprint)

        # Release Rust wraps signed integers silently, so an overflow at maximum scale is a
        # wrong answer with no crash and no warning. The timing build deliberately has the
        # checks off, matching what a judge is assumed to compile, so proving the arithmetic
        # did not wrap needs a second build with them on, run on the largest input available.
        # This costs one extra compile per Rust candidate and only runs when the budget can
        # still afford it; when it cannot, the field stays None and the report says unknown
        # rather than clean.
        if language == "rust" and live_cases and not budget.must_emit_now:
            rep.overflow_clean = _overflow_check(art, entrypoint, live_cases,
                                                 budget, case_timeout_s)
        out.reports.append(rep)

    # --- clustering by observed behaviour, not by claimed correctness ---
    for rep in out.reports:
        if rep.behaviour:
            out.clusters.setdefault(rep.behaviour, []).append(rep.framing)

    # --- the trap signal ---
    distinct = [b for b in out.clusters if b]
    if len(distinct) > 1:
        out.framing_divergence = True
        groups = " | ".join(
            f"{{{', '.join(sorted(fr))}}}" for fr in out.clusters.values()
        )
        out.ambiguity_note = (
            "Candidates written from different readings of the statement do not agree: "
            f"{groups}. Divergence across framings points at an ambiguity in the statement "
            "rather than at a typo, so the clause involved was re-read rather than "
            "resolved by majority."
        )
    return out


def _trim(value, limit: int = 400) -> str:
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except (TypeError, ValueError):
        text = str(value)
    return text if len(text) <= limit else text[:limit] + f"... ({len(text)} chars)"
