"""Tests for the command line interface.

The CLI is the surface most users touch first, so these check exit codes and
that the output actually contains the answer -- not merely that nothing raised.
"""

from __future__ import annotations

import pytest

from gtlab.cli import main


def test_list_prints_every_game(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    for key in ("prisoners_dilemma", "hawk_dove", "rock_paper_scissors", "generator_bidding"):
        assert key in out


def test_solve_prints_the_known_price_of_anarchy(capsys):
    assert main(["solve", "prisoners_dilemma"]) == 0
    out = capsys.readouterr().out
    assert "Prisoner's Dilemma" in out
    assert "4.5" in out  # PoA = 18/4


def test_solve_accepts_parameter_overrides(capsys):
    """Hawk & Dove bifurcates at C = 4, so these two must differ."""
    assert main(["solve", "hawk_dove", "-p", "C=3"]) == 0
    below = capsys.readouterr().out

    assert main(["solve", "hawk_dove", "-p", "C=8"]) == 0
    above = capsys.readouterr().out

    assert below != above


def test_solve_accepts_several_parameters(capsys):
    assert main(["solve", "war_of_attrition", "-p", "v1=6", "-p", "v2=6"]) == 0
    assert "War of Attrition" in capsys.readouterr().out


def test_unknown_game_is_reported_by_key(capsys):
    with pytest.raises(KeyError, match="no_such_game"):
        main(["solve", "no_such_game"])


def test_unknown_parameter_is_reported(capsys):
    with pytest.raises(KeyError, match="Z"):
        main(["solve", "hawk_dove", "-p", "Z=1"])


def test_no_command_prints_help_and_fails(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()
