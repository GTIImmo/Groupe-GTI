# Tache planifiee : REPRENDRE LES ENVOIS HEKTOR QUI N'ONT PAS ABOUTI
#                                                   14/10/2026, chantier ③ / 3d piece 4
#
# POURQUOI ELLE EXISTE. Depuis le lot 1 (25/09), un document ou une photo ajoute depuis
# l'app EXISTE des sa creation : le fichier est sur notre serveur, la ligne est dans
# l'app. L'envoi chez Hektor n'est plus qu'un ETAT de cette ligne :
#     envoi_hektor_statut = a_envoyer   creee, pas encore partie
#                         = echec       Hektor a refuse ou n'a pas repondu
#                         = envoye      confirmee chez Hektor
#                         = NULL        vient de Hektor, rien a envoyer
# `Console/reprendre_envois_hektor.js` remet en file ce qui attend. Il existe, il est
# EPROUVE (15 controles), mais depuis le 25/09 il etait ORPHELIN : aucune des taches
# planifiees ne l'appelait -- point D3 de notice/RESTE_A_FAIRE_DOCUMENTS_PHOTOS_2026-09-25.md,
# redit le 09/10, et le worker lui-meme l'ecrit dans son journal :
#     « Document garde chez nous, envoi Hektor en echec -- A REPRENDRE
#       (le repreneur n'est pas branche) »
# Cette tache est ce branchement.
#
# ⭐ IL NE PARLE PAS A HEKTOR. Il POSE des travaux ; c'est le worker qui envoie, a sa
#   cadence et derriere son frein. La charge chez Hektor est donc celle du worker, pas
#   celle de ce script.
#
# ETAT MESURE LE 14/10/2026 : **ZERO** ligne en a_envoyer ou echec, documents et photos
#   confondus. C'est normal et c'est attendu : le chemin differe etait DORMANT (rien ne
#   posait app_document_id), donc aucune ligne n'a jamais porte « a_envoyer ». Les 121
#   envois reussis depuis mai sont tous passes par l'ancien chemin.
#   ➡ Cette tache est un FILET, et elle ne devient utile qu'a partir de la piece 3
#     (le front), qui commence justement a creer ces lignes. Elle ne trouvera donc
#     presque toujours RIEN -- et c'est le signe que tout va bien, pas qu'elle est inutile.
#
# ⚠ POURQUOI 12:30, ET PAS LA NUIT. Le calcul, pas une impression :
#     · le run tourne de 05:00 a ~07:30, la descente jusqu'a 08:03-08:49 (mesure sur
#       12 jours) -- et TROIS etapes du run REFUSENT de demarrer s'il reste un travail
#       console en attente. Poser des travaux le matin les ferait sauter : c'est
#       exactement le degat du 30/09 et du 08/10.
#     · le rattrapage des documents part a 21:00 et finit entre 01:47 et 04:57.
#   12:30 est donc le creux : 3 h 40 apres la pire fin de descente, 8 h 30 avant le
#   rattrapage. Et le lot est plafonne a 50 : a ~20 s par envoi, la file est vide en
#   ~17 min, soit une marge de plus de huit heures avant le rattrapage.
#   ⚠ 50 envois ne sont PAS un martelement de la console : ce qui avait fait bannir
#     notre IP, c'etait le rattrapage et ses milliers de LECTURES.
#
# ⚠ CE QU'ELLE SURVEILLE, ET COMMENT ON LE SAIT. Elle sort en 1 quand une ligne est en
#   echec depuis plus de 24 h : ce n'est plus un incident passager. Windows enregistre
#   alors LastTaskResult <> 0 et check_gti_health.py le voit -- comme pour le rattrapage.
#   ⚠ Elle n'a PAS de battement (`-WorkerKey`) : la lecon du 13/10 est qu'un battement
#     sans ligne de registre part dans le vide ET compte pour un succes. Ici la
#     surveillance passe par le resultat de la tache Windows, qui ne ment pas.
#
#   node C:\Hektor\Projet\Console\reprendre_envois_hektor.js --dry-run

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "reprise_envois_hektor_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$runFailed = $false
try {
    Write-Output "=== Reprise des envois Hektor demarree $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09 a 23 h.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell ne rend pas un
    # tableau d'un element : il rend la CHAINE. Et [0] sur une chaine donne son PREMIER
    # CARACTERE. Une tache a donc deja essaye de lancer une commande nommee « C ».
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $script = Join-Path $root "Console\reprendre_envois_hektor.js"
    if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

    & $nodeExe $script "--appliquer" "--limite" "50" "--respiration" "15" "--alerte" "24"
    $code = $LASTEXITCODE

    switch ($code) {
        0 { Write-Output "--- rien a reprendre, ou tout a ete repose" }
        1 { Write-Output "--- A REGARDER : une ligne est en echec depuis plus de 24 h"; $runFailed = $true }
        default { Write-Output "--- ECHEC (code $code)"; $runFailed = $true }
    }

    Write-Output "=== Reprise des envois Hektor terminee $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
} catch {
    Write-Output "=== ERREUR reprise des envois Hektor : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "reprise_envois_hektor_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Correctif du 19/08 applique ici aussi : PROPAGER l'echec au Planificateur.
# Sans ce bloc, le catch avalerait l'exception, le script sortirait en 0, Windows
# enregistrerait LastTaskResult=0 et check_gti_health.py conclurait "0 en anomalie".
# C'est ce mecanisme qui avait cache 18 jours d'echecs nocturnes en aout.
if ($runFailed) { exit 1 }
