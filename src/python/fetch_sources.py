"""Etapa 0 - Descarga y verificacion de las fuentes primarias.

Descarga (si faltan) el paquete de replica de Mendeley y el working paper del
Federal Reserve Board, verifica los hashes contra data/raw/checksums.sha256 y
deja el codigo del autor en src/matlab/vendor/.

Es idempotente: si los archivos ya estan y el hash coincide, no hace nada.

    python src/python/fetch_sources.py [--force]
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
import zipfile
from pathlib import Path

from common import ROOT, VENDOR_DIR, ensure_dirs, log, sha256

RAW_DIR = ROOT / "data" / "raw"
PAPER_DIR = ROOT / "paper"

SOURCES = {
    # Paquete de replica oficial: https://data.mendeley.com/datasets/kcty2wvw4d/1
    RAW_DIR / "mallucci2022_replication_mendeley_v1.zip": (
        "https://data.mendeley.com/public-files/datasets/kcty2wvw4d/files/"
        "802ac0f6-162b-42aa-98ed-6c01b8cc4ee9/file_downloaded"
    ),
    # Working paper de acceso abierto (IFDP 1291, julio 2020)
    PAPER_DIR / "mallucci2020_ifdp1291_working_paper.pdf": (
        "https://www.federalreserve.gov/econres/ifdp/files/ifdp1291.pdf"
    ),
}

CHECKSUMS = RAW_DIR / "checksums.sha256"


def read_checksums() -> dict[str, str]:
    """Lee checksums.sha256 (formato de sha256sum) -> {nombre: hash}."""
    if not CHECKSUMS.exists():
        return {}
    out = {}
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, name = line.split(None, 1)
        out[name.lstrip("*").strip()] = digest
    return out


def download(url: str, dest: Path) -> None:
    ensure_dirs(dest.parent)
    log(f"descargando {dest.name}")
    with urllib.request.urlopen(url, timeout=180) as resp, open(dest, "wb") as fh:
        fh.write(resp.read())


def unzip_vendor(zip_path: Path) -> int:
    """Extrae los .m y el ReadMe del paquete a src/matlab/vendor/."""
    ensure_dirs(VENDOR_DIR)
    n = 0
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            name = Path(member).name
            if not name or not name.lower().endswith((".m", ".pdf")):
                continue
            target = VENDOR_DIR / name if name.endswith(".m") else PAPER_DIR / "mallucci2022_replication_readme.pdf"
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="vuelve a descargar aunque exista")
    args = ap.parse_args()

    expected = read_checksums()
    problems: list[str] = []

    for dest, url in SOURCES.items():
        if args.force or not dest.exists():
            download(url, dest)
        digest = sha256(dest)
        want = expected.get(dest.name)
        if want is None:
            log(f"AVISO {dest.name}: sin hash de referencia, lo registro ({digest[:12]}...)")
            with open(CHECKSUMS, "a", encoding="utf-8") as fh:
                fh.write(f"{digest} *{dest.name}\n")
        elif digest != want:
            problems.append(f"{dest.name}: hash {digest[:12]}... != esperado {want[:12]}...")
        else:
            log(f"ok {dest.name} (hash verificado)")

    if problems:
        for p in problems:
            log(f"ERROR {p}")
        log("Si la fuente cambio legitimamente, actualice data/raw/checksums.sha256 "
            "y registrelo en docs/02_bitacora.md.")
        return 1

    zip_path = next(p for p in SOURCES if p.suffix == ".zip")
    n = unzip_vendor(zip_path)
    log(f"codigo del autor extraido en src/matlab/vendor/ ({n} archivos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
