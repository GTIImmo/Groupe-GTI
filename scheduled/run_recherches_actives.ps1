# Tache planifiee : RUN RECHERCHES ACTIVES (03:00) — filet de fond (n°5).
# Rafraichit les contacts a recherche active depuis Hektor SANS filtre date_maj
# (capte les edits de recherche faits dans Hektor que le quotidien --changed-only manque).
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "recherches_actives_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
try {
    Write-Output "=== Recherches actives demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    # Aucun reglage de cadence ici : le script porte desormais les valeurs de la methode de
    # reference (lots de 100, 0,5 s entre fiches, 60 s entre lots) -- voir
    # notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md. Ce run passe donc de ~21 min a
    # ~1 h 10 pour ses 3 800 fiches : il demarre a 03:00 et finit tres avant le quotidien
    # de 05:30. Et il ne fait plus qu'UNE authentification au lieu de 13.
    & $py (Join-Path $root "phase2\sync\sync_active_searches.py")
    $code = $LASTEXITCODE
    Write-Output "=== Recherches actives termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
    if ($code -ne 0) { $runFailed = $true }
} catch {
    Write-Output "=== ERREUR recherches actives : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "recherches_actives_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Correctif 2026-08-19 : PROPAGER l'echec au Planificateur de taches.
# sync_active_searches.py rend 1 des qu'un lot echoue, mais ce code n'etait
# qu'affiche : le script sortait en 0, Windows enregistrait un succes, et la sonde
# concluait "0 en anomalie". C'est CE mecanisme qui a cache pendant 18 jours
# (01/08 -> 19/08) l'echec de 4 lots sur 13 chaque nuit, et avec lui la perte de
# 1104 recherches actives sur 3952 (27,9%) et 13384 rapprochements orphelins.
if ($runFailed) { exit 1 }
