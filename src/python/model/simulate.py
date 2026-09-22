"""Simulacion y momentos de la Tabla 2.

Port de climate_persistent_wf.m:486-665. Se conservan dos rarezas del original
porque el objetivo es reproducirlo, no corregirlo; van marcadas `# fidelidad:`.

La simulacion no es un sendero de un solo pais: el estado exogeno sigue una
cadena de Markov, pero la deuda se propaga como una *distribucion*, porque la
politica de emision es probabilistica (choques de valor extremo). Los momentos
son promedios de esa distribucion a lo largo del tiempo.
"""

from __future__ import annotations

import warnings

import numpy as np

from .calibration import Params
from .grids import Grids
from .solve import Solution


def markov_path(P: np.ndarray, i0: int, X: np.ndarray) -> np.ndarray:
    """Sendero de la cadena de Markov (port del bloque 'markov function').

    El original normaliza las filas que no suman exactamente 1 (la truncacion de
    Tauchen deja errores del orden de 1e-16) e imprime un aviso por cada una.
    """
    P = np.array(P, dtype=float, copy=True)
    sumas = P.sum(axis=1)
    malas = sumas != 1.0
    if malas.any():
        P[malas] = P[malas] / sumas[malas][:, None]

    cum = P.cumsum(axis=1)
    n_estados = P.shape[0]
    path = np.empty(len(X) + 1, dtype=np.int64)
    path[0] = i0
    s = i0
    for k, u in enumerate(X):
        # primer estado con cum >= u, que es la condicion del original
        s = int(np.searchsorted(cum[s], u, side="left"))
        s = min(s, n_estados - 1)   # blindaje: u > cum[-1] por error de redondeo
        path[k + 1] = s
    return path


def _nan(fn, x):
    """nanmean/nanmedian sin el aviso cuando el corte queda vacio."""
    if x.size == 0 or np.all(np.isnan(x)):
        return float("nan")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return float(fn(x))


def simulate(p: Params, g: Grids, sol: Solution, X: np.ndarray,
             redem: np.ndarray) -> dict[str, float]:
    """Simula T_sim periodos y devuelve los momentos.

    `X`     : (T_sim-1,) uniformes para la cadena de Markov.
    `redem` : (T_sim+1,) booleanos de readmision (u < lambda).
    """
    T, N_x, N_b = p.T_sim, p.N_x, p.N_b_g
    delta = p.delta

    # Estado inicial: MATLAB sub2ind([N_h N_y], floor(N_h/2)+1, floor(N_y/2)+1)
    i0 = (p.N_y // 2) * p.N_h + (p.N_h // 2)
    i_x = markov_path(g.P_x, i0, X[:T - 1])

    y_sim = g.y_vec_2sh[i_x[:T]]
    h_sim = g.h_vec_2sh[i_x[:T]]

    # fidelidad: los vectores se inicializan en cero y el loop solo llena
    # t = 0..T-2, asi que el ultimo periodo queda en cero y entra en los
    # promedios. Es un detalle del original que hay que conservar para poder
    # comparar motores.
    r_g = np.zeros(T)
    q_g_m = np.zeros(T)
    b_g = np.zeros(T)
    V_g = np.zeros(T)
    def_m = np.zeros(T)
    mass_acc = np.zeros(T)

    dist_cur = np.zeros((N_x, N_b))
    dist_next = np.zeros((N_x, N_b))
    mass_acc[0] = 1.0
    dist_cur[i_x[0], g.i_b_zero] = 1.0

    rendimiento = 1.0 / sol.q_g_pf - delta      # (1+1/q-delta)-1

    for t in range(T - 1):
        dist_next[:] = 0.0
        if mass_acc[t] > 0.99:                  # con acceso al mercado
            w = dist_cur * (1.0 - sol.def_pf)
            mass_acc[t + 1] = w.sum()
            dist_next[i_x[t + 1], :] = np.einsum("xb,xbp->p", w, sol.prob_choice,
                                                 optimize=True)
            den = dist_cur.sum()
            r_g[t] = (rendimiento * dist_cur).sum() / den
            q_g_m[t] = (sol.q_g_pf * dist_cur).sum() / den
            b_g[t] = (g.b_vec[None, :] * dist_cur).sum() / den
            V_g[t] = (sol.v * dist_cur).sum() / den
            def_m[t] = (sol.def_pf * dist_cur).sum() / den
        else:                                   # autarquia financiera
            mass_acc[t + 1] = float(redem[t + 1])
            dist_next[i_x[t + 1], g.i_b_zero] = 1.0
            r_g[t] = q_g_m[t] = b_g[t] = np.nan
            V_g[t] = sol.v_bad[i_x[t]]
            def_m[t] = 1.0
        dist_cur, dist_next = dist_next, dist_cur

    # ------------------------------------------------------------------ momentos
    gdp_sim = y_sim * h_sim
    B_g = (1.0 / gdp_sim) * (b_g / (delta + p.mu_r))       # valor facial / PIB
    spread = 10000.0 * ((1.0 + r_g) / (1.0 + p.mu_r) - 1.0)

    with np.errstate(invalid="ignore"):
        mercado = spread < 1e4                              # NaN -> False
    con_hur = h_sim < 1.0

    out = {
        "meanBY_sim": _nan(np.nanmean, B_g[mercado]),
        "meanBY_sim_market": _nan(np.nanmean, (q_g_m * b_g)[mercado]),
        "meanspread_sim": _nan(np.nanmean, spread[mercado]),
        "medianspread_sim": _nan(np.nanmedian, spread[mercado]),
        "meanspread_hurr_sim": _nan(np.nanmean, spread[mercado & con_hur]),
        "medianspread_hurr_sim": _nan(np.nanmedian, spread[mercado & con_hur]),
        # MATLAB std(x,0,...) normaliza por N-1
        "stdspread_sim": _nan(lambda a: np.nanstd(a, ddof=1), spread[mercado]),
        "hur_freq_sim": float(con_hur.sum()) / T,
    }

    # Incidencia de default: no es un conteo de episodios sino el promedio de la
    # probabilidad de default de la politica optima (el paper la llama
    # "default incidence").
    b_g_lag = np.concatenate([[110.0], b_g[:-1]])           # el 110 es del original
    def_sim = def_m.copy()
    def_sim[np.isnan(b_g) & np.isnan(b_g_lag)] = 0.0
    out["def_freq_sim"] = _nan(np.nanmean, def_sim)
    out["def_hur_freq_sim"] = _nan(np.nanmean, def_sim[con_hur])

    # fidelidad: b_g_sim1 y b_g_sim_curr son el mismo vector salvo el primer y
    # el ultimo elemento (el original no los desplaza), y los NaN de nx_sim se
    # rellenan con cero *antes* de calcular el consumo, de modo que las dos
    # sustituciones siguientes del codigo del autor nunca se activan. Se replica
    # el calculo tal cual porque solo alimenta cons_sim, que no esta en la Tabla 2.
    b1 = np.concatenate([b_g[:-1], [np.nan]])
    bcur = np.concatenate([[np.nan], b_g[1:]])
    nx = -q_g_m * (bcur - (1.0 - delta) * b1) + b1
    nx[np.isnan(nx)] = 0.0
    _c_sim = gdp_sim - nx

    gdp_g = (gdp_sim[1:] - gdp_sim[:-1]) / gdp_sim[:-1]
    out["gdp_g_h_sim"] = float(np.mean(gdp_g[con_hur[1:]]))  # mean, no nanmean
    with np.errstate(invalid="ignore", divide="ignore"):
        spread_g = (spread[1:] - spread[:-1]) / spread[:-1]
    out["spread_g_h_sim"] = _nan(np.nanmedian, spread_g[con_hur[1:]])

    out["gdp_mean"] = g.gdp_mean
    out["mass_acc_mean"] = float(np.mean(mass_acc))
    return out
