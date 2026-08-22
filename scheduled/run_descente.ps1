# Tache planifiee : LA DESCENTE (07:30) -- Supabase vers le serveur (blocs B.1, B.2, B.4).
#
# POURQUOI 07:30, et pas ailleurs.
#   03:00  recherches actives
#   05:30  run quotidien -> ~06:32   il POUSSE la journee vers Supabase
#   07:00  sauvegarde                 instantane de phase2.sqlite
#   07:30  ICI                        ~20 min, fin vers 07:50
# La descente doit lire Supabase APRES que le run de nuit y ait pousse la journee, et
# APRES la sauvegarde -- sinon elle ecrirait dans phase2.sqlite pendant qu'on en fait un
# instantane.
#
# DEUX ETAPES, dans cet ordre :
#   1. pull_from_supabase.py    refait les 120 copies locales (dont les 10 doublures __sb)
#   2. comparer_doublures.py    compte les ecarts et ecrit la photo du jour dans le journal
# La seconde n'a de sens qu'apres la premiere : elle mesure ce que la descente vient de
# poser. Si la descente echoue, on releve quand meme -- la photo dira alors qu'elle date.
#
# ⚠ LA DESCENTE EST LA PLUS LOURDE DE TOUTES LES TACHES qui parlent a Supabase. C'est elle
# qui a sature l'instance jusqu'au redemarrage dans la nuit du 21 au 22/08 -- deux passes
# lancees en une heure, ~2 800 requetes sans frein. Elle porte desormais trois freins
# (pauses, tables legeres d'abord, verrou contre le chevauchement) ; ne pas les retirer, et
# regarder ses premiers matins avant de considerer que c'est acquis.
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "descente_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
try {
    Write-Output "=== Descente demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    Write-Output "--- 1/2 descente Supabase -> serveur ---"
    & $py (Join-Path $root "phase2\sync\pull_from_supabase.py")
    $codeDescente = $LASTEXITCODE
    Write-Output "--- descente terminee (exit $codeDescente) ---"
    if ($codeDescente -ne 0) { $runFailed = $true }

    # Le releve tourne MEME si la descente a echoue : mieux vaut une photo qui dit
    # « les doublures datent d'hier » qu'aucune photo du tout.
    Write-Output "--- 2/2 releve des doublures ---"
    & $py (Join-Path $root "phase2\checks\comparer_doublures.py")
    $codeReleve = $LASTEXITCODE
    Write-Output "--- releve termine (exit $codeReleve) ---"
    if ($codeReleve -ne 0) { $runFailed = $true }

    Write-Output "=== Descente terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
} catch {
    Write-Output "=== ERREUR descente : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "descente_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# PROPAGER L'ECHEC AU PLANIFICATEUR -- meme correctif que run_recherches_actives.ps1 le
# 19/08 : un exit 0 menteur avait cache 18 jours de lots en echec, et avec eux la perte de
# 1 104 recherches actives. Windows doit voir l'echec, sinon la sonde conclut « 0 anomalie ».
if ($runFailed) { exit 1 }
