#!/usr/bin/env python
"""Check every emitted solution against the constraints the assignment states.

    python compliance.py runs/bench

The assignment does not only ask for a correct answer. It states the shape a solution must
have, and a solution that breaks that shape scores zero however correct its logic is:

    Python: Define the function named in `entrypoint`. Use only the standard library. No I/O.
    Rust:   Write one complete program with `fn main()`. Read from stdin and write to stdout.
            Use only the standard library.

Those are mechanical properties, so nothing here asks a model anything. The Python side is
checked by walking the AST rather than by matching text, because a comment mentioning `print`
is not a call to it and a regular expression cannot tell the difference. The Rust side is
checked on the `use` declarations and on the presence of `fn main`.

This runs over solutions that are already on disk, so it is also the check a reader can run
against the committed artefacts without spending anything.
"""

from __future__ import annotations

import argparse
import ast
import glob
import json
import os
import sys

BANNED_CALLS = {"input", "print", "open", "exec", "eval", "compile", "__import__"}


def _python_report(source: str, entrypoint: str) -> list[str]:
    """Returns a list of violations. Empty means the solution obeys every stated rule."""
    problems: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"does not parse: {exc}"]

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    outside = sorted(m for m in imported if m not in sys.stdlib_module_names)
    if outside:
        problems.append(f"imports outside the standard library: {', '.join(outside)}")

    called = sorted({
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id in BANNED_CALLS
    })
    if called:
        problems.append(f"performs I/O or dynamic execution: {', '.join(called)}")

    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if entrypoint not in defined:
        problems.append(f"does not define the entrypoint `{entrypoint}`")
    return problems


def _rust_report(source: str) -> list[str]:
    problems: list[str] = []
    if "fn main(" not in source:
        problems.append("does not define `fn main`")
    external = sorted({
        line.split()[1].split("::")[0].rstrip(";")
        for line in (l.strip() for l in source.splitlines())
        if line.startswith("use ") and not line.startswith("use std")
        and not line.startswith("use crate") and not line.startswith("use self")
        and not line.startswith("use super")
    })
    if external:
        problems.append(f"uses crates outside the standard library: {', '.join(external)}")
    if "extern crate" in source:
        problems.append("declares an external crate")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", default="runs/bench")
    ap.add_argument("--samples", default="samples")
    args = ap.parse_args(argv)

    spec: dict[str, tuple[str, str]] = {}
    for path in glob.glob(os.path.join(args.samples, "*.json")):
        with open(path, encoding="utf-8") as fh:
            problem = json.load(fh)
        spec[problem["problem_id"][:12]] = (problem["entrypoint"], problem["language"])

    paths = sorted(glob.glob(os.path.join(args.run_dir, "solutions", "*")))
    if not paths:
        print(f"no emitted solutions under {args.run_dir}/solutions", file=sys.stderr)
        return 1

    failures = 0
    for path in paths:
        short = os.path.basename(path).split(".")[0]
        if short not in spec:
            continue
        entrypoint, language = spec[short]
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        problems = (_rust_report(source) if language == "rust"
                    else _python_report(source, entrypoint))
        if problems:
            failures += 1
            print(f"FAIL {short} ({language})")
            for p in problems:
                print(f"       {p}")
        else:
            shape = "fn main, std only" if language == "rust" else \
                    f"defines {entrypoint}, std only, no I/O"
            print(f"ok   {short} ({language}) {shape}")

    print(f"\n{len(paths) - failures}/{len(paths)} emitted solutions obey every stated "
          f"constraint")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
