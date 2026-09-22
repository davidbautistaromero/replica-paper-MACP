"""Port a Python del modelo de Mallucci (2022).

Traduccion linea a linea de `src/matlab/vendor/climate_persistent_wf.m` y su
variante sin huracanes. El objetivo NO es mejorar el modelo: es tener una
segunda implementacion independiente para contrastar contra MATLAB. Donde el
codigo original hace algo raro (incluido codigo muerto), aqui se reproduce
igual, con un comentario `# fidelidad:` que lo señala.

Modulos:
    calibration  parametros comunes y por pais
    grids        procesos exogenos (Tauchen), matriz de transicion, grilla de deuda
    solve        iteracion de funcion de valor + precio del bono
    simulate     sendero simulado y momentos de la Tabla 2
"""
