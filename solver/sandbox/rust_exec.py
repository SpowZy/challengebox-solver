"""Compile and run generated Rust, twice when it matters.

Rust problems are stdin/stdout programs. Two builds are produced from the same source:

* a **release** build with ``-C overflow-checks=off``, used for timing. This is what the
  judge's own build is assumed to look like, so it is the one whose speed is measured.
* an **overflow-checked** build, used once on the largest input. Release Rust wraps signed
  integers silently, so a solution that overflows ``i64`` at maximum scale produces a wrong
  answer with no crash and no warning. The checked build turns that silence into a panic.

Compilation is cached by a hash of the source plus the flags, because the same candidate is
run against many inputs and paying rustc twice for that would eat the budget.
"""

from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass

from .python_exec import ExecResult, _run

_CACHE: dict[str, str] = {}
_TEMP_DIRS: list[str] = []


def _cleanup_temp_dirs() -> None:
    """Remove this process's Rust build directories.

    Failure here is deliberately swallowed: a leftover directory costs disk, while
    raising at interpreter exit would turn that into a confusing traceback after the
    work itself already succeeded.
    """
    for path in _TEMP_DIRS:
        shutil.rmtree(path, ignore_errors=True)
    _TEMP_DIRS.clear()


atexit.register(_cleanup_temp_dirs)


@dataclass
class BuildResult:
    ok: bool
    binary: str | None = None
    stderr: str = ""
    duration_s: float = 0.0
    error: str | None = None


def rust_available() -> bool:
    return shutil.which("rustc") is not None


def _key(source: str, overflow_checks: bool) -> str:
    h = hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]
    return f"{h}-{'oc' if overflow_checks else 'noc'}"


def compile_rust(source: str, *, overflow_checks: bool = False,
                 timeout_s: float = 60.0) -> BuildResult:
    """Build one Rust source file. Returns the path to the executable."""
    if not rust_available():
        return BuildResult(ok=False, error="rustc not found on PATH")

    key = _key(source, overflow_checks)
    cached = _CACHE.get(key)
    if cached and os.path.exists(cached):
        return BuildResult(ok=True, binary=cached, duration_s=0.0)

    # Each build gets its own directory and the binary has to outlive this call, so the
    # directory cannot be a context manager. Left alone it is a leak: one benchmark run
    # compiles seven candidates twice on four Rust problems, and a few runs had piled
    # up 206 MB of stale build directories. They are registered for removal at exit,
    # which is strictly after every measurement this process makes.
    tmp = tempfile.mkdtemp(prefix="cbox_rs_")
    _TEMP_DIRS.append(tmp)
    src = os.path.join(tmp, "main.rs")
    exe = os.path.join(tmp, "main.exe" if os.name == "nt" else "main")
    with open(src, "w", encoding="utf-8") as fh:
        fh.write(source)

    cmd = [
        "rustc", "--edition", "2021", "-O",
        "-C", f"overflow-checks={'on' if overflow_checks else 'off'}",
        "-o", exe, src,
    ]
    started = time.monotonic()
    code, _out, err, dur, timed_out = _run(cmd, stdin=None, timeout_s=timeout_s, cwd=tmp)
    if timed_out:
        return BuildResult(ok=False, stderr=err, duration_s=dur,
                           error=f"rustc timed out after {timeout_s:.1f}s")
    if code != 0 or not os.path.exists(exe):
        return BuildResult(ok=False, stderr=err, duration_s=dur,
                           error=(err.strip() or f"rustc exit {code}")[:3000])

    _CACHE[key] = exe
    return BuildResult(ok=True, binary=exe, stderr=err,
                       duration_s=time.monotonic() - started)


def run_binary(binary: str, stdin: str, *, timeout_s: float) -> ExecResult:
    code, out, err, dur, timed_out = _run([binary], stdin=stdin, timeout_s=timeout_s)
    if timed_out:
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          timed_out=True, error=f"timeout after {timeout_s:.2f}s")
    if code != 0:
        # An overflow-checked build reports a wrap as a panic; surface it verbatim so the
        # caller can tell arithmetic overflow apart from an ordinary crash.
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          error=(err.strip() or f"exit {code}")[:2000])
    return ExecResult(ok=True, stdout=out, stderr=err, duration_s=dur)


def compile_and_run(source: str, stdin: str, *, timeout_s: float,
                    overflow_checks: bool = False,
                    compile_timeout_s: float = 60.0) -> tuple[BuildResult, ExecResult | None]:
    build = compile_rust(source, overflow_checks=overflow_checks, timeout_s=compile_timeout_s)
    if not build.ok or not build.binary:
        return build, None
    return build, run_binary(build.binary, stdin, timeout_s=timeout_s)


def is_overflow_panic(result: ExecResult) -> bool:
    """Whether a failed run is specifically a signed-integer overflow."""
    blob = f"{result.stderr}\n{result.error or ''}".lower()
    return "attempt to" in blob and "overflow" in blob
