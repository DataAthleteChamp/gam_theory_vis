"""Game registry.

Adding a new game should be one decorated function, nothing else:

    from gtlab.core import Convention, register

    @register
    def my_game():
        return Game(key="my_game", name="My Game", ...)

The decorator stores a *factory*, not an instance, so every caller gets a fresh
game and parameter sliders can never leak between sessions.
"""

from __future__ import annotations

from typing import Callable, Iterator

from .game import Game

GameFactory = Callable[[], Game]

_REGISTRY: dict[str, GameFactory] = {}


def register(factory: GameFactory) -> GameFactory:
    """Register a game factory under the key of the game it builds."""
    game = factory()
    game.validate()
    key = game.key
    if key in _REGISTRY:
        raise ValueError(f"game key {key!r} is already registered")
    _REGISTRY[key] = factory
    return factory


def get(key: str) -> Game:
    """Build a fresh copy of a registered game."""
    if key not in _REGISTRY:
        raise KeyError(f"unknown game {key!r}. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[key]()


def keys() -> list[str]:
    return sorted(_REGISTRY)


def all_games() -> Iterator[Game]:
    for key in keys():
        yield get(key)


def catalogue() -> list[tuple[str, str, str]]:
    """(key, name, description) for every registered game."""
    return [(g.key, g.name, g.description) for g in all_games()]
