"""Regression tests against answers verified independently.

These are the numbers the tool must never get wrong. Each was checked by hand
and with exact fractions before the code existed.
"""

from __future__ import annotations

import numpy as np
import pytest

import gtlab
from gtlab.core import Convention


# --------------------------------------------------------------------------
# Exercise 3: Prisoner's Dilemma in cost form
# --------------------------------------------------------------------------
def test_prisoners_dilemma_unique_equilibrium_is_mutual_defection():
    game = gtlab.get("prisoners_dilemma")
    eqs = gtlab.equilibria(game)
    assert len(eqs) == 1
    eq = eqs[0]
    assert eq.is_pure
    # Defect is index 1 for both players.
    assert np.allclose(eq.row, [0.0, 1.0])
    assert np.allclose(eq.col, [0.0, 1.0])
    # Nine years each, as costs.
    assert eq.outcome_values(game) == pytest.approx((9.0, 9.0))


def test_prisoners_dilemma_price_of_anarchy_is_4_point_5():
    eff = gtlab.efficiency(gtlab.get("prisoners_dilemma"))
    assert eff.social_optimum == pytest.approx(4.0)  # both silent: 2 + 2
    assert eff.worst_nash_cost == pytest.approx(18.0)  # both betray: 9 + 9
    assert eff.meaningful
    assert eff.price_of_anarchy == pytest.approx(4.5)


def test_prisoners_dilemma_is_dominance_solvable():
    game = gtlab.get("prisoners_dilemma")
    steps = gtlab.iterated_elimination(game)
    assert len(steps) == 2
    assert all(s.strict for s in steps)
    rows, cols = gtlab.survivors(game)
    assert rows == ["Defect (betray)"]
    assert cols == ["Defect (betray)"]


def test_cost_and_payoff_conventions_agree():
    """Flipping the convention must not change a single answer."""
    cost_game = gtlab.get("prisoners_dilemma")
    payoff_game = cost_game.as_convention(Convention.PAYOFF)

    assert payoff_game.convention is Convention.PAYOFF
    cost_eq = gtlab.equilibria(cost_game)[0]
    payoff_eq = gtlab.equilibria(payoff_game)[0]
    assert np.allclose(cost_eq.row, payoff_eq.row)
    assert np.allclose(cost_eq.col, payoff_eq.col)

    # Social cost is convention-independent, so PoA must survive the round trip.
    assert gtlab.efficiency(cost_game).price_of_anarchy == pytest.approx(
        gtlab.efficiency(payoff_game).price_of_anarchy
    )


# --------------------------------------------------------------------------
# Exercise 5: Rock, Paper, Scissors
# --------------------------------------------------------------------------
def test_rps_has_no_pure_equilibrium():
    assert gtlab.pure_equilibria(gtlab.get("rock_paper_scissors")) == []


def test_rps_equilibrium_is_uniform_and_worth_zero():
    game = gtlab.get("rock_paper_scissors")
    eqs = gtlab.equilibria(game)
    assert len(eqs) == 1
    eq = eqs[0]
    assert np.allclose(eq.row, [1 / 3, 1 / 3, 1 / 3])
    assert np.allclose(eq.col, [1 / 3, 1 / 3, 1 / 3])
    assert eq.outcome_values(game) == pytest.approx((0.0, 0.0))


def test_rps_is_zero_sum_with_value_zero():
    game = gtlab.get("rock_paper_scissors")
    assert game.is_zero_sum
    value, row, col = gtlab.zero_sum_value(game)
    assert value == pytest.approx(0.0, abs=1e-9)
    assert np.allclose(row, [1 / 3, 1 / 3, 1 / 3], atol=1e-6)
    assert np.allclose(col, [1 / 3, 1 / 3, 1 / 3], atol=1e-6)


# --------------------------------------------------------------------------
# Exercise 4: Hawk & Dove -- the sheet's numbers, not the textbook's
# --------------------------------------------------------------------------
@pytest.mark.parametrize("C", [0.0, 2.0, 3.9])
def test_hawk_dove_below_threshold_hawk_dominates(C):
    game = gtlab.get("hawk_dove").with_params(V=10, C=C)
    eqs = gtlab.equilibria(game)
    assert len(eqs) == 1
    assert np.allclose(eqs[0].row, [1.0, 0.0])  # both fight
    assert np.allclose(eqs[0].col, [1.0, 0.0])


@pytest.mark.parametrize("C", [4.1, 5.0, 8.0, 12.0])
def test_hawk_dove_above_threshold_is_chicken(C):
    game = gtlab.get("hawk_dove").with_params(V=10, C=C)
    eqs = gtlab.equilibria(game)
    pure = [e for e in eqs if e.is_pure]
    mixed = [e for e in eqs if not e.is_pure]
    assert len(pure) == 2, "one fights, the other yields -- either way round"
    assert len(mixed) == 1
    # The mixed equilibrium plays Hawk with probability 4/C.
    assert mixed[0].row[0] == pytest.approx(4.0 / C)
    assert mixed[0].col[0] == pytest.approx(4.0 / C)


def test_hawk_dove_threshold_is_exactly_four():
    """Not 5 (the sheet's hint) and not 10 (the textbook's V)."""
    game = gtlab.get("hawk_dove").with_params(V=10)
    assert gtlab.find_threshold(game, "C", 0.5, 12.0) == pytest.approx(4.0, abs=1e-6)


def test_hawk_dove_sweep_finds_one_boundary():
    game = gtlab.get("hawk_dove").with_params(V=10)
    result = gtlab.sweep(game, "C", 0.5, 12.0, steps=121)
    assert len(result.regimes) == 2
    assert result.boundaries()[0] == pytest.approx(4.0, abs=0.15)


# --------------------------------------------------------------------------
# Structural guarantees
# --------------------------------------------------------------------------
def test_every_registered_game_solves_and_explains():
    for game in gtlab.all_games():
        game.validate()
        assert gtlab.equilibria(game), f"{game.key} has no equilibrium"
        text = gtlab.summary(game)
        assert game.name in text


def test_best_response_mask_marks_exactly_the_pure_equilibria():
    for game in gtlab.all_games():
        row_mask, col_mask = gtlab.best_response_mask(game)
        marked = int((row_mask & col_mask).sum())
        assert marked == len(gtlab.pure_equilibria(game)), game.key


def test_parameter_overrides_do_not_leak_between_calls():
    gtlab.get("hawk_dove").with_params(C=1.0)
    assert gtlab.get("hawk_dove").param_values["C"] == 8.0


def test_unknown_parameter_is_rejected():
    with pytest.raises(KeyError):
        gtlab.get("hawk_dove").with_params(nonsense=1.0)


def test_price_of_anarchy_refuses_meaningless_ratios():
    """Hawk & Dove is in payoffs, so 'social cost' is negative and a ratio lies."""
    eff = gtlab.efficiency(gtlab.get("hawk_dove").with_params(V=10, C=8))
    assert not eff.meaningful
    assert eff.price_of_anarchy is None
    assert eff.reason


def test_public_api_is_actually_importable():
    """Every name promised in __all__ must exist -- the app relies on them."""
    missing = [name for name in gtlab.__all__ if not hasattr(gtlab, name)]
    assert not missing, f"gtlab.__all__ promises missing names: {missing}"


def test_every_explainer_works_on_every_game():
    for game in gtlab.all_games():
        assert gtlab.explain_dominance(game)
        assert gtlab.explain_equilibria(game)
        assert gtlab.explain_efficiency(game)
        gtlab.explain_zero_sum(game)  # None is fine; must not raise
