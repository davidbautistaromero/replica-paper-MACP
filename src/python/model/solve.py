"""Iteracion de funcion de valor y precio del bono.

Port de climate_persistent_wf.m:350-465. Estructura identica: un loop externo
sobre el precio de la deuda `q` y uno interno sobre la funcion de valor, ambos
con amortiguamiento de 0.8 y los mismos criterios de parada.

Dos expresiones se implementan con su version numericamente estable
(`expit`, `logaddexp`, softmax normalizado). Son la *misma* formula: el codigo
del autor hace lo propio a mano, normalizando por el maximo y eligiendo entre
dos formas algebraicamente equivalentes segun si la probabilidad de default
supera 0.999. Ver comentarios marcados `# equivalencia:`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import expit

from .calibration import Params
from .grids import Grids


@dataclass
class Solution:
    q_g: np.ndarray          # (N_x, N_b) precio del bono por estado y deuda emitida
    q_g_pf: np.ndarray       # (N_x, N_b) precio esperado dada la politica de emision
    prob_choice: np.ndarray  # (N_x, N_b, N_b) probabilidades de eleccion de b'
    def_pf: np.ndarray       # (N_x, N_b) probabilidad de default
    v: np.ndarray            # (N_x, N_b)
    v_bad: np.ndarray        # (N_x,)
    iter_q: int
    diff_q: float
    iter_v_ultimo: int
    diff_v_ultimo: float
    tol_q: float = 1e-6
    maxiter_q: int = 600

    @property
    def converged(self) -> bool:
        """El original para por tolerancia O por iteraciones, sin avisar cual."""
        return self.diff_q <= self.tol_q


def solve(p: Params, g: Grids, util_aut: np.ndarray, verbose: bool = True) -> Solution:
    N_x, N_b = p.N_x, p.N_b_g
    eps = np.finfo(float).eps
    ev_rho, gamma, beta, lam, delta = p.ev_rho, p.gamma_c, p.beta, p.lambda_, p.delta

    # Un unico buffer 3D (x, b, b'): en el perfil del paper son 227 MB. Se
    # reutiliza para consumo -> utilidad -> maximando -> probabilidades.
    buf = np.empty((N_x, N_b, N_b))
    b_state = g.b_vec[None, :, None]     # deuda heredada
    b_choice = g.b_vec[None, None, :]    # deuda emitida
    hy = g.gdp_vec[:, None, None]        # ingreso tras huracan
    compra_activos = g.b_vec <= 0

    q_g = np.full((N_x, N_b), g.qrf_lt)
    v = np.zeros((N_x, N_b))
    v_bad = np.zeros(N_x)
    def_new = np.zeros((N_x, N_b))

    iter_q, diff_q = 1, 7.0
    iter_v, diff_v = 1, 7.0

    while diff_q > p.tol_q and iter_q < p.maxiter_q:
        iter_v, diff_v = 1, 7.0
        while diff_v > p.tol_v and iter_v < p.maxiter_v:
            e_v = g.P_x @ v                                  # continuacion esperada

            # restriccion de recursos: c = y*h - b + q(b')*(b' - (1-delta)b)
            np.multiply(q_g[:, None, :], b_choice - (1 - delta) * b_state, out=buf)
            buf += hy - b_state
            np.maximum(buf, eps, out=buf)

            # utilidad CRRA, en el mismo buffer
            np.power(buf, 1 - gamma, out=buf)
            buf /= (1 - gamma)
            buf += beta * e_v[:, None, :]                    # maximando en b'

            v_noev = buf.max(axis=2)

            # equivalencia: el autor normaliza por el maximo y aplica
            # exp/sum; esto es exactamente un softmax sobre b'.
            buf -= v_noev[:, :, None]
            buf /= ev_rho
            np.exp(buf, out=buf)
            suma = buf.sum(axis=2)
            v_good = p.eulgam * ev_rho + v_noev + ev_rho * np.log(suma)
            buf /= suma[:, :, None]                          # buf = prob_choice

            # valor en exclusion financiera
            v_bad_new = util_aut + beta * (
                lam * (g.P_x @ v[:, g.i_b_zero]) + (1 - lam) * (g.P_x @ v_bad))

            # equivalencia: 1-(exp((v_bad-v_good)/rho)+1)^-1 == expit(...)
            def_new = expit((v_bad_new[:, None] - v_good) / ev_rho)

            # equivalencia: las dos ramas del original (normalizar por v_good o
            # por v_bad segun def>0.999) son log-sum-exp de dos terminos.
            v_new = p.eulgam * ev_rho + ev_rho * np.logaddexp(
                v_good / ev_rho, v_bad_new[:, None] / ev_rho)

            diff_v = float(np.abs(v_new - v).max())
            v = p.damp_v * v_new + (1 - p.damp_v) * v
            v_bad = p.damp_v * v_bad_new + (1 - p.damp_v) * v_bad
            iter_v += 1

        prob_choice = buf
        q_g_pf = np.einsum("xp,xbp->xb", q_g, prob_choice, optimize=True)

        # precio del bono: paga el cupon si no hay default, y el resto de la
        # deuda de largo plazo se revalora al precio de continuacion
        e_def = g.P_x @ def_new
        e_deflong = g.P_x @ ((1 - def_new) * q_g_pf)
        q_new = g.qrf * (1 - e_def) + (1 - delta) * g.qrf * e_deflong
        np.maximum(q_new, 0.0, out=q_new)
        q_new[:, compra_activos] = g.qrf_lt                  # ahorro a tasa libre de riesgo

        diff_q = float(np.abs(q_new - q_g).max())
        q_g = p.damp_q * q_new + (1 - p.damp_q) * q_g
        iter_q += 1

        if verbose and (iter_q % 25 == 0 or diff_q <= p.tol_q):
            print(f"      iter_q={iter_q - 1:4d}  diff_q={diff_q:.3e}  "
                  f"(iter_v={iter_v - 1}, diff_v={diff_v:.3e})", flush=True)

    return Solution(q_g=q_g, q_g_pf=q_g_pf, prob_choice=prob_choice, def_pf=def_new,
                    v=v, v_bad=v_bad, iter_q=iter_q - 1, diff_q=diff_q,
                    iter_v_ultimo=iter_v - 1, diff_v_ultimo=diff_v,
                    tol_q=p.tol_q, maxiter_q=p.maxiter_q)
