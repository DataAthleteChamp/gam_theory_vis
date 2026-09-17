"""Core package exports."""

from .game import CellValue, Convention, Game, Number, Parameter
from .registry import all_games, catalogue, get, keys, register
from .solve import (
    DominanceStep,
    Efficiency,
    Equilibrium,
    best_response_mask,
    dominated_actions,
    efficiency,
    equilibria,
    is_degenerate,
    iterated_elimination,
    pure_equilibria,
    survivors,
    zero_sum_value,
)
from .sweep import Regime, Sweep, classify, find_threshold, sweep
from .explain import (
    explain_dominance,
    explain_efficiency,
    explain_equilibria,
    explain_zero_sum,
    summary,
)

__all__ = [
    "CellValue",
    "Convention",
    "Game",
    "Number",
    "Parameter",
    "all_games",
    "best_response_mask",
    "catalogue",
    "classify",
    "DominanceStep",
    "dominated_actions",
    "Efficiency",
    "efficiency",
    "Equilibrium",
    "equilibria",
    "explain_dominance",
    "explain_efficiency",
    "explain_equilibria",
    "explain_zero_sum",
    "find_threshold",
    "get",
    "is_degenerate",
    "iterated_elimination",
    "keys",
    "pure_equilibria",
    "register",
    "Regime",
    "summary",
    "survivors",
    "sweep",
    "Sweep",
    "zero_sum_value",
]
