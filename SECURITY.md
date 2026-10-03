# Security Policy

## Supported versions

gtlab is pre-1.0. Only the latest commit on `main` receives fixes.

| Version | Supported |
| ------- | --------- |
| `main`  | ✅        |
| 0.1.x   | ✅        |
| older   | ❌        |

## Reporting a vulnerability

Please **do not open a public issue** for a security problem.

Use GitHub's private reporting instead:
[**Report a vulnerability**](https://github.com/DataAthleteChamp/gam_theory_vis/security/advisories/new)

Include what you can: affected version or commit, reproduction steps, and what
an attacker could achieve. You can expect an acknowledgement within 7 days and,
for a confirmed issue, a fix or mitigation plan within 30 days. You will be
credited in the advisory unless you ask not to be.

## Threat model

gtlab is a local, offline analysis library and notebook. It has a deliberately
small attack surface:

- It makes **no network requests** at runtime.
- It **reads no user files** and writes none, except `scripts/share.py`, which
  writes the build output to `./site`.
- It handles **no credentials or personal data**.
- The published demo runs **entirely client-side** in your browser under
  Pyodide/WASM. Nothing you type is transmitted anywhere; there is no server.

The things most worth reporting are therefore:

- **Arbitrary code execution** from loading a game definition or parameter set
- A dependency vulnerability that reaches a code path gtlab actually uses
- Anything in the published demo that could exfiltrate data from a visitor

## Known, accepted design decisions

These are intentional, not vulnerabilities:

- **Game tables can hold arbitrary callables.** Parametric games such as
  Hawk & Dove are defined as Python functions of their parameters, and
  `register` executes a factory at import time. gtlab therefore treats a game
  module as *code*, exactly like any other Python import. **Only import game
  definitions you trust**, just as you would only `pip install` packages you
  trust.
- **`scripts/share.py` shells out** to `uv`/`pip` and `marimo` to build the
  site. It is a developer build script, not something that runs on user input.

## Correctness bugs

A wrong equilibrium or a wrong Price of Anarchy is not a security issue, but it
*is* the most serious kind of bug this project can have. Please report those as
a normal [bug report](https://github.com/DataAthleteChamp/gam_theory_vis/issues/new?template=bug_report.yml)
— they get priority.
