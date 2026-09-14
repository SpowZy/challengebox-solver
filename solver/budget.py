"""Monotonic time budget with phase allocation and a reserve that is never spent.

The scoring rule is binary: a solution returned after the deadline scores zero, exactly
like a solution that was never produced. So the emit phase gets a hard reserve carved out
before any other phase is allowed to allocate, and every long-running step asks the budget
whether it still has room before starting rather than discovering the overrun afterwards.

**Enforcement is global, not per phase.** `must_emit_now` and `spendable_s` are what the
solver actually consults, before every unit of work: each generated input in the reference
pass, each input for each candidate, each compile. The per-phase allocation below is the
planning and reporting layer, and `phase_remaining_s`, `can_afford` and `grant` exist for a
caller that wants to bound a single step against its phase rather than against the whole
clock. The solver deliberately does not: its expensive step is one indivisible burst of nine
concurrent model calls, and cutting that at a phase boundary would throw away every candidate
still in flight and leave nothing to emit, which is the opposite of what the reserve is for.
The only hard floor in the system is therefore the emit reserve.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class BudgetExhausted(RuntimeError):
    """Raised when a phase is asked for time that the budget cannot give."""


# Fractions of the *usable* budget (deadline minus emit reserve). They are weights, not
# hard walls: a phase that finishes early hands the remainder back to the pool.
#
# `adjudicate` is held open and deliberately never spent. It was the repair round, and the
# design dropped repair from the hot path on the evidence that it fixes crashes rather than
# misreadings, which are this benchmark's failure mode (see ARCHITECTURE.md). Keeping its
# share unallocated rather than redistributing it is the conservative choice: across the
# recorded runs `verify` used well under its own share, so the reservation costs nothing
# measurable and leaves room if a repair round is ever added back.
DEFAULT_WEIGHTS = {
    "analyse": 0.07,
    "generate": 0.27,
    "verify": 0.48,
    "adjudicate": 0.18,
}

# Never spent by anything except emit. Enough to serialise a file and flush it.
EMIT_RESERVE_S = 20.0

# Below this, stop starting new work and go straight to emit.
PANIC_MARGIN_S = 3.0


@dataclass
class Phase:
    name: str
    allocated_s: float
    started_at: float | None = None
    ended_at: float | None = None

    @property
    def elapsed_s(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.ended_at if self.ended_at is not None else time.monotonic()
        return end - self.started_at


@dataclass
class Budget:
    """Owns the clock for one problem.

    `deadline_s` is what the problem JSON declares. `scale` shrinks it for testing the
    emit-under-pressure path without editing the sample files.
    """

    deadline_s: float
    scale: float = 1.0
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    emit_reserve_s: float = EMIT_RESERVE_S

    _start: float = field(default_factory=time.monotonic, init=False)
    phases: dict[str, Phase] = field(default_factory=dict, init=False)
    _current: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        total = self.deadline_s * self.scale
        # On a heavily scaled-down run the fixed reserve can swallow everything, so it
        # degrades proportionally instead of leaving nothing to work with.
        self.emit_reserve_s = min(self.emit_reserve_s, total * 0.15)
        usable = max(total - self.emit_reserve_s, 0.0)
        weight_sum = sum(self.weights.values()) or 1.0
        self.phases = {
            name: Phase(name=name, allocated_s=usable * (w / weight_sum))
            for name, w in self.weights.items()
        }

    # ---- clock ----------------------------------------------------------------

    @property
    def elapsed_s(self) -> float:
        return time.monotonic() - self._start

    @property
    def total_s(self) -> float:
        return self.deadline_s * self.scale

    @property
    def remaining_s(self) -> float:
        """Wall clock left before the real deadline, reserve included."""
        return self.total_s - self.elapsed_s

    @property
    def spendable_s(self) -> float:
        """Wall clock left that is not the emit reserve. Can go negative."""
        return self.remaining_s - self.emit_reserve_s

    @property
    def must_emit_now(self) -> bool:
        return self.spendable_s <= PANIC_MARGIN_S

    # ---- phases ---------------------------------------------------------------

    def start(self, name: str) -> Phase:
        phase = self.phases.setdefault(name, Phase(name=name, allocated_s=0.0))
        phase.started_at = time.monotonic()
        self._current = name
        return phase

    def end(self, name: str) -> None:
        phase = self.phases.get(name)
        if phase is not None and phase.ended_at is None:
            phase.ended_at = time.monotonic()
        if self._current == name:
            self._current = None

    def phase_remaining_s(self, name: str) -> float:
        """Time left in this phase's own allocation, capped by the global spendable time.

        A phase may not overrun into the emit reserve even if its own allocation says
        it could, which is why this is a min and not just the phase arithmetic.
        """
        phase = self.phases.get(name)
        if phase is None:
            return max(self.spendable_s, 0.0)
        own = phase.allocated_s - phase.elapsed_s
        return max(min(own, self.spendable_s), 0.0)

    def can_afford(self, seconds: float, name: str | None = None) -> bool:
        """Whether a step of the given expected cost should be started at all."""
        if self.must_emit_now:
            return False
        room = self.phase_remaining_s(name) if name else self.spendable_s
        return room >= seconds

    def grant(self, seconds: float, name: str | None = None) -> float:
        """Largest timeout that may be handed to a subprocess right now."""
        room = self.phase_remaining_s(name) if name else self.spendable_s
        room = min(room, max(self.spendable_s, 0.0))
        if room <= 0:
            raise BudgetExhausted(f"no time left for {name or 'work'}")
        return min(seconds, room)

    # ---- reporting ------------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "deadline_s": self.deadline_s,
            "scale": self.scale,
            "total_s": round(self.total_s, 3),
            "elapsed_s": round(self.elapsed_s, 3),
            "remaining_s": round(self.remaining_s, 3),
            "emit_reserve_s": round(self.emit_reserve_s, 3),
            "phases": {
                name: {
                    "allocated_s": round(p.allocated_s, 3),
                    "elapsed_s": round(p.elapsed_s, 3),
                }
                for name, p in self.phases.items()
            },
        }
