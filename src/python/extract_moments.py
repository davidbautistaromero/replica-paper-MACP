"""Etapa 4 - Extrae los momentos simulados a un CSV tidy.

Funciona igual para los dos motores porque ambos guardan las mismas variables
indexadas por el `counter` del loop del autor: MATLAB en un `.mat`, el port en
un `.npz`. El mapa variable -> fila de la Tabla 2 vive en config/specs.json y es
el unico lugar donde esa correspondencia esta escrita.

Nota sobre signos: en el codigo `gdp_g_h_sim` ya es una tasa de crecimiento
negativa (caida del PIB en anos de huracan), igual que en la tabla del paper.

    python src/python/extract_moments.py --profile paper_memlite --engine matlab
    python src/python/extract_moments.py --profile smoke_cmp     --engine python
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from common import (
    OUT_MOMENTS, ensure_dirs, load_config, load_countries, log, raw_dir, raw_paths,
    resolve_engine, specs_only, tag,
)


def load_vars(path: Path) -> dict[str, np.ndarray]:
    """Carga un .mat (v7) o un .npz como diccionario de arreglos."""
    if path.suffix == ".mat":
        from scipy.io import loadmat
        return loadmat(path)
    with np.load(path) as z:
        return {k: z[k] for k in z.files}


def extract_one(path: Path, spec_name: str, spec: dict, cfg: dict,
                countries: dict) -> pd.DataFrame:
    md = load_vars(path)
    rows = []
    for mom, meta in cfg["moments"].items():
        if not isinstance(meta, dict):
            continue
        var = meta["var"]
        if var not in md:
            log(f"AVISO {spec_name}: la variable {var} ({mom}) no esta en {path.name}")
            continue
        arr = np.asarray(md[var], dtype=float)
        col = meta.get("col", 0)
        for counter, info in countries.items():
            if counter > arr.shape[0]:
                continue
            val = float(arr[counter - 1, col] if arr.ndim == 2 else arr[counter - 1])
            # Los paises que no se corrieron quedan en cero en el arreglo.
            if val == 0.0 or not np.isfinite(val):
                continue
            rows.append({
                "spec": spec_name,
                "panel": spec["panel"],
                "counter": counter,
                "iso3": info["iso3"],
                "country_es": info["country_es"],
                "moment": mom,
                "moment_label": meta["label"],
                "value": val,
                "source_var": var,
            })
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="paper_memlite")
    ap.add_argument("--engine", default="matlab", choices=["matlab", "python"])
    args = ap.parse_args()

    cfg = load_config()
    countries = load_countries()
    resolve_engine(cfg, args.engine)  # valida el nombre

    frames = []
    for spec_name, spec in specs_only(cfg).items():
        rutas = raw_paths(cfg, args.profile, args.engine, spec_name)
        if not rutas:
            log(f"AVISO: no hay salidas de {spec_name} con motor {args.engine}")
            continue
        # Puede haber varias: una por corrida etiquetada, cada una con sus paises.
        for path in rutas:
            df = extract_one(path, spec_name, spec, cfg, countries)
            log(f"{spec_name}: {len(df)} momentos extraidos de {path.name}")
            frames.append(df)

    if not frames:
        raise SystemExit(
            f"No hay salidas en {raw_dir(cfg, args.profile, args.engine)}. "
            f"Corra la etapa 2 con --engine {args.engine}."
        )

    out = pd.concat(frames, ignore_index=True)
    dup = out.duplicated(subset=["spec", "iso3", "moment"], keep=False)
    if dup.any():
        raise SystemExit(
            "Hay paises repetidos entre corridas etiquetadas: "
            f"{sorted(out.loc[dup, 'iso3'].unique())}. Cada etiqueta debe cubrir "
            "paises distintos, o sobra un .mat viejo en la carpeta de salida."
        )
    out.insert(0, "engine", args.engine)
    out.insert(0, "profile", args.profile)
    ensure_dirs(OUT_MOMENTS)
    dest = OUT_MOMENTS / f"moments_{tag(args.profile, args.engine)}.csv"
    out.to_csv(dest, index=False, encoding="utf-8")
    log(f"escrito {dest} ({len(out)} filas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
