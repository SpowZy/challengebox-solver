"""Isolated execution of generated code, one process per run."""

from .python_exec import ExecResult, call_function, run_stdin, syntax_ok
from .rust_exec import (
    BuildResult,
    compile_and_run,
    compile_rust,
    is_overflow_panic,
    run_binary,
    rust_available,
)

__all__ = [
    "ExecResult",
    "call_function",
    "run_stdin",
    "syntax_ok",
    "BuildResult",
    "compile_rust",
    "compile_and_run",
    "run_binary",
    "rust_available",
    "is_overflow_panic",
]
