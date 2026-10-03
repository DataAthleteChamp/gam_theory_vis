"""Game catalogue.

Importing this package registers every game. To add your own, drop a module in
here and import it below -- see ``docs`` in the README for the 20-line recipe.
"""

from . import classic, electricity, sequential

__all__ = ["classic", "electricity", "sequential"]
