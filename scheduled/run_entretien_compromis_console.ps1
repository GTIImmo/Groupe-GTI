# ENTRETIEN DES COMPROMIS PAR LA CONSOLE -- pour que le stock ne se reforme pas
# ===========================================================================
#
# LE RATTRAPAGE EST FINI le 11/09/2026 : 9 216 compromis lus sur 9 225 lisibles,
# zero erreur. Les 9 restants portent `present_in_hektor = false` -- Hektor ne
# les rend plus, donc personne ne peut les ouvrir.
#
# CE SCRIPT EXISTE POUR QUE CE TRAVAIL NE SOIT PAS A REFAIRE. Sans lui, les
# compromis nouveaux n'entrent jamais dans la lecture console, et ceux qui
# changent chez Hektor gardent chez nous l'etat du jour ou on les a lus.
#
# IL NE PREND QUE LES NOUVEAUX ET CE QUI A BOUGE. Pas de relecture tournante :
#     --suivre-annonce   reprendre une fiche quand la date de son BIEN est
#                        posterieure a notre derniere lecture
#     --stale-days 0     donc AUCUNE relecture a l'age
#     --limit            ceinture, jamais atteinte en regime normal
# Il ecarte les compromis annules (Hektor REFUSE de les ouvrir) et s'efface
# devant un travail de la console.
#
# /!\ POURQUOI LA DATE DU BIEN EST LE BON SIGNAL. Tache 0.3, MESUREE le 03/09 :
#   " seul l'ENREGISTREMENT la deplace ". Quatre positifs et quatre
#   contre-temoins -- elle ne derive pas seule, la LECTURE ne la touche pas,
#   ouvrir l'assistant et fermer SANS enregistrer ne la touche pas.
#   Le signal est LARGE (le bien bouge aussi pour une photo ou un prix) : il se
#   trompe DU BON COTE. On relit parfois pour rien, jamais on ne rate une
#   transaction modifiee.
#
# --- LE VOLUME, MESURE LE 11/09 ET NON ESTIME ---
#     compromis lus                                9 216
#     dont le bien a bouge depuis notre lecture        1   <- tout le travail
#     compromis nouveaux                            ~5 par jour
# Une rotation a 90 jours en aurait relu CENT PAR NUIT pour rien. En regime
# normal ce script lit une poignee de fiches et se termine en quelques secondes.
#
# --- LA CADENCE NE CHANGE PAS ---
# Celle de notice/NOTE_EXTRACTION_CHAUFFAGE_HEKTOR_2026-06-09.md : 1 requete par
# compromis, 0,5 s entre deux, lots de 100 avec 60 s. La seule methode console
# qui n'ait JAMAIS rien declenche.
#
# --- LES DEUX CEINTURES, GARDEES ---
#   -StopAt 04:30   il s'arrete entre deux lots avant l'heure dite. Le run
#                   quotidien de 05:00 fait LUI AUSSI de l'extraction console :
#                   deux flux en meme temps, c'est le doublement de debit qui a
#                   fait bannir notre IP en juillet.
#   -Courtoisie     il s'efface tant qu'un travail worker tourne.
#
# /!\ IL N'ECRIT RIEN CHEZ HEKTOR : il n'envoie que l'OUVERTURE de l'assistant.
#   L'enregistrement porte `actionContainer[] = save + treat`, et ces deux mots
#   n'existent pas dans son code.
#
#     .\scheduled\run_entretien_compromis_console.ps1
#     .\scheduled\run_entretien_compromis_console.ps1 -Limit 300
# ===========================================================================
param(
    [string]$StopAt = "04:30",
    [int]$Limit = 150,
    # 0 = aucune relecture a l'age. On ne relit QUE ce qui a bouge.
    [int]$StaleDays = 0,
    [switch]$SansCourtoisie
)

# Continue : un avertissement ne doit pas interrompre le run. Les vrais echecs
# sont rendus par le CODE DE SORTIE du script python.
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

$script = Join-Path $root "phase2\sync\sync_hektor_compromis_console.py"
$journal = Join-Path $root ("logs\scheduled\entretien_compromis_" +
    (Get-Date -Format "yyyy-MM-dd_HH-mm-ss") + ".log")
New-Item -ItemType Directory -Force -Path (Split-Path $journal) | Out-Null

$argsPy = @($script, "--limit", "$Limit", "--stale-days", "$StaleDays",
            "--suivre-annonce", "--refresh-session-on-expired")
if ($StopAt) { $argsPy += @("--stop-at", $StopAt) }
if (-not $SansCourtoisie) { $argsPy += "--courtoisie" }

Write-Output "=== ENTRETIEN COMPROMIS CONSOLE -- depart $(Get-Date -Format 'HH:mm:ss') ==="
Write-Output "    nouveaux + biens modifies   plafond : $Limit   arret : $StopAt"

# /!\ PAS DE `2>&1` ICI. PowerShell 5.1 enveloppe chaque ligne d'erreur d'un
# executable natif dans un ErrorRecord : une simple ligne de progression suffit
# alors a tuer le run. Mesure du 10/09, le rattrapage s'est arrete net apres
# 2 000 compromis pour cette raison.
& $py $argsPy | Tee-Object -FilePath $journal
$code = $LASTEXITCODE

# /!\ UN 403 N'EST PAS UN INCIDENT A REESSAYER, C'EST LE DEBUT D'UN BANNISSEMENT.
if ($code -eq 3) {
    Write-Output "=== ARRET SUR 403 -- NE PAS RELANCER. Verifier depuis une AUTRE IP. ==="
} elseif ($code -ne 0) {
    Write-Output "=== ARRET, code $code -- voir le journal ==="
} else {
    Write-Output "=== TERMINE $(Get-Date -Format 'HH:mm:ss') ==="
}
exit $code
