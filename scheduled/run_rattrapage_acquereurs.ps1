# RATTRAPAGE ACQUEREURS — relit chez Hektor la fiche de TOUS les contacts de
# typologie « acquereur » (~71 300), pas seulement ceux dont l'app connait deja une
# recherche active (~3 800, run de 03:00).
#
# POURQUOI. Creer une recherche dans Hektor ne bouge pas la date_maj du contact, et
# les recherches ne sont PAS dans le listing : elles ne sont que dans ContactById.
# Un contact qui gagne sa PREMIERE recherche n'entre donc dans aucun run et reste
# invisible indefiniment. Sonde du 21/08/2026, 249 fiches lues en direct : 1 portait
# une recherche que l'app ignorait -> environ 270 recherches invisibles.
#
# CADENCE. --pause-between-batches 20 : 300 fiches d'affilee (~50 s, exactement la
# rafale d'une nuit normale) puis 20 s de repos. 4,2 appels/s en moyenne au lieu de 6.
# Tenir 6 appels/s pendant des heures est la forme qui a fait bannir notre IP au
# rattrapage des documents — ne pas retirer cette pause.
#
# REPRENABLE : chaque lot est independant, un lot en echec n'arrete pas le run.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "rattrapage_acquereurs_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
try {
    Write-Output "=== Rattrapage acquereurs demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    & $py (Join-Path $root "phase2\sync\sync_active_searches.py") `
        --scope acquereurs --pause-between-batches 20
    $code = $LASTEXITCODE
    Write-Output "=== Rattrapage acquereurs termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
    if ($code -ne 0) { $runFailed = $true }
} catch {
    Write-Output "=== ERREUR rattrapage acquereurs : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "rattrapage_acquereurs_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
# Propage l'echec au Planificateur (meme correctif que run_recherches_actives.ps1,
# 19/08 : un exit 0 menteur avait cache 18 jours de lots en echec).
if ($runFailed) { exit 1 }
