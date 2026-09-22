<#
.SYNOPSIS
  Orquestador del pipeline de replica de Mallucci (2022).

.DESCRIPTION
  Corre las etapas en orden y se detiene en la primera que falle. Cada etapa es
  un script de Python independiente e idempotente, asi que se puede reanudar
  desde cualquier punto con -Stages.

  Etapas:
    0  fetch    descarga y verifica paper + paquete de replica
    1  shocks   sorteos aleatorios compartidos (solo si el perfil los usa)
    2  patch    codigo MATLAB parchado en build/matlab/<perfil>/ (solo motor matlab)
    3  solve    resuelve y simula el modelo. Es la etapa lenta.
    4  extract  salida cruda -> outputs/moments/moments_<perfil>_<motor>.csv
    5  table    tabla de comparacion .csv/.md/.tex
    6  figure   figura diagnostica paper vs. replica
    7  checks   verificaciones automaticas

  La comparacion entre corridas (MATLAB vs Python, o memlite vs original) se
  hace aparte, con -CompareWith o llamando a src/python/compare_runs.py.

.PARAMETER Profile
  Perfil de config/specs.json. 'paper_memlite' para la entrega, 'smoke' para
  probar el pipeline, '*_cmp' para contrastar motores (sorteos compartidos).

.PARAMETER Engine
  'matlab' (codigo del autor parchado) o 'python' (port del equipo).

.PARAMETER Countries
  Nombre de un conjunto de config/specs.json ('entrega1' = ATG, DOM, GRD, JAM;
  'dom_jam'; 'all') o una lista de indices, por ejemplo '1,4,5,7'.

.PARAMETER Stages
  'all' o una lista: '4,5,6,7' para rearmar tablas sin volver a resolver.

.PARAMETER CompareWith
  perfil[:motor] contra el cual comparar al terminar. Ejemplo:
  -Profile smoke_cmp -Engine python -CompareWith smoke_cmp:matlab

.EXAMPLE
  .\run_all.ps1 -Profile smoke -Engine matlab
.EXAMPLE
  .\run_all.ps1 -Profile smoke_cmp -Engine python -CompareWith smoke_cmp:matlab
.EXAMPLE
  .\run_all.ps1 -Profile paper_memlite -Engine matlab -Stages 4,5,6,7
#>
[CmdletBinding()]
param(
  [ValidateSet('paper', 'paper_memlite', 'paper_cmp', 'smoke', 'smoke_memlite', 'smoke_cmp')]
  [string] $Profile = 'paper_memlite',

  [ValidateSet('matlab', 'python')]
  [string] $Engine = 'matlab',

  [string] $Countries = 'entrega1',
  [string[]] $Stages = @('all'),
  [string] $CompareWith = '',
  [string] $Python = 'python'
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$py = Join-Path $root 'src\python'

if ($Engine -eq 'matlab') { $solver = 'run_matlab.py' } else { $solver = 'run_python.py' }

$plan = @(
  @{ n = 0; name = 'fetch';   script = 'fetch_sources.py';   args = @() },
  @{ n = 1; name = 'shocks';  script = 'make_shocks.py';     args = @('--profile', $Profile) },
  @{ n = 2; name = 'patch';   script = 'patch_vendor.py';    args = @('--profile', $Profile, '--countries', $Countries); onlyMatlab = $true },
  @{ n = 3; name = 'solve';   script = $solver;              args = @('--profile', $Profile, '--countries', $Countries) },
  @{ n = 4; name = 'extract'; script = 'extract_moments.py'; args = @('--profile', $Profile, '--engine', $Engine) },
  @{ n = 5; name = 'table';   script = 'build_table2.py';    args = @('--profile', $Profile, '--engine', $Engine) },
  @{ n = 6; name = 'figure';  script = 'make_figure.py';     args = @('--profile', $Profile, '--engine', $Engine) },
  @{ n = 7; name = 'checks';  script = 'checks.py';          args = @('--profile', $Profile, '--engine', $Engine) }
)

if ($Stages -contains 'all') {
  $seleccion = $plan
} else {
  $pedidas = $Stages | ForEach-Object { $_ -split ',' } | ForEach-Object { [int] $_.Trim() }
  $seleccion = $plan | Where-Object { $pedidas -contains $_.n }
}
if (-not $seleccion) { throw "Ninguna etapa valida en -Stages $($Stages -join ',')" }

Write-Host ""
Write-Host "Replica Mallucci (2022)" -ForegroundColor Cyan
Write-Host "  perfil: $Profile | motor: $Engine | paises: $Countries"
Write-Host ("  etapas: " + (($seleccion | ForEach-Object { "$($_.n):$($_.name)" }) -join '  '))
if ($Profile -like 'smoke*') {
  Write-Host "  perfil de prueba: los numeros que produce NO son resultados reportables." -ForegroundColor Yellow
}
Write-Host ""

$inicio = Get-Date
foreach ($etapa in $seleccion) {
  if ($etapa.onlyMatlab -and $Engine -ne 'matlab') {
    Write-Host "--- etapa $($etapa.n): $($etapa.name) (omitida: solo aplica al motor matlab) ---" -ForegroundColor DarkGray
    continue
  }
  Write-Host "--- etapa $($etapa.n): $($etapa.name) ---" -ForegroundColor Cyan
  $t0 = Get-Date
  & $Python (Join-Path $py $etapa.script) @($etapa.args)
  if ($LASTEXITCODE -ne 0) {
    Write-Host "etapa $($etapa.n) ($($etapa.name)) fallo con codigo $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
  }
  Write-Host ("etapa {0} ok ({1:N1} min)" -f $etapa.n, ((Get-Date) - $t0).TotalMinutes) -ForegroundColor Green
  Write-Host ""
}

if ($CompareWith -ne '') {
  Write-Host "--- comparacion contra $CompareWith ---" -ForegroundColor Cyan
  & $Python (Join-Path $py 'compare_runs.py') `
      '--left' $CompareWith '--right' "${Profile}:${Engine}" '--strict'
  if ($LASTEXITCODE -ne 0) {
    Write-Host "la comparacion encontro momentos divergentes" -ForegroundColor Red
    exit $LASTEXITCODE
  }
  Write-Host ""
}

Write-Host ("Pipeline completo en {0:N1} min" -f ((Get-Date) - $inicio).TotalMinutes) -ForegroundColor Green
Write-Host "Resultados: outputs\tables\  outputs\figures\  outputs\moments\"
