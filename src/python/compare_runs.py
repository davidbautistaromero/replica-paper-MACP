"""Comparacion de corridas (fuera de la secuencia de etapas) - Compara dos corridas momento a momento.

Sirve para las dos preguntas de equivalencia del proyecto:

1. **MATLAB vs Python**: ¿el port reproduce el codigo del autor?
       python src/python/compare_runs.py --left smoke_cmp:matlab --right smoke_cmp:python
   Solo tiene sentido con un perfil `shared_shocks: true`: con sorteos distintos,
   dos implementaciones correctas igual difieren por ruido de Monte Carlo.

2. **memlite vs original**: ¿la simulacion con dos rebanadas da lo mismo?
       python src/python/compare_runs.py --left smoke:matlab --right smoke_memlite:matlab

Veredicto por momento:
    identico    diferencia absoluta <= 1e-12
    equivalente diferencia relativa <= --tol-rel (1e-8 por defecto)
    cercano     diferencia relativa <= 1e-3
    DIVERGENTE  el resto

Con --strict el script devuelve codigo != 0 si algun momento divergio, que es lo
que uno quiere cuando la comparacion deberia ser exacta.
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from common import OUT_MOMENTS, OUT_TABLES, ensure_dirs, load_config, log

CLAVES = ["spec", "panel", "iso3", "moment"]


def parse_run(texto: str) -> tuple[str, str]:
    """'perfil' o 'perfil:motor' -> (perfil, motor)."""
    if ":" in texto:
        perfil, motor = texto.split(":", 1)
    else:
        perfil, motor = texto, "matlab"
    return perfil, motor


def load_run(perfil: str, motor: str) -> pd.DataFrame:
    path = OUT_MOMENTS / f"moments_{perfil}_{motor}.csv"
    if not path.exists():
        raise SystemExit(
            f"Falta {path}.\nCorra la etapa 2 y la 3 para perfil={perfil}, motor={motor}."
        )
    return pd.read_csv(path)[CLAVES + ["moment_label", "value"]]


def veredicto(abs_dif: float, rel_dif: float, tol_rel: float) -> str:
    if abs_dif <= 1e-12:
        return "identico"
    if rel_dif <= tol_rel:
        return "equivalente"
    if rel_dif <= 1e-3:
        return "cercano"
    return "DIVERGENTE"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--left", default="smoke_cmp:matlab", help="perfil[:motor] de referencia")
    ap.add_argument("--right", default="smoke_cmp:python", help="perfil[:motor] a contrastar")
    ap.add_argument("--tol-rel", type=float, default=1e-8)
    ap.add_argument("--strict", action="store_true",
                    help="falla si algun momento divergio")
    args = ap.parse_args()

    cfg = load_config()
    pl, ml = parse_run(args.left)
    pr, mr = parse_run(args.right)

    izq, der = load_run(pl, ml), load_run(pr, mr)
    df = izq.merge(der, on=CLAVES, suffixes=("_izq", "_der"), how="outer")
    df["moment_label"] = df["moment_label_izq"].fillna(df["moment_label_der"])
    df = df.drop(columns=["moment_label_izq", "moment_label_der"])

    df["dif_abs"] = (df["value_izq"] - df["value_der"]).abs()
    denom = df[["value_izq", "value_der"]].abs().max(axis=1).replace(0, np.nan)
    df["dif_rel"] = df["dif_abs"] / denom
    df["veredicto"] = [
        "FALTA" if pd.isna(a) else veredicto(a, r if pd.notna(r) else 0.0, args.tol_rel)
        for a, r in zip(df["dif_abs"], df["dif_rel"])
    ]

    # Advertencia metodologica: comparar motores sin sorteos compartidos no prueba nada.
    if ml != mr:
        sin_compartir = [p for p in (pl, pr)
                         if not cfg["profiles"][p].get("shared_shocks", False)]
        if sin_compartir:
            log(f"AVISO: {sin_compartir} no usa(n) sorteos compartidos. Las diferencias "
                f"entre motores incluiran ruido de Monte Carlo y no permiten concluir "
                f"nada sobre la traduccion. Use un perfil con shared_shocks=true.")

    resumen = df["veredicto"].value_counts().to_dict()
    ancho = df["moment"].str.len().max() + df["iso3"].str.len().max() + 4
    print()
    print(f"  {pl}:{ml}  vs  {pr}:{mr}")
    print(f"  {'momento':<{ancho}} {'izq':>14} {'der':>14} {'dif rel':>10}  veredicto")
    for _, r in df.sort_values(["panel", "iso3", "moment"]).iterrows():
        etiqueta = f"{r['moment']} {r['iso3']} ({r['panel']})"
        rel = "--" if pd.isna(r["dif_rel"]) else f"{r['dif_rel']:.2e}"
        print(f"  {etiqueta:<{ancho}} {r['value_izq']:>14.6g} {r['value_der']:>14.6g} "
              f"{rel:>10}  {r['veredicto']}")
    print()
    print(f"  resumen: {resumen}")
    if df["dif_rel"].notna().any():
        print(f"  diferencia relativa maxima: {df['dif_rel'].max():.3e}")

    ensure_dirs(OUT_TABLES)
    stem = OUT_TABLES / f"comparison_{pl}-{ml}_vs_{pr}-{mr}"
    df.to_csv(f"{stem}.csv", index=False, encoding="utf-8")
    lineas = [f"# Comparacion de corridas", "",
              f"- izquierda: perfil `{pl}`, motor `{ml}`",
              f"- derecha:   perfil `{pr}`, motor `{mr}`",
              f"- resumen: {resumen}", ""]
    lineas += ["| momento | pais | panel | izq | der | dif rel | veredicto |",
               "|---|---|---|---|---|---|---|"]
    for _, r in df.sort_values(["panel", "iso3", "moment"]).iterrows():
        rel = "--" if pd.isna(r["dif_rel"]) else f"{r['dif_rel']:.2e}"
        lineas.append(f"| {r['moment']} | {r['iso3']} | {r['panel']} | "
                      f"{r['value_izq']:.6g} | {r['value_der']:.6g} | {rel} | {r['veredicto']} |")
    (stem.with_suffix(".md")).write_text("\n".join(lineas) + "\n", encoding="utf-8")
    log(f"escritos {stem}.csv/.md")

    # --strict falla siempre por divergencia. Por ausencia solo si el momento es
    # una fila de la Tabla 2: hay momentos de diagnostico que una de las dos
    # implementaciones no calcula (el script sin huracanes del autor, por
    # ejemplo, nunca asigna medianspread_sim), y esa asimetria no es un error.
    en_tabla = {m: set(meta["in_panels"]) for m, meta in cfg["moments"].items()
                if isinstance(meta, dict)}
    es_tabla = np.array([r.panel in en_tabla.get(r.moment, set()) for r in df.itertuples()])
    divergen = (df["veredicto"] == "DIVERGENTE").to_numpy()
    ausentes = (df["veredicto"] == "FALTA").to_numpy()
    malos = int((divergen | (ausentes & es_tabla)).sum())
    informativos = int((ausentes & ~es_tabla).sum())
    if informativos:
        log(f"{informativos} momento(s) de diagnostico presentes en un solo motor "
            f"(no cuentan como divergencia)")
    if args.strict and malos:
        log(f"{malos} momento(s) divergieron o faltan en la Tabla 2")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
