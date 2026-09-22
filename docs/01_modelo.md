# Mapa modelo ↔ código ↔ port

Tabla de traducción entre las ecuaciones del paper, el código de MATLAB del
autor y el port a Python. Sirve para tres cosas: leer el código del autor sin
perderse, auditar la traducción y saber dónde tocar para la extensión.

Referencias de línea: `src/matlab/vendor/climate_persistent_wf.m` (Panel B).

## Trampas de notación

Tres nombres que significan cosas distintas de lo que uno espera:

| En el código | Qué es | Qué NO es |
|---|---|---|
| `delta` | decaimiento de la deuda de largo plazo (Hatchondo–Martínez) | el costo de default `δ(y)` del working paper |
| `wc_par_asymm` | costo de default: fracción de `E[y]` disponible en autarquía | un parámetro de bienestar |
| `mean_h` | nivel del PIB tras el huracán, `1 − μ_h` | la pérdida media |
| `lambda` | probabilidad de readmisión al mercado | la intensidad del huracán |

`counter` es el índice del país en el loop del autor: **1 = Antigua y Barbuda,
4 = República Dominicana, 5 = Granada, 7 = Jamaica** (los cuatro de esta
réplica). El mapeo completo está en `config/countries.csv`.

## Estado y grillas

| Concepto | Paper | MATLAB | Port |
|---|---|---|---|
| Estado | `(b, y, h)` | `b_g_vec`, `y_vec`, `h_vec` | `Grids.b_vec`, `.y_vec`, `.h_vec` |
| Ingreso, AR(1) log-normal | ec. (8) y §4 | Tauchen en líneas 112-148 | `grids.tauchen` |
| Choque de huracán, ec. (9) | `h = 1−ε` con prob. `p_h` | líneas 152-199 | `grids.build_grids` |
| Índice exógeno | — | `x = (i_y−1)·N_h + i_h` | igual (el huracán corre más rápido) |
| Transición conjunta | — | `P_x = kron(P_y,1_h) .* kron(1_y, P_h)`, líneas 213-224 | igual |
| Grilla de deuda (2 tramos) | — | líneas 282-322, 85% de los puntos bajo `b=0.3` | `grids.build_grids` |

**Detalle importante y no obvio** (líneas 213-221): la distribución del ingreso
del próximo período se toma del punto de la grilla más cercano al PIB *después*
del huracán, no al ingreso antes del daño. Es decir, en esta versión el daño se
propaga por el AR(1) y tiene algo de persistencia — de ahí el nombre
`climate_persistent_*` de los archivos. El working paper afirma lo contrario
("hurricanes have no persistent impact"), así que es una diferencia real entre
las dos versiones y algo que la extensión tendrá que decidir por cada capa de
riesgo.

## Problema del gobierno

| Ecuación | MATLAB | Port |
|---|---|---|
| (1) `V = max{(1−d)V^nd + dV^d}` | `v_guess_new`, líneas 407-420 | `solve.solve`, `v_new` |
| (2) `V^nd` | `borrower_maximand`, línea 382 | `buf` tras `+= beta*e_v` |
| (3) `c = y(1−h) + qb' − b` | `cons_choice`, línea 376 | `np.multiply(...)` + `buf += hy - b_state` |
| (5) `V^d` con readmisión `λ` | `v_bad_guess_new`, línea 399 | `v_bad_new` |
| (6) `c = (1−h)δ(y)` en autarquía | `c_aut`, líneas 248-257 | `grids.autarky_utility` |
| (7) precio del bono | `q_g_new`, línea 456 | `q_new` |
| Costo de default asimétrico | `c_aut(c_aut>wc_par*gdp_mean) = wc_par*gdp_mean` | `c_aut[c_aut > tope] = tope` |

El modelo cuantitativo no es exactamente el de las ecuaciones del paper: el
código añade **choques de valor extremo** (`ev_rho = 1e-2`) sobre la elección de
`b'` y sobre la decisión de default. Consecuencias:

- la política de emisión es una distribución (`prob_choice`), no un argmax;
- la política de default es una **probabilidad** entre 0 y 1, no un indicador —
  por eso la fila de la tabla se llama *default incidence* y no "número de
  defaults";
- la simulación propaga una distribución de deuda, no un sendero único.

Una discrepancia que vale registrar: el Apéndice E del artículo dice que la
escala de esos choques es `ρ_EV = 10⁻³`, pero el código usa `ev_rho = 1e-2`. El
pipeline replica el código.

En el port, tres expresiones usan su versión numéricamente estable
(`softmax`, `scipy.special.expit`, `np.logaddexp`). Son la misma fórmula: el
código del autor hace lo propio a mano, normalizando por el máximo y eligiendo
entre dos formas algebraicamente equivalentes según si la probabilidad de
default supera 0.999. Están marcadas `# equivalencia:` en `model/solve.py`.

## Iteración

| Paso | MATLAB | Port |
|---|---|---|
| Loop externo sobre `q` | `while diff_q > tol_q && iter_q < maxiter_q`, línea 353 | idéntico |
| Loop interno sobre `V` | `while diff_v > tol_v && iter_v < maxiter_v`, línea 358 | idéntico |
| Amortiguamiento | `damp_v = damp_q = 0.8` | idéntico |
| Criterio | `tol_v = 1e-3`, `tol_q = 1e-6` | del perfil |

Ambos loops paran por tolerancia **o** por número de iteraciones, sin avisar
cuál. El port expone `Solution.converged`; en MATLAB hay que mirar el último
`diff_q` del log.

## Simulación y momentos

| Fila de la Tabla 2 | Variable | Definición |
|---|---|---|
| Spread promedio (pb) | `meanspread_sim` | media de `10000·((1+r_g)/(1+r^f)−1)` en períodos con acceso |
| Spread mediano (pb) | `medianspread_sim` | mediana de lo mismo. **El script sin huracanes del autor no la calcula**, aunque el paper la reporta en el Panel C |
| Deuda externa/PIB | `meanBY_sim` | media de `b/((ψ+r^f)·y·h)`: valor facial sobre PIB |
| Deuda/PIB a valor de mercado | `meanBY_sim_market` | media de `q·b` |
| Frecuencia de huracán | `hur_freq_sim` | proporción de períodos con `h < 1` |
| Pérdida de PIB (huracán) | `gdp_g_h_sim` | crecimiento medio del PIB en años de huracán (negativo) |
| Frecuencia de default | `def_freq_sim` | media de la probabilidad de default de la política |

El paper reporta la pérdida de PIB como número positivo (0.047 = caída de 4.7%);
`data/targets/` la guarda negativa, que es la convención del código.

`meanBY_sim` descuenta con la tasa libre de riesgo (valor facial);
`meanBY_sim_market` usa el valor de mercado `q·b`. El paper reporta **las dos**
filas, así que cada una tiene su contraparte y se comparan por separado. El
valor de mercado es siempre menor, porque descuenta los cupones futuros a la
tasa riesgosa.

### Rarezas que el port reproduce a propósito

Están marcadas `# fidelidad:` en `model/simulate.py`:

1. Los vectores por período se inicializan en cero y el loop solo llena
   `t = 1..T−1`, así que el **último período queda en cero** y entra en los
   promedios (contamina 1 de cada 10 000 observaciones).
2. `b_g_sim1` y `b_g_sim_curr` pretenden ser rezago y valor corriente de la
   deuda, pero el código no los desplaza: son el mismo vector salvo el primer y
   el último elemento. Solo alimentan `cons_sim`, que no está en la Tabla 2.
3. Los `NaN` de `nx_sim` se rellenan con cero *antes* de calcular el consumo, de
   modo que las dos sustituciones siguientes del original nunca se activan
   (código muerto).
4. `def_sim` se pone en cero cuando la deuda corriente y la rezagada son `NaN`
   —períodos de exclusión encadenados—, y el vector rezagado arranca con un
   `110` literal como centinela.

Ninguna cambia las conclusiones, pero sí los decimales: si el port las
"arreglara", la comparación entre motores dejaría de ser exacta y no se podría
distinguir un error de traducción de una mejora.

## Dependencias entre paneles

El Panel C no es una corrida independiente:

| Qué hereda del Panel B | MATLAB | Port |
|---|---|---|
| `E[y]` por país | `load('gdp_mean_storemat')`, línea 241 de la variante `nh` | `run_python.inherited_gdp_mean` |
| Sorteos de readmisión | `lg.redem_sim_counter(:,counter)` | sorteos compartidos por país |
| Valor de referencia (bienestar) | `lg.V_g_mean_counter(:,counter)` | no se usa: fuera de la Tabla 2 |

Es deliberado del autor: compartir sorteos entre paneles reduce el ruido de la
comparación B vs C, que es justo el resultado que se quiere medir.

## Dónde tocar para la extensión

Una segunda capa de desastre (hidrometeorológica frecuente + sísmica rara) entra
en `grids.build_grids`: el proceso de huracán está aislado y la transición
conjunta es un producto de Kronecker, así que la capa nueva es un factor más,
`P_x = P_h1 ⊗ P_h2 ⊗ P_y`, con costo computacional multiplicativo en `N_h2`.
El resto —solución, simulación, momentos— no cambia de forma, solo de tamaño.
Conviene hacerlo en el port y no en el código del autor: `vendor/` es de solo
lectura y el port ya está organizado en funciones.
