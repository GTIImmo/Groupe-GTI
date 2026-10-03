# Tache planifiee : RUN QUOTIDIEN complet (05:30).
# Invocation identique a la commande manuelle de reference :
#   run_full_pipeline.ps1 -PushContactsToSupabase -ContactsEligibleOnly
# (annonces + mandats + contacts eligibles + chauffage + Matterport + Android ;
#  photos/documents Console NON traites = opt-in non activé).
#
# -IncludeArchivedContactSearches (21/08/2026) : on cesse de supprimer de Supabase une
# recherche que Hektor vient d'archiver. Sa ligne disparaissait, et tout ce qui pointait
# sur sa cle -- propositions, relances, retours acquereur, rapprochements -- devenait
# orphelin. Desormais elle reste, marquee inactive. Le moteur de rapprochement ne la
# calcule plus (verrou pose le meme jour) et le front ne la liste plus.
#
# -StartAtLabel (03/10/2026) : RATTRAPER un run interrompu, sans rien recopier.
#   Le 03/10 le run s'est arrete a 08:21 ; 17 etapes n'ont jamais demarre, dont
#   toutes les montees vers le cloud. On relance ALORS CETTE MEME ENVELOPPE, avec
#   LES MEMES drapeaux ci-dessous, en ajoutant seulement l'etiquette de reprise :
#     .\scheduled\run_quotidien.ps1 -StartAtLabel "phase2 perimetre contacts cites par la console"
#   ⛔ Ne remplace pas un run complet : suppose que les etapes sautees ont deja
#     tourne le jour meme. Si l'etiquette n'existe pas, le pipeline LEVE une erreur
#     au lieu de dire « reussi » sans rien faire.
param(
    [string]$StartAtLabel = ""
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "quotidien_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
try {
    Write-Output "=== Run quotidien demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    # ⚠ UN SEUL CHEMIN, et c'est volontaire : on transmet TOUJOURS -StartAtLabel.
    #   Vide, il ne change rien (c'est le defaut du pipeline). Deux invocations
    #   differentes selon le cas finiraient par diverger sur un drapeau -- et la
    #   nuit ne passerait plus par la ligne qu'on a eprouvee le jour.
    & "$root\run_full_pipeline.ps1" -PushContactsToSupabase -ContactsEligibleOnly -AllowStaleSupabaseDeletes -IncludeArchivedContactSearches -StartAtLabel $StartAtLabel
    Write-Output "=== Run quotidien termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $LASTEXITCODE) ==="
} catch {
    Write-Output "=== ERREUR run quotidien : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "quotidien_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Correctif 2026-08-19 : PROPAGER l'echec au Planificateur de taches.
# Sans ce bloc, le catch ci-dessus avalait l'exception et le script sortait en 0 :
# Windows enregistrait LastTaskResult=0 (succes), et check_gti_health.py -- qui lit
# ce code -- concluait "0 en anomalie". Constate le 19/08 : le run s'est arrete a
# l'etape 13/23 (chauffage), les 3 publications Supabase n'ont jamais tourne, et
# aucune alerte n'est partie. run_full_pipeline.ps1 leve une exception via
# Invoke-Step sur toute etape bloquante -> le catch est le signal fiable ici
# (ne PAS tester $LASTEXITCODE : apres l'appel d'un .ps1 il reflete la derniere
# commande native executee a l'interieur, non le succes global).
if ($runFailed) { exit 1 }
