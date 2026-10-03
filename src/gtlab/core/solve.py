"""Solvers: best responses, Nash equilibria, dominance, and efficiency.

Every function here takes a :class:`~gtlab.core.game.Game` and internally uses
:meth:`Game.payoff_matrices`, which is the one place costs get negated. No
function in this module may look at ``raw_matrices`` for optimisation, only for
reporting numbers back to the user.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

import numpy as np

from .game import Convention, Game

TOL = 1e-9


# --------------------------------------------------------------------------
# Best responses
# --------------------------------------------------------------------------
def best_response_mask(game: Game) -> tuple[np.ndarray, np.ndarray]:
    """Boolean masks marking best-response cells.

    ``row_mask[i, j]`` is True when row action ``i`` is a best response to
    column action ``j``. ``col_mask[i, j]`` is True when column action ``j`` is
    a best response to row action ``i``.

    A cell where both are True is a pure-strategy Nash equilibrium -- this is
    what the UI draws as two coloured triangles meeting in one cell.
    """
    a, b = game.payoff_matrices()
    row_mask = a >= (a.max(axis=0, keepdims=True) - TOL)
    col_mask = b >= (b.max(axis=1, keepdims=True) - TOL)
    return row_mask, col_mask


# --------------------------------------------------------------------------
# Equilibria
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Equilibrium:
    """A Nash equilibrium, in probabilities over each player's actions."""

    row: np.ndarray
    col: np.ndarray
    kind: Literal["pure", "mixed"]
    method: str = "support-enumeration"

    @property
    def is_pure(self) -> bool:
        return self.kind == "pure"

    def support(self, game: Game) -> tuple[list[str], list[str]]:
        r = [a for a, p in zip(game.row_actions, self.row, strict=True) if p > TOL]
        c = [a for a, p in zip(game.col_actions, self.col, strict=True) if p > TOL]
        return r, c

    def outcome_values(self, game: Game) -> tuple[float, float]:
        """Expected value to each player, in the game's own convention."""
        a, b = game.raw_matrices()
        return float(self.row @ a @ self.col), float(self.row @ b @ self.col)

    def social_cost(self, game: Game) -> float:
        return float(self.row @ game.social_cost_matrix() @ self.col)

    def describe(self, game: Game) -> str:
        if self.is_pure:
            i = int(np.argmax(self.row))
            j = int(np.argmax(self.col))
            return f"({game.row_actions[i]}, {game.col_actions[j]})"
        return f"({_fmt_mix(self.row, game.row_actions)}; {_fmt_mix(self.col, game.col_actions)})"


def _fmt_mix(dist: np.ndarray, actions: Iterable[str]) -> str:
    parts = [f"{_pretty_prob(p)} {a}" for a, p in zip(actions, dist, strict=True) if p > TOL]
    return " + ".join(parts)


def _pretty_prob(p: float) -> str:
    """Show 1/3 rather than 0.3333 when the number is a tidy fraction."""
    frac = Fraction(p).limit_denominator(64)
    if abs(float(frac) - p) < 1e-6 and frac.denominator != 1:
        return f"{frac.numerator}/{frac.denominator}"
    return f"{p:.3f}"


def pure_equilibria(game: Game) -> list[Equilibrium]:
    row_mask, col_mask = best_response_mask(game)
    both = row_mask & col_mask
    out: list[Equilibrium] = []
    rows, cols = game.shape
    for i in range(rows):
        for j in range(cols):
            if both[i, j]:
                r = np.zeros(rows)
                c = np.zeros(cols)
                r[i] = 1.0
                c[j] = 1.0
                out.append(Equilibrium(r, c, "pure", "best-response marking"))
    return out


def equilibria(game: Game) -> list[Equilibrium]:
    """All Nash equilibria found by support enumeration (via nashpy).

    Falls back to pure-equilibrium marking if nashpy is unavailable or the game
    is degenerate enough to upset it.
    """
    a, b = game.payoff_matrices()
    found: list[Equilibrium] = []
    try:
        import nashpy as nash

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for r, c in nash.Game(a, b).support_enumeration():
                r = np.asarray(r, dtype=float)
                c = np.asarray(c, dtype=float)
                if not (np.isfinite(r).all() and np.isfinite(c).all()):
                    continue
                kind: Literal["pure", "mixed"] = (
                    "pure" if _is_degenerate_pure(r) and _is_degenerate_pure(c) else "mixed"
                )
                found.append(Equilibrium(r, c, kind))
    except Exception:
        return pure_equilibria(game)

    # Support enumeration misses equilibria in degenerate games; make sure every
    # pure equilibrium is present regardless.
    for eq in pure_equilibria(game):
        if not any(_same(eq, other) for other in found):
            found.append(eq)
    return _dedupe(found)


def _is_degenerate_pure(dist: np.ndarray) -> bool:
    return bool(np.any(dist > 1.0 - TOL))


def _same(x: Equilibrium, y: Equilibrium) -> bool:
    return bool(np.allclose(x.row, y.row, atol=1e-6) and np.allclose(x.col, y.col, atol=1e-6))


def _dedupe(items: list[Equilibrium]) -> list[Equilibrium]:
    out: list[Equilibrium] = []
    for eq in items:
        if not any(_same(eq, kept) for kept in out):
            out.append(eq)
    out.sort(key=lambda e: (e.kind != "pure", tuple(np.round(e.row, 6)), tuple(np.round(e.col, 6))))
    return out


def is_degenerate(game: Game) -> bool:
    """True when the game has ties that make the equilibrium set awkward.

    Support enumeration assumes non-degeneracy; when this is True the list of
    equilibria may be incomplete (there can be a continuum of them).
    """
    a, b = game.payoff_matrices()
    for j in range(a.shape[1]):
        col = a[:, j]
        if np.sum(col >= col.max() - TOL) > 1:
            return True
    for i in range(b.shape[0]):
        row = b[i, :]
        if np.sum(row >= row.max() - TOL) > 1:
            return True
    return False


# --------------------------------------------------------------------------
# Dominance
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class DominanceStep:
    player: str
    removed: str
    dominated_by: str
    strict: bool
    explanation: str


def dominated_actions(
    game: Game, *, strict: bool = True
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Indices ``(loser, winner)`` of actions dominated by another pure action."""
    a, b = game.payoff_matrices()
    return _dominated_rows(a, strict), _dominated_rows(b.T, strict)


def _dominated_rows(m: np.ndarray, strict: bool) -> list[tuple[int, int]]:
    out = []
    n = m.shape[0]
    for loser in range(n):
        for winner in range(n):
            if loser == winner:
                continue
            diff = m[winner] - m[loser]
            if strict:
                if np.all(diff > TOL):
                    out.append((loser, winner))
                    break
            else:
                if np.all(diff >= -TOL) and np.any(diff > TOL):
                    out.append((loser, winner))
                    break
    return out


def iterated_elimination(game: Game, *, strict: bool = True) -> list[DominanceStep]:
    """Run IESDS, returning one explained step at a time.

    Strict elimination is order-independent and never removes a Nash
    equilibrium. Weak elimination is order-dependent and *can* destroy
    equilibria, which is why ``strict`` defaults to True and the UI warns.
    """
    a, b = game.payoff_matrices()
    rows = list(range(a.shape[0]))
    cols = list(range(a.shape[1]))
    steps: list[DominanceStep] = []
    better = "lower cost" if game.convention is Convention.COST else "higher payoff"

    changed = True
    while changed and (len(rows) > 1 or len(cols) > 1):
        changed = False

        sub = a[np.ix_(rows, cols)]
        for loser, winner in _dominated_rows(sub, strict):
            removed, by = rows[loser], rows[winner]
            steps.append(
                DominanceStep(
                    player=game.players[0],
                    removed=game.row_actions[removed],
                    dominated_by=game.row_actions[by],
                    strict=strict,
                    explanation=(
                        f"For {game.players[0]}, '{game.row_actions[by]}' always gives a "
                        f"{better} than '{game.row_actions[removed]}', whatever "
                        f"{game.players[1]} does. So '{game.row_actions[removed]}' can be "
                        f"crossed out."
                    ),
                )
            )
            rows.remove(removed)
            changed = True
            break
        if changed:
            continue

        sub = b[np.ix_(rows, cols)]
        for loser, winner in _dominated_rows(sub.T, strict):
            removed, by = cols[loser], cols[winner]
            steps.append(
                DominanceStep(
                    player=game.players[1],
                    removed=game.col_actions[removed],
                    dominated_by=game.col_actions[by],
                    strict=strict,
                    explanation=(
                        f"For {game.players[1]}, '{game.col_actions[by]}' always gives a "
                        f"{better} than '{game.col_actions[removed]}', whatever "
                        f"{game.players[0]} does. So '{game.col_actions[removed]}' can be "
                        f"crossed out."
                    ),
                )
            )
            cols.remove(removed)
            changed = True
            break

    return steps


def survivors(game: Game, *, strict: bool = True) -> tuple[list[str], list[str]]:
    """Actions left standing after iterated elimination."""
    steps = iterated_elimination(game, strict=strict)
    gone_rows = {s.removed for s in steps if s.player == game.players[0]}
    gone_cols = {s.removed for s in steps if s.player == game.players[1]}
    return (
        [a for a in game.row_actions if a not in gone_rows],
        [a for a in game.col_actions if a not in gone_cols],
    )


# --------------------------------------------------------------------------
# Efficiency: social optimum, Price of Anarchy / Stability
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Efficiency:
    social_optimum: float
    optimum_cells: list[tuple[int, int]]
    best_nash_cost: float
    worst_nash_cost: float
    price_of_anarchy: float | None
    price_of_stability: float | None
    meaningful: bool
    reason: str = ""

    def gap(self) -> float:
        """Absolute welfare loss at the worst equilibrium.

        Always well defined, unlike the ratio.
        """
        return self.worst_nash_cost - self.social_optimum


def efficiency(game: Game, eqs: list[Equilibrium] | None = None) -> Efficiency:
    """Social optimum and Price of Anarchy / Stability, in cost terms.

    PoA = (social cost of the WORST equilibrium) / (best possible social cost).
    PoS = (social cost of the BEST equilibrium) / (best possible social cost).

    Both are >= 1 and measure how much selfish play degrades the outcome.

    The ratio is only meaningful when the optimal social cost is strictly
    positive. For a game stated in payoffs (e.g. Hawk-Dove), social cost is
    negative and the ratio would be misleading, so we report it as not
    meaningful and the UI shows the absolute gap instead.
    """
    social = game.social_cost_matrix()
    optimum = float(social.min())
    cells = [(int(i), int(j)) for i, j in zip(*np.where(social <= optimum + TOL), strict=True)]

    eqs = equilibria(game) if eqs is None else eqs
    if not eqs:
        return Efficiency(
            optimum,
            cells,
            float("nan"),
            float("nan"),
            None,
            None,
            False,
            "no Nash equilibrium was found",
        )

    costs = [eq.social_cost(game) for eq in eqs]
    best, worst = min(costs), max(costs)

    if optimum <= TOL:
        return Efficiency(
            optimum,
            cells,
            best,
            worst,
            None,
            None,
            False,
            "the best achievable social cost is not strictly positive, so a ratio "
            "would be misleading -- compare the absolute numbers instead",
        )

    return Efficiency(optimum, cells, best, worst, worst / optimum, best / optimum, True)


# --------------------------------------------------------------------------
# Zero-sum games
# --------------------------------------------------------------------------
def zero_sum_value(game: Game) -> tuple[float, np.ndarray, np.ndarray] | None:
    """Value and optimal strategies of a zero-sum game, by linear programming.

    Returns the value **to the row player, in payoff terms**, or None if the
    game is not zero-sum.
    """
    if not game.is_zero_sum:
        return None
    a, _ = game.payoff_matrices()
    try:
        import nashpy as nash

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            row, col = nash.Game(a, -a).linear_program()
        value = float(np.asarray(row) @ a @ np.asarray(col))
        return value, np.asarray(row, dtype=float), np.asarray(col, dtype=float)
    except Exception:
        return None
