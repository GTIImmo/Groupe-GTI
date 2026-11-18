# Tache planifiee : MENAGE DES FICHIERS TEMPORAIRES DU COFFRE (13:00)       18/11/2026
#
# POURQUOI ELLE EXISTE. Plusieurs chemins deposent des fichiers sous temp/ du coffre
#   hektor-console-documents, et aucun ne les retire tous :
#     temp/uploads/<travail>/  et  temp/photos/<travail>/   -- les envois de l'ecran vers Hektor
#     temp/assistant/<personne>/<numero>/                    -- le trombone de l'assistant (17/11)
#     temp/email/<personne>/<numero>/                        -- les pieces « depuis l'ordinateur »
#                                                               de la fenetre e-mail (18/11)
#   Le script Console/nettoyer_temporaires_orphelins.js existait depuis le 14/10, mais AUCUNE
#   tache ne le lancait (verifie le 18/11). Demande de Frederic le 18/11 : « aussi le menage
#   des fichiers temporaires ». Note etape 4 §63-64.
#
# ⚠ ELLE NE PARLE JAMAIS A HEKTOR : elle lit le coffre et deux tables, puis supprime au coffre.
#   Les QUATRE gardes du script decident fichier par fichier (chemin attendu, aucune ligne
#   vivante ne pointe dessus, aucun envoi en cours, au moins 2 jours). La liste datee de ce
#   qui existait est ecrite dans logs/ AVANT toute suppression.
#
# POURQUOI 13:00 : hors de la nuit (22:00 -> 07:45) et apres la reprise des envois (12:30).
#   Un fichier d'un envoi EN COURS est de toute facon retenu par la garde ③.
#
#   .\scheduled\run_menage_temporaires.ps1            <- SUPPRIME (comme la tache)
#   .\scheduled\run_menage_temporaires.ps1 -DryRun    <- compte, ne supprime RIEN

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "menage_temporaires_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$code = 0
try {
    Write-Output "=== Menage des temporaires demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    $arguments = @("Console\nettoyer_temporaires_orphelins.js")
    if (-not $DryRun) { $arguments += "--supprimer" }
    Push-Location $root
    try {
        & node @arguments
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    Write-Output "=== Fin $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- code $code ==="
} catch {
    Write-Output "=== ECHEC : $($_.Exception.Message) ==="
    $code = 1
}

Stop-Transcript | Out-Null
# Un ecart ou un echec sort en 1 : il doit se VOIR au Planificateur et dans check_gti_health.
if ($code -ne 0) { exit 1 }
exit 0
