"""Child process entry point: import a module, call one function, write JSON back.

Kept deliberately small. It runs inside the untrusted process, so it must not depend on
anything from the solver package, and it must write its result to a file rather than stdout
so that a candidate printing debug output cannot corrupt the channel.
"""

from __future__ import annotations

import importlib.util
import json
import sys


def _jsonable(value):
    """Make the return value survive JSON without lying about its shape.

    Tuples become lists (JSON has no tuple) and sets become sorted lists. Comparison in the
    verifier is structural and applies the same normalisation to both sides, so an oracle
    returning a tuple and a candidate returning a list are not treated as a disagreement.
    """
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        try:
            return sorted(_jsonable(v) for v in value)
        except TypeError:
            return [_jsonable(v) for v in value]
    if isinstance(value, complex):
        return [value.real, value.imag]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", "replace")
    return value


def main() -> int:
    mod_path, entrypoint, args_path, out_path = sys.argv[1:5]
    result: dict

    try:
        with open(args_path, encoding="utf-8") as fh:
            args = json.load(fh)

        spec = importlib.util.spec_from_file_location("candidate", mod_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {mod_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["candidate"] = module
        spec.loader.exec_module(module)

        fn = getattr(module, entrypoint, None)
        if fn is None:
            raise AttributeError(f"module defines no {entrypoint!r}")
        if not callable(fn):
            raise TypeError(f"{entrypoint!r} is not callable")

        value = fn(*args)
        result = {"ok": True, "value": _jsonable(value)}

    except RecursionError:
        result = {"ok": False, "error": "RecursionError: recursion limit exceeded"}
    except MemoryError:
        result = {"ok": False, "error": "MemoryError: allocation failed"}
    except BaseException as exc:  # noqa: BLE001 - the point is to report anything at all
        import traceback
        result = {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-2000:],
        }

    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh)
    except (TypeError, ValueError) as exc:
        # The call itself may have succeeded while returning something unserialisable.
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump({"ok": False, "error": f"result is not JSON-serialisable: {exc}"}, fh)

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
