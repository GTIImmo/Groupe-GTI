# RATTRAPAGE ACQUEREURS — relit chez Hektor la fiche de TOUS les contacts de
# typologie « acquereur » (~71 300), pas seulement ceux dont l'app connait deja une
# recherche active (~3 800, run de 03:00).
#
# POURQUOI. Creer une recherche dans Hektor ne bouge pas la date_maj du contact, et
# les recherches ne sont PAS dans le listing : elles ne sont que dans ContactById.
# Un contact qui gagne sa PREMIERE recherche n'entre donc dans aucun run et reste
# invisible indefiniment. Sonde du 21/08/2026, 249 fiches lues en direct : 1 portait
# une recherche que l'app ignorait -> environ 270 recherches invisibles.
#
# CADENCE (revue le 23/08/2026). La pause de 20 s entre lots est REMPLACEE par un delai
# de 0,1 s entre chaque fiche. Elle ne corrigeait que la moyenne : le lot partait quand
# meme a pleine vitesse, 5,6 a 9,4 appels/s mesures cote base. Ce sont les pointes qui se
# voient, pas les moyennes. A 0,1 s le profil devient un filet regulier a ~2,5 appels/s --
# exactement celui du run quotidien, qui n'a jamais rien declenche.
#
# CADENCE : plus rien a preciser ici. La lecture Hektor se fait en UN seul processus, avec
# les defauts alignes sur le run quotidien (lots de 1 000, pause de 60 s, delai de 0,1 s) --
# le seul des trois runs a n'avoir jamais eu d'incident en quatre mois.
#
# CE QUI CASSAIT VRAIMENT (mesure le 23/08). Le rattrapage relancait sync_contact_details a
# chaque lot de 300, donc une authentification complete toutes les deux minutes :
#     30/05  ->   1 processus pour 43 842 fiches
#     22/08  ->  88 processus pour 23 059 fiches
# Et TOUS les echecs tombaient sur /Api/OAuth/Authenticate/, jamais sur ContactById. Ce
# n'etait ni le volume ni la vitesse : c'etait la redemande de jeton en rafale.
#
# PLAFOND. --limit 5000 : une session ne depasse jamais 5 000 fiches. C'est le VOLUME qui
# a fait couper l'acces le 22/08 (25 800 fiches en 1 h 47), pas la vitesse -- le run de
# nuit tire depuis un mois a 9 appels/s sans etre inquiete, mais sur 3 778 fiches.
# Une session dure ~33 min ; il en faut une dizaine pour finir les 45 500 restantes.
#
# REPRISE. -StartAfterId <id> reprend apres cet identifiant. TOUJOURS par identifiant,
# jamais par position : la liste bouge (71 341 -> 71 272 en une journee) et le compteur
# du script additionne les lots reussis ET rates. Le run affiche l'id a utiliser quand
# il se termine. Sans le parametre, il repart du debut.
#
# REPRENABLE : chaque lot est independant, un lot en echec n'arrete pas le run.
# COUPE-CIRCUIT : mais 3 lots consecutifs en echec = signature d'un bannissement d'IP
# ou d'une session Hektor morte -> le run s'abandonne (exit 2) au lieu de marteler une
# porte fermee pendant des heures. Dans ce cas, verifier depuis une AUTRE IP avant de
# relancer -- ne jamais rejouer aveuglement.
param(
    [long]$StartAfterId = 0
)
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$py = Join-Path $root ".venv\Scripts\python.exe"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "rattrapage_acquereurs_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
$runFailed = $false
try {
    Write-Output "=== Rattrapage acquereurs demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    $argsPy = @("--scope", "acquereurs", "--limit", "5000")
    if ($StartAfterId -gt 0) { $argsPy += @("--start-after-id", [string]$StartAfterId) }
    Write-Output "--- parametres : $($argsPy -join ' ') ---"
    & $py (Join-Path $root "phase2\sync\sync_active_searches.py") @argsPy
    $code = $LASTEXITCODE
    Write-Output "=== Rattrapage acquereurs termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $code) ==="
    if ($code -eq 2) {
        Write-Output "=== COUPE-CIRCUIT : run ABANDONNE sur lots consecutifs en echec. Verifier depuis une AUTRE IP (bannissement ?) avant de relancer. ==="
    }
    if ($code -ne 0) { $runFailed = $true }
} catch {
    Write-Output "=== ERREUR rattrapage acquereurs : $_ ==="
    $runFailed = $true
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "rattrapage_acquereurs_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
# Propage l'echec au Planificateur (meme correctif que run_recherches_actives.ps1,
# 19/08 : un exit 0 menteur avait cache 18 jours de lots en echec).
if ($runFailed) { exit 1 }
