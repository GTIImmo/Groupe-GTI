# Reconstruit integralement app_mandat_register_current dans Supabase.
#
# A lancer une fois, apres l'ajout du statut "Estimation" au perimetre du registre
# (commit 821a6bb) : le run quotidien travaille en delta et ne reposerait ces
# 139 lignes qu'au fil des modifications d'annonces, ce qui peut prendre des mois
# pour une estimation ancienne.
#
# Ce mode ne touche QUE la table du registre : ni les dossiers, ni les details,
# ni les index archive/historique, ni les work items. Il vide la table puis
# reinsere les ~23 818 lignes reconstruites depuis la base locale.
#
# Attendu apres execution :
#   Clos 16 326 | Vendu 6 638 | Actif 572 | Estimation 139 | Sous compromis 94 | Sous offre 49

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"

Write-Host "Reconstruction complete du registre des mandats..."
& $python "phase2\sync\push_upgrade_to_supabase.py" --rebuild-register-only
if ($LASTEXITCODE -ne 0) {
    Write-Host "ECHEC (code $LASTEXITCODE) -- le registre sera de toute facon reconstruit au prochain run quotidien." -ForegroundColor Red
    exit $LASTEXITCODE
}
Write-Host "Registre reconstruit." -ForegroundColor Green
