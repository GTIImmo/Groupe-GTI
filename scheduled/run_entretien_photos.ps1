# Tache planifiee : ENTRETIEN DES PHOTOS (21:00)                        19/10/2026
#
# POURQUOI ELLE EXISTE, ET POURQUOI SEPAREMENT.
#   Ce traitement etait la LIGNE 4/4 de « GTI Entretien Documents » depuis le
#   15/10 a 12:35. Frederic l'a releve le 18/10 : « on a normalement deja des run
#   quotidiens pour les photos, celui de 22h n'aurait pas du toucher aux photos ».
#   Il avait raison sur le fond -- verifie : NI « GTI Rattrapage Documents » (la
#   tache de 21:00), NI run_detection_documents.ps1 (14/10) ne portaient de ligne
#   photos. Elle est nee le 15/10, dans le commit qui refondait la tache en
#   quatre lignes, SANS etre soumise comme une decision a part.
#
#   ⚠ ET C'EST LE SEUL DES CINQ TRAITEMENTS PHOTOS QUI *RETIRE*. Les quatre
#     etapes du run de 05:00 AJOUTENT (rattrapage_photos telecharge,
#     generer_derives fabrique, remplir_adresses pose nos adresses,
#     sonde_photos surveille). Celui-ci seul ecrit `present_in_hektor = false`.
#     Le dangereux merite son nom, son journal et sa surveillance -- pas d'etre
#     cache dans une tache appelee « Documents ».
#
# POURQUOI 21:00, ET PAS 22:30 -- mesure du 18/10, question de Frederic.
#   Le script compare DEUX COPIES LOCALES, et il ne vaut que si les deux sont
#   fraiches :
#       le miroir Hektor (data/hektor.sqlite)  <- rafraichi par le run, ~06:47
#       notre registre  (phase2/phase2.sqlite) <- rafraichi par la DESCENTE,
#                                                 07:45, finie 08:03 a 08:49
#   ➡ A 05:00 aucune des deux n'est a jour ; A PARTIR DE ~09:00 les deux le sont.
#     L'heure n'etait donc pas imposee par 22:00 -- c'etait le wagon disponible.
#   ⛔ 22:30 etait un mauvais choix : « GTI Entretien Documents » part a 22:00 et
#     dure 1 h 17 a 1 h 25 (mesure sur trois nuits : fin 23:24, 23:20, 23:17).
#     On serait tombe en plein dedans.
#   ✅ 21:00 est LIBRE : c'est le creneau de « GTI Rattrapage Documents »,
#     desactivee le 15/10. Cette ligne dure ~2 min : finie a 21:02, bien avant
#     l'entretien des documents.
#   ⚠ L'ancienne tache garde son declencheur a 21:00 bien qu'elle soit Disabled.
#     Si on la reactivait un jour, les deux se marcheraient dessus. A savoir.
#   (Le matin, juste apres la descente, serait possible mais ECARTE : ce script
#    ecrit dans Supabase, et la regle du projet est de ne pas le charger en
#    journee -- « la descente mettait Supabase par terre ».)
#
# CE QUE LE SCRIPT FAIT, ET SES SEPT VERROUS : voir son en-tete
#   (Console/accorder_photos_miroir.js). En resume : il ne parle JAMAIS a Hektor,
#   il compare notre registre au miroir local, il marque les photos que Hektor ne
#   liste plus et corrige les ordres. Il exige une lecture fraiche, epargne les
#   photos de l'app, refuse de marquer depuis une liste vide, s'arrete au-dela
#   d'un plafond, refuse si le parc vivant est sous un plancher -- et depuis le
#   18/10, VERROU 7 : il ne prend plus une photo MASQUEE pour une SUPPRIMEE.
#
# ⛔ `--dry-run` est le DEFAUT quand on le lance a la main. La tache, elle, passe
#    `--appliquer`.
#
#   .\scheduled\run_entretien_photos.ps1            <- ECRIT (comme la tache)
#   .\scheduled\run_entretien_photos.ps1 -DryRun    <- compte, n'ecrit rien

param(
    [int]$FraicheurHeures = 48,
    [int]$Plafond = 2000,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "entretien_photos_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$echecs = @()
try {
    Write-Output "=== Entretien photos demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell rend la CHAINE
    # et non un tableau ; [0] donne alors son PREMIER CARACTERE (« C »).
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $photos = Join-Path $root "Console\accorder_photos_miroir.js"
    if (-not (Test-Path -LiteralPath $photos)) { throw "Script introuvable : $photos" }

    # ⛔⛔ CETTE FONCTION NE DOIT RIEN ECRIRE SUR LE FLUX DE SORTIE.
    #   EN POWERSHELL, TOUT CE QU'UNE FONCTION ECRIT SUR LE FLUX DE SORTIE FAIT PARTIE
    #   DE SA VALEUR DE RETOUR. Ecrite ainsi le 15/10 dans la tache documents, elle
    #   rendait un TABLEAU -- et `-not` d'un tableau non vide vaut $false, donc UNE
    #   LIGNE EN ECHEC N'ETAIT JAMAIS COMPTEE : la tache sortait 0, le planificateur
    #   etait vert et le moniteur se taisait. 6e fois de cette famille dans ce projet.
    #   REMEDE : `Write-Host` (va a l'hote, donc au journal de transcription, pas au
    #   flux) et `| Out-Host` sur l'appel a node. $LASTEXITCODE reste renseigne.
    #   La fonction ne rend donc QU'UN SEUL booleen.
    #   ⚠ Toute modification ici doit repasser scheduled\test_detecteur_echec_entretien.ps1.
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

    $args1 = @($photos, "--fraicheur-heures", "$FraicheurHeures", "--plafond", "$Plafond")
    if (-not $DryRun) { $args1 += "--appliquer" }

    if (-not (Invoke-Ligne -Titre "1/1 les PHOTOS (local, sans Hektor)" -Arguments $args1)) {
        $echecs += "photos"
    }

    if ($echecs.Count -gt 0) {
        Write-Output "=== Entretien photos termine AVEC ECHECS : $($echecs -join ', ') ==="
    } else {
        Write-Output "=== Entretien photos termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- la ligne est passee ==="
    }
} catch {
    Write-Output "=== ERREUR entretien photos : $_ ==="
    $echecs += "exception"
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "entretien_photos_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# ⚠ LE CODE DE SORTIE DOIT SE VOIR DANS LE PLANIFICATEUR, sinon la tache passe pour
#   verte alors qu'elle n'a rien fait -- defaut rebouche SIX fois dans ce projet
#   (sauvegarde 19/08, descente 08/09, recherches actives 23/09, rattrapage documents
#   26/09 a moitie, sa liste de surveillance le 15/10, le detecteur du 16/10).
if ($echecs.Count -gt 0) { exit 1 }
exit 0
