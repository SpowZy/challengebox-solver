"""Produce every model artefact for one problem in a single parallel wave.

Measured on this machine: one generation costs ~111 s through the CLI, eight in parallel cost
~127 s of wall clock. Concurrency is nearly free, serialisation is not. So the pipeline does
not run analyse, then generate, then verify. It fires everything that needs a model at once
and spends the rest of the budget on local execution.

The seven candidates do **not** receive the same prompt. That is the point, not an accident.
Sampling the same prompt seven times varies the seed; these statements are built so that the
failure is a shared misreading, and a shared misreading survives resampling unanimously
(2506.11021 measures exactly this: behavioural clustering removes stochastic error and leaves
statement misinterpretation untouched). Varying the *framing* varies the reading, which is the
one published defence against it (2406.06864). Divergence between framings is therefore not
noise to be voted away. It is the trap detector.
"""

from __future__ import annotations

import concurrent.futures as cf
from dataclasses import dataclass, field

from .analyse import Analysis
from .signature import parse_signature
from .provider import Provider, ProviderError, extract_code


@dataclass
class Artifact:
    role: str          # oracle | candidate | inputgen
    framing: str       # which prompt shape produced it
    language: str
    source: str
    ok: bool = True
    error: str | None = None
    latency_s: float = 0.0


# ---- shared prompt fragments -----------------------------------------------------

_PY_RULES = """\
Define exactly the function `{entrypoint}`. Use only the Python standard library.
Do not read stdin, do not print, do not call input(). Return the value; do not display it.
"""

_RS_RULES = """\
Write one complete Rust program containing `fn main()`. Use only the Rust standard library.
Read from stdin, write to stdout. Do not use external crates.
Integer overflow is silent in release builds: choose widths deliberately and use checked or
i128 arithmetic where a product or sum can leave i64 range.
"""


def _rules(language: str, entrypoint: str) -> str:
    return _RS_RULES if language == "rust" else _PY_RULES.format(entrypoint=entrypoint)


def _tail(language: str) -> str:
    kind = "rust" if language == "rust" else "python"
    return f"\nReply with ONE ```{kind} code block and nothing else. No explanation."


# ---- candidate framings ----------------------------------------------------------
# Each framing is a different *reading strategy*, not a different temperature.

FRAMINGS: dict[str, str] = {
    "plain": """\
Solve this problem.

{statement}

{rules}{tail}""",

    "restate": """\
Before writing any code, restate the specification to yourself clause by clause: what each
input means, what each rule does, what exactly is returned. Then implement that restatement.
Implement what the restatement says, not what the problem resembles.

{statement}

{rules}{tail}""",

    "traps": """\
This statement was written to be misread. Before writing code, answer each question below by
looking the answer up in the statement rather than assuming the usual convention. Then
implement, handling every answer explicitly.

{traps}

{statement}

{rules}{tail}""",

    "adversarial": """\
The obvious reading of this statement is probably wrong somewhere. Standard algorithms that
this problem resembles will produce the wrong answer, because at least one definition here
has been redefined to differ from its usual meaning.

Find the clauses that differ from convention and follow the page, not the convention.
Pay attention to: which unit each index counts, whether ranges are inclusive, the order in
which rules apply, and what happens at the boundaries.

{statement}

{rules}{tail}""",

    "literal": """\
Implement this specification literally, clause by clause, in the order written. Where the
statement defines a term that already has a standard meaning, the definition on the page
overrides the standard one completely. Where rules are numbered and ordered, apply them in
that order with first match winning.

Do not substitute a library function for a definition given in the statement, even when the
names match.

{statement}

{rules}{tail}""",

    "edgefirst": """\
First enumerate the degenerate and boundary cases this problem admits: empty input, a single
element, all elements equal, the minimum and maximum stated bounds, reversed or empty ranges,
negative indices. Decide what the statement says each produces.

Then write an implementation that is correct on those cases first and general afterwards.

{statement}

{rules}{tail}""",

    "complexity": """\
State the maximum input size this statement permits, then the time complexity required to
finish within a few seconds at that size. The obvious approach is often quadratic and will be
too slow; if so, do not write it.

Then implement an approach that meets the required complexity while following the statement
exactly.

{statement}

{rules}{tail}""",
}

DEFAULT_FRAMING_ORDER = [
    "adversarial", "literal", "traps", "restate", "edgefirst", "complexity", "plain",
]


ORACLE_PY = """\
Write a REFERENCE implementation of this problem. It will be used to check another, faster
implementation, so it is judged only on being unarguably correct.

Optimise for fidelity to the wording, never for speed. Prefer the slow obvious construction
over any clever one. Build things explicitly rather than deriving them. Never use a library
shortcut in place of a definition the statement gives. It will only ever be run on small
inputs, so quadratic or worse is fine and preferred if it is more clearly correct.

{statement}

Define exactly the function `{entrypoint}`. Use only the Python standard library.
Do not read stdin, do not print. Return the value.

Reply with ONE ```python code block and nothing else."""


ORACLE_RS_AS_PY = """\
Write a REFERENCE implementation of this problem **in Python**, as a complete program that
reads the same stdin format the statement describes and writes the same stdout format.

It will be used to check a Rust implementation by comparing their outputs token for token, so
it must produce byte-identical output for the same input. It is judged only on being
unarguably correct.

Optimise for fidelity to the wording, never for speed. Prefer the slow obvious construction.
Never use a library shortcut in place of a definition the statement gives. It will only ever
be run on small inputs.

{statement}

Write a complete Python program reading stdin and writing stdout, matching the statement's
output format exactly, including separators and line breaks.

Reply with ONE ```python code block and nothing else."""


INPUTGEN_PY = """\
Write a Python input generator for this problem. It produces inputs for differential testing,
so every input it returns must be VALID under the statement's constraints. An invalid input
makes two implementations disagree for reasons that mean nothing.

{statement}

Define exactly:

    def gen(rng, scale):
        ...

`rng` is a `random.Random`. `scale` is one of "edge", "small", "medium".

- "edge"   : degenerate cases. Empty, single element, all-equal, extreme permitted values,
             reversed or empty ranges, negative indices where the statement allows them.
- "small"  : a few elements. Small enough that a quadratic reference finishes instantly.
- "medium" : tens of elements. Still small enough for a slow reference.

Never generate anything near the stated maximum; a separate path handles that.

{shape}

Use only the Python standard library. Be conservative: respect every stated constraint,
including relationships between arguments such as equal lengths or in-range indices.

Reply with ONE ```python code block and nothing else."""


def _shape_hint(problem: dict, analysis: Analysis | None) -> str:
    """What `gen` must return, stated as precisely as the statement allows.

    The signature is parsed from the statement rather than described loosely, because the
    generator is a fixture and not a second opinion: every way it can differ from the
    reference about the shape of an input is a way to waste the whole run. A generator that
    invented a fifth argument for a four-parameter function cost one problem its entire
    verification, and the symptom appeared as "the reference failed on every input".
    """
    if problem.get("language") == "rust":
        base = ("Return a single string: the complete stdin text for one run, "
                "including all required tokens in the order the statement specifies.")
    else:
        entrypoint = problem.get("entrypoint", "")
        sig = parse_signature(problem.get("statement", ""), entrypoint)
        if sig and sig.params:
            base = (
                f"Return a list of EXACTLY {sig.arity} positional arguments for "
                f"`{sig.describe()}`, in that order: "
                + ", ".join(f"`{p}`" for p in sig.params) + ".\n"
                "A different number of arguments, or a different order, makes the input "
                "unusable. Represent every value the way the statement itself writes it: "
                "where the statement shows a record as a tuple, build a tuple; where it "
                "names fields, build a mapping with those exact keys. Never invent a "
                "representation the statement does not use."
            )
        else:
            base = (f"Return a list of positional arguments for "
                    f"`{entrypoint}`, in order.")
    if analysis and analysis.input_shape:
        base += f"\n\nInput shape as analysed: {analysis.input_shape}"
    return base


# ---- the wave --------------------------------------------------------------------

@dataclass
class Wave:
    oracle: Artifact | None = None
    inputgen: Artifact | None = None
    candidates: list[Artifact] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        return any(c.ok for c in self.candidates)


def generate_wave(problem: dict, analysis: Analysis | None, provider: Provider, *,
                  timeout_s: float, n_candidates: int = 7,
                  framings: list[str] | None = None) -> Wave:
    """Fire oracle, input generator and N differently-framed candidates concurrently."""
    language = problem.get("language", "python")
    entrypoint = problem.get("entrypoint", "main")
    statement = problem.get("statement", "")
    # Anchor every artefact to one contract. The statement names the function and its
    # parameters verbatim, so the reference, the candidates and the generator are all told
    # the same signature instead of each inferring one.
    sig = parse_signature(statement, entrypoint)
    sig_desc = sig.describe() if (sig and sig.params) else entrypoint
    rules = _rules(language, sig_desc)
    tail = _tail(language)
    # The checklist is static, so this framing stands on its own and does not wait for the
    # trap pass to finish. Anything the analysis found is appended when it is available.
    from .analyse import TRAP_CHECKLIST
    traps_block = TRAP_CHECKLIST
    if analysis and analysis.traps:
        traps_block += "\n" + analysis.as_prompt_block()

    order = framings or DEFAULT_FRAMING_ORDER
    chosen = [f for f in order if f in FRAMINGS][:n_candidates]
    jobs: list[tuple[str, str, str, str]] = []  # (role, framing, language, prompt)

    for f in chosen:
        template = FRAMINGS[f]
        jobs.append((
            "candidate", f, language,
            template.format(statement=statement, rules=rules, tail=tail, traps=traps_block),
        ))

    oracle_prompt = (ORACLE_RS_AS_PY if language == "rust" else ORACLE_PY).format(
        statement=statement, entrypoint=sig_desc)
    jobs.append(("oracle", "literal-reference", "python", oracle_prompt))

    jobs.append(("inputgen", "generator", "python", INPUTGEN_PY.format(
        statement=statement, shape=_shape_hint(problem, analysis))))

    wave = Wave()

    def run(job: tuple[str, str, str, str]) -> Artifact:
        role, framing, lang, prompt = job
        import time
        t0 = time.monotonic()
        try:
            raw = provider.complete(prompt, role=role, tag=framing, timeout_s=timeout_s)
        except ProviderError as exc:
            return Artifact(role=role, framing=framing, language=lang, source="",
                            ok=False, error=str(exc), latency_s=time.monotonic() - t0)
        code = extract_code(raw, lang)
        if not code.strip():
            return Artifact(role=role, framing=framing, language=lang, source="",
                            ok=False, error="empty code block",
                            latency_s=time.monotonic() - t0)
        return Artifact(role=role, framing=framing, language=lang, source=code,
                        latency_s=time.monotonic() - t0)

    with cf.ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        for art in pool.map(run, jobs):
            if art.role == "oracle":
                wave.oracle = art
            elif art.role == "inputgen":
                wave.inputgen = art
            else:
                wave.candidates.append(art)
            if not art.ok:
                wave.errors.append(f"{art.role}:{art.framing}: {art.error}")

    return wave
