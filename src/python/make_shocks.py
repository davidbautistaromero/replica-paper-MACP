"""Etapa 1 - Sorteos aleatorios compartidos entre motores.

Por que hacen falta
-------------------
MATLAB y NumPy usan ambos Mersenne Twister, pero lo siembran distinto
(`init_genrand` vs `init_by_array`), asi que `rng(s)` y `default_rng(s)` NO
producen la misma secuencia. Sin sorteos comunes, dos implementaciones
perfectamente correctas dan momentos distintos y no se puede distinguir un
error de traduccion del ruido de Monte Carlo.

Este script genera los sorteos una sola vez, en formato legible por los dos
motores (`.mat` y `.npz`), con una semilla por pais (`seed + 100*counter`) para
que el resultado de un pais no dependa de cuales otros se corran. Se generan
siempre las siete columnas, de modo que el archivo no dependa del subconjunto
de paises pedido.

Contenido:
  shocks_X : (T_sim-1, 7)  uniformes para el sendero de la cadena de Markov
  shocks_U : (T_sim+1, 7)  uniformes para el sorteo de readmision (u < lambda)

    python src/python/make_shocks.py --profile smoke_cmp
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from scipy.io import savemat

from common import (
    ensure_dirs, load_config, load_countries, log, resolve_profile, sha256,
    shocks_dir, write_manifest,
)

N_COUNTRIES = 7  # el loop del autor es fijo: counter = 1..7


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="smoke_cmp")
    args = ap.parse_args()

    cfg = load_config()
    prof = resolve_profile(cfg, args.profile)
    countries = load_countries()
    seed, T = cfg["seed"], prof["T_sim"]

    if not prof.get("shared_shocks", False):
        log(f"el perfil '{args.profile}' no usa sorteos compartidos "
            f"(shared_shocks=false): no hay nada que generar")
        return 0

    X = np.zeros((T - 1, N_COUNTRIES))
    U = np.zeros((T + 1, N_COUNTRIES))
    for counter in range(1, N_COUNTRIES + 1):
        rng = np.random.default_rng(seed + 100 * counter)
        X[:, counter - 1] = rng.random(T - 1)
        U[:, counter - 1] = rng.random(T + 1)

    sdir = shocks_dir(args.profile)
    ensure_dirs(sdir)
    mat_path, npz_path = sdir / "shocks.mat", sdir / "shocks.npz"
    # v5 para que el `load` de MATLAB lo lea sin depender de versiones.
    savemat(mat_path, {"shocks_X": X, "shocks_U": U,
                       "shocks_seed": float(seed), "shocks_T_sim": float(T)},
            format="5", do_compression=True)
    np.savez_compressed(npz_path, shocks_X=X, shocks_U=U, seed=seed, T_sim=T)

    etiquetas = ", ".join("{}={}".format(c, countries[c]["iso3"]) for c in sorted(countries))
    log(f"sorteos para {N_COUNTRIES} paises, T_sim={T}: {mat_path.name}, {npz_path.name}")
    log(f"   columnas: {etiquetas}")

    write_manifest(f"shocks_{args.profile}", {
        "etapa": "1_make_shocks",
        "perfil": args.profile,
        "semilla_base": seed,
        "semilla_por_pais": "seed + 100*counter",
        "T_sim": T,
        "shape_X": list(X.shape),
        "shape_U": list(U.shape),
        "sha256_mat": sha256(mat_path),
        "sha256_npz": sha256(npz_path),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
