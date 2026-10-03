"""Command line entry point."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gtlab", description="Game theory visualiser")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="list every registered game")

    solve = sub.add_parser("solve", help="solve a game and explain it")
    solve.add_argument("game", help="game key, e.g. prisoners_dilemma")
    solve.add_argument(
        "-p",
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="override a parameter, e.g. -p C=3",
    )

    sub.add_parser("app", help="launch the interactive app")

    args = parser.parse_args(argv)
    import gtlab

    if args.command == "list":
        for key, name, desc in gtlab.catalogue():
            first = desc.split(".")[0].replace("**", "")
            print(f"{key:24s} {name}")
            if first:
                print(f"{'':24s} {first.strip()}.")
        return 0

    if args.command == "solve":
        game = gtlab.get(args.game)
        overrides = {}
        for item in args.param:
            name, _, value = item.partition("=")
            overrides[name.strip()] = float(value)
        if overrides:
            game = game.with_params(**overrides)
        print(gtlab.summary(game))
        return 0

    if args.command == "app":
        from .app import launch

        return launch()
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
