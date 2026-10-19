# Tache planifiee : BALAYAGE DES PHOTOS MASQUEES (00:00)                19/10/2026
#
# POURQUOI ELLE EXISTE. Depuis le 18/05, deux flux ramenent nos photos et un seul
#   voit les MASQUEES : le flux API nocturne ne connait que les visibles, la couche
#   Console connait les deux -- et personne ne l'empile plus depuis le 17/08.
#   Mesure du 19/10, en direct sur 200 annonces : 1,5 % du parc porte des photos
#   masquees qu'on n'a pas, soit ~490 annonces et ~1 100 photos sur le parc vivant.
#   Le jour de la coupure, elles seraient perdues.
#
# ⚠⚠ CETTE TACHE NE PARLE JAMAIS A HEKTOR. Elle POSE des travaux (quelques
#    secondes), et c'est le worker « documents » qui appelle Hektor -- avec SES
#    freins : 1 s entre appels, 60 s toutes les 100 lectures, 300 s toutes les
#    2 000, arret net au premier refus, 15 s de recul apres un rejet.
#    ⭐ C'EST TOUT L'INTERET : un script a nous aurait son PROPRE frein, et les
#      deux s'additionneraient. « Un frein ne protege QU'A L'INTERIEUR d'un
#      client » -- c'est la cause du bannissement du 17/09. Mesure du 19/10 :
#      `sync_hektor_photos` n'est reclame que par worker_kind « documents »,
#      donc UN SEUL processus, UN SEUL frein.
#
# POURQUOI 00:00, ET POURQUOI 1 000 -- les deux sont MESURES, pas choisis.
#   LE CRENEAU : « GTI Entretien Documents » part a 22:00 et finit 23:17 a 23:25
#   (trois nuits mesurees) ; « Recherches Actives » part a 03:00. Le creux va donc
#   de ~23:18 a 03:00, soit 3 h 42. On demarre a 00:00 pour garder 40 min de marge
#   apres l'entretien.
#   LA TAILLE : la duree MEDIANE d'un travail `sync_hektor_photos` est de 10 s
#   (315 travaux reels : moyenne 12 s, max 79 s). Donc :
#         2 h 30 de creux -> ~868 annonces      3 h 42 -> ~1 285 annonces
#   ⛔ UN LOT DE 2 000 AURAIT PRIS 5,8 A 6,6 HEURES et deborde sur les recherches
#     de 03:00 puis le run de 05:00. C'est la mesure qui a corrige mon premier
#     chiffre -- j'avais calcule sur le quota Hektor alors que la contrainte
#     reelle est LE TEMPS DE DIGESTION DU WORKER.
#   ⚠ ET LE QUOTA EST TENU AUSSI : 1 000 annonces = 2 000 requetes (les DEUX
#     galeries), a ajouter aux ~4 500 que la nuit consomme deja -> ~6 500, sous la
#     cible posee par Frederic le 20/08 (« rester 40 % sous le seuil de
#     13 000-17 000 requetes »).
#
# ⭐⭐ UN SEUL LOT, DEUX PARTS -- et c'est ce qui evite deux taches qui se bloquent.
#    Deux taches separees se casseraient les dents : celle de mise a jour poserait
#    ~29 travaux, puis le balayage verrait « la file n'est pas vide » et refuserait
#    son lot entier. Donc UN lot, rempli dans cet ordre : les annonces dont LA DATE
#    A BOUGE d'abord, les JAMAIS VISITEES ensuite.
#    ⭐ QUAND LE BALAYAGE SERA FINI, le lot tombera tout seul a ~29 par nuit et
#      cette tache DEVIENDRA le run de mise a jour. Pas d'interrupteur a basculer,
#      pas de deuxieme tache a ecrire.
#
# LE PERIMETRE : LES 13 491 VIVANTES SEULEMENT -- decision du 19/10, declaree dans
#   l'empileur (HORS_AUTO). Une annonce ARCHIVEE n'est publiee NULLE PART (la
#   vitrine filtre archive=0 et statut Actif/Sous offre/Sous compromis), son taux
#   de masquees est de 0,7 % contre 3,6 % sur les vivantes, et les 44 277 archives
#   + historiques couteraient 44 NUITS pour ~700 photos. `--scope archive` reste
#   disponible A LA MAIN.
#
# LES DEUX REFUS, ET ILS SORTENT EN 1 (convention du projet : un refus doit se VOIR
#   au Planificateur et dans check_gti_health) :
#     code 3  la file n'est pas vide -> le worker est plus lent que le lot.
#             ⭐ C'EST LA GARDE QUI REGULE LA TAILLE TOUTE SEULE. Si elle sort
#               plusieurs nuits de suite : baisser -Limite.
#     code 4  10 erreurs ou plus en 24 h -> Hektor nous rejette peut-etre. On
#             s'arrete. « Un 403 arrete tout, on ne rejoue jamais. »
#
# ⚠ LA FENETRE DE POSE. La tache refuse de poser passe 01:00 : un lot pose a 02:00
#   ferait travailler le worker jusqu'a 05:00 et plus. Ce n'est pas la meme chose
#   que de borner le worker -- c'est borner le DEPART.
#
#   .\scheduled\run_balayage_photos_masquees.ps1            <- POSE (comme la tache)
#   .\scheduled\run_balayage_photos_masquees.ps1 -DryRun    <- compte, ne pose RIEN

param(
    [int]$Limite = 1000,
    [int]$MaxErreursRecentes = 10,
    [int]$HeureLimite = 1,
    [switch]$DryRun,
    [switch]$IgnorerFenetre
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "balayage_photos_masquees_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$echecs = @()
$codeNode = 0
try {
    Write-Output "=== Balayage photos masquees demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LA FENETRE DE POSE : on borne le DEPART, pas le worker. Un lot pose a 02:00
    #   ferait travailler le worker jusqu'a 05:00 et au-dela, sur les recherches
    #   actives puis le run quotidien.
    $heure = (Get-Date).Hour
    if (-not $IgnorerFenetre -and -not $DryRun -and $heure -gt $HeureLimite) {
        Write-Output "=== REFUS : il est ${heure}h, au-dela de la fenetre de pose (jusqu'a ${HeureLimite}h). Rien n'est pose. ==="
        Write-Output "    (un lot pose maintenant ferait travailler le worker sur les recherches de 03:00 et le run de 05:00)"
        Stop-Transcript | Out-Null
        exit 1
    }

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell rend la CHAINE
    # et non un tableau ; [0] donne alors son PREMIER CARACTERE (« C »).
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $empileur = Join-Path $root "Console\enqueue_photos_masquees_lot.js"
    if (-not (Test-Path -LiteralPath $empileur)) { throw "Script introuvable : $empileur" }

    # ⛔⛔ CETTE FONCTION NE DOIT RIEN ECRIRE SUR LE FLUX DE SORTIE.
    #   EN POWERSHELL, TOUT CE QU'UNE FONCTION ECRIT SUR LE FLUX DE SORTIE FAIT PARTIE
    #   DE SA VALEUR DE RETOUR. Ecrite ainsi le 15/10 dans la tache documents, elle
    #   rendait un TABLEAU -- et `-not` d'un tableau non vide vaut $false, donc UNE
    #   LIGNE EN ECHEC N'ETAIT JAMAIS COMPTEE : la tache sortait 0, le planificateur
    #   etait vert et le moniteur se taisait. 6e fois de cette famille dans ce projet.
    #   REMEDE : `Write-Host` (va a l'hote, donc au journal de transcription, pas au
    #   flux) et `| Out-Host` sur l'appel a node. $LASTEXITCODE reste renseigne.
    #   La fonction ne rend donc QU'UN SEUL booleen.
    #   ⚠ RECOPIEE A L'OCTET PRES depuis run_entretien_documents.ps1 et
    #     run_entretien_photos.ps1 : l'epreuve scheduled\test_detecteur_echec_entretien.ps1
    #     EXIGE que les trois taches portent exactement la meme. Si elles divergent,
    #     elle passe au rouge et dit de dedoubler l'epreuve.
    function Invoke-Ligne {
        param([string]$Titre, [string[]]$Arguments)
        Write-Host "--- $Titre"
        & $nodeExe @Arguments | Out-Host
        $code = $LASTEXITCODE
        if ($code -ne 0) {
            Write-Host "--- $Titre : ECHEC (code $code)"
            return $false
        }
        return $true
    }

    $args1 = @($empileur, "--limit", "$Limite", "--exiger-file-vide",
               "--max-erreurs-recentes", "$MaxErreursRecentes")
    if ($DryRun) { $args1 += "--dry-run" }

    $ok = Invoke-Ligne -Titre "1/1 l'EMPILEUR (pose des travaux, ne parle pas a Hektor)" -Arguments $args1
    # ⚠ ON RELIT $LASTEXITCODE DANS L'APPELANT pour distinguer un REFUS (3, 4) d'une
    #   PANNE (1). Invoke-Ligne ne rend qu'un booleen -- et elle ne doit pas changer,
    #   l'epreuve exige qu'elle soit identique dans les trois taches.
    $codeNode = $LASTEXITCODE
    if (-not $ok) { $echecs += "empileur(code $codeNode)" }

    if ($echecs.Count -gt 0) {
        switch ($codeNode) {
            3 { Write-Output "=== REFUS 3 : la file n'est pas vide -- le worker est plus lent que le lot. Baisser -Limite si ca se repete. ===" }
            4 { Write-Output "=== REFUS 4 : trop d'erreurs en 24 h -- Hektor nous rejette peut-etre. ON NE REJOUE PAS. ===" }
            default { Write-Output "=== Balayage photos masquees termine AVEC ECHECS : $($echecs -join ', ') ===" }
        }
    } else {
        Write-Output "=== Balayage photos masquees termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- la ligne est passee ==="
    }
} catch {
    Write-Output "=== ERREUR balayage photos masquees : $_ ==="
    $echecs += "exception"
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "balayage_photos_masquees_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# ⚠ LE CODE DE SORTIE DOIT SE VOIR DANS LE PLANIFICATEUR, sinon la tache passe pour
#   verte alors qu'elle n'a rien fait -- defaut rebouche SIX fois dans ce projet
#   (sauvegarde 19/08, descente 08/09, recherches actives 23/09, rattrapage documents
#   26/09 a moitie, sa liste de surveillance le 15/10, le detecteur du 16/10).
if ($echecs.Count -gt 0) { exit 1 }
exit 0
