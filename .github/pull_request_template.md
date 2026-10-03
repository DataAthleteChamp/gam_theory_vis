<!-- Thanks for contributing. Keep this short; the checklist matters more than prose. -->

## What does this change, and why?



## How do you know it's right?

<!--
For anything touching the maths, name the answer you checked against: a hand
calculation, a textbook result, or a lecture note. "Tests pass" is not enough
on its own if you added a new number to the catalogue.
-->



## Checklist

- [ ] `uv run ruff check .` passes
- [ ] `uv run ruff format --check .` passes
- [ ] `uv run mypy` passes
- [ ] `uv run pytest` passes
- [ ] Added a test with a **known answer** for any new game or solver
- [ ] No new dependency with binary wheels in `[project] dependencies` (the core must stay browser-safe)
- [ ] Costs vs payoffs: any new solver takes its numbers from `payoff_matrices()`, never `raw_matrices()`
- [ ] Updated the README / docstrings if behaviour changed
- [ ] No copyrighted course material added to the repository

## Related issues

<!-- e.g. Closes #12 -->
