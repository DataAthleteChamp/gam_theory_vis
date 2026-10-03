# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Continuous integration: tests on Python 3.11–3.13 across Linux, macOS and
  Windows, plus lint, type-check and wheel-install checks.
- Automatic deployment of the zero-install WebAssembly demo to GitHub Pages.
- `ruff` (lint + format) and `mypy` (strict-ish typing) configuration, both
  clean across the codebase.
- Contributor documentation: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, issue forms and a pull request template.
- Coverage reporting via `pytest-cov`.
- Test asserting the column player's optimal strategy in Rock-Paper-Scissors,
  not just the row player's.

### Changed
- `_negate` now builds a closure with an explicit signature rather than a
  default-argument lambda, so parametric games type-check cleanly.
- `zip` calls over actions and probability vectors are now `strict=True`, so a
  length mismatch raises instead of silently truncating.

## [0.1.0] — 2026-09-19

### Added
- `Game` model with an explicit `Convention` (cost or payoff) and a single
  sign-flip boundary in `Game.payoff_matrices()`.
- Solvers: best-response masks, pure and mixed Nash equilibria via support
  enumeration, iterated elimination of dominated strategies, zero-sum value by
  linear programming.
- Efficiency analysis: social optimum, Price of Anarchy and Price of Stability,
  with an explicit refusal to print a ratio when it would be meaningless.
- Parameter sweeps and threshold-finding (`find_threshold`) to locate where the
  answer changes.
- Plain-English explanations of every result.
- Game catalogue: Prisoner's Dilemma, Hawk & Dove, Rock-Paper-Scissors, War of
  Attrition, generator bidding, Braess's paradox, Matching Pennies, Stag Hunt,
  Chicken, Battle of the Sexes.
- Decorator-based game registry — one function adds a game everywhere.
- `gtlab` CLI with `list`, `solve` and `app`.
- Interactive marimo app with best-response triangles and parameter sliders.
- `scripts/share.py`, which exports the whole tool as a static site that runs
  client-side via Pyodide/WASM.

[Unreleased]: https://github.com/DataAthleteChamp/gam_theory_vis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DataAthleteChamp/gam_theory_vis/releases/tag/v0.1.0
