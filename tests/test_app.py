"""Tests for the app wiring.

These exist because of a real failure: the app source once carried PEP 723
script metadata listing this package by bare name. marimo saw it, built an
isolated sandbox, and installed the *unrelated* `gtlab` project from PyPI --
so `import gtlab` succeeded while `gtlab.app` did not exist.
"""

from __future__ import annotations

from pathlib import Path

APP = Path(__file__).parent.parent / "src" / "gtlab" / "app" / "app.py"
LAUNCHER = Path(__file__).parent.parent / "src" / "gtlab" / "app" / "__init__.py"
SHARE = Path(__file__).parent.parent / "scripts" / "share.py"


def test_app_has_no_inline_script_metadata():
    """A PEP 723 block here makes marimo sandbox the run and lose this package."""
    source = APP.read_text(encoding="utf-8")
    assert "# /// script" not in source, (
        "app.py must not carry PEP 723 metadata: marimo would sandbox the run "
        "and install the unrelated 'gtlab' package from PyPI. scripts/share.py "
        "injects it only for the browser build."
    )


def test_launcher_disables_the_sandbox():
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "--no-sandbox" in source


def test_share_script_pins_the_local_wheel_not_the_pypi_name():
    """The browser build must install our wheel, never a bare 'gtlab'."""
    source = SHARE.read_text(encoding="utf-8")
    assert 'gtlab @ ./' in source
    assert '"gtlab",' not in source


def test_app_imports_render_module():
    from gtlab.app import render

    assert hasattr(render, "matrix_html")
    assert hasattr(render, "verdict_html")
    assert hasattr(render, "regime_html")
