# Tache planifiee : SAUVEGARDE des donnees locales irremplacables (07:00).
# Chantier Phase 0.1 -- voir notice/NOTE_AUDIT_MAITRE_2026-08-17.md section 5.
#
# Pourquoi 07:00 et pas dans le pipeline : le run quotidien se termine vers 06:25 ;
# on sauvegarde APRES (donnees fraiches) mais dans une tache SEPAREE, pour que la
# sauvegarde ait lieu meme les jours ou le pipeline echoue -- precisement les jours
# ou l'on peut en avoir besoin.
#
# Niveaux : quotidien = tables critiques (~8 Mo) ; dimanche = + instantane phase2
# (~220 Mo). Retention glissante geree par le script Python (90 j / 28 j).
#
# 2026-08-18 : le niveau 3 (archive zip des documents) est DESACTIVE dans
# backup_critical.py (constante DOCUMENTS_ARCHIVE_ENABLED). Les 32,5 Go de documents
# sont desormais couverts hors site par l'agent OVH Backup Agent / Veeam. Le zip n'en
# etait qu'une seconde copie sur le meme disque, pour ~30 Go par passe et ~122 Go en
# retention. Voir notice/NOTE_PLAN_SAUVEGARDE_2026-08-18.md section 1.2.
# Empreinte en regime stable apres cette bascule : ~1 Go.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "backup_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
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
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "backup_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Correctif 2026-08-19 : PROPAGER l'echec au Planificateur de taches.
# Le `throw` ci-dessus etait bien leve sur un exit code non nul, mais le catch
# l'avalait et le script sortait en 0 -> Windows enregistrait un succes. Une
# sauvegarde qui echoue chaque nuit serait restee invisible, precisement sur la
# tache la moins surveillee (elle n'est meme pas dans la liste des taches suivies
# par check_gti_health.py). Voir notice/NOTE_BRIEF_SAUVEGARDE_2026-08-18.md, P3.
if ($runFailed) { exit 1 }
