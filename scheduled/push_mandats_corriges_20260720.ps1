# Pousse vers Supabase les annonces dont les mandats ont ete corriges le 20/07/2026
# (cle primaire hektor_mandat passee sur le couple (annonce, mandat) + rattrapage
# depuis hektor_annonce_detail.mandats_json).
#
# Aucun appel API Hektor : la reconstruction locale est deja faite
# (build_case_index cible, bootstrap_phase2, refresh_views).
#
# Mode CIBLE : le script ne traite que les annonces listees, et dans ce mode
# push_upgrade_to_supabase force stale_ids = [] -- aucune suppression distante
# n'est possible. --skip-stale-deletes le verrouille une seconde fois.
#
# Les annonces portant une edition optimiste en attente (app_annonce_pending) sont
# volontairement ignorees par le push : elles recevront la correction plus tard.

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$idsFile = Join-Path $PSScriptRoot "ids_mandats_corriges_20260720.txt"

$ids = Get-Content $idsFile | Where-Object { $_.Trim() -ne "" }
Write-Host "Push cible de $($ids.Count) annonces vers Supabase..."

$arguments = @(
    "phase2\sync\push_upgrade_to_supabase.py",
    "--dossier-batch-size", "50",
    "--detail-batch-size", "25",
    "--work-item-batch-size", "50",
    "--filter-batch-size", "50",
    "--skip-stale-deletes"
)
foreach ($id in $ids) { $arguments += @("--hektor-annonce-id", $id.Trim()) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    Write-Host "ECHEC (code $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Push termine." -ForegroundColor Green
