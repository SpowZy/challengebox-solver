"""Model access, behind one interface so the solver never names a vendor.

Two implementations ship:

* ``ClaudeCliProvider`` shells out to the ``claude`` binary in print mode. It needs no API
  key because it rides the local CLI session, which is why this system can actually be run
  and benchmarked rather than only described.
* ``OpenAICompatibleProvider`` speaks the ``/chat/completions`` shape, for any host that
  exposes it. Selected by config, no source change.

Every call is recorded: role, latency, exit status, byte counts. The run report reads those
records back, so cost and timing in the results table come from measurement, never from a
price list written by hand.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Protocol


@dataclass
class Call:
    role: str
    tag: str
    ok: bool
    latency_s: float
    prompt_chars: int
    output_chars: int
    error: str | None = None
    model: str | None = None


class ProviderError(RuntimeError):
    pass


class Provider(Protocol):
    name: str
    calls: list[Call]

    def complete(self, prompt: str, *, role: str, tag: str, timeout_s: float) -> str: ...


@dataclass
class _Base:
    name: str = "base"
    calls: list[Call] = field(default_factory=list)

    def _record(self, **kw) -> None:
        self.calls.append(Call(**kw))

    def usage(self) -> dict:
        ok = [c for c in self.calls if c.ok]
        return {
            "provider": self.name,
            "calls": len(self.calls),
            "failed": len(self.calls) - len(ok),
            "latency_s_total": round(sum(c.latency_s for c in self.calls), 3),
            "prompt_chars_total": sum(c.prompt_chars for c in self.calls),
            "output_chars_total": sum(c.output_chars for c in self.calls),
            "detail": [asdict(c) for c in self.calls],
        }


@dataclass
class ClaudeCliProvider(_Base):
    """Runs `claude -p <prompt>` and returns stdout.

    The CLI is a session, not a stateless endpoint, so each call gets its own process and
    nothing is carried between them. That isolation is deliberate: the oracle must not be
    able to see what the candidate did.
    """

    name: str = "claude-cli"
    binary: str = "claude"
    model: str | None = None

    def __post_init__(self) -> None:
        if shutil.which(self.binary) is None:
            raise ProviderError(
                f"{self.binary!r} not found on PATH; install the CLI or pick another provider"
            )

    def complete(self, prompt: str, *, role: str, tag: str, timeout_s: float) -> str:
        cmd = [self.binary, "-p", prompt]
        if self.model:
            cmd[1:1] = ["--model", self.model]
        started = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=max(timeout_s, 1.0),
            )
        except subprocess.TimeoutExpired:
            self._record(
                role=role, tag=tag, ok=False, latency_s=time.monotonic() - started,
                prompt_chars=len(prompt), output_chars=0,
                error=f"timeout after {timeout_s:.1f}s", model=self.model,
            )
            raise ProviderError(f"{role}:{tag} timed out after {timeout_s:.1f}s")

        latency = time.monotonic() - started
        out = (proc.stdout or "").strip()
        if proc.returncode != 0 or not out:
            err = (proc.stderr or "").strip()[:400] or f"exit {proc.returncode}, empty stdout"
            self._record(
                role=role, tag=tag, ok=False, latency_s=latency,
                prompt_chars=len(prompt), output_chars=len(out), error=err, model=self.model,
            )
            raise ProviderError(f"{role}:{tag} failed: {err}")

        self._record(
            role=role, tag=tag, ok=True, latency_s=latency,
            prompt_chars=len(prompt), output_chars=len(out), model=self.model,
        )
        return out


@dataclass
class OpenAICompatibleProvider(_Base):
    """Any host exposing POST {base_url}/chat/completions with a bearer key."""

    name: str = "openai-compatible"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key_env: str = "OPENROUTER_API_KEY"
    model: str = "anthropic/claude-sonnet-4.5"
    max_tokens: int = 16000

    def complete(self, prompt: str, *, role: str, tag: str, timeout_s: float) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise ProviderError(f"{self.api_key_env} is not set")
        body = json.dumps({
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=max(timeout_s, 1.0)) as resp:
                payload = json.load(resp)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            self._record(
                role=role, tag=tag, ok=False, latency_s=time.monotonic() - started,
                prompt_chars=len(prompt), output_chars=0, error=str(exc)[:400], model=self.model,
            )
            raise ProviderError(f"{role}:{tag} failed: {exc}") from exc

        latency = time.monotonic() - started
        try:
            out = payload["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, AttributeError) as exc:
            self._record(
                role=role, tag=tag, ok=False, latency_s=latency,
                prompt_chars=len(prompt), output_chars=0,
                error=f"unexpected response shape: {exc}", model=self.model,
            )
            raise ProviderError(f"{role}:{tag} returned an unexpected shape") from exc

        self._record(
            role=role, tag=tag, ok=True, latency_s=latency,
            prompt_chars=len(prompt), output_chars=len(out), model=self.model,
        )
        return out


def build_provider(kind: str = "claude-cli", **kw) -> Provider:
    if kind == "claude-cli":
        return ClaudeCliProvider(**kw)
    if kind in ("openai-compatible", "openrouter"):
        return OpenAICompatibleProvider(**kw)
    raise ProviderError(f"unknown provider {kind!r}")


# ---- extraction helpers ---------------------------------------------------------

def extract_code(text: str, language: str) -> str:
    """Pull the code out of a model reply.

    Models wrap code in fences, sometimes narrate around it, and occasionally emit several
    blocks. The last fenced block of the right language wins, because a model that revises
    itself puts the final version last. Falls back to the whole reply when unfenced.
    """
    fences = {"python": ("```python", "```py"), "rust": ("```rust", "```rs")}
    tags = fences.get(language, ())
    blocks: list[str] = []
    lowered = text.lower()
    idx = 0
    while True:
        starts = [(lowered.find(t, idx), t) for t in tags]
        starts = [(p, t) for p, t in starts if p != -1]
        if not starts:
            break
        # Earliest position wins; on a tie the LONGEST tag wins. Both "```py" and
        # "```python" match "```python" at the same offset, and consuming the short one
        # leaves "thon" as the first line of the file.
        pos = min(p for p, _ in starts)
        tag = max((t for p, t in starts if p == pos), key=len)
        body_start = pos + len(tag)
        end = text.find("```", body_start)
        if end == -1:
            blocks.append(text[body_start:].strip())
            break
        blocks.append(text[body_start:end].strip())
        idx = end + 3

    if not blocks:  # untagged fence
        first = text.find("```")
        if first != -1:
            body_start = text.find("\n", first)
            end = text.find("```", first + 3)
            if body_start != -1 and end != -1:
                blocks.append(text[body_start + 1:end].strip())

    return blocks[-1] if blocks else text.strip()
