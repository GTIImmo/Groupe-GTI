# Tache planifiee : SAUVEGARDE des donnees locales irremplacables (07:00).
# Chantier Phase 0.1 -- voir notice/NOTE_AUDIT_MAITRE_2026-08-17.md section 5.
#
# Pourquoi 07:00 et pas dans le pipeline : le run quotidien se termine vers 06:25 ;
# on sauvegarde APRES (donnees fraiches) mais dans une tache SEPAREE, pour que la
# sauvegarde ait lieu meme les jours ou le pipeline echoue -- precisement les jours
# ou l'on peut en avoir besoin.
#
# Niveaux : quotidien = tables critiques (~8 Mo) ; dimanche = + instantane phase2
# (~220 Mo) + archive documents (~51 Mo). Retention glissante geree par le script
# Python (90 j / 28 j). Empreinte en regime stable : ~1,8 Go.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "backup_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
try {
    Write-Output "=== Sauvegarde demarree $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    # Le dimanche, on ajoute l'instantane complet de phase2 + les documents.
    $args = @("$root\phase2\sync\backup_critical.py")
    if ((Get-Date).DayOfWeek -eq 'Sunday') {
        $args += "--weekly"
        Write-Output "Dimanche -> niveaux 2 et 3 inclus"
    }
    & "$root\.venv\Scripts\python.exe" @args
    $code = $LASTEXITCODE
    Write-Output "=== Sauvegarde terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
    if ($code -ne 0) { throw "backup_critical.py a echoue (exit $code)" }
} catch {
    Write-Output "=== ERREUR sauvegarde : $_ ==="
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "backup_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
