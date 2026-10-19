# Tache planifiee : ENTRETIEN DES DOCUMENTS ET DES PHOTOS (22:00)
#                            15/10/2026 — chantier 6, points 6b et 6d
#                            tache Windows a creer : « GTI Entretien Documents »
#
# ⛔ DORMANTE : aucune tache ne l'appelle encore. Son enregistrement est un geste de
#    Frederic, dans un PowerShell administrateur, et il ne doit se faire QU'APRES la
#    desactivation de « GTI Rattrapage Documents » (un seul worker, une seule file).
#
# ═══════════════════════════════════════════════════════════════════════════════════
# POURQUOI ELLE REMPLACE LE RATTRAPAGE — decision de Frederic du 15/10
# ═══════════════════════════════════════════════════════════════════════════════════
# Le rattrapage (21:00) empile une SYNCHRO COMPLETE par annonce : il telecharge, donc
# ~25 s chacune. Il a fait son travail -- 44 000 annonces -- et il finit les vendus/clos
# la nuit du 16 au 17.
# L'entretien, lui, empile une LECTURE par annonce (~1 s) et ne synchronise QUE ce qui a
# bouge. C'est 25 fois moins cher, et c'est ce qui permet de repasser sur TOUT le parc en
# quelques nuits, indefiniment.
#
# ⚠ IL Y A DEUX MANETTES, ET ELLES NE PAYENT PAS LA MEME CHOSE :
#     --max-lectures  borne la DETECTION : le temps passe chez Hektor (~1 s par annonce)
#     --cap           borne le WORKER    : le nombre de travaux (~25 s chacun)
#   Une annonce SANS empreinte est empilee SANS LECTURE -- elle ne coute donc rien a la
#   detection, et tout au worker. C'est le cap qui la tient.
#
# L'ORDRE EST CELUI DE FREDERIC : les actifs d'abord, les estimations ensuite, les
# vendus/clos apres. Une ligne qui echoue n'empeche pas les suivantes.
#
#   1. LES BIENS EN VENTE (727)        chaque nuit, ~15 min
#      C'est la que tout se passe : 8,3 a 22,4 documents par bien, et 42 % avaient du
#      nouveau au premier passage du 15/10. Un document depose arrive donc le LENDEMAIN.
#   2. LES ESTIMATIONS (12 758)        2 000 lectures/nuit -> tour complet en ~6 nuits
#      0,95 document chacune, recu a sa naissance : elles dorment, un tour par semaine
#      suffit largement.
#   3. LES VENDUS/CLOS (8 943)         2 000 lectures/nuit -> tour complet en ~5 nuits
#      ⭐ C'EST CETTE LIGNE QUI REGLE G.1-c : 49 biens vendus portent une empreinte
#      posee quand ils etaient encore vivants, le rattrapage les saute pour toujours
#      (« empreinte posee = deja faite ») et la detection ne les voyait pas. Releve du
#      14/10 : 4 sur 5 avaient du nouveau chez Hektor -- des compromis, des actes.
#      En les remettant dans la roue, le defaut se repare ET ne revient plus (l'index
#      grossit de ~30 par mois).
#      ⚠ SON CAP EST LE PLUS IMPORTANT : 1 398 vendus/clos sont encore SANS empreinte,
#        donc empiles sans lecture mais a ~25 s de worker chacun. 300 par nuit (reglage
#        de Frederic) = ~2 h de worker, et les 1 398 absorbes en ~5 nuits.
#
# ⚠⚠ LA LIGNE 4 (LES PHOTOS) EST PARTIE LE 19/10 -- elle a sa propre tache.
#    Frederic, 18/10 : « on a normalement deja des run quotidiens pour les photos,
#    celui de 22h n'aurait pas du y toucher ». Verifie : ni « GTI Rattrapage
#    Documents » (21:00) ni run_detection_documents.ps1 ne portaient de ligne photos.
#    Elle etait nee ICI le 15/10, dans le commit qui refondait la tache en quatre
#    lignes, SANS etre soumise comme une decision a part.
#    ➡ Elle vit desormais dans scheduled\run_entretien_photos.ps1, a 21:00 --
#      « GTI Entretien Photos ». Son traitement est le SEUL des cinq a RETIRER
#      (present_in_hektor = false) : il merite son nom, son journal, sa surveillance.
#    ⚠ NE PAS LA REMETTRE ICI : les deux tourneraient, et la seconde recalculerait
#      les memes candidats pour rien.
#
# POURQUOI 22:00 — l'etranglement du matin, mesure
#   05:00 le run (fin 07:14-07:34) · 07:45 la descente (18 a 64 min) · 09:00 la sauvegarde
#   Mettre ces lectures dans le run pousserait la descente sur la sauvegarde. A 22:00 :
#   agence fermee, Hektor calme, rien d'autre ne tourne, et la file est vide bien avant
#   les recherches actives de 03:00 et le run de 05:00.
#
# LE COMPTE DU TEMPS, avec les reglages par defaut
#   detection  727 + 2 000 + 2 000 = 4 727 lectures  ->  ~2 h 15   (22:00 -> 00:15)
#   worker     au plus 700 travaux, dont ~300 lourds  ->  fini vers 02:00-02:30
#   ⚠ En regime (tout rattrape), les caps ne mordent plus : quelques dizaines de
#     travaux par nuit, et le worker a fini en quelques minutes.
#
# ⚠⚠ CE QU'ELLE REMPLACE, ET QUI DOIT RESTER ETEINT : l'etape
#    `-EnqueueConsoleDocuments` du run de 05:00 (G.6). Elle fait le MEME travail. Les
#    allumer toutes les deux doublerait tout. Le run porte desormais un refus explicite
#    qui renvoie ici (run_full_pipeline.ps1, l. ~1490).
#
# Suivre ce qu'elle a fait :
#   Get-Content (Get-ChildItem C:\Hektor\Projet\logs\scheduled\entretien_documents_*.log |
#                Sort-Object LastWriteTime -Descending | Select-Object -First 1)

param(
    [int]$LecturesVente = 800,
    [int]$CapVente = 300,
    [int]$LecturesEstimation = 2000,
    [int]$CapEstimation = 100,
    [int]$LecturesVendus = 2000,
    [int]$CapVendus = 300,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "entretien_documents_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$echecs = @()
try {
    Write-Output "=== Entretien documents demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09 a 23 h.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell rend la CHAINE et
    # non un tableau ; [0] donne alors son PREMIER CARACTERE (« C »).
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $enfileur = Join-Path $root "Console\enqueue_console_sync_jobs.js"
    if (-not (Test-Path -LiteralPath $enfileur)) { throw "Script introuvable : $enfileur" }

    # Une ligne qui echoue n'empeche pas les suivantes : ce sont des lots independants,
    # et si la cause est commune (Hektor ferme) chacune s'arretera proprement d'elle-meme
    # (le balayage refuse d'insister sur un 403).
    # ⛔⛔ CETTE FONCTION NE DOIT RIEN ECRIRE SUR LE FLUX DE SORTIE.
    #
    #   LE DEFAUT ETAIT DEJA ECRIT, le 03/10, dans run_full_pipeline.ps1 (l. 228-245) :
    #   « EN POWERSHELL TOUT CE QU'UNE FONCTION ECRIT SUR LE FLUX DE SORTIE FAIT PARTIE
    #   DE SA VALEUR DE RETOUR ». Ecrite le 15/10, cette fonction a refait la meme faute,
    #   et la mesure du 16/10 a 00:45 l'a prise :
    #     · elle rendait @("--- 1/4 ...", <toute la sortie de node>, $true|$false) ;
    #     · or `-not` d'un tableau NON VIDE vaut $false
    #       -> UNE LIGNE EN ECHEC N'ETAIT JAMAIS COMPTEE : $echecs restait vide, la tache
    #          sortait 0, le planificateur etait vert et LE MONITEUR SE TAISAIT (elle y
    #          est en `critical`, il lit LastTaskResult) ;
    #     · et les 4 marqueurs « --- x/4 » n'arrivaient JAMAIS au journal (951 caracteres
    #       la 1re nuit : l'ouverture et la fermeture, rien entre les deux).
    #   C'etait la 6e fois que cette famille de defaut sortait dans ce projet, et le gel
    #   du 20/08 avait dure 7 SEMAINES.
    #
    #   REMEDE, deux mots : `Write-Host` (va a l'hote, donc au journal de transcription,
    #   et PAS au flux de sortie) et `| Out-Host` sur l'appel a node (sinon c'est SA
    #   sortie qui polluerait le retour). $LASTEXITCODE reste renseigne apres `| Out-Host`.
    #   La fonction ne rend donc plus QU'UN SEUL booleen -- c'est ce que l'epreuve verifie
    #   (scheduled/test_detecteur_echec_entretien.ps1), en executant CE code, pas une
    #   imitation : l'avertissement du 03/10 dit aussi « eprouver, c'est executer LE code ».
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

    $commun = @("--detect")
    if ($DryRun) { $commun += "--dry-run" }

    if (-not (Invoke-Ligne -Titre "1/3 les biens EN VENTE ($LecturesVente lectures, cap $CapVente)" -Arguments (
        @($enfileur, "--scope", "vente") + $commun + @("--max-lectures", "$LecturesVente", "--cap", "$CapVente")
    ))) { $echecs += "vente" }

    if (-not (Invoke-Ligne -Titre "2/3 les ESTIMATIONS ($LecturesEstimation lectures, cap $CapEstimation)" -Arguments (
        @($enfileur, "--scope", "estimation") + $commun + @("--max-lectures", "$LecturesEstimation", "--cap", "$CapEstimation")
    ))) { $echecs += "estimation" }

    if (-not (Invoke-Ligne -Titre "3/3 les VENDUS/CLOS ($LecturesVendus lectures, cap $CapVendus)" -Arguments (
        @($enfileur, "--scope", "historical") + $commun + @("--max-lectures", "$LecturesVendus", "--cap", "$CapVendus")
    ))) { $echecs += "vendus_clos" }

    if ($echecs.Count -gt 0) {
        Write-Output "=== Entretien documents termine AVEC ECHECS : $($echecs -join ', ') ==="
    } else {
        Write-Output "=== Entretien documents termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- les 4 lignes sont passees ==="
    }
} catch {
    Write-Output "=== ERREUR entretien documents : $_ ==="
    $echecs += "exception"
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "entretien_documents_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# ⚠ LE CODE DE SORTIE DOIT SE VOIR DANS LE PLANIFICATEUR, sinon la tache passe pour
#   verte alors qu'elle n'a rien fait -- defaut rebouche CINQ fois dans ce projet
#   (sauvegarde 19/08, descente 08/09, recherches actives 23/09, rattrapage documents
#   26/09 a moitie, et sa liste de surveillance le 15/10).
if ($echecs.Count -gt 0) { exit 1 }
exit 0
