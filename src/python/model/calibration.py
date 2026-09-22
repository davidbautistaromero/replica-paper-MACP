"""Parametros del modelo.

Los parametros por pais NO se repiten aqui: se leen de
`data/targets/table1_calibration_vendor_code.csv`, que es la transcripcion de
las lineas 8-80 del codigo del autor. Una sola fuente de verdad para los dos
motores.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

TARGETS = Path(__file__).resolve().parents[3] / "data" / "targets"
CALIB_CSV = TARGETS / "table1_calibration_vendor_code.csv"

# Parametros comunes a los siete paises (climate_persistent_wf.m:83-110, 259-290)
COMMON = {
    "gamma_c": 2.0,       # aversion al riesgo (CRRA)
    "lambda_": 1.0 / 3.0,  # probabilidad de readmision (Richmond y Dias, 2009)
    "mu_r": 0.0451,       # tasa libre de riesgo anual
    "int_y": 2.5,         # desviaciones estandar cubiertas por la grilla de y
    "int_h": 2.0,         # idem para el choque de huracan
    "ev_rho": 1e-2,       # escala de los choques de valor extremo
    "eulgam": 0.5772,     # constante de Euler-Mascheroni, redondeada como en el original
    "damp_v": 0.8,
    "damp_q": 0.8,
    "maxiter_v": 300,
    "tol_v": 1e-3,
    # Grilla de deuda: dos tramos, 85% de los puntos entre b_min y b_mid
    "b_g_min": -0.05,
    "b_g_max": 1.18,
    "b_g_mid": 0.30,
    "b_g_mid_share": 0.85,
}


@dataclass
class Params:
    """Parametros de un pais para una especificacion y un perfil dados."""

    counter: int
    iso3: str
    # pais
    rho_y: float
    sigma_ey: float
    beta: float
    wc_par_asymm: float   # costo de default: fraccion de E[y] disponible en autarquia
    delta: float          # decaimiento de la deuda de largo plazo
    sigma_eh: float
    mu_h: float           # perdida media de PIB por huracan
    p_hu_base: float      # frecuencia de huracanes calibrada
    # escenario (cc_freq=cc_int=1 baseline; 0 elimina el riesgo)
    cc_freq: float = 1.0
    cc_int: float = 1.0
    # perfil
    N_y: int = 63
    N_h: int = 20
    N_b_g: int = 150
    T_sim: int = 10000
    maxiter_q: int = 600
    tol_q: float = 1e-6
    common: dict = field(default_factory=lambda: dict(COMMON))

    @property
    def p_hu(self) -> float:
        return self.cc_freq * self.p_hu_base

    @property
    def mean_h(self) -> float:
        """Nivel del PIB tras un huracan: 1 - cc_int * mu_h."""
        return 1.0 - self.cc_int * self.mu_h

    @property
    def N_x(self) -> int:
        return self.N_h * self.N_y

    def __getattr__(self, name):  # acceso directo a los comunes: p.gamma_c
        try:
            return self.__dict__["common"][name]
        except KeyError:
            raise AttributeError(name) from None


def load_country_table() -> dict[int, dict[str, str]]:
    with open(CALIB_CSV, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(
            line for line in fh if not line.startswith("#"))]
    return {int(r["counter"]): r for r in rows}


def build_params(counter: int, spec: dict, profile: dict) -> Params:
    """Arma los parametros de un pais combinando CSV + especificacion + perfil."""
    row = load_country_table()[counter]
    return Params(
        counter=counter,
        iso3=row["iso3"],
        rho_y=float(row["rho_y"]),
        sigma_ey=float(row["sigma_ey"]),
        beta=float(row["beta"]),
        wc_par_asymm=float(row["output_cost_frac"]),
        delta=float(row["delta_decay"]),
        sigma_eh=float(row["sigma_eh"]),
        mu_h=float(row["mu_h"]),
        p_hu_base=float(row["p_hu"]),
        cc_freq=float(spec.get("cc_freq", 1)),
        cc_int=float(spec.get("cc_int", 1)),
        N_y=int(profile["N_y"]),
        N_h=int(profile["N_h"]),
        N_b_g=int(profile["N_b_g"]),
        T_sim=int(profile["T_sim"]),
        maxiter_q=int(profile["maxiter_q"]),
        tol_q=float(profile["tol_q"]),
    )
