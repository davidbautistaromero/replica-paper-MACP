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

import pandas as pd

from common import OUT_TABLES, TARGETS_DIR, ensure_dirs, load_config, log, tag

OK, WARN, FAIL = "OK", "AVISO", "FALLA"


def add(res: list, tipo: str, estado: str, nombre: str, detalle: str) -> None:
    res.append({"tipo": tipo, "estado": estado, "chequeo": nombre, "detalle": detalle})


def structural(df: pd.DataFrame, cfg: dict, res: list) -> None:
    calib = pd.read_csv(TARGETS_DIR / "table1_calibration_vendor_code.csv", comment="#")

    # 1. Cobertura: cada objetivo tiene su contraparte simulada.
    faltantes = df[df["value"].isna()]
    add(res, "estructural", OK if faltantes.empty else FAIL, "cobertura de momentos",
        "todos los objetivos tienen contraparte simulada" if faltantes.empty
        else f"sin simular: {faltantes[['panel', 'iso3', 'moment']].to_dict('records')}")

    # 2. La frecuencia simulada de huracanes debe acercarse a la p_h calibrada.
    hf = df[(df["moment"] == "hurricane_freq") & (df["panel"] == "B")]
    for _, r in hf.iterrows():
        p_hu = float(calib.loc[calib["iso3"] == r["iso3"], "p_hu"].iloc[0])
        dif = abs(r["value"] - p_hu)
        add(res, "estructural", OK if dif <= 0.03 else FAIL,
            f"frecuencia de huracan {r['iso3']}",
            f"simulada {r['value']:.3f} vs. calibrada p_h={p_hu:.3f} (dif {dif:.3f})")

    # 3. El Panel C no debe registrar huracanes.
    c_hur = df[(df["panel"] == "C") & (df["moment"] == "hurricane_freq") & (df["value"] > 0)]
    add(res, "estructural", OK if c_hur.empty else FAIL, "Panel C sin huracanes",
        "ningun huracan simulado en el Panel C" if c_hur.empty
        else f"aparecen huracanes en: {sorted(c_hur['iso3'])}")

    # 4. Frecuencias de default en rango plausible.
    dfq = df[df["moment"] == "default_freq"]
    malas = dfq[(dfq["value"] <= 0) | (dfq["value"] > 0.15)]
    add(res, "estructural", OK if malas.empty else FAIL, "default_freq en rango",
        "todas en (0, 0.15]" if malas.empty
        else f"fuera de rango: {malas[['panel', 'iso3', 'value']].to_dict('records')}")


def targets_available(df: pd.DataFrame, cfg: dict, res: list) -> None:
    """Avisa (sin fallar) si faltan valores del paper para algun pais pedido."""
    tabla = [m for m, meta in cfg["moments"].items()
             if isinstance(meta, dict) and meta["in_panels"]]
    falta = df[df["target"].isna() & df["moment"].isin(tabla)]
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

    res: list[dict] = []
    structural(df, cfg, res)
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
