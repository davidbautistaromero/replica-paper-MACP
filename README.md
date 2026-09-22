# Réplica: Mallucci (2022), *Natural Disasters, Climate Change, and Sovereign Risk*

Réplica de la **Tabla 2, Paneles B y C** (momentos simulados con y sin riesgo de
huracán) para **Antigua y Barbuda, República Dominicana, Granada y Jamaica**,
con dos motores independientes: el código MATLAB del autor y un port a Python
del equipo.

| | |
|---|---|
| Artículo | Mallucci, E. (2022), *Journal of International Economics* 139, 103672 · [DOI](https://doi.org/10.1016/j.jinteco.2022.103672) |
| Working paper (acceso abierto) | IFDP 1291, julio 2020 → [`paper/`](paper/) |
| Paquete de réplica | [Mendeley Data `kcty2wvw4d`](https://data.mendeley.com/datasets/kcty2wvw4d/1) → [`src/matlab/vendor/`](src/matlab/vendor/) |
| Curso | Macroeconomía Avanzada de Corto Plazo, 2026-2 (Uniandes) |
| Equipo | David Bautista · Jonathan Cadena · Iván Katz |

## Arranque rápido

```powershell
# 0. Verificaciones estáticas: config, parches y calibración (segundos)
python tests\test_static.py

# 1. Validar el pipeline completo con grillas gruesas (números no reportables)
.\run_all.ps1 -Profile smoke -Engine matlab

# 2. ¿El port a Python reproduce al código del autor?
.\run_all.ps1 -Profile smoke_cmp -Engine matlab
.\run_all.ps1 -Profile smoke_cmp -Engine python -CompareWith smoke_cmp:matlab

# 3. Corrida de la entrega (horas; ver "Costo computacional")
.\run_all.ps1 -Profile paper_memlite -Engine matlab

# 4. Rearmar tablas y figuras sin volver a resolver el modelo
.\run_all.ps1 -Profile paper_memlite -Engine matlab -Stages 4,5,6,7
```

Requisitos: **Python 3.11+** con `pip install -r requirements.txt`. **MATLAB**
(probado en R2026a, sin toolboxes) solo para el motor `matlab`: con
`-Engine python` el pipeline corre completo sin licencia.

## Los dos motores

| | `matlab` | `python` |
|---|---|---|
| Qué es | código del autor + parches auditables | traducción del equipo en NumPy |
| Dónde | [`src/matlab/vendor/`](src/matlab/vendor/) → `build/matlab/<perfil>/` | [`src/python/model/`](src/python/model/) |
| Rol | referencia de la réplica | verificación independiente y base de la extensión |
| Salida | `outputs/raw_mat/<perfil>/*.mat` | `outputs/raw_npz/<perfil>/*.npz` |

Producen las mismas variables con los mismos nombres, así que las etapas 4 a 7
del pipeline son comunes. Para que la comparación signifique algo, los perfiles
`*_cmp` hacen que **ambos motores lean los mismos sorteos aleatorios**: MATLAB y
NumPy siembran el Mersenne Twister de forma distinta, y sin sorteos comunes dos
implementaciones correctas igual darían números distintos por ruido de Monte
Carlo. Con sorteos compartidos la comparación es una prueba de equivalencia de
verdad.

## El pipeline

Siete etapas, cada una un script independiente e idempotente. Se puede reanudar
desde cualquier punto, que es lo que uno necesita cuando la etapa 3 tarda horas.

| # | Etapa | Script | Entrada → Salida |
|---|-------|--------|------------------|
| 0 | `fetch` | [fetch_sources.py](src/python/fetch_sources.py) | Mendeley + Fed → `data/raw/`, `src/matlab/vendor/` (verifica SHA-256) |
| 1 | `shocks` | [make_shocks.py](src/python/make_shocks.py) | semilla → `build/shocks/<perfil>/` (solo perfiles `*_cmp`) |
| 2 | `patch` | [patch_vendor.py](src/python/patch_vendor.py) | código del autor → `build/matlab/<perfil>/` + diffs (solo motor `matlab`) |
| 3 | `solve` | [run_matlab.py](src/python/run_matlab.py) / [run_python.py](src/python/run_python.py) | VFI + simulación → `outputs/raw_*/<perfil>/` |
| 4 | `extract` | [extract_moments.py](src/python/extract_moments.py) | `.mat`/`.npz` → `outputs/moments/moments_<perfil>_<motor>.csv` |
| 5 | `table` | [build_table2.py](src/python/build_table2.py) | momentos + objetivos → `outputs/tables/table2_comparison_*.{csv,md,tex}` |
| 6 | `figure` | [make_figure.py](src/python/make_figure.py) | comparación → `outputs/figures/*.{png,pdf}` |
| 7 | `checks` | [checks.py](src/python/checks.py) | comparación → `outputs/tables/checks_*.md` + código de salida |
| — | `compare` | [compare_runs.py](src/python/compare_runs.py) | dos corridas → veredicto momento a momento |

El entregable es `outputs/tables/table2_comparison_paper_memlite_matlab.tex`,
listo para `\input` en el documento de la entrega.

## Estructura y por qué

```
config/          specs.json + countries.csv  -> TODO lo que varía entre corridas
data/raw/        paquete original + checksums.sha256 (inmutable)
data/targets/    valores del paper transcritos a CSV (los "objetivos" de la réplica)
data/external/   (vacío) datos propios para la extensión Colombia
paper/           PDFs del artículo y notas de versiones
src/matlab/vendor/   código del autor, SIN MODIFICAR
src/matlab/shims/    nanmean/nanmedian (salieron del MATLAB base)
src/python/      las siete etapas del pipeline
src/python/model/    el port: calibration, grids, solve, simulate
tests/           verificaciones estáticas (config, parches, calibración)
build/           código parchado, sorteos, área de trabajo de MATLAB (regenerable)
outputs/         raw_mat, raw_npz, moments, tables, figures, logs
docs/            diseño del pipeline, mapa modelo-código, bitácora, entregas
```

Cinco decisiones que explican la forma del repo:

1. **`src/matlab/vendor/` no se edita nunca.** La etapa 2 escribe *copias*
   parchadas en `build/` y deja el `diff` completo en
   `build/matlab/<perfil>/patches/`. Así, en la sustentación, la respuesta a
   "¿qué cambiaron del código del autor?" es un archivo, no un recuerdo. Cada
   parche se aplica con conteo esperado de coincidencias: si el original
   cambiara, la etapa falla en vez de generar código distinto en silencio.
2. **MATLAB solo resuelve el modelo; Python hace todo lo demás.** El código del
   autor usa `clearvars -except` y `save`/`load` relativos al directorio de
   trabajo, así que envolverlo en más MATLAB es frágil. Cada especificación
   corre con `matlab -batch` en su propio proceso y lo único que cruza la
   frontera es un `.mat`.
3. **Dos motores con el mismo contrato de salida.** El port no reemplaza al
   original: lo verifica. Y es la base natural de la extensión, donde toca
   modificar el modelo y no solo correrlo.
4. **Perfiles en vez de constantes.** `smoke` valida el pipeline en minutos;
   `paper_memlite` produce los números de la entrega; `*_cmp` contrasta motores.
   Un perfil no reportable se marca como tal en la tabla, en la figura y en los
   chequeos, para que nunca termine en el documento por accidente.
5. **La réplica se verifica automáticamente.** La etapa 7 separa chequeos
   *estructurales* (¿la frecuencia simulada de huracanes coincide con la `p_h`
   calibrada? ¿el Panel C realmente no tiene huracanes?) de los de *tolerancia
   y signo* (¿los números caen cerca del paper? ¿la deuda sostenible sube al
   eliminar el riesgo de huracán?). Las bandas están en `config/specs.json`.

Detalle completo en [docs/00_pipeline.md](docs/00_pipeline.md); la
correspondencia ecuación ↔ código ↔ port, en [docs/01_modelo.md](docs/01_modelo.md).

## Cuatro cosas que hay que saber antes de correr

**El paquete del autor no corre tal cual.** `Main.m` falla en su segundo paso:
`climate_persistent_nh_wf.m` (Panel C) hace `load('climate_persistent_wf_new')`,
un archivo que ningún script del paquete produce, y de él lee
`V_g_mean_counter_rn`, una variable que el baseline nunca calcula. Además el
código usa `nanmean`/`nanmedian`, que ya no vienen en el MATLAB base. La etapa 2
resuelve las tres cosas sin tocar el original.

**Los números del working paper no son los del artículo publicado.** El IFDP
1291 (2020) usa deuda de un período; el código y el artículo publicado usan
deuda de largo plazo y otra calibración (deuda/PIB de Jamaica: 0.16 en el WP,
0.53 en el publicado). El objetivo de la réplica es la tabla del **artículo
publicado**. Ver [paper/NOTES_versions.md](paper/NOTES_versions.md).

**Faltan valores objetivo para Antigua y Granada.** `data/targets/table2_mallucci2022_jie.csv`
solo tiene las columnas de República Dominicana y Jamaica, transcritas de la
Primera Entrega. Hasta que se transcriban las otras dos del PDF publicado, la
tabla las muestra como `--` y la etapa 7 lo reporta como aviso.

**Costo computacional.** La grilla del paper es 1260 estados exógenos × 150 de
deuda; el VFI trabaja con arreglos de 28 millones de elementos. Presupueste
**horas por país y por panel**, no minutos. El perfil `paper` tal como está
escrito el código pide ~15 GB solo para guardar la distribución simulada: use
`paper_memlite`, que hace lo mismo con dos rebanadas.

## Estado

- [x] Fuentes descargadas y verificadas por hash; paquete del autor en `vendor/`
- [x] Pipeline de siete etapas, dos motores, seis perfiles
- [x] Verificaciones estáticas en verde (`python tests\test_static.py`)
- [ ] **Correr nada todavía** — el motor Python está escrito pero sin ejecutar
- [ ] Verificar `smoke_cmp:matlab` vs `smoke_cmp:python` (equivalencia de motores)
- [ ] Verificar `smoke` vs `smoke_memlite` (equivalencia de `memlite`)
- [ ] Transcribir los objetivos de ATG y GRD desde el PDF publicado
- [ ] Cotejar los objetivos de DOM y JAM (`verified=FALSE`)
- [ ] Corrida `paper_memlite` para los cuatro países
- [ ] Extensión (dos capas de riesgo, caso Colombia): ver
      [docs/00_pipeline.md](docs/00_pipeline.md#extension)

Bitácora de corridas y decisiones: [docs/02_bitacora.md](docs/02_bitacora.md).
