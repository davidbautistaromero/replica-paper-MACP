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

## 2026-09-22 — primera corrida: pipeline validado y dos equivalencias probadas

**Perfil `smoke`, motor `matlab`, países `entrega1` — las siete etapas en verde.**
Duración: 3.4 min de MATLAB (1.5 min el Panel B, 1.8 min el Panel C) y 0.4 min
el resto. Confirmado que el perfil **no converge** a propósito: último
`diff_q ≈ 9.4e-4` contra `tol_q = 1e-4`, es decir salió por agotar las 25
iteraciones. Sirve para validar el encadenamiento de etapas, no para números.

Resultado cualitativo, incluso con grillas gruesas: **la deuda sostenible sube
al eliminar el riesgo de huracán en los cuatro países** (ATG +35.6%, DOM +13.5%,
GRD +14.4%, JAM +27.3%). Es el resultado central del paper.

**Equivalencia de `memlite`: 48 de 48 momentos idénticos**, diferencia relativa
máxima `0.000e+00`. Bit a bit. La reescritura que baja la memoria de 15.1 GB a
1.5 MB no cambia un dígito.

**Equivalencia de motores (`smoke_cmp`, sorteos compartidos):**

| Momento | Diferencia relativa MATLAB vs. Python |
|---|---|
| Frecuencia de huracán, pérdida de PIB | exactamente 0 |
| Frecuencia de default | ~1e-12 |
| Deuda externa/PIB | ~1e-11 |
| Spread promedio | 1e-8 a 1.2e-5 (peor caso: 0.007 pb sobre 557 pb) |

41 de 44 momentos comparables salen `identico` o `equivalente`; los 7 `cercano`
son todos spreads, lo esperado porque el spread sale de `1/q` y amplifica
diferencias en el orden de las sumas en punto flotante. Los 4 `FALTA` son
`spread_median_bp` del Panel C, que el script sin huracanes del autor nunca
asigna y el port sí calcula: asimetría en un momento de diagnóstico, no en la
Tabla 2. Tiempos: Python 2.3 min contra MATLAB 3.4 min.

Hipótesis a verificar con el perfil del artículo: al converger de verdad
(`tol_q = 1e-6`) las diferencias de spread deberían encogerse, porque ambos
motores llegan al mismo punto fijo en vez de quedar en puntos distintos del
mismo camino.

### Cuatro defectos encontrados y corregidos en esta corrida

1. **Bug propio en el port**: el bloque `markov function` del autor guarda el
   estado *antes* de transitar y luego vuelve a anteponer el inicial, así que el
   sendero es `[s0, s0, s1, ...]` —el inicial sale dos veces y el último sorteo
   se descarta—. El port no lo duplicaba. Se detectó al ver que el Panel C
   reporta frecuencia de huracán `2/T_sim` en vez de 0: el estado inicial tiene
   el índice de huracán a mitad de la grilla, así que la economía sin riesgo
   igual arranca con dos períodos de daño. Cubierto ahora por un test.
2. `build_table2` fallaba al recorrer el mapa de momentos sin filtrar la clave
   de documentación.
3. El aviso de objetivos faltantes se evaluaba sin mirar el panel, y reportaba
   como faltantes momentos que el paper no publica en ese panel.
4. El chequeo "Panel C sin huracanes" era demasiado estricto: ahora admite el
   artefacto del estado inicial (`≤ 2.5/T_sim`) y falla por encima de eso.

## 2026-09-22 — Tabla 2 verificada contra el artículo publicado

Con el PDF publicado a mano (en `paper/`, fuera del control de versiones por
licencia) se reemplazaron los objetivos por la Tabla 2 completa: **siete países,
tres paneles, `verified=TRUE`**, 125 celdas.

**La transcripción de la Primera Entrega tenía errores.** Spread de DOM 497 (real
479), de JAM 526 (real 554), deuda/PIB de JAM 0.53 —que es el valor de
**Granada**— y frecuencia de default de DOM 0.040 (real 0.083). Hay que
corregirlo en el documento de la entrega.

**Dos filas nuevas que el pipeline ya calculaba:** *median spread* y *market
value of debt*. Con eso el Panel B pasa de 5 a 7 momentos comparables, y se
resuelve la duda de qué medida de deuda reportaba el paper: reporta las dos.
Detalle: el script sin huracanes del autor nunca asigna `medianspread_sim`,
así que esa celda del Panel C queda vacía con el motor `matlab` (el port sí la
calcula). Quedó registrado en `config/specs.json` como `no_calculado`, y los
chequeos y comparaciones ya no fallan por eso.

**Dos discrepancias entre el artículo y su paquete de réplica** (ver
[../paper/NOTES_versions.md](../paper/NOTES_versions.md)):

1. Calibración de República Dominicana: el artículo reporta `β = 0.88` y costo
   de default `0.895`; el código usa `0.895` y `0.8175`. El `0.895` aparece en
   las dos filas del artículo.
2. El Apéndice E dice `ρ_EV = 10⁻³`; el código usa `1e-2`. También: el artículo
   dice 9.500 períodos simulados y el código tiene 10.000.

**Primera señal con los objetivos correctos** (perfil `smoke`, que no converge,
así que es indicativo y nada más): ATG, GRD y JAM caen cerca del publicado
—Jamaica: spread 556 contra 554, deuda/PIB 0.45 contra 0.49—, mientras
**República Dominicana se va +179 pb en el Panel B y +194 en el C**. RD es
justamente el país con la calibración en disputa. Es contrastable con una sola
corrida.

### El contrafactual de República Dominicana: hipótesis descartada

Se corrió RD con los parámetros de la Tabla 1 publicada (perfil `smoke_pubcal`,
idéntico a `smoke_cmp` salvo `β` y el costo de default). El resultado **descarta**
la hipótesis y de paso resuelve la discrepancia:

| | paper | calibración del código | calibración del artículo |
|---|---|---|---|
| Spread Panel B | 479 | 669 | **1188** |
| Deuda/PIB Panel B | 0.25 | 0.231 | **0.135** |
| Spread Panel C | 416 | 557 | **1004** |
| Deuda/PIB Panel C | 0.29 | 0.265 | **0.158** |

Con los parámetros del artículo el spread se duplica y la deuda cae a la mitad.
La dirección tiene sentido: bajar `β` hace al gobierno más impaciente, y subir el
costo de default de 0.8175 a 0.895 significa *menos* castigo en autarquía (es la
fracción del PIB disponible); ambos empujan el spread hacia arriba.

**Conclusión: los valores del código son los que generaron la Tabla 2, y es la
Tabla 1 del artículo la que tiene el error.** No es conjetura: los parámetros de
la Tabla 1 son cuantitativamente incompatibles con la Tabla 2 del mismo artículo.

## 2026-09-22 — LA RÉPLICA, corrida con las grillas del artículo

Perfil `paper_memlite`, motor `matlab`, cuatro países, los dos paneles.
**Las ocho corridas convergieron** (`diff_q` final entre 8.3e-07 y 9.9e-07,
todas bajo la tolerancia de 1e-6). **56 chequeos automáticos, cero fallas.**

| Corrida | Duración | Iteraciones externas |
|---|---|---|
| Jamaica, Panel B | 17 min | 156 |
| Jamaica, Panel C | 23 min | 123 |
| ATG/DOM/GRD, Panel B | 118 min | 108, 71, 114 |
| ATG/DOM/GRD, Panel C | 124 min | 98, 63, 98 |

Total ~4.5 h de máquina. La corrida sobrevivió al reinicio de la sesión: MATLAB
siguió por su cuenta y solo hubo que recoger los `.mat` al final.

### Resultado

| Momento (Panel B) | ATG | DOM | GRD | JAM |
|---|---|---|---|---|
| Spread, paper → réplica | 465 → 464 | 479 → 507 | 484 → 472 | 554 → 584 |
| Deuda/PIB | 0.38 → 0.38 | 0.25 → 0.25 | 0.53 → 0.52 | 0.49 → 0.48 |
| Deuda a valor de mercado | 0.31 → 0.32 | 0.22 → 0.22 | 0.41 → 0.41 | 0.43 → 0.43 |
| Frecuencia de default | 0.061 → 0.059 | 0.083 → 0.086 | 0.057 → 0.060 | 0.043 → 0.042 |

**El resultado central se reproduce en los cuatro países: al eliminar el riesgo
de huracán la deuda sostenible sube** (ATG +38%, JAM +32%, GRD +22%, DOM +13%).
Las razones de deuda coinciden hasta el segundo decimal; los spreads quedan
dentro de ±33 pb, que es lo esperable sin la semilla del autor.

**La brecha de República Dominicana era la corrida tosca**, como se sospechaba:
de +179 pb en el perfil `smoke` a +28 pb con las grillas del artículo y
convergencia real, y la deuda/PIB da exacta. No hay razón para sacar a RD de la
entrega.

### Pendientes inmediatos

- [ ] Escribir el documento con estos números.
- [ ] Corregir en la entrega la tabla transcrita de la Primera Entrega.
- [ ] Opcional: repetir el contraste de motores con `paper_cmp`, para ver si las
      diferencias de spread se encogen al converger de verdad.
- [ ] Corrida `paper_memlite` para los cuatro países; anotar duración y el
      último `diff_q` de cada log.
- [ ] Repetir el contraste de motores con `paper_cmp`.

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
