# Diseño del pipeline y justificación de las decisiones

Documento de referencia del equipo. Explica *por qué* el repositorio tiene esta
forma, qué se le cambió al código del autor y qué queda pendiente.

---

## 1. El problema que hay que resolver

El paquete de Mallucci (2022) son 18 archivos `.m` sueltos. `Main.m` los corre en
orden con `run(...)`, cada uno recorre los siete países del Caribe con
`for counter = 1:7`, y cada uno termina con

```matlab
clearvars -except <lista de variables>
save('nombre_del_script.mat')
```

Eso implica tres cosas incómodas:

- **No se puede envolver en más MATLAB.** `clearvars` borra el espacio de
  trabajo, incluidas las variables de cualquier script que lo invoque. Un
  "runner" en MATLAB se autodestruye.
- **Las rutas son relativas al directorio de trabajo.** Los `save` y `load`
  asumen que todos los scripts corren en la misma carpeta y se pisan entre sí.
- **Nada está parametrizado.** Países, grillas, tolerancias y número de períodos
  simulados están escritos dentro del código, y las simulaciones usan `rand`
  sin semilla: dos corridas del mismo código dan números distintos.

## 2. Las decisiones

### 2.1 El código del autor es de solo lectura

`src/matlab/vendor/` es una copia fiel del paquete (hash verificado contra
`data/raw/checksums.sha256`) y **no se edita**. La etapa 2 aplica parches a
*copias* en `build/matlab/<perfil>/` y escribe el `diff` unificado en
`build/matlab/<perfil>/patches/`.

Por qué importa: en una réplica, la pregunta relevante no es "¿funcionó?" sino
"¿qué exactamente cambiaron respecto al original?". Con esta separación la
respuesta es un archivo auditable que se puede anexar al documento. Además,
cada regla de parche declara cuántas coincidencias espera; si el archivo del
autor fuera distinto al que se usó para escribir el parche, la etapa **falla**
en vez de producir código silenciosamente diferente.

### 2.2 MATLAB resuelve el modelo (si se usa ese motor); Python orquesta

`matlab -batch` por especificación, en su propio proceso, con directorio de
trabajo `build/matlab/<perfil>/`. Es la única forma de garantizar que el Panel B
no contamine al Panel C. Lo único que cruza la frontera entre lenguajes es un
`.mat`, que `scipy.io.loadmat` lee sin problemas.

Consecuencia práctica: las etapas 4 a 7 (extracción, tablas, figura, chequeos)
no necesitan MATLAB. Y con el motor `python` (§2.7) tampoco hace falta licencia
para resolver el modelo.

### 2.3 Toda la parametrización vive en `config/specs.json`

Países, grillas, tolerancias, semilla, mapa de momentos y bandas de aceptación.
El código no tiene constantes mágicas y la configuración es el objeto que se
cita en el documento cuando haya que decir "con qué se corrió esto".

`config/countries.csv` fija la correspondencia entre el índice del loop del
autor (`counter = 1..7`) y el país. Es un mapeo que solo existe implícitamente
en los comentarios del código original y que es fácil equivocar: los cuatro
países de esta réplica son **1 = Antigua y Barbuda, 4 = República Dominicana,
5 = Granada, 7 = Jamaica** (conjunto `entrega1`).

### 2.4 Perfiles: `smoke` para probar, `paper` para entregar

| Perfil | N_y | N_h | N_b_g | T_sim | `memlite` | sorteos | Para qué |
|---|---|---|---|---|---|---|---|
| `smoke` | 21 | 6 | 60 | 2 000 | no | propios | validar el pipeline en minutos |
| `smoke_memlite` | 21 | 6 | 60 | 2 000 | sí | propios | verificar que `memlite` ≡ original |
| `smoke_cmp` | 21 | 6 | 60 | 2 000 | sí | compartidos | verificar que Python ≡ MATLAB, barato |
| `paper` | 63 | 20 | 150 | 10 000 | no | propios | grillas del artículo, código sin optimizar |
| `paper_memlite` | 63 | 20 | 150 | 10 000 | sí | propios | **la corrida de la entrega** |
| `paper_cmp` | 63 | 20 | 150 | 10 000 | sí | compartidos | contrastar motores con las grillas del artículo |

Los perfiles no reportables (`reportable: false`) se marcan como tales en la
tabla, en la figura y en el reporte de chequeos, y sus fallas de tolerancia no
tumban el pipeline. Es una barrera deliberada: es demasiado fácil pegar en el
documento el número de una corrida de prueba.

### 2.5 Semillas por país

Se inyecta `rng(seed + 100*counter, 'twister')` justo antes de que el script
consuma el primer `rand`. Sembrar *por país* (y no una vez al inicio) hace que
el resultado de Jamaica no dependa de si República Dominicana se corrió antes:
la corrida es reproducible y también divisible entre máquinas.

La contrapartida honesta: **nuestros números no pueden coincidir dígito a dígito
con los del paper**, porque el autor no publicó su semilla. Con T_sim = 10 000 el
error de Monte Carlo es pequeño pero no nulo; por eso la etapa 7 evalúa bandas
de tolerancia y el signo del resultado, no igualdad exacta.

### 2.6 `memlite`: 15 GB de RAM que no hacían falta

El código del autor simula guardando la distribución completa:

```matlab
dist_sim = zeros(N_x, N_b_g, T_sim+1);   % 1260 x 150 x 10001 = 15.1 GB
```

`dist_sim` solo se usa dentro del loop de simulación, y solo las rebanadas `t` y
`t+1` (verificable: no aparece en ninguna línea posterior al loop). El parche
`memlite` la reemplaza por dos matrices `N_x × N_b_g` que rotan en cada período:
mismo álgebra, ~1.5 MB.

**Verificación de la equivalencia** — los perfiles `smoke` y `smoke_memlite`
comparten grillas y semilla, así que sus momentos deben coincidir:

```powershell
.\run_all.ps1 -Profile smoke         -Engine matlab -Stages 2,3,4
.\run_all.ps1 -Profile smoke_memlite -Engine matlab -Stages 2,3,4
python src\python\compare_runs.py --left smoke:matlab --right smoke_memlite:matlab --strict
```

Resultado de esta verificación: ver [02_bitacora.md](02_bitacora.md).

### 2.7 Dos motores, y cómo se comparan de verdad

El modelo se resuelve con dos implementaciones independientes:

- **`matlab`**: el código del autor con los parches de §3. Es la referencia de
  la réplica.
- **`python`**: un port a NumPy en `src/python/model/`, traducción línea a línea
  documentada en [01_modelo.md](01_modelo.md). Sirve para dos cosas: verificar
  que el resultado no depende de una implementación, y tener una base
  modificable para la extensión, ya que `vendor/` es de solo lectura.

Ambos escriben las mismas variables con los mismos nombres —MATLAB en un `.mat`,
el port en un `.npz`—, así que las etapas 4 a 7 son comunes y la comparación
queda apples-to-apples por construcción.

**El punto metodológico.** MATLAB y NumPy usan los dos Mersenne Twister, pero lo
siembran distinto (`init_genrand` vs `init_by_array`): `rng(s)` y
`default_rng(s)` producen secuencias diferentes. Comparar motores con sorteos
distintos no prueba nada, porque dos implementaciones correctas darían números
distintos por puro ruido de Monte Carlo. Por eso los perfiles `*_cmp` generan
los sorteos una sola vez (etapa 1, `make_shocks.py`) en formato `.mat` y `.npz`,
y los dos motores los leen. Las diferencias que queden son de traducción, no de
azar, y `compare_runs.py` las clasifica:

```powershell
.\run_all.ps1 -Profile smoke_cmp -Engine matlab
.\run_all.ps1 -Profile smoke_cmp -Engine python -CompareWith smoke_cmp:matlab
```

Qué esperar: `identico` o `equivalente` (diferencia relativa ≤ 1e-8).
Diferencias de 1e-12 a 1e-9 son normales, porque el orden de las sumas en punto
flotante no es idéntico entre el BLAS de MATLAB y el de NumPy. Cualquier cosa
por encima de 1e-3 es un error de traducción, y hay que buscarlo en `model/`.

## 3. Parches {#parches}

Todos generados por [`src/python/patch_vendor.py`](../src/python/patch_vendor.py),
y todos con `diff` auditable en `build/matlab/<perfil>/patches/`. Los tres
primeros son adaptaciones nuestras; los dos que siguen corrigen errores del
paquete publicado; los últimos tres son opcionales o de compatibilidad.

| Parche | Qué hace | Por qué |
|---|---|---|
| subconjunto de países | `for counter = 1:7` → `[1 4 5 7]` | la réplica necesita ATG, DOM, GRD y JAM; cada país de más son horas de VFI |
| semilla por país | inyecta `rng(seed + 100*counter)` | el original no siembra: no es reproducible |
| grillas | `N_y`, `N_h`, `N_b_g`, `T_sim`, `maxiter_q`, `tol_q` | habilita el perfil de prueba |
| último `save` → `*_final.mat` | conserva el `.mat` completo | el `save` posterior al loop sobreescribe el archivo dejando *menos* variables de las que el Panel C necesita leer del Panel B |
| `filename_guess` | `'climate_persistent_wf_new'` → `'climate_persistent_wf'` | **el paquete no produce ningún archivo `*_new`**: `Main.m` falla en su segundo paso |
| `V_g_mean_counter_rn` → `NaN` | elimina una lectura imposible | el baseline nunca calcula la versión *risk-neutral* de la función de valor; solo afecta el bienestar equivalente, que no está en la Tabla 2 |
| `memlite` (opcional) | dos rebanadas en vez de `T_sim+1` | 15.1 GB → 1.5 MB, sin cambiar el álgebra |
| sorteos compartidos (opcional) | `rand(...)` → columnas de `shocks.mat` | sin sorteos comunes, comparar motores mide ruido de Monte Carlo (§2.7) |
| `nanmean` / `nanmedian` | **no es un parche**: se copian shims al directorio de trabajo | las dos funciones salieron del MATLAB base (venían del Statistics Toolbox) y el código las llama 246 veces; MATLAB resuelve primero las funciones del cwd, así que no hay que tocar el original |

Los dos errores de empaquetado son de la versión publicada en Mendeley
(v1, 2022-07-19) y vale la pena mencionarlos en el documento: sin corregirlos,
la Tabla 2 del artículo no es reproducible con el material publicado.

## 4. De la salida cruda a la Tabla 2

El mapa está en `config/specs.json`, sección `moments`, y aplica igual al `.mat`
de MATLAB y al `.npz` del port, porque los dos motores usan los mismos nombres:

| Fila de la Tabla 2 | Variable | Definición en el código |
|---|---|---|
| Spread promedio (pb) | `meanspread_sim` | media de `10000*((1+r_g)/(1+r^f)-1)` sobre períodos con acceso al mercado |
| Deuda externa/PIB | `meanBY_sim` | media de `b/((delta+r^f)·y·h)`: valor facial de la deuda de largo plazo sobre PIB |
| Frecuencia de huracán | `hur_freq_sim` | proporción de períodos con `h < 1` |
| Pérdida de PIB (huracán) | `gdp_g_h_sim` | crecimiento medio del PIB en años de huracán (negativo) |
| Frecuencia de default | `def_freq_sim` | media de la probabilidad de default de la política óptima |

Dos advertencias que costaron lectura de código:

- `meanBY_sim` descuenta con la tasa libre de riesgo; `meanBY_sim_market`
  (también se extrae) usa el precio de mercado `q·b`. El paper reporta
  deuda/PIB sin aclarar cuál; la etapa 5 muestra la primera y guarda la segunda
  para poder discutirlo si la brecha resulta grande.
- `def_freq_sim` **no** es un conteo de defaults: el modelo usa choques
  extremos-valor (`ev_rho = 1e-2`) y la política de default es una probabilidad,
  no un indicador. Por eso el paper la llama *default incidence*.

## 5. Límites conocidos

1. **Los valores objetivo del paper están sin cotejar.** `data/targets/table2_mallucci2022_jie.csv`
   tiene `verified=FALSE`: son la transcripción de la Primera Entrega. Cotejarlos
   contra el PDF publicado (acceso Uniandes) es el primer pendiente; el working
   paper de acceso abierto **no** sirve para eso (§6).
2. **No hay igualdad exacta posible** sin la semilla del autor (§2.5).
3. **`maxiter_q = 600` no garantiza convergencia.** El código itera hasta
   `tol_q = 1e-6` o 600 iteraciones, cualquiera ocurra primero, y no avisa si
   salió por iteraciones. El log de MATLAB (`outputs/logs/matlab_*.log`) imprime
   `diff_q` en cada iteración: **revisar el último valor** antes de reportar.
4. **Faltan objetivos para Antigua y Granada.** `data/targets/table2_mallucci2022_jie.csv`
   solo tiene DOM y JAM. Mientras no se transcriban las otras dos columnas del
   PDF publicado, esos países se simulan pero no se pueden comparar: la tabla
   los muestra como `--` y la etapa 7 lo reporta como aviso.
5. **El port a Python está escrito pero sin correr.** Las verificaciones
   estáticas (`python tests/test_static.py`) pasan: configuración coherente,
   parches que calzan contra el código del autor en los seis perfiles y
   calibración idéntica. La equivalencia numérica con MATLAB está pendiente de
   la corrida `smoke_cmp` (§2.7).
6. **Solo cuatro países.** Correr los siete (`-Countries all`) es cuestión de
   tiempo de CPU, no de código.

## 6. Versiones del artículo

El working paper (IFDP 1291, 2020) y el artículo publicado (JIE, 2022) **no son
la misma calibración ni el mismo modelo de deuda**. El código replica el
publicado. Detalle y comparación de cifras: [../paper/NOTES_versions.md](../paper/NOTES_versions.md).

## 7. Hacia la extensión {#extension}

La propuesta de la entrega —dos capas de riesgo de desastre (hidrometeorológica
frecuente y sísmica rara) para el caso colombiano— cae naturalmente en esta
estructura:

- el proceso de huracán está en un bloque aislado (discretización tipo Tauchen de
  `h` y armado de `P_h`, luego el producto de Kronecker con `P_y`). Una segunda
  capa es un tercer factor en ese producto: `P_x = P_h1 ⊗ P_h2 ⊗ P_y`, con costo
  computacional multiplicativo en `N_h2`;
- conviene implementarla **en el port**, no en el código del autor: `vendor/` es
  de solo lectura y `model/grids.py` ya tiene el proceso de desastre aislado en
  una función. La capa nueva será una **especificación nueva** en
  `config/specs.json`, con sus propios parámetros y su conjunto de objetivos en
  `data/targets/`;
- la corrida de la réplica con el motor `matlab` sigue sirviendo como control:
  la extensión se compara contra ella con `compare_runs.py`;
- las etapas 4 a 7 no cambian: el mapa de momentos y la comparación ya son
  genéricos;
- los datos de calibración colombianos van en `data/external/` con su propio
  script de preparación, y los momentos objetivo (UNGRD/DesInventar, precio del
  bono catastrófico) en `data/targets/`.

Antes de escribir código para la extensión, conviene medir cuánto tarda una
corrida `paper_memlite` de un país: el espacio de estados crece con `N_h2` y ese
número decide si la capa sísmica puede tener grilla propia o debe entrar como un
choque de dos estados.
