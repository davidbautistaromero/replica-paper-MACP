"""Verificaciones estaticas: no resuelven el modelo, tardan segundos.

Contestan las preguntas que uno no quiere descubrir dos horas despues de lanzar
una corrida:

* ¿la configuracion es coherente (perfiles, motores, especificaciones, paises)?
* ¿los parches siguen calzando contra el codigo del autor, en todos los perfiles?
* ¿el codigo parchado queda sin las llamadas rotas del paquete original?
* ¿la calibracion que lee el port coincide con la del codigo de MATLAB?

    python tests/test_static.py          # directo
    pytest tests/test_static.py          # si alguien prefiere pytest
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "python"))

import common  # noqa: E402
import patch_vendor as pv  # noqa: E402
from model.calibration import build_params  # noqa: E402

PERFILES = ["paper", "paper_memlite", "paper_cmp", "smoke", "smoke_memlite", "smoke_cmp"]
CLAVES_PERFIL = {"N_y", "N_h", "N_b_g", "T_sim", "maxiter_q", "tol_q",
                 "memlite", "shared_shocks", "reportable"}


def _sin_comentarios(texto: str) -> str:
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("%"))


def test_config_coherente():
    cfg = common.load_config()
    assert set(common.profile_names(cfg)) == set(PERFILES)
    for nombre in PERFILES:
        prof = common.resolve_profile(cfg, nombre)
        assert CLAVES_PERFIL <= set(prof), (nombre, CLAVES_PERFIL - set(prof))
    for spec_name, spec in common.specs_only(cfg).items():
        assert (common.VENDOR_DIR / spec["vendor_file"]).exists(), spec_name
        assert {"cc_freq", "cc_int", "panel", "mat_file", "inherits_gdp_mean"} <= set(spec)
    # el mapa de momentos debe cubrir las filas de los dos paneles
    paneles = {p for meta in cfg["moments"].values() if isinstance(meta, dict)
               for p in meta["in_panels"]}
    assert paneles == {"B", "C"}
    for archivo in ("table2_mallucci2022_jie.csv", "table2_mallucci2020_ifdp.csv",
                    "table1_calibration_vendor_code.csv"):
        assert (common.TARGETS_DIR / archivo).exists(), archivo


def test_parches_calzan_en_todos_los_perfiles():
    cfg = common.load_config()
    counters = common.resolve_countries(cfg, "entrega1")
    lista = "[" + " ".join(str(c) for c in counters) + "]"

    for nombre in PERFILES:
        prof = common.resolve_profile(cfg, nombre)
        for spec_name, spec in common.specs_only(cfg).items():
            texto = (common.VENDOR_DIR / spec["vendor_file"]).read_text(
                encoding="utf-8", errors="surrogateescape")
            reglas = [pv._rule_countries(counters), pv._rule_seed(cfg["seed"]),
                      *pv._rules_grid(prof), pv._rule_last_save(spec["mat_file"]),
                      *pv.EXTRA_RULES.get(spec_name, [])]
            if prof["shared_shocks"]:
                reglas += pv._rules_shared_shocks(nombre, spec_name)
            if prof["memlite"]:
                reglas += pv._rules_memlite()

            # apply_rule levanta SystemExit si el conteo de coincidencias no calza
            for regla in reglas:
                texto = pv.apply_rule(texto, regla, spec["vendor_file"])
            codigo = _sin_comentarios(texto)

            # los dos errores del paquete quedan corregidos
            assert "'climate_persistent_wf_new'" not in codigo
            assert "lg.V_g_mean_counter_rn" not in codigo
            # el perfil se aplico de verdad
            assert f"N_b_g       = {prof['N_b_g']};" in codigo, (nombre, "N_b_g")
            assert f"T_sim = {prof['T_sim']};" in codigo, (nombre, "T_sim")
            assert f"for counter= {lista}" in codigo, (nombre, "paises")
            # memlite y sorteos compartidos son excluyentes con lo que reemplazan
            assert ("dist_sim" in codigo) != prof["memlite"], (nombre, spec_name)
            assert ("rand(" in codigo) != prof["shared_shocks"], (nombre, spec_name)
            if prof["shared_shocks"]:
                assert f"'shocks','{nombre}','shocks.mat'" in codigo
                assert "shocks_X(:,counter)" in codigo


def test_calibracion_del_port():
    """Contraste puntual contra los valores escritos en el codigo del autor."""
    cfg = common.load_config()
    spec_b = common.specs_only(cfg)["panelB_hurricane"]
    spec_c = common.specs_only(cfg)["panelC_no_hurricane"]
    prof = common.resolve_profile(cfg, "paper_memlite")

    esperado = {                    # counter: (beta, rho_y, delta, p_hu, mu_h)
        1: (0.915, 0.92, 0.0824, 0.103, 0.049),
        4: (0.895, 0.88, 0.1731, 0.051, 0.040),
        5: (0.910, 0.91, 0.0612, 0.051, 0.070),
        7: (0.930, 0.96, 0.0564, 0.103, 0.023),
    }
    for counter, (beta, rho, delta, p_hu, mu_h) in esperado.items():
        p = build_params(counter, spec_b, prof)
        assert (p.beta, p.rho_y, p.delta, p.p_hu, p.mu_h) == (beta, rho, delta, p_hu, mu_h)
        assert p.N_x == prof["N_y"] * prof["N_h"]
        # el Panel C apaga el riesgo: p_h = 0 y sin dano
        pc = build_params(counter, spec_c, prof)
        assert pc.p_hu == 0.0 and pc.mean_h == 1.0


if __name__ == "__main__":
    fallos = 0
    for nombre, fn in sorted(globals().items()):
        if not nombre.startswith("test_"):
            continue
        try:
            fn()
            print(f"  [OK]    {nombre}")
        except Exception as exc:  # noqa: BLE001
            fallos += 1
            print(f"  [FALLA] {nombre}: {exc}")
    print("\nsin fallas" if not fallos else f"\n{fallos} verificacion(es) fallaron")
    sys.exit(1 if fallos else 0)
