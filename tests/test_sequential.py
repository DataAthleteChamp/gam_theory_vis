"""Tests for the timing problems: the bed decision and the war of attrition."""

from __future__ import annotations

import numpy as np
import pytest

from gtlab.games.sequential import (
    attrition_payoff_grid,
    bed_decision,
    bed_indifference_point,
    best_bed_plan,
    war_of_attrition_equilibria,
    war_of_attrition_outcome,
)


# --------------------------------------------------------------------------
# Exercise 6 -- the bed
# --------------------------------------------------------------------------
def test_bed_options_cover_every_day_plus_never():
    plans = bed_decision(pain_per_night=1.0, trip_cost=8.0, deadline=30)
    assert len(plans) == 31  # 30 days, plus "never go"
    assert plans[-1].day is None


def test_going_on_day_one_costs_only_the_trip():
    plans = bed_decision(pain_per_night=1.0, trip_cost=8.0, deadline=30)
    assert plans[0].day == 1
    assert plans[0].pain_cost == pytest.approx(0.0)  # no bad nights yet
    assert plans[0].total_cost == pytest.approx(8.0)


def test_waiting_only_ever_adds_pain():
    """Pain accrues but the trip is a one-off, so cost rises strictly with the day."""
    plans = bed_decision(pain_per_night=1.0, trip_cost=8.0, deadline=30)
    daily = [p.total_cost for p in plans if p.day is not None]
    assert daily == sorted(daily)
    assert daily[0] < daily[-1]


def test_cheap_trip_means_go_immediately():
    best = best_bed_plan(pain_per_night=1.0, trip_cost=8.0, deadline=30)
    assert best.day == 1
    assert best.total_cost == pytest.approx(8.0)  # vs 30 for never going


def test_expensive_trip_means_never_go():
    """At 40 for the trip against 30 nights of pain, suffering is cheaper."""
    best = best_bed_plan(pain_per_night=1.0, trip_cost=40.0, deadline=30)
    assert best.day is None
    assert best.total_cost == pytest.approx(30.0)


def test_the_answer_is_never_a_day_in_between():
    """The whole lesson of the exercise: it is day 1 or never, never day 15."""
    for trip in (1.0, 5.0, 8.0, 20.0, 29.0, 31.0, 50.0):
        best = best_bed_plan(pain_per_night=1.0, trip_cost=trip, deadline=30)
        assert best.day in (1, None), f"trip={trip} gave day {best.day}"


def test_indifference_point_is_where_the_decision_flips():
    deadline = 30
    trip = 8.0
    threshold = bed_indifference_point(trip_cost=trip, deadline=deadline)
    assert threshold == pytest.approx(8 / 30)

    # Just above the threshold, pain dominates and you go on day 1.
    assert best_bed_plan(threshold + 0.01, trip, deadline).day == 1
    # Just below it, the trip is not worth making.
    assert best_bed_plan(threshold - 0.01, trip, deadline).day is None


# --------------------------------------------------------------------------
# Exercise 7 -- war of attrition
# --------------------------------------------------------------------------
def test_whoever_quits_first_loses_the_object():
    r = war_of_attrition_outcome(v1=10, v2=5, t1=1, t2=3)
    assert r.winner == "Player 2"
    assert r.concede_time == pytest.approx(1.0)
    assert r.payoffs == pytest.approx((-1.0, 4.0))  # P2 gets 5 minus 1 of waiting


def test_the_mirror_case_is_symmetric():
    r = war_of_attrition_outcome(v1=10, v2=5, t1=3, t2=1)
    assert r.winner == "Player 1"
    assert r.payoffs == pytest.approx((9.0, -1.0))  # P1 gets 10 minus 1 of waiting


def test_quitting_together_splits_the_object():
    r = war_of_attrition_outcome(v1=10, v2=5, t1=2, t2=2)
    assert r.winner is None
    assert r.payoffs == pytest.approx((10 / 2 - 2, 5 / 2 - 2))


def test_waiting_burns_value_for_both_sides():
    """Total payoff falls as the fight drags on -- the fight itself is the loss."""
    early = sum(war_of_attrition_outcome(10, 5, 1, 4).payoffs)
    late = sum(war_of_attrition_outcome(10, 5, 3, 4).payoffs)
    assert late < early


def test_equilibria_include_both_pure_and_the_mixed_one():
    lines = war_of_attrition_equilibria(v1=10, v2=5)
    text = " ".join(lines)
    assert "Pure equilibrium 1" in text
    assert "Pure equilibrium 2" in text
    assert "Mixed equilibrium" in text


def test_symmetric_values_get_the_extra_warning():
    assert any("symmetric" in line for line in war_of_attrition_equilibria(7, 7))
    assert not any("symmetric" in line for line in war_of_attrition_equilibria(10, 5))


def test_payoff_grid_matches_the_outcome_function():
    times = np.array([0.0, 1.0, 2.0])
    p1, p2 = attrition_payoff_grid(10, 5, times)
    assert p1.shape == (3, 3)

    for i, t1 in enumerate(times):
        for j, t2 in enumerate(times):
            expected = war_of_attrition_outcome(10, 5, float(t1), float(t2)).payoffs
            assert (p1[i, j], p2[i, j]) == pytest.approx(expected)
