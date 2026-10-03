# Contributing to gtlab

Thanks for taking a look. gtlab is a teaching tool, so the bar for a good
contribution is *does this help someone understand the game better* — a clearer
explanation is as welcome as a new solver.

## Getting set up

```bash
git clone https://github.com/DataAthleteChamp/gam_theory_vis
cd gam_theory_vis
uv sync --extra app --extra dev
uv run pytest
```

No `uv`? `python -m venv .venv && .venv/bin/pip install -e ".[app,dev]"` works too.

## Before you open a pull request

Run the same three gates CI runs:

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy                # types
uv run pytest              # tests
```

All four must be clean. CI runs them on Python 3.11–3.13 across Linux, macOS
and Windows.

## The one rule you must not break

**The course states games in *cost*, which players minimise. Every solver
library maximises payoffs.** Mixing those up silently produces wrong answers
that still look plausible, which is the worst kind of bug in a teaching tool.

So:

- A `Game` stores numbers **exactly as the user typed them**, plus a
  `Convention` flag saying what they mean.
- The sign flip happens in **exactly one function**: `Game.payoff_matrices()`.
- Anything handing numbers to a solver calls `payoff_matrices()`.
- `raw_matrices()` is for **reporting numbers back to the user only** — never
  for optimisation.

If you add a solver, it must follow this. A test that passes a cost-stated game
and its `as_convention(PAYOFF)` twin through your function and asserts identical
answers is the cheapest way to prove you got it right.

## Adding a game

One decorated function in `src/gtlab/games/`, and it appears everywhere — CLI,
app, solver, sweeps. There is no registration list to update.

```python
from gtlab.core import Convention, Game, register


@register
def my_game() -> Game:
    return Game(
        key="my_game",
        name="My Game",
        row_actions=["Left", "Right"],
        col_actions=["Left", "Right"],
        table=[
            [(1, 1), (0, 3)],  # each cell is (player 1, player 2)
            [(3, 0), (2, 2)],
        ],
        convention=Convention.COST,  # or PAYOFF
        description="What this game is about.",
    )
```

Import your module in `src/gtlab/games/__init__.py` so the decorator runs.

Make a cell a callable of the parameters and you get sliders and regime maps
for free:

```python
from gtlab.core import Parameter

table = ([[(lambda p: p["V"] / 2 - p["C"], ...), ...], ...],)
parameters = ((Parameter("C", value=8.0, min=0.0, max=20.0, label="Cost of fighting"),),)
```

**Every new game needs a test with a known answer.** Not "it returns something"
— an answer you worked out by hand or took from a textbook, with the source in
a comment. That is what the existing tests do, and it is why the suite is worth
having.

## Testing philosophy

The suite is made of **regression tests against known answers**:

- Prisoner's Dilemma has Price of Anarchy 4.5
- Rock-Paper-Scissors has equilibrium (1/3, 1/3, 1/3) and value 0
- Hawk & Dove bifurcates at C = 4, with `p(Hawk) = 4/C` above it

A test that merely asserts the code does not crash is not much of a test. If
you cannot state the expected answer, that is usually a sign the feature needs
more thought.

## Keeping the browser build working

The core must stay **pure Python** (`numpy`, `scipy`, `nashpy`) so the whole
tool can run client-side under Pyodide/WASM. That is what makes the zero-install
demo possible.

This means:

- Do **not** add a dependency with binary wheels to `dependencies`. Put it in an
  optional extra, as `pygambit` is.
- Do not use threading, subprocesses, local file writes, or network calls on an
  import path the app touches.

Check your change survives the export:

```bash
uv run python scripts/share.py
python -m http.server -d site     # open localhost:8000
```

## Commit messages and PRs

- Explain **why**, not just what. "Fix sign flip in efficiency()" tells a
  reviewer far more than "update solve.py".
- One logical change per PR.
- If you fixed a bug, add the test that would have caught it.

## Reporting bugs

A wrong *number* is the highest-priority bug this project can have. If you find
one, please include the game, the parameters, what gtlab said, and what the
right answer is — see the bug report template.

## Licence

By contributing, you agree your contributions are licensed under the MIT
Licence, the same as the rest of the project.
