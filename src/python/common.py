"""Rutas, configuracion y utilidades compartidas por el pipeline de replica.

Regla de oro del proyecto: `src/matlab/vendor/` es codigo de terceros y no se
edita nunca. Todo lo que este modulo hace es resolver rutas y leer
`config/specs.json`, de modo que ninguna ruta quede escrita a mano en los scripts.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = ROOT / "config"
VENDOR_DIR = ROOT / "src" / "matlab" / "vendor"
BUILD_DIR = ROOT / "build" / "matlab"
TARGETS_DIR = ROOT / "data" / "targets"
OUT_RAW_MAT = ROOT / "outputs" / "raw_mat"
OUT_MOMENTS = ROOT / "outputs" / "moments"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGURES = ROOT / "outputs" / "figures"
OUT_LOGS = ROOT / "outputs" / "logs"


# --------------------------------------------------------------------------- #
# Configuracion
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    """Devuelve config/specs.json como diccionario."""
    with open(CONFIG_DIR / "specs.json", encoding="utf-8") as fh:
        return json.load(fh)


def load_countries() -> dict[int, dict[str, str]]:
    """Mapa counter (indice del loop del autor) -> metadatos del pais."""
    out: dict[int, dict[str, str]] = {}
    with open(CONFIG_DIR / "countries.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out[int(row["counter"])] = row
    return out


def profile_names(cfg: dict) -> list[str]:
    return [k for k, v in cfg["profiles"].items() if isinstance(v, dict)]


def resolve_profile(cfg: dict, name: str) -> dict:
    if name not in profile_names(cfg):
        raise SystemExit(f"Perfil desconocido: {name}. Opciones: {profile_names(cfg)}")
    return cfg["profiles"][name]


def country_set_names(cfg: dict) -> list[str]:
    return [k for k, v in cfg["country_sets"].items() if isinstance(v, list)]


def resolve_countries(cfg: dict, name_or_list: str) -> list[int]:
    """Acepta el nombre de un country_set o una lista tipo '4,7'."""
    if name_or_list in country_set_names(cfg):
        return list(cfg["country_sets"][name_or_list])
    try:
        return [int(x) for x in str(name_or_list).replace(" ", "").split(",") if x]
    except ValueError:
        raise SystemExit(f"No pude interpretar el conjunto de paises: {name_or_list!r}")


def specs_only(cfg: dict) -> dict[str, dict]:
    """Las especificaciones reales, sin las claves de documentacion."""
    return {k: v for k, v in cfg["specs"].items() if isinstance(v, dict)}


def spec_order(cfg: dict) -> list[str]:
    """Especificaciones ordenadas respetando `depends_on` (orden topologico simple)."""
    specs = specs_only(cfg)
    done: list[str] = []
    pending = list(specs)
    while pending:
        progress = False
        for name in list(pending):
            if all(dep in done for dep in specs[name].get("depends_on", [])):
                done.append(name)
                pending.remove(name)
                progress = True
        if not progress:
            raise SystemExit(f"Dependencias circulares en specs: {pending}")
    return done


# --------------------------------------------------------------------------- #
# Rutas derivadas del perfil
# --------------------------------------------------------------------------- #
def build_dir(profile: str, tag_run: str = "") -> Path:
    """Directorio de trabajo de MATLAB para un perfil.

    `tag_run` aisla corridas concurrentes del mismo perfil. Hace falta porque los
    scripts del autor guardan sus .mat en el directorio de trabajo con nombre
    fijo: dos procesos en la misma carpeta se sobreescriben los artefactos y el
    Panel C terminaria leyendo el E[y] y los sorteos del pais equivocado.
    """
    return BUILD_DIR / (f"{profile}__{tag_run}" if tag_run else profile)


def shocks_dir(profile: str) -> Path:
    """Sorteos aleatorios compartidos entre motores, por perfil."""
    return ROOT / "build" / "shocks" / profile


def raw_mat_dir(profile: str) -> Path:
    return OUT_RAW_MAT / profile


# --------------------------------------------------------------------------- #
# Motores (matlab / python)
# --------------------------------------------------------------------------- #
def resolve_engine(cfg: dict, name: str) -> dict:
    engines = {k: v for k, v in cfg["engines"].items() if isinstance(v, dict)}
    if name not in engines:
        raise SystemExit(f"Motor desconocido: {name}. Opciones: {list(engines)}")
    return engines[name]


def raw_dir(cfg: dict, profile: str, engine: str) -> Path:
    """Donde cada motor deja su salida cruda (.mat o .npz)."""
    return ROOT / "outputs" / resolve_engine(cfg, engine)["raw_dir"] / profile


def raw_path(cfg: dict, profile: str, engine: str, spec_name: str,
             tag_run: str = "") -> Path:
    ext = resolve_engine(cfg, engine)["ext"]
    sufijo = f"__{tag_run}" if tag_run else ""
    return raw_dir(cfg, profile, engine) / f"{spec_name}{sufijo}{ext}"


def raw_paths(cfg: dict, profile: str, engine: str, spec_name: str) -> list[Path]:
    """Todas las salidas de una especificacion: la corrida completa y las
    parciales por etiqueta. Se juntan en la extraccion, porque cada una trae
    solo las filas de sus paises."""
    ext = resolve_engine(cfg, engine)["ext"]
    d = raw_dir(cfg, profile, engine)
    if not d.exists():
        return []
    return sorted(p for p in d.iterdir()
                  if p.suffix == ext and (p.stem == spec_name
                                          or p.stem.startswith(f"{spec_name}__")))


def tag(profile: str, engine: str) -> str:
    """Sufijo comun de los archivos de salida: perfil + motor."""
    return f"{profile}_{engine}"


def moments_only(cfg: dict) -> dict[str, dict]:
    return {k: v for k, v in cfg["moments"].items() if isinstance(v, dict)}


def expected_missing(cfg: dict, engine: str | None = None) -> set[tuple[str, str]]:
    """Celdas (momento, panel) que un motor no calcula, y no por error.

    El script sin huracanes del autor, por ejemplo, nunca asigna
    medianspread_sim: el paper reporta ese numero pero su codigo no lo produce.
    Con engine=None devuelve las celdas que le faltan a cualquiera de los dos.
    """
    faltan = set()
    for mom, meta in moments_only(cfg).items():
        for motor, paneles in meta.get("no_calculado", {}).items():
            if engine is None or motor == engine:
                faltan.update((mom, p) for p in paneles)
    return faltan


def ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Procedencia / trazabilidad
# --------------------------------------------------------------------------- #
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def matlab_version(matlab_exe: str) -> str:
    """Version de MATLAB, o 'desconocida' si no se puede invocar."""
    try:
        res = subprocess.run(
            [matlab_exe, "-batch", "disp(version)"],
            capture_output=True, text=True, timeout=180,
        )
        return res.stdout.strip().splitlines()[-1] if res.stdout.strip() else "desconocida"
    except Exception:
        return "desconocida"


def write_manifest(name: str, payload: dict) -> Path:
    """Guarda un manifiesto de corrida en outputs/logs/ (una corrida = un archivo)."""
    ensure_dirs(OUT_LOGS)
    payload = {
        "escrito_utc": utc_now(),
        "host": platform.node(),
        "python": platform.python_version(),
        **payload,
    }
    path = OUT_LOGS / f"manifest_{name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path


def log(msg: str) -> None:
    print(f"[{utc_now()}] {msg}", flush=True)
