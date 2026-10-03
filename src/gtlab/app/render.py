"""Rendering the payoff/cost matrix as HTML.

The central idea, borrowed from Gambit and Game Theory Explorer and made
explicit: in every cell, draw a triangle in player 1's colour when that cell is
player 1's best response to the column, and a triangle in player 2's colour
when it is player 2's best response to the row.

A cell with **both** triangles is a pure Nash equilibrium. You can see it
without being told what to look for, which is the whole point.
"""

from __future__ import annotations

import numpy as np

from ..core import Convention, Game, best_response_mask, efficiency, equilibria

P1_COLOUR = "#2563eb"  # blue
P2_COLOUR = "#d97706"  # amber
NE_BG = "#ecfdf5"
NE_BORDER = "#059669"
OPT_BORDER = "#7c3aed"  # violet: the socially best cell

# Blue/amber/violet stay distinguishable for the common forms of colour
# blindness; the triangles also differ in position, so colour is never the only
# signal.


def _fmt(x: float) -> str:
    if abs(x - round(x)) < 1e-9:
        return str(round(x))
    return f"{x:.4g}".rstrip("0").rstrip(".") if "." in f"{x:.4g}" else f"{x:.4g}"


def matrix_html(game: Game, *, show_best_responses: bool = True) -> str:
    """The full matrix, with best-response triangles and legend."""
    a, b = game.raw_matrices()
    row_mask, col_mask = best_response_mask(game)
    if not show_best_responses:
        row_mask = np.zeros_like(row_mask)
        col_mask = np.zeros_like(col_mask)

    eff = efficiency(game)
    optimum_cells = set(eff.optimum_cells)
    rows, cols = game.shape

    better = game.convention.better
    unit = "cost" if game.convention is Convention.COST else "payoff"

    css = f"""
    <style>
      .gt-wrap {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
      .gt-table {{ border-collapse: separate; border-spacing: 0; margin: 0.5rem 0; }}
      .gt-table th {{ padding: 8px 12px; font-weight: 600; font-size: 0.85rem; color: #374151; }}
      .gt-corner {{ font-size: 0.75rem; color: #6b7280; font-weight: 400 !important; text-align: left; }}
      .gt-colhead {{ border-bottom: 2px solid #e5e7eb; }}
      .gt-rowhead {{ text-align: right; border-right: 2px solid #e5e7eb; }}
      .gt-cell {{ position: relative; width: 116px; height: 62px; border: 1px solid #e5e7eb;
                  text-align: center; vertical-align: middle; background: #fff; }}
      .gt-ne {{ background: {NE_BG}; border: 2px solid {NE_BORDER}; }}
      .gt-opt {{ box-shadow: inset 0 0 0 3px {OPT_BORDER}33; }}
      .gt-vals {{ position: relative; z-index: 2; font-variant-numeric: tabular-nums;
                  font-size: 0.95rem; }}
      .gt-v1 {{ color: {P1_COLOUR}; font-weight: 600; }}
      .gt-v2 {{ color: {P2_COLOUR}; font-weight: 600; }}
      .gt-tri1 {{ position: absolute; top: 0; left: 0; width: 0; height: 0;
                  border-top: 20px solid {P1_COLOUR}; border-right: 20px solid transparent;
                  opacity: 0.85; }}
      .gt-tri2 {{ position: absolute; bottom: 0; right: 0; width: 0; height: 0;
                  border-bottom: 20px solid {P2_COLOUR}; border-left: 20px solid transparent;
                  opacity: 0.85; }}
      .gt-star {{ position: absolute; top: 2px; right: 4px; color: {OPT_BORDER};
                  font-size: 0.8rem; z-index: 3; }}
      .gt-legend {{ font-size: 0.8rem; color: #4b5563; margin-top: 0.4rem; line-height: 1.7; }}
      .gt-chip {{ display: inline-block; padding: 1px 7px; border-radius: 4px;
                  font-size: 0.75rem; margin-right: 6px; }}
    </style>
    """

    head = [f'<th class="gt-corner">{game.players[0]} ↓ &nbsp; {game.players[1]} →</th>']
    head += [f'<th class="gt-colhead">{c}</th>' for c in game.col_actions]

    body = []
    for i in range(rows):
        cells = [f'<th class="gt-rowhead">{game.row_actions[i]}</th>']
        for j in range(cols):
            is_ne = bool(row_mask[i, j] and col_mask[i, j])
            classes = ["gt-cell"]
            if is_ne:
                classes.append("gt-ne")
            if (i, j) in optimum_cells:
                classes.append("gt-opt")

            inner = ""
            if row_mask[i, j]:
                inner += '<div class="gt-tri1"></div>'
            if col_mask[i, j]:
                inner += '<div class="gt-tri2"></div>'
            if (i, j) in optimum_cells:
                inner += '<span class="gt-star" title="best for both together">★</span>'
            inner += (
                f'<div class="gt-vals">'
                f'<span class="gt-v1">{_fmt(a[i, j])}</span>'
                f'<span style="color:#9ca3af">, </span>'
                f'<span class="gt-v2">{_fmt(b[i, j])}</span>'
                f"</div>"
            )
            cells.append(f'<td class="{" ".join(classes)}">{inner}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")

    n_ne = int((row_mask & col_mask).sum())
    legend = f"""
    <div class="gt-legend">
      Each cell shows <span class="gt-v1">{game.players[0]}'s {unit}</span>,
      <span class="gt-v2">{game.players[1]}'s {unit}</span> &mdash;
      <b>{better} is better</b>.<br>
      <span class="gt-chip" style="background:{P1_COLOUR};color:#fff">◤ top-left</span>
      best for {game.players[0]}, given the column.
      <span class="gt-chip" style="background:{P2_COLOUR};color:#fff">◢ bottom-right</span>
      best for {game.players[1]}, given the row.<br>
      <span class="gt-chip" style="background:{NE_BG};border:1px solid {NE_BORDER}">
      both triangles</span> = a pure Nash equilibrium
      ({n_ne} here). <span style="color:{OPT_BORDER}">★</span> = best for the two together.
    </div>
    """

    return f"""{css}
    <div class="gt-wrap">
      <table class="gt-table">
        <thead><tr>{"".join(head)}</tr></thead>
        <tbody>{"".join(body)}</tbody>
      </table>
      {legend}
    </div>"""


def verdict_html(game: Game) -> str:
    """The banner: equilibrium, social optimum, and Price of Anarchy."""
    eqs = equilibria(game)
    eff = efficiency(game, eqs)

    if eff.meaningful and eff.price_of_anarchy is not None:
        poa = f"{eff.price_of_anarchy:.4g}×"
        poa_note = "worse than the best they could do together"
        colour = "#b91c1c" if eff.price_of_anarchy > 1.05 else "#047857"
    else:
        poa = f"{eff.gap():.4g}"
        poa_note = "absolute loss (a ratio would mislead here)"
        colour = "#b45309"

    names = ", ".join(e.describe(game) for e in eqs) or "none found"

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                display:flex;gap:10px;flex-wrap:wrap;margin:0.5rem 0;">
      <div style="flex:2;min-width:230px;background:#f8fafc;border-left:4px solid {NE_BORDER};
                  padding:9px 13px;border-radius:5px;">
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;
                    letter-spacing:0.05em;">Equilibrium</div>
        <div style="font-size:1rem;font-weight:600;color:#0f172a;">{names}</div>
      </div>
      <div style="flex:1;min-width:150px;background:#f8fafc;border-left:4px solid {OPT_BORDER};
                  padding:9px 13px;border-radius:5px;">
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;
                    letter-spacing:0.05em;">Best together</div>
        <div style="font-size:1rem;font-weight:600;color:#0f172a;">
          {_fmt(eff.social_optimum)} <span style="font-weight:400;color:#64748b;
          font-size:0.8rem;">vs {_fmt(eff.worst_nash_cost)} at equilibrium</span></div>
      </div>
      <div style="flex:1;min-width:150px;background:#f8fafc;border-left:4px solid {colour};
                  padding:9px 13px;border-radius:5px;">
        <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;
                    letter-spacing:0.05em;">Price of Anarchy</div>
        <div style="font-size:1rem;font-weight:600;color:{colour};">{poa}</div>
        <div style="font-size:0.7rem;color:#64748b;">{poa_note}</div>
      </div>
    </div>"""


def regime_html(game: Game, sweep_result, current: float) -> str:
    """A coloured band showing which answer holds over which parameter range."""
    palette = ["#dbeafe", "#fce7f3", "#dcfce7", "#fef3c7", "#ede9fe", "#ffe4e6"]
    total = sweep_result.values[-1] - sweep_result.values[0]
    if total <= 0:
        return ""

    segments = []
    for n, regime in enumerate(sweep_result.regimes):
        width = 100.0 * regime.width() / total
        colour = palette[n % len(palette)]
        segments.append(
            f'<div title="{regime.label}" style="width:{width}%;background:{colour};'
            f"padding:7px 4px;font-size:0.7rem;text-align:center;color:#1f2937;"
            f'border-right:1px solid #fff;overflow:hidden;white-space:nowrap;">'
            f"{regime.n_pure} pure"
            f"{' + 1 mixed' if regime.n_mixed else ''}</div>"
        )

    marker = 100.0 * (current - sweep_result.values[0]) / total
    marker = min(max(marker, 0.0), 100.0)

    ticks = "".join(
        f'<div style="position:absolute;left:{100.0 * (b - sweep_result.values[0]) / total:.3f}%;'
        f'top:-6px;font-size:0.7rem;color:#b91c1c;transform:translateX(-50%);">'
        f"▼ {b:.3g}</div>"
        for b in sweep_result.boundaries()
    )

    return f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:1.2rem 0 0.5rem;">
      <div style="font-size:0.8rem;color:#374151;margin-bottom:14px;">
        <b>Where the answer changes</b> as <code>{sweep_result.parameter}</code> varies:</div>
      <div style="position:relative;">{ticks}
        <div style="display:flex;border-radius:5px;overflow:hidden;border:1px solid #e5e7eb;">
          {"".join(segments)}
        </div>
        <div style="position:absolute;left:{marker:.3f}%;top:-3px;height:calc(100% + 6px);
                    border-left:2px solid #111827;transform:translateX(-1px);"></div>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.7rem;
                  color:#6b7280;margin-top:3px;">
        <span>{sweep_result.values[0]:.3g}</span>
        <span>you are here: {current:.3g}</span>
        <span>{sweep_result.values[-1]:.3g}</span>
      </div>
    </div>"""
