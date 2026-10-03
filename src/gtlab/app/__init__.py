"""Interactive marimo app."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP = Path(__file__).parent / "app.py"


def launch() -> int:
    """Open the app in a browser via marimo."""
    try:
        import marimo  # noqa: F401
    except ImportError:
        print(
            'The app needs marimo. Install it with:\n    uv pip install -e ".[app]"',
            file=sys.stderr,
        )
        return 1
    # --no-sandbox keeps marimo in the environment this package is installed
    # into. Without it marimo builds an isolated venv that does not contain
    # gtlab, and the app cannot import itself.
    return subprocess.call([sys.executable, "-m", "marimo", "run", "--no-sandbox", str(APP)])
