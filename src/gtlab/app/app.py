"""gtlab — the interactive app.

Run it with:  gtlab app       (or)  marimo run src/gtlab/app/app.py
Edit it with: marimo edit src/gtlab/app/app.py

The block below is PEP 723 script metadata. It is what lets the browser
(WASM/Pyodide) build of this app install its own dependencies, so a classmate
can open a URL and run everything with nothing installed. ``scripts/share.py``
rewrites the gtlab entry to point at the wheel it builds alongside the export.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "numpy",
#     "scipy",
#     "nashpy==0.0.43",
#     "gtlab",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium", app_title="gtlab — Game Theory Visualiser")


@app.cell(hide_code=True)
def _():
    import marimo as mo

    import gtlab
    from gtlab.app import render

    return gtlab, mo, render


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        # 🎲 Game Theory Visualiser

        Pick a game, look at the table, and find out what rational players do — and
        what it costs everyone when they do it.
        """
    )
    return


@app.cell(hide_code=True)
def _(gtlab, mo):
    catalogue = gtlab.catalogue()
    game_picker = mo.ui.dropdown(
        options={name: key for key, name, _ in catalogue},
        value=next(name for key, name, _ in catalogue if key == "prisoners_dilemma"),
        label="**Game**",
    )
    show_br = mo.ui.switch(value=True, label="Best-response triangles")
    flip = mo.ui.switch(value=False, label="Flip cost ⇄ payoff")
    mo.hstack([game_picker, show_br, flip], justify="start", gap=2)
    return flip, game_picker, show_br


@app.cell(hide_code=True)
def _(game_picker, gtlab):
    base_game = gtlab.get(game_picker.value)
    return (base_game,)


@app.cell(hide_code=True)
def _(base_game, mo):
    sliders = {
        p.name: mo.ui.slider(
            start=p.min,
            stop=p.max,
            step=p.step,
            value=p.value,
            label=f"**{p.name}** — {p.described()}",
            show_value=True,
            full_width=True,
        )
        for p in base_game.parameters
    }
    slider_dict = mo.ui.dictionary(sliders) if sliders else None
    slider_dict if slider_dict is not None else mo.md("")
    return (slider_dict,)


@app.cell(hide_code=True)
def _(base_game, flip, slider_dict):
    game = base_game
    if slider_dict is not None and slider_dict.value:
        game = game.with_params(**{k: float(v) for k, v in slider_dict.value.items()})
    if flip.value:
        game = game.as_convention(game.convention.flip())
    return (game,)


@app.cell(hide_code=True)
def _(game, mo):
    mo.md(f"### {game.name}\n\n{game.description}")
    return


@app.cell(hide_code=True)
def _(game, mo, render, show_br):
    mo.Html(render.matrix_html(game, show_best_responses=show_br.value))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ---
        ### First, have a guess

        Committing to an answer before you look is the single best thing you can do
        for your own learning.
        """
    )
    return


@app.cell(hide_code=True)
def _(game, mo):
    guess = mo.ui.radio(
        options=[
            "They reach the outcome that is best for them jointly",
            "They end up somewhere worse for both than they could have done",
            "There is no single answer — it depends what they expect",
            "They must randomise; no fixed choice is stable",
        ],
        label=f"What do two rational players do in {game.name}?",
    )
    guess
    return (guess,)


@app.cell(hide_code=True)
def _(game, gtlab):
    equilibria_ = gtlab.equilibria(game)
    efficiency_ = gtlab.efficiency(game, equilibria_)
    return efficiency_, equilibria_


@app.cell(hide_code=True)
def _(efficiency_, equilibria_, game, gtlab, guess, mo, render):
    if guess.value is None:
        answer = mo.callout("Choose an answer above to reveal the solution.", kind="neutral")
    else:
        pure_ = [e for e in equilibria_ if e.is_pure]
        mixed_ = [e for e in equilibria_ if not e.is_pure]
        if not pure_ and mixed_:
            truth = "They must randomise; no fixed choice is stable"
        elif len(pure_) > 1:
            truth = "There is no single answer — it depends what they expect"
        elif efficiency_.gap() > 1e-9:
            truth = "They end up somewhere worse for both than they could have done"
        else:
            truth = "They reach the outcome that is best for them jointly"

        right = guess.value == truth
        answer = mo.vstack(
            [
                mo.callout(
                    mo.md("✅ **That's it.**" if right else f"❌ **Not quite** — it is: *{truth}*"),
                    kind="success" if right else "warn",
                ),
                mo.Html(render.verdict_html(game)),
                mo.md(gtlab.explain_equilibria(game, equilibria_)),
            ]
        )
    answer
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""---\n### Why — step by step""")
    return


@app.cell(hide_code=True)
def _(game, gtlab, mo):
    tabs = {
        "Crossing out bad actions": mo.md(gtlab.explain_dominance(game)),
        "How bad is selfishness?": mo.md(gtlab.explain_efficiency(game)),
    }
    zero_sum_text = gtlab.explain_zero_sum(game)
    if zero_sum_text:
        tabs["Zero-sum"] = mo.md(zero_sum_text)
    if game.notes:
        tabs["What to notice"] = mo.md(game.notes)
    mo.ui.tabs(tabs)
    return


@app.cell(hide_code=True)
def _(base_game, mo):
    has_params = bool(base_game.parameters)
    (
        mo.md(
            """---\n### Where does the answer change?

            Drag a slider above and watch the band below. Each colour is a stretch of
            values where the answer keeps the same shape; the red markers are the exact
            points where it flips.
            """
        )
        if has_params
        else mo.md("")
    )
    return (has_params,)


@app.cell(hide_code=True)
def _(base_game, game, gtlab, has_params, mo, render, slider_dict):
    if not has_params:
        regime_view = mo.md("")
    else:
        swept = base_game.parameters[-1]
        current = float(slider_dict.value[swept.name]) if slider_dict else swept.value
        fixed = {
            k: float(v)
            for k, v in (slider_dict.value if slider_dict else {}).items()
            if k != swept.name
        }
        sweep_result = gtlab.sweep(
            base_game.with_params(**fixed) if fixed else base_game,
            swept.name,
            swept.min + 1e-6,
            swept.max,
            steps=97,
        )
        boundaries = sweep_result.boundaries()
        note = (
            mo.md(
                f"**The answer changes at {swept.name} ≈ "
                f"{', '.join(f'{b:.3g}' for b in boundaries)}.**"
            )
            if boundaries
            else mo.md(f"The answer never changes over this range of {swept.name}.")
        )
        regime_view = mo.vstack([mo.Html(render.regime_html(game, sweep_result, current)), note])
    regime_view
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ---
        ### The lecture's example: your bid is not the only thing that matters

        Three generators, demand of 280 MW. G1 and G2 together can only make 230 MW,
        so **G3 must run whatever it bids** — that is what market power looks like.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    from gtlab.games.electricity import (
        LECTURE_DEMAND,
        LECTURE_GENERATORS,
        lecture_scenarios,
        residual_supply_index,
    )

    rsi = residual_supply_index(LECTURE_GENERATORS, "G3", LECTURE_DEMAND)
    rows = [
        {
            "Scenario": label,
            "Price (EUR/MWh)": round(result.clearing_price, 1),
            "G1 profit": round(result.profit["G1"]),
            "G2 profit": round(result.profit["G2"]),
            "G3 profit": round(result.profit["G3"]),
            "Consumers pay": round(result.consumer_cost),
        }
        for label, result in lecture_scenarios().items()
    ]

    mo.vstack(
        [
            mo.md(f"G3's Residual Supply Index is **{rsi:.3f}** — below 1, so G3 is *pivotal*."),
            mo.ui.table(rows, selection=None),
            mo.callout(
                mo.md(
                    "Look at **G1 and G2's profits** in the middle row. They never changed "
                    "their bids, yet they earn thousands more — because G3 raised the price "
                    "*everyone* is paid. That is the lecture's point: your profit depends on "
                    "everybody's bid, not just your own."
                ),
                kind="info",
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        """
        ---
        <sub>Built with [nashpy](https://nashpy.readthedocs.io) ·
        Add your own game in 20 lines — see the README.</sub>
        """
    )
    return


if __name__ == "__main__":
    app.run()
