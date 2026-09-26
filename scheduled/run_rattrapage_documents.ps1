# Tache planifiee : RATTRAPAGE DES DOCUMENTS (23:00) — un lot de 3 000 par nuit.
#                                                                        25/09/2026
# POURQUOI : au 25/09, 40 612 annonces sur 58 140 n'ont jamais ete regardees pour leurs
# documents. Le rattrapage avait tourne du 18 au 23/08 puis s'etait ARRETE (pas echoue :
# 0 en erreur) -- le 20/08, notre IP avait ete bannie et le frein avait ete pose.
# Au debit mesure apres frein (594 annonces/h), il reste ~61 h, soit 15 nuits :
#     archive 11  ·  historique 3  ·  brouillon 1
#
# CE QU'ELLE FAIT : elle POSE un lot de travaux, c'est tout. Elle ne parle pas a Hektor.
# C'est le worker `documents` qui travaille ensuite, a SA cadence (1 s entre requetes,
# +60 s toutes les 100, +300 s toutes les 2 000). Un lot de 3 000 prend 2 h 30 a 5 h :
# lance a 23:00, il finit largement avant le run quotidien de 05:00.
#
# 23:00 est un choix de Frederic : hors des heures d'agence, et loin du run de nuit.
#
# ⚠ ELLE S'ARRETE TOUTE SEULE dans trois cas, et c'est le coeur du dispositif :
#   - plus rien a faire            -> succes, elle ne pose rien (on peut la desactiver)
#   - la file n'est pas vide       -> le lot d'hier n'est pas digere. Poser par-dessus
#                                     ferait grossir le retard nuit apres nuit sans que
#                                     personne ne le voie.
#   - >= 20 erreurs en 24 h        -> Hektor nous rejette peut-etre. Regle du projet :
#                                     un 403 arrete tout, on ne rejoue JAMAIS une annonce
#                                     deja en echec (c'est ce qui a fait bannir l'IP).
#   Les deux derniers sortent en 1 : ils DOIVENT se voir dans le Planificateur et dans
#   check_gti_health.py. Un rattrapage qui cale en silence pendant 15 nuits serait pire
#   que pas de rattrapage du tout.
#
# Suivre l'avancement :
#   node C:\Hektor\Projet\Console\enqueue_empreinte_lot.js --scope auto --dry-run

$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "rattrapage_documents_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

$runFailed = $false
try {
    Write-Output "=== Rattrapage documents demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

    # ⚠ LE @() AUTOUR DU FILTRE EST INDISPENSABLE -- piege PowerShell vecu le 25/09 a 23 h.
    # Quand Where-Object ne laisse passer QU'UN SEUL element, PowerShell ne rend pas un
    # tableau d'un element : il rend la CHAINE. Et [0] sur une chaine donne son PREMIER
    # CARACTERE. La tache de 23 h a donc essaye de lancer une commande nommee « C » :
    #   « Le terme "C" n'est pas reconnu comme nom d'applet de commande... »
    # Les autres scripts tenaient par chance -- deux installations de Node sur la machine.
    $nodeCandidates = @(@(
        $env:CONSOLE_NODE_EXE,
        "C:\Program Files\nodejs\node.exe"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })
    if ($nodeCandidates.Count -eq 0) { throw "node.exe introuvable" }
    $nodeExe = $nodeCandidates[0]

    $script = Join-Path $root "Console\enqueue_empreinte_lot.js"
    if (-not (Test-Path -LiteralPath $script)) { throw "Script introuvable : $script" }

    & $nodeExe $script "--scope" "auto" "--limit" "3000" "--exiger-file-vide" "--max-erreurs-recentes" "20"
    $code = $LASTEXITCODE

    switch ($code) {
        0 { Write-Output "--- lot pose (ou plus rien a faire)" }
        3 { Write-Output "--- ARRET : la file n'est pas vide, le lot precedent n'est pas digere"; $runFailed = $true }
        4 { Write-Output "--- ARRET : trop d'erreurs en 24 h, Hektor nous rejette peut-etre"; $runFailed = $true }
        default { Write-Output "--- ECHEC (code $code)"; $runFailed = $true }
    }

    Write-Output "=== Rattrapage documents termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
} catch {
    Write-Output "=== ERREUR rattrapage documents : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "rattrapage_documents_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Correctif du 19/08 applique ici aussi : PROPAGER l'echec au Planificateur.
# Sans ce bloc, le catch avalerait l'exception, le script sortirait en 0, Windows
# enregistrerait LastTaskResult=0 et check_gti_health.py conclurait "0 en anomalie".
# C'est ce mecanisme qui avait cache 18 jours d'echecs nocturnes en aout.
if ($runFailed) { exit 1 }
