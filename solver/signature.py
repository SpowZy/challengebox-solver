"""Parse the entrypoint signature out of the statement.

Every Python statement in this benchmark opens by naming the function it wants, with its
parameters, in backticks: ``Implement `capture_binders(nodes, expr_root, target,
replacement_root)`.`` That line is the contract between the reference, the candidates and the
input generator, and it is machine-readable, so nothing here asks a model what the arguments
are. A generator that returns five values for a four-parameter function is then a detectable
error rather than a silent one that surfaces later as "no candidate agreed".
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Signature:
    name: str
    params: list[str]

    @property
    def arity(self) -> int:
        return len(self.params)

    def describe(self) -> str:
        return f"{self.name}({', '.join(self.params)})"


_IDENT = r"[A-Za-z_][A-Za-z0-9_]*"


def parse_signature(statement: str, entrypoint: str) -> Signature | None:
    """Find `entrypoint(a, b, c)` in the statement. Returns None when it is not stated."""
    if not entrypoint:
        return None
    for m in re.finditer(re.escape(entrypoint) + r"\s*\(([^()]*)\)", statement):
        inner = m.group(1).strip()
        if not inner:
            return Signature(name=entrypoint, params=[])
        parts = [p.strip() for p in inner.split(",")]
        # Only accept a genuine parameter list. A prose mention such as
        # `f(x)` computed over the whole array would not be one.
        if all(re.fullmatch(_IDENT, p) for p in parts):
            return Signature(name=entrypoint, params=parts)
    return None
