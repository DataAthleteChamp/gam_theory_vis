"""The games from Exercise Sheet 1, plus the standard companions.

Numbers follow the course sheet exactly. Where the sheet differs from the
textbook version of a game, the sheet wins and the difference is noted --
Hawk-Dove is the important case.
"""

from __future__ import annotations

from ..core import Convention, Game, Parameter, register


@register
def prisoners_dilemma() -> Game:
    """Exercise 3. Stated in prison-years, so these are COSTS."""
    return Game(
        key="prisoners_dilemma",
        name="Prisoner's Dilemma",
        row_actions=["Cooperate (stay silent)", "Defect (betray)"],
        col_actions=["Cooperate (stay silent)", "Defect (betray)"],
        table=[
            [(2, 2), (10, 0)],
            [(0, 10), (9, 9)],
        ],
        convention=Convention.COST,
        players=("Suspect 1", "Suspect 2"),
        description=(
            "Two suspects are questioned separately. Staying silent together earns 2 years "
            "each; betraying each other earns 9 each; betraying alone gets you free while "
            "the silent one serves 10. The numbers are years in prison, so **lower is "
            "better**."
        ),
        source="Exercise Sheet 1, Exercise 3",
        tags=("course", "social-dilemma", "dominance"),
        notes=(
            "Betraying is strictly dominant, so both betray and serve 9 years each -- "
            "worse for both than the 2 years they could have had. Price of Anarchy = "
            "18/4 = 4.5."
        ),
    )


@register
def hawk_dove() -> Game:
    """Exercise 4. Parametric in the fight cost C.

    The sheet's numbers are NOT the textbook Hawk-Dove:
      - both Hawk    -> they share the resource and both pay the fight cost: V/2 - C
      - Hawk vs Dove -> the Hawk takes 9 (not the full V), the Dove retreats with 1 (not 0)
      - both Dove    -> they split it: 5 each

    That changes where the answer flips. Hawk strictly dominates Dove exactly
    when 5 - C > 1, i.e. **C < 4** -- not C = 5 as the sheet's hint suggests,
    and not C = V = 10 as the textbook version gives. Above C = 4 the game turns
    into Chicken, with mixed equilibrium probability p(Hawk) = 4/C.
    """
    return Game(
        key="hawk_dove",
        name="Hawk & Dove",
        row_actions=["Hawk (fight)", "Dove (share)"],
        col_actions=["Hawk (fight)", "Dove (share)"],
        table=[
            [
                (lambda p: p["V"] / 2 - p["C"], lambda p: p["V"] / 2 - p["C"]),
                (9, 1),
            ],
            [
                (1, 9),
                (lambda p: p["V"] / 2, lambda p: p["V"] / 2),
            ],
        ],
        convention=Convention.PAYOFF,
        players=("Bird 1", "Bird 2"),
        parameters=(
            Parameter("V", 10.0, 0.0, 20.0, 0.5, "Value of the resource"),
            Parameter("C", 8.0, 0.0, 20.0, 0.1, "Cost of fighting"),
        ),
        description=(
            "Two birds contest a resource worth V. Both back down and they split it. One "
            "fights alone and it takes 9, leaving 1 for the bird that retreats. Both fight "
            "and they split the resource but each pays the fight cost C. Higher is better."
        ),
        source="Exercise Sheet 1, Exercise 4",
        tags=("course", "parametric", "anti-coordination"),
        notes=(
            "Drag C. Below C = 4 fighting is dominant and both birds fight. Above C = 4 "
            "there is no dominant action: two pure equilibria (one fights, one yields) plus "
            "a mixed one where each fights with probability 4/C."
        ),
    )


@register
def rock_paper_scissors() -> Game:
    """Exercise 5. Zero-sum, no pure equilibrium."""
    return Game(
        key="rock_paper_scissors",
        name="Rock, Paper, Scissors",
        row_actions=["Rock", "Paper", "Scissors"],
        col_actions=["Rock", "Paper", "Scissors"],
        table=[
            [(0, 0), (-1, 1), (1, -1)],
            [(1, -1), (0, 0), (-1, 1)],
            [(-1, 1), (1, -1), (0, 0)],
        ],
        convention=Convention.PAYOFF,
        description=(
            "Rock beats Scissors, Scissors beats Paper, Paper beats Rock. Winner +1, "
            "loser -1, tie 0."
        ),
        source="Exercise Sheet 1, Exercise 5",
        tags=("course", "zero-sum", "mixed-only"),
        notes=(
            "No pure equilibrium exists -- whatever you always play, you can be beaten. "
            "The only equilibrium is to randomise 1/3, 1/3, 1/3, which makes the game "
            "worth exactly 0 to both. That is unexploitable, but it also never punishes a "
            "predictable opponent."
        ),
    )


@register
def matching_pennies() -> Game:
    return Game(
        key="matching_pennies",
        name="Matching Pennies",
        row_actions=["Heads", "Tails"],
        col_actions=["Heads", "Tails"],
        table=[
            [(1, -1), (-1, 1)],
            [(-1, 1), (1, -1)],
        ],
        convention=Convention.PAYOFF,
        players=("Matcher", "Mismatcher"),
        description=(
            "The Matcher wins if the coins agree; the Mismatcher wins if they differ. "
            "The simplest game with no pure equilibrium."
        ),
        tags=("classic", "zero-sum", "mixed-only"),
        notes="Unique equilibrium: both randomise 50/50, and the game is worth 0.",
    )


@register
def stag_hunt() -> Game:
    return Game(
        key="stag_hunt",
        name="Stag Hunt",
        row_actions=["Stag", "Hare"],
        col_actions=["Stag", "Hare"],
        table=[
            [(4, 4), (0, 3)],
            [(3, 0), (3, 3)],
        ],
        convention=Convention.PAYOFF,
        description=(
            "Hunting a stag together feeds everyone, but only if both commit. Hunting hare "
            "alone is safe and small. Higher is better."
        ),
        tags=("classic", "coordination"),
        notes=(
            "Two pure equilibria. (Stag, Stag) is better for both, but (Hare, Hare) is "
            "safer. This is about trust, not conflict -- the problem is coordination."
        ),
    )


@register
def chicken() -> Game:
    return Game(
        key="chicken",
        name="Chicken",
        row_actions=["Swerve", "Straight"],
        col_actions=["Swerve", "Straight"],
        table=[
            [(0, 0), (-1, 1)],
            [(1, -1), (-10, -10)],
        ],
        convention=Convention.PAYOFF,
        description="Two drivers head at each other. Swerving is embarrassing; neither swerving is a disaster.",
        tags=("classic", "anti-coordination"),
        notes="Same shape as Hawk & Dove with an expensive fight: two pure equilibria plus a mixed one.",
    )


@register
def battle_of_the_sexes() -> Game:
    return Game(
        key="battle_of_the_sexes",
        name="Battle of the Sexes",
        row_actions=["Opera", "Football"],
        col_actions=["Opera", "Football"],
        table=[
            [(2, 1), (0, 0)],
            [(0, 0), (1, 2)],
        ],
        convention=Convention.PAYOFF,
        players=("Alex", "Bo"),
        description=(
            "Both would rather be together than apart, but they prefer different outings."
        ),
        tags=("classic", "coordination"),
        notes="Two pure equilibria plus a mixed one in which they sometimes miss each other entirely.",
    )


@register
def braess_paradox() -> Game:
    """Adding a road can make everyone slower -- the network version of Gijón."""
    return Game(
        key="braess_paradox",
        name="Braess's Paradox (route choice)",
        row_actions=["Route A (via shortcut)", "Route B (avoid shortcut)"],
        col_actions=["Route A (via shortcut)", "Route B (avoid shortcut)"],
        table=[
            [(4, 4), (2.5, 3.5)],
            [(3.5, 2.5), (3, 3)],
        ],
        convention=Convention.COST,
        players=("Driver 1", "Driver 2"),
        description=(
            "Two drivers pick a route. The numbers are travel times in tens of minutes, so "
            "**lower is better**. A tempting shortcut is open to both."
        ),
        tags=("congestion", "social-dilemma", "network"),
        notes=(
            "Both take the shortcut and both arrive later than if neither had. Closing the "
            "shortcut would make everyone faster -- the classic argument that adding "
            "capacity to a network can hurt it."
        ),
    )
