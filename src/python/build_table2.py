"""Etapa 5 - Construye la tabla de comparacion (paper vs replica).

Toma outputs/moments/moments_<perfil>.csv y los valores objetivo de
data/targets/, y produce el entregable central:

  outputs/tables/table2_comparison_<perfil>_<motor>.csv  (formato largo)
  outputs/tables/table2_comparison_<perfil>_<motor>.md   (para leer en el repo)
  outputs/tables/table2_comparison_<perfil>_<motor>.tex  (\\input en LaTeX)

Si un pais del conjunto pedido no tiene valores objetivo transcritos, la tabla
lo muestra como "--" y el script avisa: es el caso de los paises agregados a la
replica despues de la Primera Entrega.

    python src/python/build_table2.py --profile paper_memlite --engine matlab
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from common import (
    OUT_MOMENTS, OUT_TABLES, TARGETS_DIR, ensure_dirs, load_config, log,
    resolve_engine, specs_only, tag,
)

TARGET_FILE = "table2_mallucci2022_jie.csv"


def load_targets(name: str = TARGET_FILE) -> pd.DataFrame:
    path = TARGETS_DIR / name
    df = pd.read_csv(path, comment="#")
    df = df.rename(columns={"value": "target"})
    return df[["panel", "iso3", "moment", "target", "verified", "source"]]


def build_long(profile: str, engine: str) -> pd.DataFrame:
    mom_path = OUT_MOMENTS / f"moments_{tag(profile, engine)}.csv"
    if not mom_path.exists():
        raise SystemExit(f"Falta {mom_path}. Corra la etapa 4 (extract_moments.py).")
    sim = pd.read_csv(mom_path)
    tgt = load_targets()

    df = sim.merge(tgt, on=["panel", "iso3", "moment"], how="left")
    df["gap"] = df["value"] - df["target"]
    df["gap_pct"] = 100 * df["gap"] / df["target"].abs()

    # Aviso explicito: momentos que el paper SI reporta en ese panel y para los
    # que no hay valor transcrito. Se evalua panel por panel, porque hay
    # momentos que solo existen en el Panel B (la frecuencia de huracan, por
    # ejemplo, que el Panel C no reporta).
    esperados = {m: set(meta["in_panels"])
                 for m, meta in load_config()["moments"].items()
                 if isinstance(meta, dict)}
    falta = df["target"].isna() & np.array(
        [r.panel in esperados.get(r.moment, set()) for r in df.itertuples()])
    if falta.any():
        paises = sorted(df.loc[falta, "iso3"].unique())
        log(f"AVISO: sin valor objetivo del paper para {paises} "
            f"({int(falta.sum())} momentos). Transcriba esas columnas de la "
            f"Tabla 2 a data/targets/table2_mallucci2022_jie.csv para comparar.")
    return df


def falta_objetivo(df: pd.DataFrame, cfg: dict) -> pd.Series:
    """True donde el paper SI reporta ese momento en ese panel y no hay valor."""
    esperados = {m: set(meta["in_panels"]) for m, meta in cfg["moments"].items()
                 if isinstance(meta, dict)}
    return df["target"].isna() & np.array(
        [r.panel in esperados.get(r.moment, set()) for r in df.itertuples()])


def fmt(value, digits: int) -> str:
    if pd.isna(value):
        return "--"
    return f"{value:,.{digits}f}" if digits else f"{value:,.0f}"


def md_table(block: pd.DataFrame) -> str:
    """Tabla markdown sin dependencias extra (evita `tabulate`)."""
    cols = list(block.columns)
    widths = [max(len(str(c)), *(len(str(v)) for v in block[c])) for c in cols]
    head = "| " + " | ".join(str(c).ljust(w) for c, w in zip(cols, widths)) + " |"
    rule = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    body = ["| " + " | ".join(str(r[c]).ljust(w) for c, w in zip(cols, widths)) + " |"
            for _, r in block.iterrows()]
    return "\n".join([head, rule, *body])


def wide_blocks(df: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """Un bloque por panel: filas = momentos, columnas = pais x (paper, replica, brecha)."""
    blocks = {}
    for panel, sub in df.groupby("panel", sort=True):
        moms = [m for m, meta in cfg["moments"].items()
                if isinstance(meta, dict) and panel in meta["in_panels"]]
        paises = sorted(sub["iso3"].unique())
        rows = []
        for mom in moms:
            meta = cfg["moments"][mom]
            row = {"Momento": meta["label"]}
            for iso in paises:
                cell = sub[(sub["moment"] == mom) & (sub["iso3"] == iso)]
                if cell.empty:
                    row[f"{iso} paper"] = row[f"{iso} replica"] = row[f"{iso} brecha"] = "--"
                    continue
                r = cell.iloc[0]
                d = meta["digits"]
                row[f"{iso} paper"] = fmt(r["target"], d)
                row[f"{iso} replica"] = fmt(r["value"], d)
                row[f"{iso} brecha"] = fmt(r["gap"], d)
            rows.append(row)
        blocks[panel] = pd.DataFrame(rows)
    return blocks


def to_markdown(blocks: dict[str, pd.DataFrame], cfg: dict, profile: str,
                engine: str, df: pd.DataFrame) -> str:
    titulos = {s["panel"]: s["paper_ref"] for s in specs_only(cfg).values()}
    out = [f"# Tabla 2 - replica vs. paper", "",
           f"- perfil: `{profile}`", f"- motor: {resolve_engine(cfg, engine)['label']}", ""]
    if not cfg["profiles"][profile].get("reportable", False):
        out += ["> **Perfil no reportable**: grillas gruesas, corrida de prueba del pipeline.", ""]
    for panel, block in blocks.items():
        out += [f"## Panel {panel} - {titulos.get(panel, '')}", "", md_table(block), ""]
    sin_obj = sorted(df.loc[falta_objetivo(df, cfg), "iso3"].unique())
    if sin_obj:
        out += [f"_Sin valores objetivo transcritos para: {', '.join(sin_obj)}._", ""]
    no_ver = df["verified"].eq(False).any() if "verified" in df else False
    if no_ver:
        out += ["_Los valores del paper provienen de la transcripcion del grupo "
                "(`verified=FALSE` en data/targets/): cotejar contra el PDF publicado._", ""]
    return "\n".join(out)


def to_latex(blocks: dict[str, pd.DataFrame], cfg: dict, profile: str,
             engine: str) -> str:
    titulos = {s["panel"]: s["label"] for s in specs_only(cfg).values()}
    partes = ["% Generado por src/python/build_table2.py -- no editar a mano",
              f"% perfil: {profile} | motor: {engine}",
              "% requiere \\usepackage{booktabs}", ""]
    for panel, block in blocks.items():
        cols = list(block.columns)
        paises = sorted({c.split()[0] for c in cols if c != "Momento"})
        partes += [
            r"\begin{tabular}{l" + "rrr" * len(paises) + "}",
            r"\toprule",
            r"\multicolumn{%d}{l}{\textbf{Panel %s: %s}} \\" % (1 + 3 * len(paises), panel,
                                                                titulos.get(panel, "")),
            r"\midrule",
            "Momento & " + " & ".join(
                r"\multicolumn{3}{c}{%s}" % p for p in paises) + r" \\",
            " & " + " & ".join(["Paper & Replica & Brecha"] * len(paises)) + r" \\",
            r"\midrule",
        ]
        for _, row in block.iterrows():
            celdas = [row["Momento"]] + [str(row[f"{p} {k}"]) for p in paises
                                         for k in ("paper", "replica", "brecha")]
            partes.append(" & ".join(celdas) + r" \\")
        partes += [r"\bottomrule", r"\end{tabular}", ""]
    return "\n".join(partes)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="paper_memlite")
    ap.add_argument("--engine", default="matlab", choices=["matlab", "python"])
    args = ap.parse_args()

    cfg = load_config()
    df = build_long(args.profile, args.engine)
    blocks = wide_blocks(df, cfg)

    ensure_dirs(OUT_TABLES)
    stem = OUT_TABLES / f"table2_comparison_{tag(args.profile, args.engine)}"
    df.to_csv(f"{stem}.csv", index=False, encoding="utf-8")
    md = to_markdown(blocks, cfg, args.profile, args.engine, df)
    (stem.with_suffix(".md")).write_text(md, encoding="utf-8")
    (stem.with_suffix(".tex")).write_text(
        to_latex(blocks, cfg, args.profile, args.engine), encoding="utf-8")

    log(f"escritos {stem}.csv/.md/.tex")
    print()
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
