"""Procesos exogenos y grillas.

Port de climate_persistent_wf.m:111-340. El orden de los estados exogenos es el
del original: `x = (i_y-1)*N_h + i_h`, es decir el indice del huracan corre
mas rapido. Respetarlo importa porque de el dependen los productos de Kronecker
y el estado inicial de la simulacion.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import erfc

from .calibration import Params


def tauchen(N: int, mu: float, rho: float, sigma: float, m: float
            ) -> tuple[np.ndarray, np.ndarray]:
    """Discretizacion de un AR(1) tal como la implementa el autor.

    Se reproduce su formula con `erfc` (y no una version "mejorada") para que
    los dos motores partan exactamente de la misma grilla y de las mismas
    probabilidades.
    """
    Z = np.zeros(N)
    a = (1.0 - rho) * mu

    Z[N - 1] = m * np.sqrt(sigma ** 2 / (1.0 - rho ** 2))
    Z[0] = -Z[N - 1]
    zstep = (Z[N - 1] - Z[0]) / (N - 1)
    for i in range(1, N - 1):
        Z[i] = Z[0] + zstep * i
    Z = Z + a / (1.0 - rho)

    def cdf(x):  # 0.5*erfc(-x/sqrt(2)) = Phi(x)
        return 0.5 * erfc(-x / np.sqrt(2.0))

    P = np.zeros((N, N))
    for j in range(N):
        centro = a + rho * Z[j]
        borde_izq = (Z - centro + zstep / 2.0) / sigma
        borde_der = (Z - centro - zstep / 2.0) / sigma
        P[j, :] = cdf(borde_izq) - cdf(borde_der)
        P[j, 0] = cdf(borde_izq[0])
        P[j, N - 1] = 1.0 - cdf(borde_der[N - 1])
    return Z, P


@dataclass
class Grids:
    y_vec: np.ndarray        # (N_y,)   ingreso en niveles
    h_vec: np.ndarray        # (N_h,)   1 = sin huracan; resto = 1 - perdida
    P_y: np.ndarray          # (N_y, N_y)
    P_h: np.ndarray          # (N_h, N_h)
    P_x: np.ndarray          # (N_x, N_x)
    gdp_vec: np.ndarray      # (N_x,)   y*h por estado exogeno
    y_vec_2sh: np.ndarray    # (N_x,)
    h_vec_2sh: np.ndarray    # (N_x,)
    b_vec: np.ndarray        # (N_b_g,)
    i_b_zero: int
    gdp_mean: float
    qrf: float
    qrf_lt: float


def build_grids(p: Params, gdp_mean: float | None = None) -> Grids:
    """Construye grillas y matriz de transicion.

    `gdp_mean` se pasa cuando la especificacion lo hereda del Panel B, igual que
    el `load('gdp_mean_storemat')` del codigo original (linea 241 de la variante
    sin huracanes): E[y] se calcula una sola vez, en la economia con huracanes.
    """
    # --- proceso de ingreso (lineas 112-148)
    ly_vec, P_y = tauchen(
        p.N_y, mu=-0.5 * p.sigma_ey ** 2 / (1 - p.rho_y ** 2),
        rho=p.rho_y, sigma=p.sigma_ey, m=p.int_y,
    )
    y_vec = np.exp(ly_vec)

    # --- proceso de huracan (lineas 152-199)
    if p.N_h > 1:
        lh_vec, P_h_core = tauchen(
            p.N_h - 1, mu=-0.5 * p.sigma_eh ** 2, rho=0.0, sigma=p.sigma_eh, m=p.int_h,
        )
        P_h = p.p_hu * P_h_core
        P_h = np.hstack([(1 - p.p_hu) * np.ones((p.N_h - 1, 1)), P_h])
        P_h = np.vstack([P_h[0:1, :], P_h])           # duplica la primera fila
        h_vec = np.concatenate([[1.0], p.mean_h * np.exp(lh_vec)])
    else:
        lh_vec, P_h = np.array([1.0]), np.ones((1, 1))
        h_vec = np.array([1.0])

    # --- estados exogenos combinados (lineas 201-232)
    h_vec_2sh = np.kron(np.ones(p.N_y), h_vec)
    y_vec_2sh = np.kron(y_vec, np.ones(p.N_h))
    gdp_vec = h_vec_2sh * y_vec_2sh

    # El ingreso del proximo periodo se sortea desde el punto de la grilla mas
    # cercano al PIB *despues* del huracan: en esta version los danos pasan al
    # AR(1) y tienen algo de persistencia (de ahi el nombre "persistent" de los
    # archivos del autor).
    idx = np.abs(gdp_vec[:, None] - y_vec[None, :]).argmin(axis=1)
    P_x_int = P_y[idx, :]                              # (N_x, N_y)
    P_x = np.kron(P_x_int, np.ones((1, p.N_h))) * np.kron(np.ones((p.N_y, p.N_y)), P_h)

    # --- E[y] (linea 228): el autor lo aproxima elevando P_x a 100000
    if gdp_mean is None:
        estacionaria = np.linalg.matrix_power(P_x, 100000) @ gdp_vec
        gdp_mean = float(estacionaria[p.N_x // 2])
    else:
        gdp_mean = float(gdp_mean)

    # --- grilla de deuda en dos tramos (lineas 282-322)
    N_tot, N_1 = p.N_b_g, int(np.floor(p.b_g_mid_share * p.N_b_g))
    low, mid, upp = p.b_g_min, p.b_g_mid, p.b_g_max
    tramo1 = np.linspace(low, mid, N_1)
    tramo2 = np.linspace(mid + (upp - mid) / (N_tot - N_1), upp, N_tot - N_1)
    b_vec = np.concatenate([tramo1, tramo2])
    i_b_zero = int(np.abs(b_vec).argmin())
    b_vec[i_b_zero] = 0.0

    # --- precios libres de riesgo (lineas 240-242)
    qrf = 1.0 / (1.0 + p.mu_r)
    qrf_lt = qrf / (1.0 - (1.0 - p.delta) * qrf)

    return Grids(y_vec=y_vec, h_vec=h_vec, P_y=P_y, P_h=P_h, P_x=P_x,
                 gdp_vec=gdp_vec, y_vec_2sh=y_vec_2sh, h_vec_2sh=h_vec_2sh,
                 b_vec=b_vec, i_b_zero=i_b_zero, gdp_mean=gdp_mean,
                 qrf=qrf, qrf_lt=qrf_lt)


def autarky_utility(p: Params, g: Grids) -> np.ndarray:
    """Utilidad en exclusion: consumo = min(y*h, wc_par * E[y]) (lineas 245-257).

    Es el costo de default asimetrico de Arellano (2008): el tope solo muerde en
    realizaciones altas del ingreso.
    """
    c_aut = g.gdp_vec.copy()
    tope = p.wc_par_asymm * g.gdp_mean
    c_aut[c_aut > tope] = tope
    return c_aut ** (1 - p.gamma_c) / (1 - p.gamma_c)
