"""Tests for the Game model: validation, conventions, and the registry.

`Game.validate()` is the safety net every contributor hits when adding a game,
and `as_convention` is the one place a sign flip can silently corrupt an answer.
Both are tested here against hand-checked expectations.
"""

from __future__ import annotations

import numpy as np
import pytest

import gtlab
from gtlab.core import Convention, Game, Parameter
from gtlab.core.registry import register


def make_game(**kwargs) -> Game:
    base: dict = {
        "key": "t",
        "name": "T",
        "row_actions": ["a", "b"],
        "col_actions": ["x", "y"],
        "table": [[(1, 2), (3, 4)], [(5, 6), (7, 8)]],
        "convention": Convention.COST,
    }
    base.update(kwargs)
    return Game(**base)


# --------------------------------------------------------------------------
# validate()
# --------------------------------------------------------------------------
def test_a_well_formed_game_validates():
    make_game().validate()


def test_rejects_a_game_with_no_actions():
    with pytest.raises(ValueError, match="at least one action"):
        make_game(row_actions=[], table=[]).validate()


def test_rejects_a_table_with_the_wrong_number_of_rows():
    with pytest.raises(ValueError, match="2 rows but 3 row actions"):
        make_game(row_actions=["a", "b", "c"]).validate()


def test_rejects_a_row_with_the_wrong_number_of_cells():
    with pytest.raises(ValueError, match=r"table row 1 has 1 cells"):
        make_game(table=[[(1, 2), (3, 4)], [(5, 6)]]).validate()


def test_rejects_a_cell_that_is_not_a_pair():
    with pytest.raises(ValueError, match=r"cell \(0,1\) must be a \(p1, p2\) pair"):
        make_game(table=[[(1, 2), (3, 4, 5)], [(5, 6), (7, 8)]]).validate()


def test_validate_resolves_callables_so_bad_formulas_fail_early():
    """A formula referring to a parameter that does not exist must fail at
    registration time, not silently when a user moves a slider."""
    bad = make_game(
        table=[[(lambda p: p["nope"], 1), (1, 1)], [(1, 1), (1, 1)]],
        parameters=(Parameter("C", 1.0),),
    )
    with pytest.raises(KeyError):
        bad.validate()


# --------------------------------------------------------------------------
# cost vs payoff -- the one rule that must never break
# --------------------------------------------------------------------------
def test_payoff_matrices_negate_costs_exactly_once():
    game = make_game(convention=Convention.COST)
    raw_a, raw_b = game.raw_matrices()
    pay_a, pay_b = game.payoff_matrices()
    assert np.allclose(pay_a, -raw_a)
    assert np.allclose(pay_b, -raw_b)


def test_payoff_matrices_leave_payoffs_alone():
    game = make_game(convention=Convention.PAYOFF)
    raw_a, _ = game.raw_matrices()
    pay_a, _ = game.payoff_matrices()
    assert np.allclose(pay_a, raw_a)


@pytest.mark.parametrize("key", ["prisoners_dilemma", "hawk_dove", "stag_hunt", "chicken"])
def test_restating_a_game_in_the_other_convention_changes_no_answer(key):
    """The headline guarantee: cost form and payoff form are the same game."""
    cost_form = gtlab.get(key)
    payoff_form = cost_form.as_convention(cost_form.convention.flip())

    assert payoff_form.convention is not cost_form.convention

    cost_a, cost_b = cost_form.payoff_matrices()
    pay_a, pay_b = payoff_form.payoff_matrices()
    assert np.allclose(cost_a, pay_a)
    assert np.allclose(cost_b, pay_b)

    a = sorted(e.describe(cost_form) for e in gtlab.equilibria(cost_form))
    b = sorted(e.describe(payoff_form) for e in gtlab.equilibria(payoff_form))
    assert a == b


def test_round_tripping_the_convention_returns_the_original_numbers():
    game = gtlab.get("prisoners_dilemma")
    there_and_back = game.as_convention(Convention.PAYOFF).as_convention(Convention.COST)

    before_a, before_b = game.raw_matrices()
    after_a, after_b = there_and_back.raw_matrices()
    assert np.allclose(before_a, after_a)
    assert np.allclose(before_b, after_b)


def test_as_convention_is_a_no_op_for_the_same_convention():
    game = gtlab.get("prisoners_dilemma")
    assert game.as_convention(game.convention) is game


def test_negation_survives_parametric_cells():
    """Hawk & Dove's cells are callables, so the flip must negate the function."""
    game = gtlab.get("hawk_dove").with_params(C=8)
    flipped = game.as_convention(game.convention.flip())
    assert np.allclose(game.raw_matrices()[0], -flipped.raw_matrices()[0])


def test_convention_helpers_describe_themselves():
    assert Convention.COST.better == "lower"
    assert Convention.PAYOFF.better == "higher"
    assert Convention.COST.symbol == "c"
    assert Convention.PAYOFF.symbol == "u"
    assert Convention.COST.flip() is Convention.PAYOFF
    assert Convention.PAYOFF.flip() is Convention.COST


# --------------------------------------------------------------------------
# parameters
# --------------------------------------------------------------------------
def test_unknown_parameter_is_rejected_with_the_known_names_listed():
    with pytest.raises(KeyError, match="Z"):
        gtlab.get("hawk_dove").with_params(Z=1.0)


def test_with_params_does_not_mutate_the_original():
    game = gtlab.get("hawk_dove")
    before = game.param_values["C"]
    game.with_params(C=before + 5)
    assert game.param_values["C"] == before


def test_registry_hands_out_a_fresh_game_each_time():
    """Slider state must never leak between sessions."""
    first = gtlab.get("hawk_dove").with_params(C=1.0)
    second = gtlab.get("hawk_dove")
    assert first.param_values["C"] == 1.0
    assert second.param_values["C"] != 1.0


def test_parameter_label_falls_back_to_its_name():
    assert Parameter("C", 1.0).described() == "C"
    assert Parameter("C", 1.0, label="Fight cost").described() == "Fight cost"


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------
def test_registering_a_duplicate_key_is_refused():
    with pytest.raises(ValueError, match="already registered"):

        @register
        def prisoners_dilemma() -> Game:  # the key already exists
            return make_game(key="prisoners_dilemma")


def test_unknown_game_lists_what_is_available():
    with pytest.raises(KeyError, match="Available"):
        gtlab.get("not_a_game")


def test_every_registered_game_is_valid_and_solvable():
    for game in gtlab.all_games():
        game.validate()
        assert gtlab.equilibria(game), f"{game.key} has no equilibrium"
        assert str(game)


# --------------------------------------------------------------------------
# shape helpers
# --------------------------------------------------------------------------
def test_symmetry_and_zero_sum_detection():
    assert gtlab.get("prisoners_dilemma").is_symmetric
    assert gtlab.get("rock_paper_scissors").is_zero_sum
    assert not gtlab.get("prisoners_dilemma").is_zero_sum


def test_a_non_square_game_is_not_symmetric():
    game = make_game(col_actions=["x", "y", "z"], table=[[(1, 1)] * 3, [(2, 2)] * 3])
    assert not game.is_symmetric


def test_same_shape_but_different_action_names_is_not_symmetric():
    game = make_game(row_actions=["a", "b"], col_actions=["x", "y"])
    assert not game.is_symmetric
