"""Etapa 7 - Verificaciones automaticas de la replica.

Separa dos cosas que suelen confundirse:

* Chequeos ESTRUCTURALES: el pipeline hizo lo que dijo (cobertura de momentos,
  frecuencia simulada de huracanes coherente con la p_h calibrada, Panel C
  efectivamente sin huracanes, frecuencias de default en rango plausible).
  Se exigen siempre, en cualquier perfil.
* Chequeos de TOLERANCIA y de SIGNO: la replica reproduce los numeros y el
  resultado cualitativo del paper (sin riesgo de huracan el gobierno se endeuda
  mas). Solo deciden el codigo de salida en perfiles reportables; en el perfil
  de prueba se informan pero no fallan, porque sus grillas son gruesas.

    python src/python/checks.py --profile paper_memlite --engine matlab
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from common import (
    OUT_TABLES, TARGETS_DIR, ensure_dirs, expected_missing, load_config, log,
    moments_only, tag,
)

OK, WARN, FAIL = "OK", "AVISO", "FALLA"


def add(res: list, tipo: str, estado: str, nombre: str, detalle: str) -> None:
    res.append({"tipo": tipo, "estado": estado, "chequeo": nombre, "detalle": detalle})


def structural(df: pd.DataFrame, tgt: pd.DataFrame, cfg: dict, res: list,
               t_sim: int, engine: str) -> None:
    calib = pd.read_csv(TARGETS_DIR / "table1_calibration_vendor_code.csv", comment="#")

    # 1. Cobertura: cada celda de la Tabla 2 que el paper reporta para los paises
    #    simulados tiene su contraparte. Se descuentan las celdas que el motor no
    #    calcula por diseno del codigo del autor (ver 'no_calculado' en config).
    esperadas = {(m, p) for m, meta in moments_only(cfg).items() for p in meta["in_panels"]}
    excusadas = expected_missing(cfg, engine)
    simuladas = {(r.moment, r.panel, r.iso3) for r in df.itertuples()}
    objetivos = {(r.moment, r.panel, r.iso3) for r in tgt.itertuples()
                 if (r.moment, r.panel) in esperadas and r.iso3 in set(df["iso3"])}
    faltan = sorted(o for o in objetivos - simuladas if (o[0], o[1]) not in excusadas)
    omitidas = sorted(o for o in objetivos - simuladas if (o[0], o[1]) in excusadas)
    add(res, "estructural", OK if not faltan else FAIL, "cobertura de la Tabla 2",
        (f"{len(objetivos)} celdas reportadas por el paper, todas simuladas"
         + (f"; {len(omitidas)} omitidas por diseno del codigo del autor: "
            f"{sorted({(m, p) for m, p, _ in omitidas})}" if omitidas else ""))
        if not faltan else f"sin simular: {faltan}")

    # 2. La frecuencia simulada de huracanes debe acercarse a la p_h calibrada.
    hf = df[(df["moment"] == "hurricane_freq") & (df["panel"] == "B")]
    for _, r in hf.iterrows():
        p_hu = float(calib.loc[calib["iso3"] == r["iso3"], "p_hu"].iloc[0])
        dif = abs(r["value"] - p_hu)
        add(res, "estructural", OK if dif <= 0.03 else FAIL,
            f"frecuencia de huracan {r['iso3']}",
            f"simulada {r['value']:.3f} vs. calibrada p_h={p_hu:.3f} (dif {dif:.3f})")

    # 3. El Panel C no debe registrar huracanes, salvo el artefacto del estado
    #    inicial: el codigo del autor arranca la simulacion con el indice de
    #    huracan a mitad de la grilla y duplica el estado inicial en el sendero,
    #    asi que incluso sin riesgo aparecen exactamente 2 periodos con dano.
    tope = 2.5 / t_sim
    c_hur = df[(df["panel"] == "C") & (df["moment"] == "hurricane_freq")]
    exceso = c_hur[c_hur["value"] > tope]
    add(res, "estructural", OK if exceso.empty else FAIL, "Panel C sin huracanes",
        f"frecuencias <= {tope:.2}, compatible con el artefacto del estado inicial "
        f"(2/{t_sim})" if exceso.empty
        else f"por encima del artefacto: {exceso[['iso3', 'value']].to_dict('records')}")

    # 4. Frecuencias de default en rango plausible.
    dfq = df[df["moment"] == "default_freq"]
    malas = dfq[(dfq["value"] <= 0) | (dfq["value"] > 0.15)]
    add(res, "estructural", OK if malas.empty else FAIL, "default_freq en rango",
        "todas en (0, 0.15]" if malas.empty
        else f"fuera de rango: {malas[['panel', 'iso3', 'value']].to_dict('records')}")


def targets_available(df: pd.DataFrame, cfg: dict, res: list) -> None:
    """Avisa (sin fallar) si faltan valores del paper para algun pais pedido."""
    esperados = {m: set(meta["in_panels"]) for m, meta in cfg["moments"].items()
                 if isinstance(meta, dict)}
    falta = df[df["target"].isna() & np.array(
        [r.panel in esperados.get(r.moment, set()) for r in df.itertuples()])]
    if falta.empty:
        add(res, "estructural", OK, "objetivos del paper disponibles",
            "todos los paises pedidos tienen valores transcritos")
    else:
        paises = sorted(falta["iso3"].unique())
        add(res, "estructural", WARN, "objetivos del paper disponibles",
            f"sin transcribir: {paises} ({len(falta)} momentos). "
            f"Complete data/targets/table2_mallucci2022_jie.csv")


def tolerances(df: pd.DataFrame, cfg: dict, res: list) -> None:
    tol = cfg["tolerances"]
    for _, r in df.dropna(subset=["target", "value"]).iterrows():
        banda = tol.get(r["moment"])
        if banda is None:
            continue
        dentro = abs(r["gap"]) <= banda
        add(res, "tolerancia", OK if dentro else FAIL,
            f"{r['moment']} {r['iso3']} panel {r['panel']}",
            f"replica {r['value']:.4g} vs. paper {r['target']:.4g} "
            f"(brecha {r['gap']:+.4g}, banda +-{banda:g})")


def signs(df: pd.DataFrame, res: list) -> None:
    """Resultado central del paper: sin riesgo de huracan la deuda sostenible es mayor."""
    piv = (df[df["moment"] == "debt_gdp"]
           .pivot_table(index="iso3", columns="panel", values="value"))
    for iso, row in piv.iterrows():
        if {"B", "C"} - set(piv.columns):
            add(res, "signo", WARN, f"deuda/PIB {iso}", "faltan ambos paneles para comparar")
            continue
        sube = row["C"] > row["B"]
        add(res, "signo", OK if sube else FAIL, f"deuda/PIB sin huracan mayor ({iso})",
            f"Panel B {row['B']:.3f} -> Panel C {row['C']:.3f} "
            f"({100 * (row['C'] / row['B'] - 1):+.1f}%)")


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
    df = pd.read_csv(src)
    tgt = pd.read_csv(TARGETS_DIR / "table2_mallucci2022_jie.csv", comment="#")

    res: list[dict] = []
    structural(df, tgt, cfg, res, int(cfg["profiles"][args.profile]["T_sim"]), args.engine)
    targets_available(df, cfg, res)
    tolerances(df, cfg, res)
    signs(df, res)
    out = pd.DataFrame(res)

    reportable = cfg["profiles"][args.profile].get("reportable", False)
    ancho = max(len(r["chequeo"]) for r in res)
    for r in res:
        print(f"  [{r['estado']:>6}] {r['chequeo']:<{ancho}}  {r['detalle']}")

    fallas = out[out["estado"] == FAIL]
    duras = fallas[fallas["tipo"] == "estructural"] if not reportable else fallas

    ensure_dirs(OUT_TABLES)
    dest = OUT_TABLES / f"checks_{etiqueta}.md"
    lines = [f"# Verificaciones - perfil `{args.profile}`, motor `{args.engine}`", "",
             f"- chequeos: {len(out)} | fallas: {len(fallas)} "
             f"| decisivas en este perfil: {len(duras)}", ""]
    if not reportable:
        lines += ["> Perfil no reportable: las fallas de tolerancia y signo se informan "
                  "pero no hacen fallar el pipeline.", ""]
    for _, r in out.iterrows():
        lines.append(f"- `{r['estado']}` **{r['chequeo']}** ({r['tipo']}): {r['detalle']}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"escrito {dest}")

    if len(duras):
        log(f"{len(duras)} chequeo(s) decisivo(s) fallaron")
        return 1
    log("todos los chequeos decisivos pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
