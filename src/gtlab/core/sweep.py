"""Parametric sweeps: find where the answer changes.

The course asks, for Hawk-Dove with V = 10: "does your answer change if C
becomes smaller? If so, when?". That question is a bifurcation hunt, and it is
the reason this module exists: sweep a parameter, classify the equilibrium set
at each value, and report the exact points where the classification changes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .game import Game
from .solve import Equilibrium, equilibria

TOL = 1e-9


@dataclass(frozen=True)
class Regime:
    """A stretch of parameter values over which the answer keeps its shape."""

    start: float
    end: float
    label: str
    n_pure: int
    n_mixed: int

    def contains(self, value: float) -> bool:
        return self.start - TOL <= value <= self.end + TOL

    def width(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class Sweep:
    parameter: str
    values: np.ndarray
    labels: list[str]
    regimes: list[Regime]
    mixed_prob: np.ndarray  # row player's probability on action 0, NaN if no mixed NE

    def boundaries(self) -> list[float]:
        """Parameter values where the equilibrium structure changes."""
        return [r.end for r in self.regimes[:-1]]

    def regime_at(self, value: float) -> Regime | None:
        for r in self.regimes:
            if r.contains(value):
                return r
        return None


def classify(eqs: list[Equilibrium], game: Game) -> str:
    """A short human label for an equilibrium set."""
    if not eqs:
        return "no equilibrium found"
    pure = [e for e in eqs if e.is_pure]
    mixed = [e for e in eqs if not e.is_pure]
    bits = []
    if pure:
        names = ", ".join(e.describe(game) for e in pure)
        bits.append(f"{len(pure)} pure: {names}")
    if mixed:
        bits.append(f"{len(mixed)} mixed")
    return "; ".join(bits)


def sweep(
    game: Game,
    parameter: str,
    start: float,
    stop: float,
    steps: int = 241,
) -> Sweep:
    """Sweep one parameter and group the results into regimes."""
    values = np.linspace(start, stop, steps)
    labels: list[str] = []
    mixed_prob = np.full(steps, np.nan)

    for k, v in enumerate(values):
        variant = game.with_params(**{parameter: float(v)})
        eqs = equilibria(variant)
        labels.append(classify(eqs, variant))
        for eq in eqs:
            if not eq.is_pure:
                mixed_prob[k] = float(eq.row[0])
                break

    regimes: list[Regime] = []
    run_start = 0
    for k in range(1, steps + 1):
        if k == steps or labels[k] != labels[run_start]:
            eqs_here = equilibria(game.with_params(**{parameter: float(values[run_start])}))
            regimes.append(
                Regime(
                    start=float(values[run_start]),
                    end=float(values[k - 1]),
                    label=labels[run_start],
                    n_pure=sum(1 for e in eqs_here if e.is_pure),
                    n_mixed=sum(1 for e in eqs_here if not e.is_pure),
                )
            )
            run_start = k

    return Sweep(parameter, values, labels, regimes, mixed_prob)


def find_threshold(
    game: Game,
    parameter: str,
    low: float,
    high: float,
    iterations: int = 60,
) -> float | None:
    """Bisect to pin down a single change-point between ``low`` and ``high``.

    Assumes the structure differs at the two ends. Returns the parameter value
    where the answer flips, to within floating point.
    """
    def label_at(v: float) -> str:
        variant = game.with_params(**{parameter: float(v)})
        return classify(equilibria(variant), variant)

    lo_label, hi_label = label_at(low), label_at(high)
    if lo_label == hi_label:
        return None

    for _ in range(iterations):
        mid = (low + high) / 2.0
        if label_at(mid) == lo_label:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0
