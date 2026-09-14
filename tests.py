#!/usr/bin/env python
"""Tests for the parts that decide correctness. No model calls, no network.

    python tests.py

Everything here is deterministic and runs in a few seconds. The model-dependent behaviour is
covered by the recorded runs under `runs/`, which is a different kind of evidence and is kept
separate on purpose: these assertions would still hold if the provider were swapped.

The extraction tests exist because of a real bug. `extract_code` tried the fence tags
"```python" and "```py" and took `min()` of the matches; both match "```python" at the same
offset, `min` compared the tags lexicographically, "```py" won, and every generated file
began with a stray `thon`. It broke every artefact in the system silently, and it was found
by running the thing rather than by reading it.
"""

from __future__ import annotations

import os
import sys
import time
import unittest

sys.path.insert(0, ".")

from solver.budget import Budget, BudgetExhausted, PANIC_MARGIN_S  # noqa: E402
from solver.provider import extract_code                            # noqa: E402
from solver.sandbox import call_function, run_stdin, syntax_ok      # noqa: E402
from solver.verify import (                                           # noqa: E402
    build_cases, normalise, same_output, same_value, tokens)
from solver.generate import Artifact                                  # noqa: E402
from solver.signature import parse_signature                          # noqa: E402
from solver.analyse import _extract_json                              # noqa: E402


class TestExtractCode(unittest.TestCase):
    def test_python_fence_long_tag_wins_over_prefix(self):
        # The regression: "```py" is a prefix of "```python" at the same offset.
        self.assertEqual(extract_code("```python\nimport os\n```", "python"), "import os")

    def test_short_python_tag(self):
        self.assertEqual(extract_code("```py\nx = 1\n```", "python"), "x = 1")

    def test_rust_fence_long_tag_wins(self):
        self.assertEqual(extract_code("```rust\nfn main(){}\n```", "rust"), "fn main(){}")

    def test_short_rust_tag(self):
        self.assertEqual(extract_code("```rs\nfn main(){}\n```", "rust"), "fn main(){}")

    def test_last_block_wins(self):
        # A model that revises itself puts the final version last.
        text = "try\n```python\nOLD\n```\nactually\n```python\nNEW\n```"
        self.assertEqual(extract_code(text, "python"), "NEW")

    def test_untagged_fence(self):
        self.assertEqual(extract_code("```\nx = 2\n```", "python"), "x = 2")

    def test_no_fence_returns_whole_reply(self):
        self.assertEqual(extract_code("x = 3", "python"), "x = 3")

    def test_prose_around_fence_is_dropped(self):
        text = "Here you go:\n```python\nx = 4\n```\nHope that helps."
        self.assertEqual(extract_code(text, "python"), "x = 4")


class TestBudget(unittest.TestCase):
    def test_reserve_is_carved_before_phases(self):
        b = Budget(deadline_s=300.0)
        allocated = sum(p.allocated_s for p in b.phases.values())
        self.assertAlmostEqual(allocated, 300.0 - b.emit_reserve_s, delta=0.5)

    def test_reserve_degrades_on_a_scaled_run(self):
        # A fixed 20 s reserve would swallow a 15 s budget entirely.
        b = Budget(deadline_s=300.0, scale=0.05)
        self.assertLess(b.emit_reserve_s, b.total_s)
        self.assertGreater(b.spendable_s, 0.0)

    def test_grant_never_exceeds_spendable(self):
        b = Budget(deadline_s=300.0)
        self.assertLessEqual(b.grant(10_000.0, "verify"), b.spendable_s + 0.01)

    def test_grant_raises_when_empty(self):
        b = Budget(deadline_s=1.0, scale=0.001)
        time.sleep(0.05)
        with self.assertRaises(BudgetExhausted):
            b.grant(1.0, "verify")

    def test_must_emit_now_trips_near_the_reserve(self):
        b = Budget(deadline_s=300.0)
        self.assertFalse(b.must_emit_now)
        b._start = time.monotonic() - (300.0 - b.emit_reserve_s - PANIC_MARGIN_S + 1.0)
        self.assertTrue(b.must_emit_now)

    def test_phase_cannot_borrow_from_the_reserve(self):
        b = Budget(deadline_s=300.0)
        b._start = time.monotonic() - 285.0          # 15 s left, all of it reserve
        self.assertLessEqual(b.phase_remaining_s("verify"), 0.01)


class TestComparison(unittest.TestCase):
    def test_tuple_and_list_are_the_same_answer(self):
        # JSON has no tuple; a reference returning one must not read as a disagreement.
        self.assertTrue(same_value((1, 2, [3, 4]), [1, 2, (3, 4)]))

    def test_nested_normalisation(self):
        self.assertEqual(normalise({"b": (1, 2), "a": [3]}), {"a": [3], "b": [1, 2]})

    def test_float_that_is_an_integer(self):
        self.assertTrue(same_value(3.0, 3))

    def test_float_tolerance_is_narrow(self):
        self.assertTrue(same_value(1.0000000001, 1.0000000001))
        self.assertFalse(same_value(1.001, 1.002))

    def test_real_difference_is_a_disagreement(self):
        self.assertFalse(same_value([1, 2, 3], [1, 2, 4]))

    def test_stdout_compared_by_tokens_like_the_judge(self):
        # The statement says output is judged by splitting on ASCII whitespace.
        self.assertTrue(same_output("1 2\n3\n", "  1\t2   3  \n\n"))

    def test_token_order_still_matters(self):
        self.assertFalse(same_output("1 2", "2 1"))

    def test_tokens_helper(self):
        self.assertEqual(tokens(" a\tb\nc "), ["a", "b", "c"])


GOOD_JSON = '{"summary": "s", "max_scale": "10^9", "traps": [{"kind": "RANGES"}]}'


class TestAnalysisExtraction(unittest.TestCase):
    """The trap pass quotes clauses verbatim from statements full of backticks, braces and
    quotation marks, so its reply is a hostile place to find JSON. An earlier version took
    the first fenced block and the first balanced object and gave up if either failed: on one
    problem that silently discarded 3,466 characters of a successful analysis, and the run
    reported zero traps for a call that had worked."""

    def test_bare_object(self):
        self.assertEqual(_extract_json(GOOD_JSON)["max_scale"], "10^9")

    def test_fenced_object(self):
        text = "Here is the analysis:\n```json\n" + GOOD_JSON + "\n```\nThat is all."
        self.assertIn("traps", _extract_json(text))

    def test_prose_before_the_object(self):
        self.assertIn("traps", _extract_json("Analysis follows.\n" + GOOD_JSON))

    def test_a_decoy_object_does_not_win(self):
        # A leading object that parses but is not the analysis must not be accepted, or the
        # report silently loses every trap the pass actually found.
        got = _extract_json('{"note": "thinking out loud"}\n' + GOOD_JSON)
        self.assertIn("traps", got)
        self.assertNotIn("note", got)

    def test_trailing_comma_is_repaired(self):
        self.assertIn("traps", _extract_json('{"summary": "s", "traps": [],}'))

    def test_a_fence_inside_a_string_does_not_break_extraction(self):
        self.assertIn("traps", _extract_json('{"summary": "write ```json", "traps": []}'))

    def test_braces_inside_a_quoted_clause(self):
        text = '{"summary": "the rule is {a, b}", "traps": [], "input_shape": "x"}'
        self.assertEqual(_extract_json(text)["input_shape"], "x")

    def test_no_json_at_all(self):
        self.assertIsNone(_extract_json("I was not able to analyse this statement."))

    def test_empty_reply(self):
        self.assertIsNone(_extract_json(""))


class TestSignature(unittest.TestCase):
    """The statement names the function and its parameters verbatim, so nothing has to ask a
    model what the arguments are."""

    def test_parses_the_statement_line(self):
        st = "Implement `capture_binders(nodes, expr_root, target, replacement_root)`."
        sig = parse_signature(st, "capture_binders")
        self.assertEqual(sig.arity, 4)
        self.assertEqual(sig.params[0], "nodes")
        self.assertEqual(sig.describe(),
                         "capture_binders(nodes, expr_root, target, replacement_root)")

    def test_zero_argument_entrypoint(self):
        self.assertEqual(parse_signature("Write `main()`.", "main").arity, 0)

    def test_prose_call_is_not_a_signature(self):
        # `score(3)` in prose names no parameter; accepting it would invent an arity.
        self.assertIsNone(parse_signature("the value of `score(3)` is fixed", "score"))

    def test_absent_entrypoint(self):
        self.assertIsNone(parse_signature("no mention here", "solve"))


GEN_TUPLE = """
def gen(rng, scale):
    return (1, 2, 3)
"""

GEN_FIVE = """
def gen(rng, scale):
    return [1, 2, 3, 4, 5]
"""

GEN_TWO = """
def gen(rng, scale):
    return [1, 2]
"""

GEN_RANDOM = """
def gen(rng, scale):
    return [rng.random()]
"""

SEED_PROBE = """
import sys
sys.path.insert(0, '.')
from solver.verify import build_cases
from solver.generate import Artifact
src = open('probe_gen.txt').read()
art = Artifact(role='inputgen', framing='g', language='python', source=src)
cases, _ = build_cases(art, 'python', per_scale=2)
print([c.seed for c in cases])
"""


class TestGeneratedInputs(unittest.TestCase):
    """The input generator is a fixture, not a second opinion. Every way it can disagree with
    the statement about the shape of an input wastes the whole run, and the symptom surfaces
    far from the cause, as the reference failing on every input."""

    @staticmethod
    def _gen(body):
        return Artifact(role="inputgen", framing="generator", language="python", source=body)

    def test_a_returned_tuple_is_an_argument_list(self):
        # The regression: a 3-tuple for a 3-parameter function was collapsed into ONE
        # argument, so the reference was called wrongly and failed on every input. normalise()
        # already treats a tuple and a list as the same thing; this path did not.
        sig = parse_signature("Implement `f(a, b, c)`.", "f")
        cases, err = build_cases(self._gen(GEN_TUPLE), "python", signature=sig, per_scale=1)
        self.assertIsNone(err)
        self.assertTrue(cases)
        self.assertEqual(cases[0].payload, [1, 2, 3])

    def test_wrong_arity_is_reported_as_a_generator_error(self):
        sig = parse_signature("Implement `f(a, b, c, d)`.", "f")
        cases, err = build_cases(self._gen(GEN_FIVE), "python", signature=sig, per_scale=1)
        self.assertEqual(cases, [])
        self.assertIn("does not match the signature", err)
        self.assertIn("f(a, b, c, d)", err)

    def test_right_arity_passes(self):
        sig = parse_signature("Implement `f(a, b)`.", "f")
        cases, err = build_cases(self._gen(GEN_TWO), "python", signature=sig, per_scale=1)
        self.assertIsNone(err)
        self.assertEqual(len(cases), 3)          # one per scale

    def test_seeds_are_stable_across_processes(self):
        # hash() is salted per process, so hash((scale, i)) produced a different input set on
        # every run: the same artefacts scored differently twice in a row, and a results table
        # that moves when you rerun it is not evidence.
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            probe = os.path.join(tmp, "probe.py")
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write(SEED_PROBE)
            with open("probe_gen.txt", "w", encoding="utf-8") as fh:
                fh.write(GEN_RANDOM)
            try:
                seen = {subprocess.run([sys.executable, probe], capture_output=True,
                                       text=True, cwd=".").stdout.strip()
                        for _ in range(2)}
            finally:
                os.remove("probe_gen.txt")
        self.assertEqual(len(seen), 1, f"seeds moved between processes: {seen}")
        self.assertTrue(seen.pop().startswith("["))


class TestSandbox(unittest.TestCase):
    def test_return_value_round_trip(self):
        r = call_function("def f(a, b):\n    return [a + b, (a, b)]\n", "f", [2, 3],
                          timeout_s=15)
        self.assertTrue(r.ok)
        self.assertEqual(r.value, [5, [2, 3]])

    def test_exception_text_survives_the_process_boundary(self):
        # The driver exits non-zero on a handled exception but still writes the message;
        # reading only the exit code would throw away the one useful diagnostic.
        r = call_function("def f(x):\n    return 1 / 0\n", "f", [1], timeout_s=15)
        self.assertFalse(r.ok)
        self.assertIn("ZeroDivisionError", r.error or "")

    def test_missing_entrypoint_is_named(self):
        r = call_function("def g(x):\n    return x\n", "f", [1], timeout_s=15)
        self.assertFalse(r.ok)
        self.assertIn("f", r.error or "")

    def test_infinite_loop_is_killed(self):
        r = call_function("def f(x):\n    while True:\n        pass\n", "f", [1],
                          timeout_s=2)
        self.assertFalse(r.ok)
        self.assertTrue(r.timed_out)

    def test_candidate_printing_does_not_corrupt_the_result(self):
        src = "def f(x):\n    print('noise on stdout')\n    return x * 2\n"
        r = call_function(src, "f", [21], timeout_s=15)
        self.assertTrue(r.ok)
        self.assertEqual(r.value, 42)

    def test_stdin_program(self):
        src = "import sys\nprint(sum(int(t) for t in sys.stdin.read().split()))\n"
        r = run_stdin(src, "1 2 3", timeout_s=15)
        self.assertTrue(r.ok)
        self.assertEqual(r.stdout.strip(), "6")

    def test_syntax_gate_rejects_before_spending_a_process(self):
        ok, err = syntax_ok("def f(:\n    pass\n")
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_syntax_gate_accepts_valid(self):
        self.assertEqual(syntax_ok("def f():\n    return 1\n"), (True, None))


class TestRust(unittest.TestCase):
    """Skipped when rustc is absent, so the suite still runs on a machine without it."""

    def setUp(self):
        from solver.sandbox import rust_available
        if not rust_available():
            self.skipTest("rustc not on PATH")

    def test_compiles_and_runs(self):
        from solver.sandbox import compile_and_run
        src = ("use std::io::{self,Read};\n"
               "fn main(){let mut s=String::new();io::stdin().read_to_string(&mut s).unwrap();\n"
               "let n:i64=s.split_whitespace().map(|x|x.parse::<i64>().unwrap()).sum();\n"
               "println!(\"{}\",n);}\n")
        build, res = compile_and_run(src, "1 2 3", timeout_s=20)
        self.assertTrue(build.ok, build.error)
        self.assertEqual(res.stdout.strip(), "6")

    def test_overflow_is_silent_without_checks_and_caught_with_them(self):
        # This is the whole reason the second build exists: release Rust wraps i64 without
        # a crash, so a maximum-scale overflow is a wrong answer with no signal at all.
        from solver.sandbox import compile_and_run, is_overflow_panic
        src = "fn main(){let mut a:i64=i64::MAX; a=a+1; println!(\"{}\",a);}\n"

        _, silent = compile_and_run(src, "", timeout_s=20, overflow_checks=False)
        self.assertTrue(silent.ok)
        self.assertEqual(silent.stdout.strip(), "-9223372036854775808")

        _, caught = compile_and_run(src, "", timeout_s=20, overflow_checks=True)
        self.assertFalse(caught.ok)
        self.assertTrue(is_overflow_panic(caught))


if __name__ == "__main__":
    unittest.main(verbosity=2)
