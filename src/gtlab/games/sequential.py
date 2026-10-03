"""Games that play out over time.

Exercise 6 (when to fetch the bed) and Exercise 7 (War of Attrition) are not
matrices -- they are decisions about *when*. Both are handled here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core import Convention, Game, Parameter, register


# --------------------------------------------------------------------------
# Exercise 6 -- the bed, and when to fetch it
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class BedPlan:
    day: int | None  # None means "never; let the partner bring it"
    total_cost: float
    pain_cost: float
    trip_cost: float
    explanation: str


def bed_decision(
    pain_per_night: float = 1.0,
    trip_cost: float = 8.0,
    deadline: int = 30,
) -> list[BedPlan]:
    """Cost of fetching the bed on each possible day.

    Sleeping badly costs ``pain_per_night`` every night until the bed arrives.
    Fetching it costs ``trip_cost`` once. If you never go, the partner brings it
    on day ``deadline`` and you suffer the pain until then.

    This is a one-player decision problem, so there is no strategic opponent --
    which is exactly the point worth learning: not every decision is a game.
    """
    plans: list[BedPlan] = []
    for day in range(1, deadline + 1):
        pain = pain_per_night * (day - 1)
        plans.append(
            BedPlan(
                day=day,
                total_cost=pain + trip_cost,
                pain_cost=pain,
                trip_cost=trip_cost,
                explanation=(
                    f"Fetch on day {day}: {day - 1} bad nights ({pain:.3g}) "
                    f"+ the trip ({trip_cost:.3g}) = {pain + trip_cost:.3g}"
                ),
            )
        )
    never_pain = pain_per_night * deadline
    plans.append(
        BedPlan(
            day=None,
            total_cost=never_pain,
            pain_cost=never_pain,
            trip_cost=0.0,
            explanation=(
                f"Never go: {deadline} bad nights ({never_pain:.3g}), the partner brings it"
            ),
        )
    )
    return plans


def best_bed_plan(
    pain_per_night: float = 1.0, trip_cost: float = 8.0, deadline: int = 30
) -> BedPlan:
    """The cheapest plan.

    Because pain accumulates but the trip is a one-off, the answer is always
    'go on day 1' or 'never go' -- never a day in between. Waiting until day k
    just adds k-1 nights of pain to the same trip cost. To make day 15 optimal
    you need the cost of the trip itself to fall over time (a cheaper rental
    later, say), not just different values for pain.
    """
    plans = bed_decision(pain_per_night, trip_cost, deadline)
    return min(plans, key=lambda p: p.total_cost)


def bed_indifference_point(trip_cost: float = 8.0, deadline: int = 30) -> float:
    """The pain-per-night at which going and not going cost the same.

    Below it, put up with the air mattress; above it, rent the car today.
    """
    return trip_cost / deadline


# --------------------------------------------------------------------------
# Exercise 7 -- War of Attrition
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class AttritionResult:
    winner: str | None
    concede_time: float
    payoffs: tuple[float, float]
    note: str


def war_of_attrition_outcome(v1: float, v2: float, t1: float, t2: float) -> AttritionResult:
    """Who gets the object when the two players plan to concede at t1 and t2.

    Waiting costs one unit of payoff per unit of time, for both players, until
    the first concession.
    """
    if abs(t1 - t2) < 1e-12:
        return AttritionResult(
            None,
            t1,
            (v1 / 2 - t1, v2 / 2 - t1),
            "Both conceded at the same moment, so they split the object.",
        )
    if t1 < t2:
        return AttritionResult(
            "Player 2",
            t1,
            (-t1, v2 - t1),
            "Player 1 gave up first, so Player 2 takes the object.",
        )
    return AttritionResult(
        "Player 1",
        t2,
        (v1 - t2, -t2),
        "Player 2 gave up first, so Player 1 takes the object.",
    )


def war_of_attrition_equilibria(v1: float, v2: float) -> list[str]:
    """The equilibria of the continuous-time war of attrition.

    There are two pure ones (either player concedes immediately while the other
    is willing to wait indefinitely) and a mixed one in which each concedes at an
    exponential rate set by the *opponent's* value, not their own.
    """
    lines = [
        "**Pure equilibrium 1:** Player 1 concedes at t = 0, Player 2 waits. "
        f"Payoffs (0, {v2:.3g}).",
        "**Pure equilibrium 2:** Player 2 concedes at t = 0, Player 1 waits. "
        f"Payoffs ({v1:.3g}, 0).",
    ]
    if v1 > 0 and v2 > 0:
        lines.append(
            f"**Mixed equilibrium:** each concedes at a constant hazard rate -- "
            f"Player 1 at 1/{v2:.3g} and Player 2 at 1/{v1:.3g} per unit time. "
            f"Note the rate depends on the *other* player's value: the more the object "
            f"is worth to your opponent, the longer you must be willing to wait to keep "
            f"them honest. In this equilibrium both players' expected payoff is 0 -- the "
            f"whole value of the object is burned away by waiting."
        )
    if abs(v1 - v2) < 1e-12:
        lines.append(
            "With v1 = v2 the game is symmetric, so there is no way to agree on *who* "
            "should back down. The symmetric mixed equilibrium is the only symmetric "
            "answer, and it wastes the entire prize."
        )
    return lines


def attrition_payoff_grid(v1: float, v2: float, times: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Payoff surfaces over a grid of concession times, for plotting."""
    n = len(times)
    p1 = np.empty((n, n))
    p2 = np.empty((n, n))
    for i, t1 in enumerate(times):
        for j, t2 in enumerate(times):
            result = war_of_attrition_outcome(v1, v2, float(t1), float(t2))
            p1[i, j], p2[i, j] = result.payoffs
    return p1, p2


@register
def war_of_attrition() -> Game:
    """A discrete approximation, so it can be solved like any other matrix."""
    times = [0.0, 1.0, 2.0, 4.0]
    labels = [f"Quit at t={t:g}" for t in times]

    def cell(i: int, j: int):
        def p1(params, _i=i, _j=j):
            return war_of_attrition_outcome(
                params["v1"], params["v2"], times[_i], times[_j]
            ).payoffs[0]

        def p2(params, _i=i, _j=j):
            return war_of_attrition_outcome(
                params["v1"], params["v2"], times[_i], times[_j]
            ).payoffs[1]

        return (p1, p2)

    return Game(
        key="war_of_attrition",
        name="War of Attrition (discrete times)",
        row_actions=labels,
        col_actions=labels,
        table=[[cell(i, j) for j in range(len(times))] for i in range(len(times))],
        convention=Convention.PAYOFF,
        parameters=(
            Parameter("v1", 10.0, 1.0, 20.0, 0.5, "Object's value to Player 1"),
            Parameter("v2", 5.0, 1.0, 20.0, 0.5, "Object's value to Player 2"),
        ),
        description=(
            "Two players want the same object. Each picks a time to give up. Whoever holds "
            "out longer takes it, but **both** lose one unit of payoff per unit of time "
            "until the first one quits. Higher is better."
        ),
        source="Exercise Sheet 1, Exercise 7",
        tags=("course", "timing", "parametric"),
        notes=(
            "Waiting burns value for both sides, so the fight itself is the loss. Set "
            "v1 = v2 to see the symmetric case, where there is no natural way to decide "
            "who should back down."
        ),
    )
