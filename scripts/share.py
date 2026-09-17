"""Build a zero-install, shareable version of the app.

Produces a directory of static files that runs the whole tool in the browser
via WebAssembly. Drop it on GitHub Pages and anyone can use it with nothing
installed -- no Python, no pip, no server.

    python scripts/share.py            # builds into ./site
    python -m http.server -d site      # try it locally first

How it works: the app carries PEP 723 metadata listing its dependencies. Those
are all pure-Python wheels, so Pyodide can install them in the browser. gtlab
itself is not on PyPI, so we build a wheel, copy it next to the page, and point
the metadata at it by relative URL.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "src" / "gtlab" / "app" / "app.py"
OUT = ROOT / "site"


def run(*args: str) -> None:
    print(f"$ {' '.join(args)}")
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def build_wheel() -> Path:
    dist = ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    if shutil.which("uv"):
        run("uv", "build", "--wheel")
    else:
        run(sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(dist), str(ROOT))

    wheels = sorted(dist.glob("gtlab-*.whl"))
    if not wheels:
        sys.exit("no wheel was produced in ./dist")
    return wheels[-1]


def export(app_path: Path) -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    run(
        sys.executable, "-m", "marimo", "export", "html-wasm",
        str(app_path), "-o", str(OUT), "--mode", "run",
    )


def main() -> int:
    wheel = build_wheel()
    print(f"built {wheel.name}")

    # Point the PEP 723 metadata at the wheel we just built, by relative URL.
    source = APP.read_text(encoding="utf-8")
    patched = re.sub(
        r'^#\s+"gtlab",\s*$',
        f'#     "gtlab @ ./{wheel.name}",',
        source,
        count=1,
        flags=re.MULTILINE,
    )
    if patched == source:
        print("warning: could not patch the gtlab dependency line", file=sys.stderr)

    staged = ROOT / "_share_app.py"
    staged.write_text(patched, encoding="utf-8")
    # marimo resolves a local wheel dependency relative to the notebook, so the
    # wheel has to sit beside the staged file at export time.
    staged_wheel = ROOT / wheel.name
    if not staged_wheel.exists():
        shutil.copy2(wheel, staged_wheel)
    try:
        export(staged)
    finally:
        staged.unlink(missing_ok=True)
        staged_wheel.unlink(missing_ok=True)

    if not (OUT / wheel.name).exists():
        shutil.copy2(wheel, OUT / wheel.name)
    (OUT / ".nojekyll").touch()  # GitHub Pages must not mangle the asset folders

    print(f"\n✅ shareable site in {OUT}")
    print("   try it:   python -m http.server -d site")
    print("   publish:  push the 'site' folder to a gh-pages branch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
