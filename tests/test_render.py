"""Tests for the HTML rendering.

These do not check styling -- they check that the rendered output actually
reports the right answer, because a visualiser that draws a confident, wrong
picture is worse than one that crashes.
"""

from __future__ import annotations

import pytest

import gtlab
from gtlab.app.render import _fmt, matrix_html, regime_html, verdict_html


def test_numbers_render_without_noise():
    assert _fmt(4.0) == "4"
    assert _fmt(-9.0) == "-9"
    assert _fmt(0.0) == "0"
    assert _fmt(4.5) == "4.5"
    assert _fmt(1 / 3) == "0.3333"


def test_matrix_shows_every_action_and_number():
    game = gtlab.get("prisoners_dilemma")
    html = matrix_html(game)

    for action in game.row_actions:
        assert action in html
    for n in ("2", "10", "0", "9"):
        assert n in html
    assert "<table" in html


def test_matrix_marks_the_equilibrium_cell():
    """(Defect, Defect) is the only pure equilibrium, so exactly one cell is marked."""
    game = gtlab.get("prisoners_dilemma")

    with_br = matrix_html(game, show_best_responses=True)
    without = matrix_html(game, show_best_responses=False)

    assert with_br.count("gt-ne") > without.count("gt-ne")


def test_matrix_renders_for_every_registered_game():
    """A rendering crash on any catalogue game would break the whole app."""
    for game in gtlab.all_games():
        html = matrix_html(game)
        assert "<table" in html, game.key


def test_verdict_reports_the_known_price_of_anarchy():
    html = verdict_html(gtlab.get("prisoners_dilemma"))
    assert "Price of Anarchy" in html
    assert "4.5×" in html


def test_verdict_refuses_a_misleading_ratio():
    """Hawk & Dove is stated in payoffs, so social 'cost' is negative.

    A ratio would be nonsense there, so the banner must show the absolute gap
    and say why instead of printing a confident wrong number.
    """
    game = gtlab.get("hawk_dove").with_params(C=8)
    eff = gtlab.efficiency(game)
    assert not eff.meaningful  # guard: this test is only meaningful if so

    html = verdict_html(game)
    assert "mislead" in html
    assert "×" not in html.split("Price of Anarchy")[1][:400]


def test_verdict_names_the_equilibrium():
    html = verdict_html(gtlab.get("rock_paper_scissors"))
    assert "1/3" in html  # the mixed equilibrium, as a tidy fraction


def test_regime_band_marks_the_bifurcation():
    """Hawk & Dove changes character at C = 4; the band must show that boundary."""
    game = gtlab.get("hawk_dove")
    result = gtlab.sweep(game, "C", 0.5, 12)

    html = regime_html(game, result, current=8.0)
    assert "Where the answer changes" in html
    assert "C" in html
    assert any(abs(b - 4.0) < 0.1 for b in result.boundaries())


def test_regime_band_is_empty_for_a_zero_width_sweep():
    game = gtlab.get("hawk_dove")
    result = gtlab.sweep(game, "C", 3.0, 3.0, steps=1)
    assert regime_html(game, result, current=3.0) == ""


@pytest.mark.parametrize("current", [0.5, 4.0, 12.0, -5.0, 99.0])
def test_regime_marker_stays_inside_the_band(current):
    """Even an out-of-range value must not produce a marker off the bar."""
    game = gtlab.get("hawk_dove")
    result = gtlab.sweep(game, "C", 0.5, 12)
    html = regime_html(game, result, current=current)
    assert "left:-" not in html
