# Tache planifiee : LA NUIT DES CONTACTS, PUIS LES RECHERCHES                03/11/2026
#
# Note : notice/SYNTHESE_CHANTIER_CONTACTS_COUPLES_2026-11-01.md sections 40 a 48.
#
# POURQUOI. La nuit ne relit une fiche contact que si elle remonte en tete de la liste
#   triee par « date de dernier traitement ». Un rattachement de couple (EA32621,
#   02/11) change la date de modification de la fiche, PAS cette date : la fiche
#   n'est jamais relue. Le passage a blanc du 03/11 (8 503 pages, 1 h 18, 0 refus)
#   a compte 236 fiches ainsi ratees sur les actifs.
#
# « TOUT DANS UNE TACHE » (decision de Frederic, 03/11) : cette tache remplace le
#   SEUL lanceur de « GTI Recherches Actives ». Elle enchaine :
#     1. la liste entiere des contacts (actifs du lundi au samedi, archives le
#        dimanche), par l'API seule, a la vitesse d'avant le 07/09 -- APRES que le
#        worker a fini son balayage des photos (garde « file vide ») ;
#     2. les fiches modifiees, AU FREIN ACTUEL (seule la liste va plus vite) ;
#     3. les recherches, PAR LE MEME SCRIPT QU'AUJOURD'HUI, inchange, lance comme la
#        tache le lance aujourd'hui, et JAMAIS AVANT $HeureRecherches.
#   ⛔ « Les recherches ne changent pas : ne touche a rien » -- ni leur code, ni leur
#     vitesse, ni leur heure de depart (02:00 a l'horloge des declencheurs).
#
# L'HORLOGE. Les declencheurs du projet sont ecrits en +01:00 : l'ete, toute la nuit
#   glisse d'une heure locale. Les heures de ce script sont lues a la MEME horloge
#   (UTC+1 fixe), dans PowerShell comme dans le script Python.
#
# LES CODES. Sortie 1 si les recherches echouent, ou si la liste s'arrete sur un
#   refus (3) ou une panne (4) de Hektor -- un refus doit se VOIR au Planificateur et
#   dans check_gti_health. Une nuit SANS liste parce que le worker n'a pas fini est
#   ecrite au journal et au rapport, et ne fait pas sortir en 1.
#   ⚠ APRES UN REFUS DE HEKTOR, LES RECHERCHES NE PARTENT PAS (« un 403 arrete
#     tout, on ne rejoue jamais ») -- sauf -RecherchesMalgreRefus. A TRANCHER PAR
#     FREDERIC avant la bascule : aujourd'hui les recherches partent chaque nuit.
#
# RETOUR ARRIERE : remettre l'action de la tache sur run_recherches_actives.ps1 a
#   02:00 (scheduled/installer_tache_nuit_contacts.ps1 -Retour). Ou, sans toucher a
#   la tache : -SansListe fait EXACTEMENT ce que faisait l'ancienne action.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File scheduled\run_nuit_contacts_et_recherches.ps1

param(
    [string]$HeureLimiteListe = "01:55",
    [string]$HeureLimiteFiches = "01:58",
    [string]$HeureRecherches = "02:00",
    [int]$IntervalleMs = 400,
    [switch]$SansListe,
    [switch]$RecherchesMalgreRefus
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "nuit_contacts_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

# L'heure a l'horloge des declencheurs (+01:00), au format HH:mm.
function Get-HeureDeclencheurs { return [DateTime]::UtcNow.AddHours(1) }

$runFailed = $false
$codeListe = 0
$codeRecherches = 0
try {
    Write-Output "=== Nuit des contacts demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (horloge des declencheurs $((Get-HeureDeclencheurs).ToString('HH:mm'))) ==="

    if ($SansListe) {
        Write-Output "=== -SansListe : la liste des contacts est sautee (ancien comportement) ==="
    } else {
        $env:PYTHONIOENCODING = "utf-8"
        & $py (Join-Path $root "phase2\sync\liste_contacts_nuit.py") `
            --scope auto --reel --attendre-file-vide `
            --intervalle-ms $IntervalleMs `
            --heure-limite $HeureLimiteListe `
            --heure-limite-fiches $HeureLimiteFiches
        $codeListe = $LASTEXITCODE
        Write-Output "=== Liste des contacts terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $codeListe) ==="
        if ($codeListe -ne 0) { $runFailed = $true }
    }

    if ($codeListe -eq 3 -and -not $RecherchesMalgreRefus) {
        Write-Output "=== REFUS DE HEKTOR pendant la liste : les recherches NE PARTENT PAS cette nuit ==="
    } else {
        # Jamais avant l'heure d'aujourd'hui : « les recherches ne changent pas ».
        $h, $m = $HeureRecherches.Split(":")
        $cible = (Get-HeureDeclencheurs).Date.AddHours([int]$h).AddMinutes([int]$m)
        $maintenant = Get-HeureDeclencheurs
        # Un depart du soir (20:00 ou plus tard) vise 02:00 le LENDEMAIN ; un lancement a la
        # main dans la journee n'attend pas.
        if ($maintenant.Hour -ge 20) { $cible = $cible.AddDays(1) }
        if ($maintenant -lt $cible) {
            $attente = [int][Math]::Ceiling(($cible - $maintenant).TotalSeconds)
            Write-Output "=== Attente de $HeureRecherches (horloge des declencheurs) : $attente s ==="
            Start-Sleep -Seconds $attente
        }
        Write-Output "=== Recherches actives : lancement $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
        # Lance EXACTEMENT comme l'action d'aujourd'hui (processus a part, son propre journal).
        & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass `
            -File (Join-Path $root "scheduled\run_recherches_actives.ps1")
        $codeRecherches = $LASTEXITCODE
        Write-Output "=== Recherches actives terminees $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $codeRecherches) ==="
        if ($codeRecherches -ne 0) { $runFailed = $true }
    }
} catch {
    Write-Output "=== ERREUR nuit des contacts : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "nuit_contacts_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

if ($runFailed) { exit 1 }
