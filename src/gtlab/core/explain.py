"""Turn a solved game into plain English.

The point of the tool is learning, so every number on screen should come with a
sentence a beginner can read. Nothing here does any maths; it only phrases what
:mod:`gtlab.core.solve` already computed.
"""

from __future__ import annotations

from .game import Convention, Game
from .solve import (
    Efficiency,
    Equilibrium,
    efficiency,
    equilibria,
    is_degenerate,
    iterated_elimination,
    survivors,
    zero_sum_value,
)


def explain_equilibria(game: Game, eqs: list[Equilibrium] | None = None) -> str:
    eqs = equilibria(game) if eqs is None else eqs
    verb = "pays the least" if game.convention is Convention.COST else "gets the most"

    if not eqs:
        return "No Nash equilibrium was found, which usually means the game is degenerate."

    lines = []
    if len(eqs) == 1:
        eq = eqs[0]
        lines.append(f"This game has exactly one Nash equilibrium: **{eq.describe(game)}**.")
    else:
        lines.append(f"This game has **{len(eqs)} Nash equilibria**:")
        for eq in eqs:
            lines.append(f"- {eq.describe(game)} ({eq.kind})")

    eq = eqs[0]
    v1, v2 = eq.outcome_values(game)
    unit = "cost" if game.convention is Convention.COST else "payoff"
    lines.append(
        f"\nAt {eq.describe(game)} the {unit} is {v1:.3g} for {game.players[0]} "
        f"and {v2:.3g} for {game.players[1]}."
    )
    lines.append(
        f"\nAn equilibrium means neither player can change their own action alone and "
        f"do better. Each one {verb} they can, *given what the other is doing*."
    )

    if any(not e.is_pure for e in eqs):
        lines.append(
            "\nA **mixed** equilibrium means randomising. The probabilities are chosen so "
            "the opponent is left indifferent between their options -- that is exactly what "
            "stops them from exploiting you."
        )

    if is_degenerate(game):
        lines.append(
            "\n⚠️ This game is *degenerate* (there are ties in best responses), so the list "
            "above may not be complete -- there can be infinitely many equilibria."
        )
    return "\n".join(lines)


def explain_dominance(game: Game, *, strict: bool = True) -> str:
    steps = iterated_elimination(game, strict=strict)
    if not steps:
        kind = "strictly" if strict else "weakly"
        return f"No action is {kind} dominated, so nothing can be eliminated this way."

    lines = ["Eliminating dominated actions, one step at a time:\n"]
    for n, step in enumerate(steps, 1):
        lines.append(f"{n}. {step.explanation}")

    rows, cols = survivors(game, strict=strict)
    if len(rows) == 1 and len(cols) == 1:
        lines.append(
            f"\nOnly ({rows[0]}, {cols[0]}) survives. A game solvable this way is called "
            f"*dominance solvable*, and that surviving outcome must be the unique Nash "
            f"equilibrium."
        )
    else:
        lines.append(
            f"\nWhat survives: {game.players[0]} may play {rows}, "
            f"{game.players[1]} may play {cols}."
        )
    if not strict:
        lines.append(
            "\n⚠️ Weak elimination depends on the order you do it in, and it can delete "
            "genuine equilibria. Strict elimination never does."
        )
    return "\n".join(lines)


def explain_efficiency(game: Game, eff: Efficiency | None = None) -> str:
    eff = efficiency(game) if eff is None else eff
    unit = "total cost" if game.convention is Convention.COST else "total cost (= minus total payoff)"

    lines = [
        f"The best possible outcome for the two players together has {unit} "
        f"**{eff.social_optimum:.3g}**."
    ]
    cells = ", ".join(
        f"({game.row_actions[i]}, {game.col_actions[j]})" for i, j in eff.optimum_cells
    )
    lines.append(f"That happens at: {cells}.")
    lines.append(f"The worst equilibrium has total cost **{eff.worst_nash_cost:.3g}**.")

    if eff.meaningful and eff.price_of_anarchy is not None:
        lines.append(
            f"\n**Price of Anarchy = {eff.worst_nash_cost:.3g} / {eff.social_optimum:.3g} "
            f"= {eff.price_of_anarchy:.4g}.**"
        )
        lines.append(
            f"Selfish play is {eff.price_of_anarchy:.4g}× worse than the best the players "
            f"could have done together. A value of 1 would mean selfishness costs nothing."
        )
        if eff.price_of_stability is not None and abs(
            eff.price_of_stability - eff.price_of_anarchy
        ) > 1e-9:
            lines.append(
                f"The Price of Stability is {eff.price_of_stability:.4g}, using the *best* "
                f"equilibrium instead of the worst."
            )
    else:
        lines.append(
            f"\nA Price of Anarchy ratio is not meaningful here: {eff.reason}. "
            f"The absolute loss at the worst equilibrium is {eff.gap():.3g}."
        )
    return "\n".join(lines)


def explain_zero_sum(game: Game) -> str | None:
    result = zero_sum_value(game)
    if result is None:
        return None
    value, row, col = result
    sign = "in payoff terms" if game.convention is Convention.PAYOFF else "in payoff terms (= minus cost)"
    lines = [
        f"This is a **zero-sum** game: whatever one player gains, the other loses.",
        f"Its value is **{value:.3g}** {sign} to {game.players[0]}.",
    ]
    if abs(value) < 1e-9:
        lines.append("A value of 0 means the game is perfectly fair -- neither side has an edge.")
    lines.append(
        "The strategy below is *unexploitable*: it guarantees this result no matter how "
        "cleverly the opponent plays. It does not try to punish a bad opponent, though."
    )
    return "\n".join(lines)


def summary(game: Game) -> str:
    """Everything, in reading order."""
    eqs = equilibria(game)
    blocks = [f"## {game.name}"]
    if game.description:
        blocks.append(game.description)
    blocks.append("### Dominated actions\n" + explain_dominance(game))
    blocks.append("### Equilibrium\n" + explain_equilibria(game, eqs))
    zs = explain_zero_sum(game)
    if zs:
        blocks.append("### Zero-sum\n" + zs)
    blocks.append("### Efficiency\n" + explain_efficiency(game, efficiency(game, eqs)))
    return "\n\n".join(blocks)
