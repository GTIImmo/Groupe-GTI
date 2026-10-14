# Tache planifiee : DETECTION DOCUMENTS DU PARC VIVANT (22:00)     14/10/2026
#                                                        chantier 6, point 6b
# ⛔⛔ DORMANTE : ce fichier n'est appele par AUCUNE tache planifiee a ce jour.
#    L'enregistrement de la tache est un geste de Frederic, dans un PowerShell
#    administrateur, et il ne doit se faire QU'APRES deux choses (voir plus bas).
#
# POURQUOI ELLE EXISTE
#   Mesure du 14/10 : le parc vivant (13 484 annonces) n'a plus ete relu depuis le
#   20/08. Consequence chiffree, sans avoir appele Hektor : sur les mandats signes
#   APRES le 20/08, nous n'avons le document que dans 4 cas sur 97 -- alors que pour
#   ceux signes AVANT, nous en avons 399 sur 472. Un mandat est un acte : son
#   document EXISTE forcement chez Hektor. 93 mandats signes n'existent donc QUE
#   chez lui, et ~12 de plus s'ajoutent chaque semaine.
#   La cause n'est pas une panne : l'etape du run qui fait ce travail
#   (-EnqueueConsoleDocuments) N'A JAMAIS ETE ALLUMEE.
#
# POURQUOI 22:00, ET PAS DANS LE RUN DE 05:00 -- mesure de l'etranglement du matin
#   05:00  le run           finit 07:18-07:34
#   07:45  la descente      attend le run jusqu'a 45 min, puis dure 18 a 64 min
#   09:00  la sauvegarde
#   19 min de plus dans le run -> il finit 07:37-07:53, la descente part vers 07:53
#   et, au pire, se termine a 08:57 : TROIS MINUTES avant la sauvegarde. C'est le
#   genre d'empilement qui a deja coute (le decalage-pansement du 12/10).
#   A 22:00 : l'agence est fermee, Hektor est calme, rien d'autre ne tourne
#   (03:00, 05:00, 07:45, 08:00, 09:00, 12:30, 18:00, 21:00), et le travail est
#   digere vers 23:00 -- loin des recherches actives de 03:00 et du run de 05:00.
#
# ⛔ LES DEUX CONDITIONS AVANT D'ENREGISTRER CETTE TACHE
#   ① LA TACHE DE 21:00 DOIT ETRE RETIREE. « GTI Rattrapage Documents » pose
#      1 000 travaux a 21:00, qui occupent le worker jusqu'a 01:47-04:57 : les
#      notres passeraient derriere. Le projet l'avait deja prevu (liste, D.0-e :
#      « quand il repond rien_a_faire -> retirer la tache »). Fin du rattrapage
#      mesuree : la nuit du 16 au 17/10.
#   ② ELLE DOIT ETRE AJOUTEE A LA LISTE DU MONITEUR. check_gti_health.py ne
#      regarde que les noms de son argument --scheduled-tasks (6 noms pour 8 taches
#      le 14/10). Poser la gravite dans TASK_CRITICALITY NE SUFFIT PAS : c'est
#      l'erreur a moitie faite du 26/09 sur la tache de 21:00, qui n'a donc jamais
#      ete surveillee. Une tache non surveillee est une tache qui echoue en silence.
#
# CE QU'ELLE FAIT -- les deux lignes, et elles ne font pas la meme chose
#   A) LES NOUVELLES ANNONCES, pour UNE SEULE requete Hektor.
#      Une annonce sans empreinte est empilee AVANT toute lecture : il n'y a rien a
#      comparer. Le budget a 1 sert donc uniquement de garde-fou -- on ramasse tout
#      le parc vivant, estimations comprises, pour une requete.
#   B) LA MISE A JOUR DES BIENS EN VENTE (Actif, Sous offre, Sous compromis).
#      La seule facon de voir qu'un document a ete ajoute est de RELIRE la page :
#      la date de mise a jour d'une annonce ne bouge pas quand on y depose une
#      piece (91 % des documents sont plus recents que la MAJ declaree de leur
#      annonce). D'ou la comparaison d'empreinte, et d'ou le cout en lectures.
#      ⚠ Perimetre « vente » et NON « daily-cloud » : les 13 028 empreintes du parc
#        vivant portent TOUTES la meme date (19-20/08), donc le tri « les plus
#        anciennes d'abord » ne sait pas les distinguer et sert les lignes dans
#        l'ordre ou elles viennent. Sur 13 484 annonces dont 12 757 estimations, un
#        budget de 800 lectures en depenserait ~760 sur des estimations qui dorment.
#        Et une estimation recoit 0,95 document contre 8 a 22 pour un bien en vente
#        -- et elle les recoit A SA NAISSANCE, donc la ligne A les attrape deja.
#
# ELLE NE PARLE PAS A HEKTOR POUR TELECHARGER : elle POSE des travaux. C'est le
# worker « documents » qui travaille ensuite, a sa cadence. Et il ne retelecharge
# jamais un document deja sur le serveur -- il le relit sur le disque.
#
# SUIVRE CE QU'ELLE A FAIT :
#   Get-Content (Get-ChildItem C:\Hektor\Projet\logs\scheduled\detection_documents_*.log |
#                Sort-Object LastWriteTime -Descending | Select-Object -First 1)

param(
    [int]$Lectures = 800,
    [int]$Cap = 400,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "detection_documents_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$runFailed = $false
try {
    Write-Output "=== Detection documents demarree $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09 a 23 h.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell ne rend pas un
    # tableau d'un element : il rend la CHAINE. Et [0] sur une chaine donne son PREMIER
    # CARACTERE -- la tache de 23 h a donc essaye de lancer une commande nommee « C ».
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $script = Join-Path $root "Console\enqueue_console_sync_jobs.js"
    if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

    $commun = @("--detect")
    if ($DryRun) { $commun += "--dry-run" }

    # ── A) LES NOUVELLES ANNONCES -- une requete, tout le parc vivant ──────────────
    Write-Output "--- A) nouvelles annonces (parc vivant entier, 1 lecture)"
    & $nodeExe $script "--scope" "daily-cloud" @commun "--max-lectures" "1" "--cap" "600"
    $codeA = $LASTEXITCODE
    if ($codeA -ne 0) {
        Write-Output "--- A) ECHEC (code $codeA)"
        $runFailed = $true
    }

    # ── B) LA MISE A JOUR DES BIENS EN VENTE ──────────────────────────────────────
    # ⚠ ELLE TOURNE MEME SI A A ECHOUE, et c'est voulu : ce sont deux lots
    #   independants. Une session perdue sur A ne doit pas priver les biens en vente
    #   de leur relecture -- et si la cause est commune (Hektor ferme), B s'arretera
    #   proprement de lui-meme (il refuse d'insister sur un 403).
    Write-Output "--- B) mise a jour des biens en vente ($Lectures lectures max, cap $Cap)"
    & $nodeExe $script "--scope" "vente" @commun "--max-lectures" "$Lectures" "--cap" "$Cap"
    $codeB = $LASTEXITCODE
    if ($codeB -ne 0) {
        Write-Output "--- B) ECHEC (code $codeB)"
        $runFailed = $true
    }

    Write-Output "=== Detection documents terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (A=$codeA B=$codeB) ==="
} catch {
    Write-Output "=== ERREUR detection documents : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "detection_documents_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# ⚠ LE CODE DE SORTIE DOIT SE VOIR DANS LE PLANIFICATEUR, sinon la tache passe pour
#   verte alors qu'elle n'a rien fait -- c'est le defaut rebouche quatre fois dans ce
#   projet (sauvegarde 19/08, descente 08/09, recherches actives 23/09, rattrapage
#   documents 26/09, et ce dernier a ete corrige A MOITIE : voir la condition ② en tete).
if ($runFailed) { exit 1 }
exit 0
