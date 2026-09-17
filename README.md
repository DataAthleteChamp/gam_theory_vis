# gtlab — a game theory visualiser you can actually learn from

An interactive tool for **seeing**, **simulating** and **solving** the games from a
*Game Theory in Electricity Markets* course — Prisoner's Dilemma, Hawk & Dove,
Rock-Paper-Scissors, War of Attrition, and the generator-bidding auction that
started the whole thing.

It answers the questions you actually have:

- Where is the Nash equilibrium, and **why** is it there?
- Which actions can I cross out, and in what order?
- How bad is selfish play? (**Price of Anarchy**)
- **When does the answer change** if I turn a knob?

---

## Quick start

```bash
uv venv && uv pip install -e ".[app]"
uv run gtlab list                       # see every game
uv run gtlab solve prisoners_dilemma    # solve one, in plain English
uv run gtlab app                        # open the visual app
```

No `uv`? `python -m venv .venv && .venv/bin/pip install -e ".[app]"` works too.

---

## What makes it different

### 1. It speaks *cost*, like the course does

The course defines a game with **cost** functions `c_i` that players *minimise*.
Every Python game-theory library assumes players *maximise* payoffs. Mixing
those up silently gives wrong answers.

gtlab stores your numbers exactly as you typed them plus a flag saying what
they mean, and negates them in **exactly one function** (`Game.payoff_matrices`).
Flip the convention any time:

```python
import gtlab
pd = gtlab.get("prisoners_dilemma")          # stated in prison-years (cost)
print(pd.convention)                          # Convention.COST
same_game = pd.as_convention(gtlab.Convention.PAYOFF)   # -> identical answers
```

### 2. Price of Anarchy is a first-class number

```python
eff = gtlab.efficiency(gtlab.get("prisoners_dilemma"))
print(eff.price_of_anarchy)   # 4.5
```

Both suspects betray and serve 9 years each (total 18) when staying silent would
have cost 2 each (total 4). **18 / 4 = 4.5.**

gtlab refuses to print a ratio when it would be nonsense — if the best possible
social cost isn't strictly positive, it reports the absolute gap instead and
tells you why.

### 3. It finds where the answer changes

The course asks: for Hawk & Dove with V = 10, *does your answer change if C
gets smaller — and when?* Don't guess, bisect:

```python
hd = gtlab.get("hawk_dove")
print(gtlab.find_threshold(hd, "C", 0.5, 12))   # 4.0
```

> ⚠️ **The sheet's Hawk & Dove is not the textbook one.** It uses
> `V/2 − C` for a mutual fight and **9 / 1** for Hawk-vs-Dove (not V / 0).
> Hawk strictly dominates exactly when `5 − C > 1`, i.e. **C < 4** — not 5, and
> not the textbook's C = V = 10. Above C = 4 it becomes Chicken, with mixed
> equilibrium `p(Hawk) = 4/C`. This tool was what caught that.

---

## Add your own game in 20 lines

Drop a file in `src/gtlab/games/`, decorate a function, and it appears
everywhere — CLI, app, solver, sweeps. No registration list to update.

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
            [(1, 1), (0, 3)],     # each cell is (player 1, player 2)
            [(3, 0), (2, 2)],
        ],
        convention=Convention.COST,     # or PAYOFF
        description="What this game is about.",
    )
```

Import it in `src/gtlab/games/__init__.py` and you're done.

**Parametric games** — make a cell a function of named parameters and you get
sliders and regime maps for free:

```python
from gtlab.core import Parameter

table=[[(lambda p: p["V"] / 2 - p["C"], ...), ...], ...],
parameters=(Parameter("C", value=8.0, min=0.0, max=20.0, label="Cost of fighting"),),
```

---

## Library use

```python
import gtlab

game = gtlab.get("hawk_dove").with_params(C=8)

gtlab.equilibria(game)            # every Nash equilibrium
gtlab.best_response_mask(game)    # which cells are best responses
gtlab.iterated_elimination(game)  # dominance, one explained step at a time
gtlab.efficiency(game)            # social optimum, PoA, PoS
gtlab.sweep(game, "C", 0.5, 12)   # regimes across a parameter range
gtlab.summary(game)               # all of the above, in plain English
```

Run a real electricity auction:

```python
from gtlab.games.electricity import lecture_scenarios
for name, result in lecture_scenarios().items():
    print(name, result.clearing_price, result.profit)
```

---

## Share it with zero install

```bash
python scripts/share.py          # builds ./site
python -m http.server -d site    # try it at localhost:8000
```

`./site` is a fully static folder that runs **the entire tool in the browser**
via WebAssembly — Python and all. Push it to a `gh-pages` branch and a classmate
opens a URL and starts using it: no Python, no pip, no server, nothing to break.

This is verified, not aspirational: the exported site was loaded in a headless
browser, a prediction was clicked, and the Price of Anarchy of **4.5** was
computed by Python running client-side.

---

## The games

| Key | Game | From |
|---|---|---|
| `prisoners_dilemma` | Prisoner's Dilemma (in prison-years, cost form) | Exercise 3 |
| `hawk_dove` | Hawk & Dove, parametric in V and C | Exercise 4 |
| `rock_paper_scissors` | Rock, Paper, Scissors | Exercise 5 |
| `war_of_attrition` | War of Attrition, parametric in v1 and v2 | Exercise 7 |
| `generator_bidding` | Uniform-price auction bidding | Lecture (G3) |
| `braess_paradox` | Adding a road makes everyone slower | Congestion |
| `matching_pennies`, `stag_hunt`, `chicken`, `battle_of_the_sexes` | The standard companions | Classic |

Exercise 6 (when to fetch the bed) is a one-player decision, so it lives in
`gtlab.games.sequential.best_bed_plan()` rather than the matrix catalogue.

---

## Design notes

- **Core is pure Python** (`numpy`, `scipy`, `nashpy`) so the whole thing can run
  in a browser via Pyodide/WASM — that's how classmates use it with zero install.
- **`pygambit` is deliberately optional.** It ships binary wheels only, has no
  cp314 wheel (it compiles from source for ~5 minutes), and cannot run in the
  browser. Keeping it off the core path is what makes sharing possible.
- Equilibria come from `nashpy`'s support enumeration, with pure equilibria
  always re-checked directly so degenerate games don't silently lose answers.

## Testing

```bash
uv run pytest -q
```

The tests are regression tests against **known** answers: PD's Price of Anarchy
is 4.5, RPS's equilibrium is (1/3, 1/3, 1/3) with value 0, and Hawk & Dove
bifurcates at C = 4 with `p(Hawk) = 4/C`.

## Licence

MIT — use it, fork it, teach with it.
