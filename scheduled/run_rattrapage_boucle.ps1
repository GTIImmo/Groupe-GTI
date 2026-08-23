# BOUCLE DE RATTRAPAGE ACQUEREURS -- enchaine des sessions jusqu'a epuiser la liste.
#
# Chaque session lit 5 000 fiches en UNE authentification (correctif du 23/08), puis on
# laisse 5 min de repos avant la suivante. La reprise se fait par IDENTIFIANT, lu dans la
# ligne de fin de la session precedente -- jamais par position : la liste bouge (71 341 ->
# 71 112 en trois jours) et un rang ne designe pas les memes contacts d'un jour a l'autre.
#
# ARRET AUTOMATIQUE. La boucle s'arrete des qu'une session sort en erreur (coupe-circuit,
# lecture Hektor en echec) ou qu'elle n'annonce plus d'identifiant de reprise. On ne
# reessaie JAMAIS derriere un echec : c'est ce qui a aggrave chaque incident de la semaine.
param(
    [long]$StartAfterId  = 0,
    [int]$SessionSize    = 2000,
    [int]$PauseSeconds   = 300,
    [int]$MaxSessions    = 20
)
$ErrorActionPreference = "Continue"
$root   = "C:\Hektor\Projet"
$py     = Join-Path $root ".venv\Scripts\python.exe"
$script = Join-Path $root "phase2\sync\sync_active_searches.py"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$log = Join-Path $logDir "rattrapage_boucle_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').log"
Start-Transcript -Path $log -Append | Out-Null

$courant = $StartAfterId
$n = 0
$fini = $false
try {
    while ($n -lt $MaxSessions) {
        $n++
        Write-Output "=== SESSION $n -- depart apres l'id $courant -- $(Get-Date -Format 'HH:mm:ss') ==="
        $a = @("--scope", "acquereurs", "--limit", [string]$SessionSize)
        if ($courant -gt 0) { $a += @("--start-after-id", [string]$courant) }
        $sortie = & $py $script @a 2>&1
        $code = $LASTEXITCODE
        $sortie | ForEach-Object { Write-Output $_ }

        if ($code -ne 0) {
            Write-Output "=== SESSION $n EN ECHEC (exit $code) -- BOUCLE ARRETEE, on ne reessaie pas ==="
            break
        }
        $texte = ($sortie | Out-String)
        if ($texte -match "liste terminee") {
            Write-Output "=== LISTE EPUISEE apres $n session(s) ==="
            $fini = $true
            break
        }
        if ($texte -match "--start-after-id\s+(\d+)\s*$" -or $texte -match "session suivante\s*:\s*--start-after-id\s+(\d+)") {
            $suivant = [long]$Matches[1]
        } else {
            Write-Output "=== AUCUN identifiant de reprise annonce -- BOUCLE ARRETEE par securite ==="
            break
        }
        if ($suivant -le $courant) {
            Write-Output "=== l'identifiant de reprise n'avance pas ($courant -> $suivant) -- ARRET ==="
            break
        }
        $courant = $suivant
        if ($n -lt $MaxSessions) {
            Write-Output "--- repos de $PauseSeconds s avant la session suivante (reprise apres $courant) ---"
            Start-Sleep -Seconds $PauseSeconds
        }
    }
    Write-Output "=== BOUCLE TERMINEE -- $n session(s), liste epuisee : $fini, dernier id $courant ==="
} finally {
    Stop-Transcript | Out-Null
}
if (-not $fini) { exit 1 }
