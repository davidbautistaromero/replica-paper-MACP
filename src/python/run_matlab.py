"""Etapa 3 (motor MATLAB) - Corre el modelo (una especificacion por proceso).

Cada especificacion se ejecuta con `matlab -batch` en su propio proceso y con
directorio de trabajo build/matlab/<perfil>/, porque los scripts del autor
usan `clearvars -except ...` y `save`/`load` relativos al cwd: aislar el
proceso es lo unico que garantiza que un script no contamine al siguiente.

Antes de correr el Panel C se verifica que los artefactos que hereda del Panel B
existan y sean compatibles (mismo T_sim, mismos paises). Es la falla mas
probable del paquete original y conviene detectarla en 2 segundos, no en 2 horas.

    python src/python/run_matlab.py --profile smoke --countries entrega1
    python src/python/run_matlab.py --profile paper_memlite --specs panelB_hurricane
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

from scipy.io import loadmat

from common import (
    OUT_LOGS, build_dir, ensure_dirs, load_config, log, matlab_version, raw_path,
    resolve_countries, resolve_profile, shocks_dir, spec_order, specs_only, utc_now,
    write_manifest,
)


def preflight(spec_name: str, cfg: dict, prof: dict, profile_name: str,
              counters: list[int], bdir: Path) -> None:
    """Chequeos baratos antes de gastar horas de CPU."""
    spec = specs_only(cfg)[spec_name]
    patched = bdir / spec["vendor_file"]
    if not patched.exists():
        raise SystemExit(f"Falta el codigo parchado {patched}. Corra la etapa 2 (patch_vendor.py).")

    if prof.get("shared_shocks", False):
        # El codigo parchado hace load('../../shocks/<perfil>/shocks.mat').
        sh = shocks_dir(profile_name) / "shocks.mat"
        if not sh.exists():
            raise SystemExit(
                f"El perfil '{profile_name}' usa sorteos compartidos y falta {sh}.\n"
                f"Corra: python src/python/make_shocks.py --profile {profile_name}"
            )

    for dep in spec.get("depends_on", []):
        dep_mat = bdir / specs_only(cfg)[dep]["mat_file"]
        if not dep_mat.exists():
            raise SystemExit(
                f"{spec_name} depende de {dep}, pero no existe {dep_mat.name} en {bdir}.\n"
                f"Corra primero: --specs {dep} (con el mismo perfil)."
            )
        # El Panel C lee del baseline: E[y] por pais, sorteos de readmision y
        # valor de referencia. Si el baseline se corrio con otros paises u otro
        # T_sim, el resultado seria basura silenciosa.
        gdp_mat = bdir / "gdp_mean_storemat.mat"
        if not gdp_mat.exists():
            raise SystemExit(f"Falta {gdp_mat.name}: lo produce {dep} dentro de su loop.")
        gdp = loadmat(gdp_mat, variable_names=["gdp_mean_store"])["gdp_mean_store"]
        faltan = [c for c in counters if abs(float(gdp[c - 1, 0])) < 1e-12]
        if faltan:
            raise SystemExit(
                f"gdp_mean_store esta en cero para los paises {faltan}: {dep} no se corrio "
                f"para ellos. Vuelva a correr {dep} con --countries que los incluya."
            )
        md = loadmat(dep_mat, variable_names=["redem_sim_counter"])
        redem = md.get("redem_sim_counter")
        if redem is None:
            raise SystemExit(
                f"{dep_mat.name} no contiene redem_sim_counter. Probablemente se sobreescribio "
                f"con el save posterior al loop; revise el parche 'ultimo save -> *_final.mat'."
            )
        if redem.shape[0] != prof["T_sim"] + 1:
            raise SystemExit(
                f"T_sim incompatible: {dep_mat.name} trae {redem.shape[0] - 1} periodos y el "
                f"perfil pide {prof['T_sim']}. Use el mismo perfil en todas las etapas."
            )
        if redem.shape[1] < max(counters):
            raise SystemExit(f"{dep_mat.name} no tiene columna para el pais {max(counters)}.")


def run_spec(spec_name: str, cfg: dict, prof: dict, profile_name: str,
             counters: list[int], matlab_exe: str, tag_run: str = "") -> dict:
    spec = specs_only(cfg)[spec_name]
    bdir = build_dir(profile_name, tag_run)
    preflight(spec_name, cfg, prof, profile_name, counters, bdir)

    destino = raw_path(cfg, profile_name, 'matlab', spec_name, tag_run)
    ensure_dirs(OUT_LOGS, destino.parent)
    etiqueta = f"_{tag_run}" if tag_run else ""
    log_path = OUT_LOGS / f"matlab_{profile_name}{etiqueta}_{spec_name}.log"

    # -batch: sin escritorio, sin splash, devuelve codigo != 0 si el script falla.
    cmd = [matlab_exe, "-batch", f"run('{spec['vendor_file']}')"]
    log(f"{spec_name}: corriendo {spec['vendor_file']} (perfil={profile_name}, paises={counters})")
    log(f"{spec_name}: log -> {log_path}")

    t0 = time.time()
    with open(log_path, "w", encoding="utf-8", errors="replace") as fh:
        fh.write(f"# {utc_now()} | {' '.join(cmd)} | cwd={bdir}\n")
        fh.flush()
        proc = subprocess.run(cmd, cwd=bdir, stdout=fh, stderr=subprocess.STDOUT, text=True)
    mins = (time.time() - t0) / 60

    if proc.returncode != 0:
        log(f"{spec_name}: MATLAB devolvio {proc.returncode} tras {mins:.1f} min. Ultimas lineas:")
        print("".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines(True)[-25:]))
        raise SystemExit(f"{spec_name} fallo. Revise {log_path}.")

    src_mat = bdir / spec["mat_file"]
    if not src_mat.exists():
        raise SystemExit(f"{spec_name} termino sin producir {spec['mat_file']}. Revise {log_path}.")
    dst_mat = destino
    shutil.copy2(src_mat, dst_mat)

    log(f"{spec_name}: listo en {mins:.1f} min -> {dst_mat}")
    return {
        "especificacion": spec_name,
        "archivo": spec["vendor_file"],
        "minutos": round(mins, 2),
        "mat": str(dst_mat.relative_to(dst_mat.parents[3])),
        "log": str(log_path.relative_to(log_path.parents[2])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", default="paper")
    ap.add_argument("--countries", default="entrega1")
    ap.add_argument("--specs", default="all", help="'all' o nombres separados por coma")
    ap.add_argument("--tag", default="", help="aisla esta corrida de otras del mismo perfil que corran en paralelo")
    args = ap.parse_args()

    cfg = load_config()
    prof = resolve_profile(cfg, args.profile)
    counters = resolve_countries(cfg, args.countries)
    matlab_exe = cfg.get("matlab_exe", "matlab")
    etiqueta = f"_{args.tag}" if args.tag else ""

    todos = spec_order(cfg)
    specs = list(todos) if args.specs == "all" else [s.strip() for s in args.specs.split(",")]
    desconocidas = [s for s in specs if s not in specs_only(cfg)]
    if desconocidas:
        raise SystemExit(f"Especificaciones desconocidas: {desconocidas}. Disponibles: {todos}")
    specs.sort(key=todos.index)  # respeta el orden de dependencias

    if not prof.get("reportable", False):
        log(f"AVISO: el perfil '{args.profile}' no es reportable "
            f"(grillas gruesas). Sirve para validar el pipeline, no para la entrega.")

    corridas = [run_spec(s, cfg, prof, args.profile, counters, matlab_exe, args.tag)
                for s in specs]

    write_manifest(f"run_{args.profile}{etiqueta}_matlab", {
        "etapa": "3_run_matlab",
        "motor": "matlab",
        "perfil": args.profile,
        "etiqueta": args.tag,
        "reportable": prof.get("reportable", False),
        "paises_counter": counters,
        "semilla": cfg["seed"],
        "matlab": matlab_version(matlab_exe),
        "corridas": corridas,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
