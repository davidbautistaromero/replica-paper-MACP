"""Etapa 2 - Genera copias parchadas del codigo del autor.

Por que existe esta etapa
-------------------------
El paquete de Mallucci (2022) no se puede correr tal cual en este proyecto por
cuatro razones, y las cuatro se resuelven aqui *sin tocar el original*:

1. `for counter = 1:7` recorre los siete paises. La replica solo necesita
   cuatro (Antigua y Barbuda, Republica Dominicana, Granada y Jamaica);
   cada pais de mas son horas de VFI.
2. Las grillas estan fijas en el codigo. Para validar el pipeline de punta a
   punta hace falta un perfil de prueba con grillas gruesas ("smoke").
3. Las simulaciones usan `rand` sin semilla: dos corridas del mismo codigo dan
   numeros distintos. Se inyecta `rng(seed + 100*counter)` para que cada pais
   sea reproducible e independiente del conjunto de paises que se corra.
4. Dos errores de empaquetado del autor:
   a. `climate_persistent_nh_wf.m` hace `load('climate_persistent_wf_new')`,
      un archivo que ningun script del paquete produce (el baseline guarda
      `climate_persistent_wf.mat`). Tal cual, `Main.m` falla en el paso 2.
   b. Del mismo archivo lee `V_g_mean_counter_rn`, una variable que el baseline
      nunca calcula (no existe bloque "risk neutral" en el baseline). Se
      reemplaza por NaN: solo afecta el estadistico de bienestar equivalente,
      que no forma parte de la Tabla 2.
   c. El `save` posterior al loop sobreescribe el .mat con menos variables de
      las que el Panel C necesita leer del baseline. Se renombra ese ultimo
      save a `*_final.mat` para conservar el .mat completo.

Cada regla se aplica con conteo esperado: si el archivo del autor cambiara, la
etapa falla en vez de generar codigo silenciosamente distinto. El diff completo
queda en build/matlab/<perfil>/patches/ para poder auditarlo o anexarlo.

    python src/python/patch_vendor.py --profile paper_memlite --countries entrega1
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys

from common import (
    ROOT, TARGETS_DIR, VENDOR_DIR, specs_only, build_dir, ensure_dirs, load_config, log, resolve_countries,
    resolve_profile, sha256, write_manifest,
)

SHIMS_DIR = ROOT / "src" / "matlab" / "shims"

HEADER = """% ============================================================================
% ARCHIVO GENERADO - NO EDITAR A MANO
% Origen : src/matlab/vendor/{src}
% Parches: src/python/patch_vendor.py  (perfil={profile}, paises={countries})
% Semilla: {seed}
% El diff contra el original esta en patches/{src}.diff
% ============================================================================
"""


def _rule_countries(counters: list[int]) -> dict:
    lst = "[" + " ".join(str(c) for c in counters) + "]"
    return {
        "nombre": "subconjunto de paises",
        "pattern": r"(?m)^(\s*for counter=\s*)1:7\s*$",
        "repl": lambda m: f"{m.group(1)}{lst}",
        "count": 1,
    }


def _rule_seed(seed: int) -> dict:
    # Toda la aleatoriedad (sendero de ingreso y sorteos de readmision) se
    # consume despues de la linea `T=P_x;`, asi que sembrar ahi hace que cada
    # pais sea reproducible por separado.
    return {
        "nombre": "semilla por pais",
        "pattern": r"(?m)^T=P_x;",
        "repl": lambda m: f"rng({seed} + 100*counter, 'twister');\nT=P_x;",
        "count": 1,
    }


def _rules_grid(prof: dict) -> list[dict]:
    rules = []
    for var in ("N_y", "N_h", "N_b_g", "T_sim", "maxiter_q"):
        rules.append({
            "nombre": f"grilla {var}={prof[var]}",
            "pattern": rf"(?m)^({var}\s*=\s*)\d+",
            "repl": (lambda v: (lambda m: f"{m.group(1)}{v}"))(prof[var]),
            "count": 1,
        })
    rules.append({
        "nombre": f"tolerancia tol_q={prof['tol_q']}",
        "pattern": r"(?m)^(tol_q\s*=\s*)[0-9.eE+-]+",
        "repl": (lambda v: (lambda m: f"{m.group(1)}{v}"))(prof["tol_q"]),
        "count": 1,
    })
    return rules


def _rule_last_save(mat_name: str) -> dict:
    """Renombra SOLO el ultimo save (el posterior al loop) a *_final.mat."""
    stem = mat_name[:-4]
    return {
        "nombre": f"ultimo save -> {stem}_final.mat",
        "pattern": rf"save\('{re.escape(stem)}\.mat'\)",
        "repl": f"save('{stem}_final.mat')",
        "count": "last",
    }


def _rules_shared_shocks(profile: str, spec_name: str) -> list[dict]:
    """Hace que MATLAB lea los sorteos de build/shocks/<perfil>/shocks.mat.

    Sin esto, MATLAB y Python generan secuencias distintas (siembran el Mersenne
    Twister de forma diferente) y la comparacion entre motores mediria ruido de
    Monte Carlo en vez de equivalencia. Ver src/python/make_shocks.py.
    """
    ruta = f"fullfile('..','..','shocks','{profile}','shocks.mat')"
    rules = [
        {
            "nombre": "sorteos compartidos: carga del archivo",
            "pattern": r"(?m)^T=P_x;",
            "repl": (f"load({ruta}); % PARCHE sorteos compartidos\n"
                     "T=P_x;"),
            "count": 1,
        },
        {
            "nombre": "sorteos compartidos: sendero de la cadena",
            "pattern": r"X=rand\(n-1,1\);",
            "repl": "X = shocks_X(:,counter); % PARCHE sorteos compartidos",
            "count": 1,
        },
    ]
    if spec_name == "panelB_hurricane":
        # El Panel C no sortea readmision: la hereda del .mat del Panel B.
        rules.append({
            "nombre": "sorteos compartidos: readmision",
            "pattern": r"redem_sim = \(rand\(T_sim\+1,1\)<lambda\);",
            "repl": "redem_sim = (shocks_U(:,counter) < lambda); % PARCHE sorteos compartidos",
            "count": 1,
        })
    return rules


def _rules_calibration(prof: dict) -> list[dict]:
    """Sustituye beta y el costo de default por los de la Tabla 1 publicada.

    Solo se usa en perfiles con calibration='published', que son
    CONTRAFACTUALES: sirven para contrastar la discrepancia entre el articulo y
    su propio codigo, no para la replica. Hoy la diferencia es unicamente en
    Republica Dominicana (articulo: beta=0.88 y costo 0.895; codigo: 0.895 y
    0.8175), pero las reglas se generan comparando los dos CSV, asi que si
    apareciera otra diferencia se aplicaria sola.

    Las lineas se localizan por el valor del codigo, y apply_rule exige una sola
    coincidencia: si el valor dejara de ser unico en el archivo, la etapa falla
    en vez de parchar el pais equivocado.
    """
    if prof.get("calibration", "vendor") != "published":
        return []

    import csv

    def leer(nombre):
        with open(TARGETS_DIR / nombre, encoding="utf-8") as fh:
            return {r["iso3"]: r for r in csv.DictReader(
                l for l in fh if not l.startswith("#"))}

    codigo, articulo = leer("table1_calibration_vendor_code.csv"), leer(
        "table1_mallucci2022_jie_published.csv")
    pares = [("beta", "beta", "beta"),
             ("output_cost_frac", "output_cost", "wc_par_asymm")]

    reglas = []
    for iso, fila in codigo.items():
        for col_cod, col_art, var_matlab in pares:
            viejo, nuevo_valor = float(fila[col_cod]), float(articulo[iso][col_art])
            if abs(viejo - nuevo_valor) < 1e-12:
                continue
            decimales = f"{viejo:.10f}".rstrip("0").split(".")[1]
            reglas.append({
                "nombre": f"calibracion publicada: {iso} {var_matlab} {viejo} -> {nuevo_valor}",
                "pattern": rf"(?m)^({var_matlab}\s*=\s*)0*\.{decimales};",
                "repl": (lambda v: (lambda m: f"{m.group(1)}{v}; % PARCHE calibracion publicada"))(nuevo_valor),
                "count": 1,
            })
    return reglas


def _rules_memlite() -> list[dict]:
    """Simulacion con dos rebanadas de la distribucion en vez de T_sim+1.

    El autor guarda la distribucion completa: dist_sim = zeros(N_x,N_b_g,T_sim+1).
    Con las grillas del paper eso son 1260*150*10001 doubles = 15.1 GB, mas de lo
    que tiene un portatil. dist_sim solo se usa dentro del loop de simulacion
    (rebanadas t y t+1, verificado en el codigo), asi que mantener dos matrices
    N_x x N_b_g es algebraicamente identico y baja la memoria a ~1.5 MB.

    Equivalencia verificada corriendo los perfiles smoke y smoke_memlite y
    comparando momento a momento (ver docs/00_pipeline.md).
    """
    return [
        {
            "nombre": "memlite: dos rebanadas en vez de T_sim+1",
            "pattern": r"dist_sim = zeros\(N_x,N_b_g,T_sim\+1\);",
            "repl": ("dist_cur = zeros(N_x,N_b_g); dist_next = zeros(N_x,N_b_g); "
                     "% PARCHE memlite"),
            "count": 1,
        },
        {
            "nombre": "memlite: condicion inicial",
            "pattern": r"dist_sim\(i_x_sim\(1,1\),i_b_g_zero,1\) = 1;",
            "repl": "dist_cur(i_x_sim(1,1),i_b_g_zero) = 1; % PARCHE memlite",
            "count": 1,
        },
        {
            "nombre": "memlite: rotacion de rebanadas al inicio del loop",
            "pattern": r"(?m)^for t_sim = 1:T_sim1",
            "repl": ("for t_sim = 1:T_sim1\n"
                     "    if t_sim>1, dist_cur = dist_next; end % PARCHE memlite\n"
                     "    dist_next(:) = 0;                     % PARCHE memlite"),
            "count": 1,
        },
        {
            "nombre": "memlite: escrituras en t+1",
            "pattern": r"dist_sim\(([^;]*?),:,t_sim\+1\)",
            "repl": r"dist_next(\1,:)",
            "count": 1,
        },
        {
            "nombre": "memlite: escritura en autarquia",
            "pattern": r"dist_sim\(i_x_sim\(t_sim\+1,1\),i_b_g_zero,t_sim\+1\) = 1;",
            "repl": "dist_next(i_x_sim(t_sim+1,1),i_b_g_zero) = 1; % PARCHE memlite",
            "count": 1,
        },
        {
            "nombre": "memlite: lecturas en t",
            "pattern": r"dist_sim\(:,:,t_sim\)",
            "repl": "dist_cur",
            "count": "all",
        },
    ]


# Parches propios de cada especificacion, ademas de los comunes.
EXTRA_RULES: dict[str, list[dict]] = {
    "panelC_no_hurricane": [
        {
            "nombre": "fix: nombre del .mat del baseline",
            "pattern": r"filename_guess = 'climate_persistent_wf_new';",
            "repl": "filename_guess = 'climate_persistent_wf'; % PARCHE: el paquete no genera '*_new'",
            "count": 1,
        },
        {
            "nombre": "fix: V_g_mean_counter_rn inexistente -> NaN",
            "pattern": r"V_g_mean_baseline_rn\s*=\s*lg\.V_g_mean_counter_rn\(:,counter\);",
            "repl": ("V_g_mean_baseline_rn  = NaN(size(V_g_mean_baseline)); "
                     "% PARCHE: el baseline no calcula la version risk-neutral; "
                     "solo afecta el bienestar equivalente, no la Tabla 2"),
            "count": 1,
        },
    ],
}


def apply_rule(text: str, rule: dict, src_name: str) -> str:
    pattern, repl, count = rule["pattern"], rule["repl"], rule["count"]
    hits = list(re.finditer(pattern, text))
    if count in ("last", "all") and not hits:
        raise SystemExit(f"[{src_name}] la regla '{rule['nombre']}' no encontro coincidencias")
    if count == "last":
        m = hits[-1]
        new = repl(m) if callable(repl) else repl
        return text[:m.start()] + new + text[m.end():]
    if count == "all":
        return re.sub(pattern, repl, text)
    if len(hits) != count:
        raise SystemExit(
            f"[{src_name}] la regla '{rule['nombre']}' esperaba {count} coincidencia(s) "
            f"y encontro {len(hits)}. El codigo del autor cambio: revise el parche."
        )
    return re.sub(pattern, repl, text, count=count)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="paper")
    ap.add_argument("--countries", default="entrega1")
    ap.add_argument("--tag", default="", help="directorio de trabajo aparte, para correr en paralelo")
    args = ap.parse_args()

    cfg = load_config()
    prof = resolve_profile(cfg, args.profile)
    counters = resolve_countries(cfg, args.countries)
    seed = cfg["seed"]

    bdir = build_dir(args.profile, args.tag)
    pdir = bdir / "patches"
    ensure_dirs(bdir, pdir)

    # Shims de compatibilidad: nanmean/nanmedian salieron del MATLAB base. Se
    # copian al directorio de trabajo en vez de reescribir 246 llamadas del autor
    # (MATLAB resuelve primero las funciones del cwd).
    shims = sorted(SHIMS_DIR.glob("*.m"))
    for shim in shims:
        (bdir / shim.name).write_text(shim.read_text(encoding="utf-8"), encoding="utf-8")
    log(f"shims copiados: {[s.name for s in shims]}")

    registro = {}
    for spec_name, spec in specs_only(cfg).items():
        src = VENDOR_DIR / spec["vendor_file"]
        if not src.exists():
            raise SystemExit(f"Falta el codigo del autor: {src}. Corra la etapa 0 (fetch_sources.py).")
        original = src.read_text(encoding="utf-8", errors="surrogateescape")

        rules = [_rule_countries(counters), _rule_seed(seed), *_rules_grid(prof),
                 _rule_last_save(spec["mat_file"]), *EXTRA_RULES.get(spec_name, [])]
        rules += _rules_calibration(prof)
        if prof.get("shared_shocks", False):
            rules += _rules_shared_shocks(args.profile, spec_name)
        if prof.get("memlite", False):
            rules += _rules_memlite()

        text = original
        for rule in rules:
            text = apply_rule(text, rule, spec["vendor_file"])

        text = HEADER.format(src=spec["vendor_file"], profile=args.profile,
                             countries=counters, seed=seed) + text

        dest = bdir / spec["vendor_file"]
        dest.write_text(text, encoding="utf-8", errors="surrogateescape")

        diff = "".join(difflib.unified_diff(
            original.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile=f"vendor/{spec['vendor_file']}", tofile=f"build/{spec['vendor_file']}",
        ))
        (pdir / f"{spec['vendor_file']}.diff").write_text(diff, encoding="utf-8")

        registro[spec_name] = {
            "archivo_autor": spec["vendor_file"],
            "sha256_autor": sha256(src),
            "sha256_parchado": sha256(dest),
            "reglas": [r["nombre"] for r in rules],
        }
        log(f"{spec_name}: {len(rules)} parches -> {dest.relative_to(bdir.parents[2])}")

    write_manifest(f"patch_{args.profile}" + (f"_{args.tag}" if args.tag else ""), {
        "etapa": "2_patch_vendor",
        "perfil": args.profile,
        "grillas": {k: v for k, v in prof.items() if not k.startswith("_")},
        "paises_counter": counters,
        "semilla": seed,
        "shims": [s.name for s in shims],
        "especificaciones": registro,
    })
    log(f"diffs auditables en {pdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
