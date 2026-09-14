"""Run generated Python in a separate process, with a wall-clock kill.

Everything the model writes is treated as hostile-by-accident rather than hostile-by-intent:
it can loop forever, allocate without bound, or raise from module scope. A thread cannot be
killed in CPython, so each execution is its own process and the timeout is enforced from the
outside.

Two shapes are supported because the problems come in two shapes:

* ``call_function``: the Python problems name an ``entrypoint`` to be called with arguments.
* ``run_stdin``: the Rust problems are stdin/stdout programs, and the Python oracle written
  against them has to be driven the same way so the two can be compared token for token.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "_py_driver.py")


@dataclass
class ExecResult:
    ok: bool
    value: object = None          # decoded return value, for call_function
    stdout: str = ""              # raw stdout, for run_stdin
    stderr: str = ""
    duration_s: float = 0.0
    timed_out: bool = False
    error: str | None = None

    @property
    def failed(self) -> bool:
        return not self.ok


def _run(cmd: list[str], *, stdin: str | None, timeout_s: float, cwd: str | None = None) -> tuple[int, str, str, float, bool]:
    started = time.monotonic()
    kwargs: dict = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        proc = subprocess.run(
            cmd,
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(timeout_s, 0.2),
            cwd=cwd,
            **kwargs,
        )
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        err = exc.stderr or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        return -1, out, err, time.monotonic() - started, True
    return proc.returncode, proc.stdout or "", proc.stderr or "", time.monotonic() - started, False


def call_function(source: str, entrypoint: str, args: list, *, timeout_s: float,
                  workdir: str | None = None) -> ExecResult:
    """Import ``source``, call ``entrypoint(*args)``, return the decoded result.

    Arguments and the return value cross the process boundary as JSON, so anything the
    problems actually use (numbers, strings, lists, tuples, nested combinations) survives.
    Tuples arrive back as lists; comparison is done structurally, which makes that harmless.
    """
    tmp = workdir or tempfile.mkdtemp(prefix="cbox_py_")
    mod_path = os.path.join(tmp, "candidate.py")
    args_path = os.path.join(tmp, "args.json")
    out_path = os.path.join(tmp, "out.json")
    with open(mod_path, "w", encoding="utf-8") as fh:
        fh.write(source)
    with open(args_path, "w", encoding="utf-8") as fh:
        json.dump(args, fh)

    code, out, err, dur, timed_out = _run(
        [sys.executable, DRIVER, mod_path, entrypoint, args_path, out_path],
        stdin=None, timeout_s=timeout_s, cwd=tmp,
    )
    if timed_out:
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          timed_out=True, error=f"timeout after {timeout_s:.2f}s")

    # Read the result file before looking at the exit code: the driver exits 1 on a handled
    # exception but still writes the exception text, and that text is what adjudication needs.
    # Falling through on the exit code alone would throw away the only useful diagnostic.
    payload = None
    try:
        with open(out_path, encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError):
        payload = None

    if payload is None:
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          error=(err.strip() or f"exit {code}, no result written")[:2000])
    if not payload.get("ok"):
        detail = str(payload.get("error") or "")
        tb = payload.get("traceback")
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          error=(detail or tb or f"exit {code}")[:2000])
    return ExecResult(ok=True, value=payload.get("value"), stdout=out, stderr=err, duration_s=dur)


def run_stdin(source: str, stdin: str, *, timeout_s: float,
              workdir: str | None = None) -> ExecResult:
    """Run ``source`` as a script with ``stdin`` piped in, return stdout."""
    tmp = workdir or tempfile.mkdtemp(prefix="cbox_pys_")
    path = os.path.join(tmp, "program.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(source)
    code, out, err, dur, timed_out = _run(
        [sys.executable, path], stdin=stdin, timeout_s=timeout_s, cwd=tmp
    )
    if timed_out:
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          timed_out=True, error=f"timeout after {timeout_s:.2f}s")
    if code != 0:
        return ExecResult(ok=False, stdout=out, stderr=err, duration_s=dur,
                          error=(err.strip() or f"exit {code}")[:2000])
    return ExecResult(ok=True, stdout=out, stderr=err, duration_s=dur)


def syntax_ok(source: str) -> tuple[bool, str | None]:
    """Cheap gate before spending a process on obviously broken output."""
    try:
        compile(source, "<candidate>", "exec")
    except SyntaxError as exc:
        return False, f"{exc.msg} at line {exc.lineno}"
    return True, None
