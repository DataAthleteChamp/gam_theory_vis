"""Core game model.

The course defines a strategic game in normal form as

    G = (N, (A_i)_{i in N}, (c_i)_{i in N})

where ``c_i`` is a COST that player ``i`` MINIMISES, and notes that the
payoff description ``u_i = -c_i`` is interchangeable.

Every solver in the Python ecosystem (nashpy, Gambit, Axelrod) assumes players
MAXIMISE payoffs. Mixing the two conventions is the single easiest way to get
silently wrong answers, so this module enforces one rule:

    A game stores its numbers exactly as the user typed them, plus a flag
    saying what they mean. Negation happens in exactly ONE place --
    :meth:`Game.payoff_matrices` -- which is the only function allowed to hand
    numbers to a solver.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum

import numpy as np

Number = float | int
# A cell entry is either a literal number, or a function of the game's
# parameters, which is what makes a game parametric (e.g. Hawk-Dove in V and C).
CellValue = Number | Callable[[Mapping[str, float]], Number]


class Convention(str, Enum):
    """What the numbers in the table mean."""

    COST = "cost"  # lower is better; players minimise (the course default)
    PAYOFF = "payoff"  # higher is better; players maximise

    @property
    def better(self) -> str:
        return "lower" if self is Convention.COST else "higher"

    @property
    def symbol(self) -> str:
        return "c" if self is Convention.COST else "u"

    def flip(self) -> Convention:
        return Convention.PAYOFF if self is Convention.COST else Convention.COST


@dataclass(frozen=True)
class Parameter:
    """A named, adjustable number, e.g. the fight cost ``C`` in Hawk-Dove."""

    name: str
    value: float
    min: float = 0.0
    max: float = 20.0
    step: float = 0.1
    label: str = ""

    def described(self) -> str:
        return self.label or self.name


@dataclass(frozen=True)
class Game:
    """A two-player game in normal form.

    ``table[i][j]`` holds the pair of entries for row action ``i`` and column
    action ``j``. Each entry is a number or a callable of the parameters.
    """

    key: str
    name: str
    row_actions: Sequence[str]
    col_actions: Sequence[str]
    table: Sequence[Sequence[tuple[CellValue, CellValue]]]
    convention: Convention = Convention.COST
    players: tuple[str, str] = ("Player 1", "Player 2")
    parameters: tuple[Parameter, ...] = ()
    description: str = ""
    source: str = ""
    tags: tuple[str, ...] = ()
    notes: str = ""
    _overrides: Mapping[str, float] = field(default_factory=dict, repr=False)

    # -- parameters ---------------------------------------------------------
    @property
    def param_values(self) -> dict[str, float]:
        values = {p.name: p.value for p in self.parameters}
        values.update(self._overrides)
        return values

    def with_params(self, **overrides: float) -> Game:
        """Return a copy with different parameter values (for sliders)."""
        unknown = set(overrides) - {p.name for p in self.parameters}
        if unknown:
            raise KeyError(
                f"{self.key} has no parameter(s) {sorted(unknown)}; "
                f"known: {[p.name for p in self.parameters]}"
            )
        merged = dict(self._overrides)
        merged.update(overrides)
        return replace(self, _overrides=merged)

    # -- the numbers --------------------------------------------------------
    def _resolve(self, cell: CellValue) -> float:
        if callable(cell):
            return float(cell(self.param_values))
        return float(cell)

    def raw_matrices(self) -> tuple[np.ndarray, np.ndarray]:
        """The numbers exactly as the user sees them, in the game's own
        convention. Never hand these to a solver."""
        rows, cols = self.shape
        first = np.empty((rows, cols), dtype=float)
        second = np.empty((rows, cols), dtype=float)
        for i in range(rows):
            for j in range(cols):
                a, b = self.table[i][j]
                first[i, j] = self._resolve(a)
                second[i, j] = self._resolve(b)
        return first, second

    def payoff_matrices(self) -> tuple[np.ndarray, np.ndarray]:
        """THE ONLY sign-flip boundary in the whole codebase.

        Returns matrices in maximisation form, which is what every solver
        expects. If the game is stated in costs we return ``-c``.
        """
        a, b = self.raw_matrices()
        if self.convention is Convention.COST:
            return -a, -b
        return a, b

    def social_cost_matrix(self) -> np.ndarray:
        """Total cost of each outcome (always 'lower is better').

        Social welfare is the negative of this.
        """
        a, b = self.raw_matrices()
        total = a + b
        return total if self.convention is Convention.COST else -total

    def as_convention(self, convention: Convention) -> Game:
        """Restate the same game in the other convention, negating the table."""
        if convention is self.convention:
            return self
        flipped = [[(_negate(a), _negate(b)) for (a, b) in row] for row in self.table]
        return replace(self, table=flipped, convention=convention)

    # -- shape helpers ------------------------------------------------------
    @property
    def shape(self) -> tuple[int, int]:
        return len(self.row_actions), len(self.col_actions)

    @property
    def is_symmetric(self) -> bool:
        if self.shape[0] != self.shape[1]:
            return False
        if list(self.row_actions) != list(self.col_actions):
            return False
        a, b = self.raw_matrices()
        return bool(np.allclose(a, b.T))

    @property
    def is_zero_sum(self) -> bool:
        a, b = self.raw_matrices()
        return bool(np.allclose(a + b, 0.0))

    def validate(self) -> None:
        rows, cols = self.shape
        if rows == 0 or cols == 0:
            raise ValueError(f"{self.key}: game needs at least one action per player")
        if len(self.table) != rows:
            raise ValueError(f"{self.key}: table has {len(self.table)} rows but {rows} row actions")
        for i, row in enumerate(self.table):
            if len(row) != cols:
                raise ValueError(
                    f"{self.key}: table row {i} has {len(row)} cells but {cols} column actions"
                )
            for j, cell in enumerate(row):
                if len(cell) != 2:
                    raise ValueError(f"{self.key}: cell ({i},{j}) must be a (p1, p2) pair")
        self.raw_matrices()  # force-resolve every callable to catch bad formulas

    def __str__(self) -> str:
        return f"{self.name} [{self.convention.value}, {self.shape[0]}x{self.shape[1]}]"


def _negate(cell: CellValue) -> CellValue:
    if callable(cell):
        inner = cell

        def negated(params: Mapping[str, float]) -> float:
            return -float(inner(params))

        return negated
    return -float(cell)
