"""Etapa 6 - Figura diagnostica: momento por momento, paper vs replica.

Dumbbell plot en pequenos multiplos: una celda por (panel, momento), un par de
puntos por pais unidos por una linea. Cada celda tiene su propio eje porque los
momentos estan en unidades distintas (puntos base vs. razones): nunca dos escalas
en un mismo eje.

Paleta: slots categoricos 1 y 2 del sistema de diseno, validados para vision
tricromatica y CVD (protan/deutan/tritan) contra la superficie clara. La forma
del marcador (circulo vs. diamante) repite la identidad por si la figura se
imprime en blanco y negro.

    python src/python/make_figure.py --profile paper_memlite --engine matlab
"""

from __future__ import annotations

import argparse
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import OUT_FIGURES, OUT_TABLES, ensure_dirs, load_config, log, tag

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
C_PAPER = "#2a78d6"   # slot categorico 1
C_REPL = "#eb6834"    # slot categorico 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="paper_memlite")
    ap.add_argument("--engine", default="matlab", choices=["matlab", "python"])
    args = ap.parse_args()

    cfg = load_config()
    etiqueta = tag(args.profile, args.engine)
    src = OUT_TABLES / f"table2_comparison_{etiqueta}.csv"
    if not src.exists():
        raise SystemExit(f"Falta {src}. Corra la etapa 5 (build_table2.py).")
    df = pd.read_csv(src).dropna(subset=["target"])
    if df.empty:
        raise SystemExit("No hay momentos con valor objetivo para graficar.")

    panels = sorted(df["panel"].unique())
    moments = [m for m in cfg["moments"] if m in set(df["moment"])]

    fig, axes = plt.subplots(
        len(panels), len(moments),
        figsize=(2.35 * len(moments), 1.35 * len(panels) + 1.7),
        squeeze=False,
    )
    fig.patch.set_facecolor(SURFACE)

    for i, panel in enumerate(panels):
        for j, mom in enumerate(moments):
            ax = axes[i][j]
            ax.set_facecolor(SURFACE)
            sub = df[(df["panel"] == panel) & (df["moment"] == mom)].sort_values("iso3")
            if sub.empty:
                ax.axis("off")
                continue

            ys = range(len(sub))
            for y, (_, r) in zip(ys, sub.iterrows()):
                ax.plot([r["target"], r["value"]], [y, y], color=GRID, lw=2, zorder=1,
                        solid_capstyle="round")
                ax.plot(r["target"], y, "o", ms=8, color=C_PAPER, mec=SURFACE, mew=2, zorder=3)
                ax.plot(r["value"], y, "D", ms=7.5, color=C_REPL, mec=SURFACE, mew=2, zorder=3)

            ax.set_yticks(list(ys))
            ax.set_yticklabels(sub["iso3"] if j == 0 else [""] * len(sub),
                               color=INK_MUTED, fontsize=8)
            ax.set_ylim(-0.6, len(sub) - 0.4)
            ax.tick_params(axis="x", colors=INK_MUTED, labelsize=7, length=0)
            ax.tick_params(axis="y", length=0)
            ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
            for side in ("top", "right", "left"):
                ax.spines[side].set_visible(False)
            ax.spines["bottom"].set_color(GRID)
            if i == 0:
                ax.set_title(cfg["moments"][mom]["label"].replace(" (", "\n("),
                             fontsize=8.5, color=INK, pad=8)
            if j == 0:
                ax.annotate(f"Panel {panel}", xy=(-0.42, 0.5), xycoords="axes fraction",
                            rotation=90, va="center", ha="center",
                            fontsize=9, color=INK, weight="bold")

    handles = [
        plt.Line2D([], [], marker="o", ls="", ms=8, color=C_PAPER, mec=SURFACE, mew=2,
                   label="Mallucci (2022)"),
        plt.Line2D([], [], marker="D", ls="", ms=7.5, color=C_REPL, mec=SURFACE, mew=2,
                   label=f"Replica ({args.engine})"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=9, labelcolor=INK_MUTED, bbox_to_anchor=(0.5, -0.01))

    nota = f"Perfil {args.profile} - motor {args.engine}"
    if not cfg["profiles"][args.profile].get("reportable", False):
        nota += " - corrida de prueba, no reportable"
    # Titulo y bajada como texto suelto, no como suptitle: asi el espacio que
    # ocupan se reserva con `rect` y no se montan sobre las celdas ni entre si.
    fig.text(0.02, 0.975, "Tabla 2: momentos simulados, paper vs. replica",
             fontsize=11.5, color=INK, ha="left", va="top")
    fig.text(0.02, 0.915, nota, fontsize=8, color=INK_MUTED, ha="left", va="top")

    fig.tight_layout(rect=(0.03, 0.06, 1, 0.88))
    ensure_dirs(OUT_FIGURES)
    for ext in ("png", "pdf"):
        dest = OUT_FIGURES / f"table2_comparison_{etiqueta}.{ext}"
        fig.savefig(dest, dpi=200, facecolor=SURFACE, bbox_inches="tight")
        log(f"escrito {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
