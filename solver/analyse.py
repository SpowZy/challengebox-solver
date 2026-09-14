"""Read the statement before writing any code, and write down what can go wrong.

The problems are adversarial by construction: the README says so, and reading the samples
confirms it. The failure they are built to produce is not "the model cannot code" but "the
model codes the problem it expected instead of the problem on the page": real Unicode
segmentation instead of the six rules given, exclusive ranges instead of inclusive ones,
byte counts instead of UTF-16 code units.

So this phase produces no code at all. It produces a written list of the specific traps in
this specific statement, each with the clause that creates it.

Where its output goes, stated precisely, because it is easy to overclaim here. The eleven
point checklist below is static, so the `traps` framing carries it into generation without
waiting for anything. The *analysed* traps do not reach the generation prompts at all in the
default pipeline: the trap pass runs concurrently with the wave rather than before it, and
it is usually the slowest call of the ten, so the candidates are already written by the time
it returns. `as_prompt_block` exists for a caller that runs the two phases in sequence, and
`solve.py` deliberately does not, because a sequential trap pass costs more of the 300 s
budget than it returns. What the analysed traps are actually for is the report a human
reads, and the record of what the statement hides.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict

from .provider import Provider, ProviderError


# The checklist is fixed, not generated. It comes from the failure modes that actually recur
# when judging model-written code, and it is stated as questions so the answer has to be
# looked up in the statement rather than assumed.
TRAP_CHECKLIST = """\
1.  MAGNITUDE. Do any stated bounds exceed 2^53, where a float loses integer precision?
    Do intermediate products or sums exceed i64 even when inputs fit? Rust wraps silently.
2.  MEMORY. Can the structure the statement describes actually be materialised at the
    stated maximum, or must it be represented implicitly?
3.  UNITS. Bytes, Unicode scalar values, UTF-16 code units, graphemes, and characters are
    five different things. Which one does each index in this statement use?
4.  REDEFINITION. Does the statement define a term that already has a standard meaning
    (grapheme, sorted, adjacent, balanced)? If so the given definition wins over the
    standard one, even when it disagrees with it.
5.  RANGES. Inclusive or exclusive at each end? Is an empty range possible, and what does
    it mean? Is a reversed range an error, empty, or silently swapped?
6.  INDEXING. Zero or one based? Are negative indices allowed, and is the resolution done
    before or after clamping? Order matters and is usually stated only once.
7.  ORDERING. When two items compare equal, does the output order matter? Is stability
    required or forbidden?
8.  DEGENERATE INPUT. Empty input, one element, all elements identical, maximum repeated
    value. What does the statement say each produces?
9.  RULE PRECEDENCE. If rules are numbered and the statement says the order is
    authoritative, they must be applied in that order with first-match-wins, not merged.
10. OUTPUT SHAPE. Exact type, exact count, separator, trailing newline, and what is printed
    when the answer is empty.
11. COMPLEXITY. At the stated maximum, what is the cost of the obvious approach? If it is
    quadratic in a bound of 10^5 or more, the obvious approach is a wrong answer.
"""


@dataclass
class Trap:
    kind: str
    quote: str          # the clause in the statement that creates it
    consequence: str    # what a solution that misses it produces
    guard: str          # what to do instead
    fidelity: str = ""  # verbatim | fragments | paraphrase, checked against the text


@dataclass
class Analysis:
    problem_id: str
    language: str
    entrypoint: str
    summary: str = ""
    traps: list[Trap] = field(default_factory=list)
    input_shape: str = ""
    output_shape: str = ""
    invariants: list[str] = field(default_factory=list)
    max_scale: str = ""
    raw: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        return d

    def as_prompt_block(self) -> str:
        """The part that gets pasted into generation prompts."""
        if not self.traps:
            return ""
        lines = ["Traps identified in this statement. Handle every one explicitly:"]
        for i, t in enumerate(self.traps, 1):
            lines.append(f'{i}. [{t.kind}] "{t.quote}"')
            lines.append(f"   If missed: {t.consequence}")
            lines.append(f"   Required: {t.guard}")
        if self.invariants:
            lines.append("")
            lines.append("Invariants stated or implied by the problem:")
            lines.extend(f"- {inv}" for inv in self.invariants)
        return "\n".join(lines)


ANALYSE_PROMPT = """\
You are reviewing a competitive programming statement before anyone writes code for it.
Your only job is to find the traps. Do not solve the problem and do not write any solution.

Apply this checklist. For each item, look up the answer in the statement rather than
assuming the usual convention:

{checklist}

Statement:
---
{statement}
---

Target language: {language}. Entry point: {entrypoint}.

Reply with one JSON object and nothing else. No prose before or after, no code fence.

{{
  "summary": "one sentence, what the function computes",
  "input_shape": "the arguments or stdin format with the stated bounds, under 40 words",
  "output_shape": "the return value or stdout format, under 25 words",
  "max_scale": "the largest permitted input, as concrete numbers, under 20 words",
  "invariants": ["at most 3, each under 20 words, checkable without knowing the answer"],
  "traps": [
    {{
      "kind": "one of MAGNITUDE, MEMORY, UNITS, REDEFINITION, RANGES, INDEXING, ORDERING, DEGENERATE, PRECEDENCE, OUTPUT, COMPLEXITY",
      "quote": "the clause from the statement, verbatim, truncated to 20 words",
      "consequence": "what a solution that misses this produces, under 15 words",
      "guard": "what the implementation must do instead, under 20 words"
    }}
  ]
}}

Report the **six most dangerous traps at most**, ordered with the one most likely to be
missed first. Only report a trap you can quote. Be terse: this output is consumed by a
program under a deadline, not read for pleasure. Do not restate the problem.
"""


def _candidate_objects(text: str):
    """Yield every balanced {...} slice in `text`, outermost first, left to right."""
    depth, in_str, esc, start = 0, False, False, -1
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == chr(92):
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    yield text[start:i + 1]
                    start = -1


def _loads_lenient(blob: str) -> dict | None:
    """json.loads, then one repair pass for the two things models actually get wrong."""
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError:
        # A trailing comma before a closing brace or bracket, and a stray code fence
        # inside the object. Nothing more adventurous: a repair that guesses at the
        # content would put invented traps into the report.
        repaired = re.sub(r",(\s*[}\]])", r"\1", blob)
        repaired = repaired.replace("```", "")
        try:
            obj = json.loads(repaired)
        except json.JSONDecodeError:
            return None
    return obj if isinstance(obj, dict) else None


def _extract_json(text: str) -> dict | None:
    """Pull the analysis object out of a reply.

    The trap pass quotes clauses from the statement verbatim, and the statements are full of
    backticks, braces and quotation marks, so the reply is a hostile place to find JSON. An
    earlier version took the first fenced block and the first balanced object and gave up if
    either failed to parse: on `6eca8a91` that silently discarded 3,466 characters of a
    successful analysis and the problem was reported as having zero traps. So every plausible
    slice is tried, and the first one that parses into an object with recognisable keys wins.
    """
    if not text:
        return None

    attempts: list[str] = [text]
    attempts += re.findall(r"```(?:json)?\s*(.+?)```", text, re.S)
    attempts += list(_candidate_objects(text))
    for blob in attempts:
        for sub in ([blob] if blob is text else [blob]) + list(_candidate_objects(blob)):
            obj = _loads_lenient(sub.strip())
            if obj is None:
                continue
            # A bare {} or an unrelated object is not the analysis. Require at least one
            # field the prompt asks for, so a fragment cannot pass as a result.
            if any(k in obj for k in ("traps", "summary", "input_shape", "max_scale")):
                return obj
    return None


def _normalise_for_quote(text: str) -> str:
    """Collapse whitespace and unify the punctuation a model silently rewrites."""
    for code in (0x2018, 0x2019):          # curly single quotes
        text = text.replace(chr(code), "'")
    for code in (0x201C, 0x201D):          # curly double quotes
        text = text.replace(chr(code), '"')
    for code in (0x2014, 0x2013):          # long dashes
        text = text.replace(chr(code), "-")
    text = text.replace("`", "")
    return " ".join(text.split()).lower()


def locate_quote(quote: str, statement: str) -> str:
    """Classify a trap quote against the statement it claims to come from.

    Returns "verbatim", "fragments" or "paraphrase".

    This exists because the trap prompt asks for the clause verbatim and the model does not
    always comply: it stitches two non-adjacent constraints together with a connecting word,
    rewrites `10**18` as `10^18`, or summarises instead of quoting. A report that calls all
    of those "copied from the statement" is making a claim it has not checked, and the whole
    point of the report is that its claims are checkable. So the check is mechanical and its
    verdict is printed next to every quote.

    "fragments" is a real and useful middle case: an elision marked with an ellipsis, or a
    quote whose every substantial run of words appears in the statement, points at a genuine
    clause even though it is not one contiguous span.
    """
    if not quote or not statement:
        return "paraphrase"
    hay = _normalise_for_quote(statement)
    needle = _normalise_for_quote(quote)
    if not needle:
        return "paraphrase"
    if needle in hay:
        return "verbatim"

    # An elision the model marked itself, or one it did not: split on ellipses first, then
    # fall back to testing whether every long enough run of words is present.
    parts = [p.strip() for p in needle.replace(chr(0x2026), "...").split("...") if p.strip()]
    if len(parts) > 1 and all(p in hay for p in parts if len(p) > 8):
        return "fragments"

    words = needle.split()
    if len(words) >= 4:
        spans = [" ".join(words[i:i + 4]) for i in range(len(words) - 3)]
        present = sum(1 for s in spans if s in hay)
        if present and present >= max(1, int(len(spans) * 0.6)):
            return "fragments"
    return "paraphrase"


def analyse(problem: dict, provider: Provider, *, timeout_s: float) -> Analysis:
    """Run the trap pass. Never raises: a failed analysis degrades to an empty one.

    An empty analysis is worse than a good one but far better than no solution, so the
    caller continues either way.
    """
    result = Analysis(
        problem_id=problem.get("problem_id", ""),
        language=problem.get("language", "python"),
        entrypoint=problem.get("entrypoint", "main"),
    )
    prompt = ANALYSE_PROMPT.format(
        checklist=TRAP_CHECKLIST,
        statement=problem.get("statement", ""),
        language=result.language,
        entrypoint=result.entrypoint,
    )
    try:
        raw = provider.complete(prompt, role="analyse", tag=result.problem_id[:8],
                                timeout_s=timeout_s)
    except ProviderError as exc:
        result.summary = f"(analysis unavailable: {exc})"
        return result

    result.raw = raw
    data = _extract_json(raw)
    if not data:
        # Keep the reply. A parse failure that throws away the model output leaves nothing
        # to diagnose, which is how one problem reported zero traps for a call that had
        # in fact returned 3,466 characters of analysis.
        result.summary = (f"(analysis returned no parsable JSON; {len(raw)} characters of "
                          f"reply kept in the run directory)")
        return result

    result.summary = str(data.get("summary", ""))[:500]
    result.input_shape = str(data.get("input_shape", ""))[:1500]
    result.output_shape = str(data.get("output_shape", ""))[:1000]
    result.max_scale = str(data.get("max_scale", ""))[:500]
    result.invariants = [str(x)[:300] for x in (data.get("invariants") or [])][:12]
    for t in (data.get("traps") or [])[:15]:
        if not isinstance(t, dict):
            continue
        quote = str(t.get("quote", ""))[:400]
        result.traps.append(Trap(
            kind=str(t.get("kind", "UNKNOWN"))[:20],
            quote=quote,
            consequence=str(t.get("consequence", ""))[:400],
            guard=str(t.get("guard", ""))[:400],
            # The prompt asks for the clause verbatim. Asking is not checking, and the model
            # does not always comply: it stitches two non-adjacent constraints together, or
            # rewrites 10**18 as 10^18, or summarises. The verdict is recorded next to the
            # quote so the report never calls a paraphrase a citation.
            fidelity=locate_quote(quote, problem.get("statement", "")),
        ))
    return result
