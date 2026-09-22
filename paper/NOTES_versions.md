# Working paper (2020) vs. artículo publicado (2022)

**Conclusión práctica: el objetivo de la réplica es la Tabla 2 del artículo
publicado, no la del working paper.** El código de `src/matlab/vendor/`
corresponde a la versión publicada.

## Por qué no son intercambiables

| | IFDP 1291 (jul. 2020) | JIE 139 (2022) — lo que replica el código |
|---|---|---|
| Deuda | un período | largo plazo, decaimiento `delta` (Hatchondo–Martínez) |
| Descuento β | 0.82, común a los 7 países | específico por país (0.8575–0.945) |
| σ_h | 0.040, común | específico por país (0.020–0.052) |
| Escenario de cambio climático | frecuencia ×1.9, daños ×2 | frecuencia +29.2% (Bhatia et al.), costos +48.5% (Acevedo) |

## Contraste de cifras (Tabla 2, DOM y JAM)

| Panel | Momento | WP 2020 DOM | JIE 2022 DOM | WP 2020 JAM | JIE 2022 JAM |
|---|---|---|---|---|---|
| B (con huracán) | Spread (pb) | 477 | 497 | 479 | 526 |
| B | Deuda/PIB | 0.13 | 0.25 | 0.16 | 0.53 |
| C (sin huracán) | Spread (pb) | 489 | 423 | 395 | 400 |
| C | Deuda/PIB | 0.14 | 0.28 | 0.17 | 0.67 |

La deuda de largo plazo es lo que acerca el modelo a los datos (deuda/PIB
observada: DOM 0.25, JAM 0.49). Con deuda de un período el modelo subpredice
deuda a la mitad, algo que el propio WP reconoce.

## Estado de las fuentes

- `mallucci2020_ifdp1291_working_paper.pdf` — acceso abierto, en este repo.
  Sirve para el modelo, la narrativa y el Apéndice; **no** para los números.
- Artículo publicado — no redistribuible; descargar vía Uniandes.
- Valores objetivo transcritos en `data/targets/`:
  `table2_mallucci2022_jie.csv` (`verified=FALSE`, pendiente de cotejo) y
  `table2_mallucci2020_ifdp.csv` (`verified=TRUE`, transcrito del PDF de este repo).
