"""gtlab -- an interactive game theory visualiser and simulator.

Quick start::

    import gtlab

    game = gtlab.get("prisoners_dilemma")
    print(gtlab.summary(game))

Every game is registered by importing :mod:`gtlab.games`, which happens here.
"""

from . import games  # noqa: F401  (registers the catalogue)
from .core import (
    Convention,
    Game,
    Parameter,
    all_games,
    best_response_mask,
    catalogue,
    efficiency,
    equilibria,
    explain_dominance,
    explain_efficiency,
    explain_equilibria,
    explain_zero_sum,
    find_threshold,
    get,
    is_degenerate,
    iterated_elimination,
    keys,
    pure_equilibria,
    register,
    summary,
    survivors,
    sweep,
    zero_sum_value,
)

__version__ = "0.1.0"

__all__ = [
    "Convention",
    "Game",
    "Parameter",
    "__version__",
    "all_games",
    "best_response_mask",
    "catalogue",
    "efficiency",
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
    "summary",
    "survivors",
    "sweep",
    "zero_sum_value",
]
