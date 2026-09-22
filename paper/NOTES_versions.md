# Versiones del artículo y discrepancias con el código

**Conclusión práctica: el objetivo de la réplica es la Tabla 2 del artículo
publicado (JIE 2022), no la del working paper.** El código de
`src/matlab/vendor/` corresponde a la versión publicada.

## 1. Working paper (2020) vs. artículo publicado (2022)

| | IFDP 1291 (jul. 2020) | JIE 139 (2022) — lo que replica el código |
|---|---|---|
| Deuda | un período | largo plazo, decaimiento `ψ` (Hatchondo–Martínez) |
| Descuento β | 0.82, común a los 7 países | específico por país (0.8575–0.945) |
| σ_h | 0.040, común | específico por país (0.020–0.052) |
| Escenario de cambio climático | frecuencia ×1.9, daños ×2 | frecuencia +29.2% (Bhatia et al.), costos +48.5% (Acevedo/Mejía) |
| Filas de la Tabla 2 | 6 en el Panel B | 7 en el Panel B, con *median spread* y *market value of debt* |

### Contraste de cifras (Tabla 2, los cuatro países de la réplica)

| Panel | Momento | | ATG | DOM | GRD | JAM |
|---|---|---|---|---|---|---|
| B | Spread promedio | WP 2020 | 456 | 477 | 489 | 479 |
| B | | **JIE 2022** | **465** | **479** | **484** | **554** |
| B | Deuda/PIB | WP 2020 | 0.15 | 0.13 | 0.17 | 0.16 |
| B | | **JIE 2022** | **0.38** | **0.25** | **0.53** | **0.49** |
| C | Spread promedio | WP 2020 | 436 | 489 | 497 | 395 |
| C | | **JIE 2022** | **314** | **416** | **406** | **435** |
| C | Deuda/PIB | WP 2020 | 0.18 | 0.14 | 0.19 | 0.17 |
| C | | **JIE 2022** | **0.52** | **0.29** | **0.64** | **0.65** |

La deuda de largo plazo es lo que acerca el modelo a los datos (deuda/PIB
observada: ATG 0.36, DOM 0.25, GRD 0.53, JAM 0.49). Con deuda de un período el
modelo subpredice la deuda a menos de la mitad, algo que el propio WP reconoce.

> **Nota sobre la Primera Entrega.** La tabla que se incluyó en la Primera
> Entrega tenía errores de transcripción: spread de DOM 497 (real 479), de JAM
> 526 (real 554), deuda/PIB de JAM 0.53 (que es el valor de **Granada**; el de
> Jamaica es 0.49) y frecuencia de default de DOM 0.040 (real 0.083). Los
> valores verificados están en `data/targets/table2_mallucci2022_jie.csv`.

## 2. Discrepancias entre el artículo publicado y su paquete de réplica

Encontradas al cotejar el PDF con el código. Son hallazgos propios y vale
mencionarlos en el documento.

**a. Calibración de República Dominicana.** La Tabla 1 del artículo reporta
`β = 0.88` y costo de default `δ = 0.895`; el código usa `β = 0.895` y
`0.8175`. El `0.895` aparece en las dos filas del artículo, así que parece que
`β` se copió sobre la fila de `δ`. Para los otros seis países, artículo y
código coinciden en todos los parámetros. Las dos versiones están en
`data/targets/`: `table1_mallucci2022_jie_published.csv` y
`table1_calibration_vendor_code.csv`.

Esto **no es anecdótico**: en la corrida de prueba, República Dominicana es el
único de los cuatro países cuyo spread queda lejos del publicado (+179 pb en el
Panel B), mientras ATG, GRD y JAM caen cerca. Es una hipótesis contrastable con
una sola corrida: si con los parámetros de la Tabla 1 el spread de RD se acerca
a 479, el código publicado no es el que generó esa columna.

**b. Escala de los choques de valor extremo.** El Apéndice E dice
`ρ_EV = 10⁻³`; el código usa `ev_rho = 1e-2` (y `1/ev_rho = 100` para la
decisión de default). Un orden de magnitud de diferencia en cuánta
aleatoriedad tienen las decisiones del gobierno.

**c. Períodos simulados.** El artículo dice 9.500 en las notas de las Tablas 2
a 5; el código tiene `T_sim = 10000`.

**d. Inconsistencias internas del artículo.** La Sección 5.1 dice que la
deuda/PIB va "de 0.27 en República Dominicana a 0.78 en Belice", pero el Panel A
de la Tabla 2 reporta 0.25 para RD. En el mismo párrafo dice que la
probabilidad de huracán va "de casi 14% en Antigua a 2.6% en República
Dominicana": el 13.8% y el 2.6% son los valores del working paper, y el 2.6%
corresponde a **Dominica**, no a República Dominicana. Son restos de la versión
anterior que sobrevivieron a la revisión.

## 3. Estado de las fuentes

- `mallucci2020_ifdp1291_working_paper.pdf` — acceso abierto, versionado en el
  repo. Sirve para el modelo y la narrativa; **no** para los números.
- `mallucci2022_jie103672_published_NO_VERSIONAR.pdf` — el artículo publicado.
  Está en la carpeta pero **fuera del control de versiones**: es de acceso
  restringido (Elsevier) y no corresponde redistribuirlo. La regla está en
  `.gitignore`.
- Valores objetivo: `data/targets/table2_mallucci2022_jie.csv`, los siete países
  y los tres paneles, `verified=TRUE` contra el PDF publicado.
  `table2_mallucci2020_ifdp.csv` conserva la tabla del working paper solo como
  contraste histórico.
