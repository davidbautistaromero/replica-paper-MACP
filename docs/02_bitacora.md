# Bitácora

Una entrada por corrida o decisión. Sirve para el apéndice de replicabilidad del
documento final: qué se corrió, con qué configuración y qué salió.

Formato sugerido: fecha · perfil · motor · países · resultado · observación.

---

## 2026-09-22 — montaje del repositorio

- Descargados y verificados por hash: paquete de réplica (Mendeley
  `kcty2wvw4d` v1, 2022-07-19) y working paper IFDP 1291.
- Estructura y pipeline de siete etapas creados (ver [00_pipeline.md](00_pipeline.md)).
- Hallazgos al leer el paquete del autor, antes de correr nada:
  1. `Main.m` **no corre de principio a fin**: el Panel C hace
     `load('climate_persistent_wf_new')`, archivo que ningún script produce, y
     lee `V_g_mean_counter_rn`, variable que el baseline no calcula.
  2. El `save` posterior al loop del baseline sobreescribe su `.mat` dejando
     menos variables de las que el Panel C necesita heredar.
  3. El código usa `nanmean`/`nanmedian` (246 llamadas), que salieron del MATLAB
     base. Resuelto con shims en `src/matlab/shims/`, sin tocar el original.
  4. `dist_sim = zeros(N_x,N_b_g,T_sim+1)` pide ~15 GB con las grillas del
     paper; de ahí el perfil `paper_memlite`.
- Etapa de parcheo ejecutada y revisada en los perfiles `smoke` y
  `smoke_memlite`; diffs en `build/matlab/<perfil>/patches/`.

## 2026-09-22 — cambio de alcance: cuatro países y segundo motor

- **Países de la réplica**: ahora `entrega1 = [1, 4, 5, 7]` = Antigua y Barbuda,
  República Dominicana, Granada y Jamaica (antes solo DOM y JAM). El conjunto
  anterior queda disponible como `dom_jam`.
- **Motor Python** (`src/python/model/`): port del modelo en NumPy —
  `calibration`, `grids`, `solve`, `simulate`— con el mismo contrato de salida
  que el `.mat` del autor, de modo que las etapas 4 a 7 no distinguen motores.
  Traducción documentada en [01_modelo.md](01_modelo.md).
- **Sorteos compartidos** (`make_shocks.py`, perfiles `*_cmp`): MATLAB y NumPy
  siembran el Mersenne Twister distinto, así que sin sorteos comunes la
  comparación entre motores mide ruido de Monte Carlo. Con ellos, es una prueba
  de equivalencia. Ver [00_pipeline.md §2.7](00_pipeline.md).
- **Perfiles nuevos**: `smoke_cmp` y `paper_cmp` (memlite + sorteos compartidos).
- **`tests/test_static.py`**: verificaciones que tardan segundos — coherencia de
  `config/specs.json`, reglas de parcheo aplicadas en memoria contra el código
  del autor en los seis perfiles, y calibración del port contra los valores
  escritos en el `.m`. Estado: **las tres en verde**.
- Detalle del port que vale mencionar en el documento: el código del autor
  condiciona la distribución del ingreso del próximo período al PIB *posterior*
  al huracán, así que el daño se propaga por el AR(1). El working paper afirma
  lo contrario; es una diferencia real entre versiones y una decisión que la
  extensión tendrá que tomar capa por capa.
- **No se corrió nada del modelo** en esta sesión, por pedido explícito.

### Pendientes inmediatos

- [ ] Correr `smoke -Engine matlab` completo (etapas 2–7) y anotar el tiempo.
- [ ] Verificar `memlite`: `compare_runs.py --left smoke:matlab --right smoke_memlite:matlab --strict`.
- [ ] Verificar motores: `smoke_cmp` con los dos motores y `-CompareWith smoke_cmp:matlab`.
- [ ] Transcribir los objetivos de ATG y GRD de la Tabla 2 publicada.
- [ ] Cotejar los de DOM y JAM y pasar `verified` a `TRUE`.
- [ ] Corrida `paper_memlite` para los cuatro países; anotar duración y el
      último `diff_q` de cada log.

---

## Plantilla

```
## AAAA-MM-DD — <qué se corrió>

- Perfil: <paper_memlite | smoke_cmp | ...>   Motor: <matlab | python>
- Países: <entrega1 | 1,4,5,7 | ...>
- Comando: .\run_all.ps1 -Profile ... -Engine ... -Stages ...
- Duración: ... min     Último diff_q: ...  (¿convergió o se agotaron las iteraciones?)
- Salidas: outputs/tables/..., outputs/figures/...
- Chequeos: N pasaron / M fallaron  ->  detalle en outputs/tables/checks_<perfil>_<motor>.md
- Observación:
```
