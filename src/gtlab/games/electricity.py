"""Electricity market games.

The lecture's point about generator G3 -- "its profit did not depend on its own
bid alone, but on its bid together with everyone else's bids" -- is the whole
subject in one sentence. This module makes that concrete: a merit-order auction
you can actually run, plus a bidding game you can solve like any other matrix.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import Convention, Game, Parameter, register


# --------------------------------------------------------------------------
# A real (small) uniform-price auction
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Generator:
    name: str
    marginal_cost: float  # EUR/MWh, the true cost of producing
    capacity: float       # MW available


@dataclass(frozen=True)
class Dispatch:
    """The result of clearing one auction."""

    clearing_price: float
    dispatched: dict[str, float]
    profit: dict[str, float]
    consumer_cost: float
    unserved: float
    marginal_unit: str | None
    bids: dict[str, float] = field(default_factory=dict)

    def total_profit(self) -> float:
        return sum(self.profit.values())


def clear_uniform_price(
    generators: list[Generator],
    bids: dict[str, float],
    demand: float,
    price_cap: float = 3000.0,
    offered: dict[str, float] | None = None,
) -> Dispatch:
    """Clear a pay-as-clear (uniform price) auction by merit order.

    Cheapest bids are dispatched first. The price everyone receives is the bid
    of the last unit needed to meet demand -- so a generator's revenue depends
    on *everybody's* bids, not just its own.

    ``offered`` lets a generator withhold capacity physically (offer less than
    it has), as opposed to economically (bid high).
    """
    offered = offered or {g.name: g.capacity for g in generators}
    stack = sorted(generators, key=lambda g: bids[g.name])

    remaining = demand
    dispatched: dict[str, float] = {g.name: 0.0 for g in generators}
    marginal_unit: str | None = None
    price = 0.0

    for gen in stack:
        if remaining <= 1e-9:
            break
        take = min(offered.get(gen.name, gen.capacity), remaining)
        if take <= 0:
            continue
        dispatched[gen.name] = take
        remaining -= take
        marginal_unit = gen.name
        price = bids[gen.name]

    unserved = max(remaining, 0.0)
    if unserved > 1e-9:
        # Demand could not be met: scarcity pricing kicks in at the cap.
        price = price_cap
        marginal_unit = None

    profit = {
        g.name: (price - g.marginal_cost) * dispatched[g.name] for g in generators
    }
    return Dispatch(
        clearing_price=price,
        dispatched=dispatched,
        profit=profit,
        consumer_cost=price * (demand - unserved),
        unserved=unserved,
        marginal_unit=marginal_unit,
        bids=dict(bids),
    )


def residual_supply_index(generators: list[Generator], who: str, demand: float) -> float:
    """RSI < 1 means this generator is *pivotal*: demand cannot be met without it.

    A pivotal generator knows it will be dispatched whatever it bids, which is
    exactly when market power appears.
    """
    others = sum(g.capacity for g in generators if g.name != who)
    return others / demand if demand else float("inf")


#: The lecture's example: G1+G2 = 230 MW cannot cover 280 MW, so G3 is pivotal.
LECTURE_GENERATORS = [
    Generator("G1", marginal_cost=20.0, capacity=100.0),
    Generator("G2", marginal_cost=40.0, capacity=130.0),
    Generator("G3", marginal_cost=70.0, capacity=80.0),
]
LECTURE_DEMAND = 280.0


def lecture_scenarios() -> dict[str, Dispatch]:
    """Truthful bidding vs economic vs physical withholding, side by side."""
    gens = LECTURE_GENERATORS
    truthful = {g.name: g.marginal_cost for g in gens}
    return {
        "Everyone bids their true cost": clear_uniform_price(gens, truthful, LECTURE_DEMAND),
        "G3 bids 100 (economic withholding)": clear_uniform_price(
            gens, {**truthful, "G3": 100.0}, LECTURE_DEMAND
        ),
        "G3 offers only 20 MW (physical withholding)": clear_uniform_price(
            gens, truthful, LECTURE_DEMAND, offered={"G1": 100.0, "G2": 130.0, "G3": 20.0}
        ),
    }


# --------------------------------------------------------------------------
# The same idea as a matrix game you can solve
# --------------------------------------------------------------------------
def _bidding_payoff(player: int, my_bid: float, other_bid: float, params) -> float:
    """Profit for a symmetric two-generator uniform-price auction.

    Both generators have capacity below demand, so both are always dispatched
    and the higher bid sets the price. Undercutting wins nothing extra (you are
    dispatched anyway) but drags the price down for both -- so bidding high is
    individually tempting, which is the market-power story.
    """
    cost = params["cost"]
    demand = params["demand"]
    cap = demand / 2.0
    price = max(my_bid, other_bid)
    return (price - cost) * cap


@register
def generator_bidding() -> Game:
    """Two pivotal generators choosing a bid level."""
    bids = {"Bid cost (20)": 20.0, "Bid medium (60)": 60.0, "Bid high (100)": 100.0}
    names = list(bids)

    def cell(i: int, j: int):
        def p1(params, _i=i, _j=j):
            return _bidding_payoff(0, bids[names[_i]], bids[names[_j]], params)

        def p2(params, _i=i, _j=j):
            return _bidding_payoff(1, bids[names[_j]], bids[names[_i]], params)

        return (p1, p2)

    return Game(
        key="generator_bidding",
        name="Generator Bidding (uniform-price auction)",
        row_actions=names,
        col_actions=names,
        table=[[cell(i, j) for j in range(len(names))] for i in range(len(names))],
        convention=Convention.PAYOFF,
        players=("Generator A", "Generator B"),
        parameters=(
            Parameter("cost", 20.0, 0.0, 100.0, 1.0, "True marginal cost (EUR/MWh)"),
            Parameter("demand", 200.0, 50.0, 400.0, 10.0, "Demand (MW)"),
        ),
        description=(
            "Two generators each bid into a pay-as-clear auction. Both are needed to meet "
            "demand, so both are always dispatched and the **higher** bid sets the price "
            "everyone is paid. Profit is (price - cost) x quantity, so higher is better."
        ),
        source="Lecture example (generator G3)",
        tags=("electricity", "auction", "market-power"),
        notes=(
            "Bidding high is dominant here, because being pivotal means you get dispatched "
            "whatever you bid. Consumers pay for it. Real markets stop this with price caps "
            "and market monitoring, not by hoping generators are nice."
        ),
    )
