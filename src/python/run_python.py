"""Etapa 3 (motor Python) - Resuelve y simula el modelo sin MATLAB.

Mismo contrato que run_matlab.py: recibe perfil, paises y especificaciones, y
deja en outputs/raw_npz/<perfil>/<spec>.npz las mismas variables que el .mat del
autor (`meanspread_sim`, `meanBY_sim`, ...), como matrices de 7 filas indexadas
por el `counter` del loop original. Gracias a eso las etapas 3 a 7 son comunes a
los dos motores.

Reproduce tambien las dependencias entre paneles del codigo original: el Panel C
hereda E[y] del Panel B en vez de recalcularlo, y ambos paneles comparten los
sorteos de readmision.

    python src/python/run_python.py --profile smoke_cmp --countries entrega1
    python src/python/run_python.py --profile smoke_cmp --specs panelB_hurricane
"""

from __future__ import annotations

import argparse
import sys
import time

import numpy as np

from common import (
    ensure_dirs, load_config, load_countries, log, raw_dir, raw_path,
    resolve_countries, resolve_profile, shocks_dir, spec_order, specs_only,
    write_manifest,
)
from model.calibration import build_params
from model.grids import autarky_utility, build_grids
from model.simulate import simulate
from model.solve import solve

N_COUNTRIES = 7

# Variables que se guardan como vector por pais (mismo nombre que en el .mat).
MOMENT_VARS = [
    "meanBY_sim", "meanBY_sim_market", "meanspread_sim", "medianspread_sim",
    "meanspread_hurr_sim", "medianspread_hurr_sim", "stdspread_sim",
    "hur_freq_sim", "def_freq_sim", "def_hur_freq_sim", "gdp_g_h_sim",
    "spread_g_h_sim",
]


def draws_for(cfg: dict, prof: dict, profile_name: str, counter: int, T: int):
    """Sorteos de un pais: compartidos con MATLAB o generados aqui.

    En los dos casos el orden es el mismo (primero X, luego U) y la semilla es
    `seed + 100*counter`, de modo que un perfil con sorteos compartidos y uno sin
    ellos dan exactamente los mismos numeros en Python.
    """
    if prof.get("shared_shocks", False):
        path = shocks_dir(profile_name) / "shocks.npz"
        if not path.exists():
            raise SystemExit(
                f"Falta {path}. El perfil '{profile_name}' usa sorteos compartidos: "
                f"corra primero src/python/make_shocks.py --profile {profile_name}."
            )
        z = np.load(path)
        if int(z["T_sim"]) != T:
            raise SystemExit(
                f"{path.name} tiene T_sim={int(z['T_sim'])} y el perfil pide {T}. "
                f"Regenere los sorteos."
            )
        return z["shocks_X"][:, counter - 1], z["shocks_U"][:, counter - 1]

    rng = np.random.default_rng(cfg["seed"] + 100 * counter)
    return rng.random(T - 1), rng.random(T + 1)


def inherited_gdp_mean(cfg: dict, profile_name: str, spec: dict, counters: list[int]):
    """E[y] por pais heredado del panel del que depende la especificacion."""
    dep = spec["depends_on"][0]
    path = raw_path(cfg, profile_name, "python", dep)
    if not path.exists():
        raise SystemExit(
            f"Esta especificacion hereda E[y] de '{dep}', pero no existe {path}.\n"
            f"Corra primero: --specs {dep} (mismo perfil)."
        )
    store = np.load(path)["gdp_mean_store"].ravel()
    faltan = [c for c in counters if abs(store[c - 1]) < 1e-12]
    if faltan:
        raise SystemExit(
            f"gdp_mean_store esta en cero para {faltan}: '{dep}' no se corrio para "
            f"esos paises. Vuelva a correrlo incluyendolos."
        )
    return store


def run_spec(spec_name: str, cfg: dict, prof: dict, profile_name: str,
             counters: list[int], paises: dict) -> list[dict]:
    spec = specs_only(cfg)[spec_name]
    log(f"{spec_name}: {spec['paper_ref']} (cc_freq={spec['cc_freq']}, cc_int={spec['cc_int']})")

    store = (inherited_gdp_mean(cfg, profile_name, spec, counters)
             if spec.get("inherits_gdp_mean") else None)

    acumulado = {v: np.zeros((N_COUNTRIES, 1)) for v in MOMENT_VARS}
    acumulado["gdp_mean_store"] = np.zeros((N_COUNTRIES, 1))
    diagnostico = []

    for counter in counters:
        iso = paises[counter]["iso3"]
        p = build_params(counter, spec, prof)
        t0 = time.time()

        g = build_grids(p, gdp_mean=None if store is None else store[counter - 1])
        util_aut = autarky_utility(p, g)
        log(f"   {iso}: N_x={p.N_x} x N_b={p.N_b_g}, resolviendo...")
        sol = solve(p, g, util_aut)

        X, U = draws_for(cfg, prof, profile_name, counter, p.T_sim)
        mom = simulate(p, g, sol, X, U < p.lambda_)

        for v in MOMENT_VARS:
            acumulado[v][counter - 1, 0] = mom[v]
        acumulado["gdp_mean_store"][counter - 1, 0] = g.gdp_mean

        mins = (time.time() - t0) / 60
        estado = "convergio" if sol.converged else f"SIN CONVERGER (tope {sol.maxiter_q - 1} iter)"
        log(f"   {iso}: {mins:.1f} min | iter_q={sol.iter_q} diff_q={sol.diff_q:.2e} "
            f"({estado}) | spread={mom['meanspread_sim']:.0f} pb, "
            f"deuda/PIB={mom['meanBY_sim']:.3f}")
        diagnostico.append({
            "counter": counter, "iso3": iso, "minutos": round(mins, 2),
            "iter_q": sol.iter_q, "diff_q": sol.diff_q, "convergio": sol.converged,
            "iter_v_ultimo": sol.iter_v_ultimo, "diff_v_ultimo": sol.diff_v_ultimo,
        })

    dest = raw_path(cfg, profile_name, "python", spec_name)
    ensure_dirs(dest.parent)
    np.savez_compressed(dest, **acumulado, counters=np.array(counters))
    log(f"{spec_name}: guardado {dest}")
    return diagnostico


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="smoke_cmp")
    ap.add_argument("--countries", default="entrega1")
    ap.add_argument("--specs", default="all", help="'all' o nombres separados por coma")
    args = ap.parse_args()

    cfg = load_config()
    prof = resolve_profile(cfg, args.profile)
    counters = resolve_countries(cfg, args.countries)
    paises = load_countries()

    todos = spec_order(cfg)
    specs = list(todos) if args.specs == "all" else [s.strip() for s in args.specs.split(",")]
    desconocidas = [s for s in specs if s not in specs_only(cfg)]
    if desconocidas:
        raise SystemExit(f"Especificaciones desconocidas: {desconocidas}. Disponibles: {todos}")
    specs.sort(key=todos.index)

    if not prof.get("reportable", False):
        log(f"AVISO: el perfil '{args.profile}' no es reportable (grillas gruesas).")

    t0 = time.time()
    diagnosticos = {s: run_spec(s, cfg, prof, args.profile, counters, paises) for s in specs}

    write_manifest(f"run_{args.profile}_python", {
        "etapa": "3_run_python",
        "motor": "python",
        "perfil": args.profile,
        "reportable": prof.get("reportable", False),
        "sorteos_compartidos": prof.get("shared_shocks", False),
        "paises_counter": counters,
        "semilla": cfg["seed"],
        "numpy": np.__version__,
        "minutos_total": round((time.time() - t0) / 60, 2),
        "diagnostico": diagnosticos,
    })
    log(f"listo en {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
