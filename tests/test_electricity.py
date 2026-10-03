"""Tests for the electricity-market auction.

Every number here is worked out by hand from the lecture example:

    G1: cost 20, capacity 100
    G2: cost 40, capacity 130
    G3: cost 70, capacity  80      demand = 280 MW

G1 + G2 = 230 MW cannot cover 280 MW, so G3 is pivotal -- it is dispatched
whatever it bids, which is exactly where market power comes from.
"""

from __future__ import annotations

import pytest

import gtlab
from gtlab.games.electricity import (
    LECTURE_DEMAND,
    LECTURE_GENERATORS,
    clear_uniform_price,
    lecture_scenarios,
    residual_supply_index,
)

TRUTHFUL = {"G1": 20.0, "G2": 40.0, "G3": 70.0}


def test_truthful_bidding_clears_at_the_marginal_unit():
    """Merit order fills G1 (100) then G2 (130) then 50 MW of G3, so G3 sets the price."""
    d = clear_uniform_price(LECTURE_GENERATORS, TRUTHFUL, LECTURE_DEMAND)

    assert d.clearing_price == pytest.approx(70.0)
    assert d.marginal_unit == "G3"
    assert d.dispatched == pytest.approx({"G1": 100.0, "G2": 130.0, "G3": 50.0})
    assert d.unserved == pytest.approx(0.0)

    # Everyone is paid the clearing price, so the cheap units earn the margin.
    assert d.profit["G1"] == pytest.approx((70 - 20) * 100)  # 5000
    assert d.profit["G2"] == pytest.approx((70 - 40) * 130)  # 3900
    assert d.profit["G3"] == pytest.approx(0.0)  # it bid its own cost
    assert d.consumer_cost == pytest.approx(70 * 280)  # 19600


def test_economic_withholding_pays_the_pivotal_generator():
    """G3 bidding 100 instead of 70 lifts the price for *everyone*.

    This is the lecture's point: G3's profit depends on its bid together with
    everybody else's, and raising it costs G3 no dispatch at all.
    """
    d = clear_uniform_price(LECTURE_GENERATORS, {**TRUTHFUL, "G3": 100.0}, LECTURE_DEMAND)

    assert d.clearing_price == pytest.approx(100.0)
    assert d.dispatched["G3"] == pytest.approx(50.0)  # unchanged: it is pivotal
    assert d.profit["G3"] == pytest.approx((100 - 70) * 50)  # 1500, up from 0
    assert d.profit["G1"] == pytest.approx((100 - 20) * 100)  # 8000, up from 5000
    assert d.consumer_cost == pytest.approx(100 * 280)  # 28000, up from 19600


def test_physical_withholding_causes_scarcity_pricing():
    """Offering only 20 MW leaves 30 MW unserved, so the price jumps to the cap."""
    d = clear_uniform_price(
        LECTURE_GENERATORS,
        TRUTHFUL,
        LECTURE_DEMAND,
        offered={"G1": 100.0, "G2": 130.0, "G3": 20.0},
    )

    assert d.unserved == pytest.approx(30.0)
    assert d.clearing_price == pytest.approx(3000.0)  # the price cap
    assert d.marginal_unit is None  # nothing set the price; scarcity did
    assert d.consumer_cost == pytest.approx(3000 * 250)  # only served load pays


def test_price_cap_is_configurable():
    d = clear_uniform_price(LECTURE_GENERATORS, TRUTHFUL, 400.0, price_cap=500.0)
    assert d.unserved == pytest.approx(90.0)
    assert d.clearing_price == pytest.approx(500.0)


def test_withholding_strictly_helps_the_withholder_and_hurts_consumers():
    s = lecture_scenarios()
    assert len(s) == 3

    truthful = s["Everyone bids their true cost"]
    economic = s["G3 bids 100 (economic withholding)"]

    assert economic.profit["G3"] > truthful.profit["G3"]
    assert economic.consumer_cost > truthful.consumer_cost
    assert economic.total_profit() > truthful.total_profit()


def test_residual_supply_index_detects_a_pivotal_generator():
    """RSI < 1 means demand cannot be met without that generator."""
    # Without G3 only 230 MW remain against 280 MW of demand.
    assert residual_supply_index(LECTURE_GENERATORS, "G3", LECTURE_DEMAND) == pytest.approx(
        230 / 280
    )
    assert residual_supply_index(LECTURE_GENERATORS, "G3", LECTURE_DEMAND) < 1.0

    # With plenty of demand headroom nobody is pivotal.
    assert residual_supply_index(LECTURE_GENERATORS, "G3", 100.0) == pytest.approx(2.3)

    # Zero demand is guarded rather than dividing by zero.
    assert residual_supply_index(LECTURE_GENERATORS, "G3", 0.0) == float("inf")


def test_bidding_game_rewards_bidding_high():
    """With cost 20 and demand 200 each generator serves 100 MW at the higher bid."""
    game = gtlab.get("generator_bidding")
    a, b = game.raw_matrices()

    # Both bid cost: price 20, zero margin.
    assert a[0, 0] == pytest.approx(0.0)
    # Either side bidding 100 sets the price at 100 for both.
    assert a[2, 0] == pytest.approx((100 - 20) * 100)  # 8000
    assert b[0, 2] == pytest.approx((100 - 20) * 100)  # 8000

    # The auction is symmetric: the higher bid sets the price for both.
    assert a == pytest.approx(b)


def test_every_equilibrium_of_the_bidding_game_burns_consumers():
    """In every pure equilibrium someone bids high, so both earn the maximum.

    Bidding high only *weakly* dominates (if the other already bids 100 you are
    indifferent), which is why there are several equilibria rather than one.
    """
    game = gtlab.get("generator_bidding")
    pures = [eq for eq in gtlab.equilibria(game) if eq.is_pure]

    assert pures, "the bidding game must have at least one pure equilibrium"
    for eq in pures:
        p1, p2 = eq.outcome_values(game)
        assert p1 == pytest.approx(8000.0)
        assert p2 == pytest.approx(8000.0)
