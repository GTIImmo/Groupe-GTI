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
try {
    Write-Output "=== Recherches actives demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    & $py (Join-Path $root "phase2\sync\sync_active_searches.py")
    Write-Output "=== Recherches actives termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $LASTEXITCODE) ==="
} catch {
    Write-Output "=== ERREUR recherches actives : $_ ==="
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "recherches_actives_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
