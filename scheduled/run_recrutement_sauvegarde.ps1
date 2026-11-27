# Tache planifiee « GTI Recrutement Sauvegarde » : CHAQUE JOUR, CE QUE L'APP ECRIT AU RECRUTEMENT   24/11/2026
#
# Note : notice/CHANTIER_RECRUTEMENT_ANNUAIRE_MANDATAIRES_2026-11-20.md, §13 (R5 bis) et §14 (R6.8).
#   Le run de deux mois (« GTI Recrutement », run_recrutement.ps1) fait la descente et la sauvegarde de la base
#   LOCALE. Mais depuis l'ecran (R6), l'app ecrit TOUS LES JOURS en base : suivi, fil, retraits, corrections,
#   liste « ne plus contacter », fiches ajoutees a la main. Cette petite tache, quelques secondes par jour :
#
#   1. SAUVEGARDE  recrutement/sauvegarder_app.py : copie datee et RELUE de ces tables, lues par le robot en
#                  lecture seule, dans C:\Hektor\Backups\recrutement\quotidien\ (90 gardees)
#   2. DESCENTE    recrutement/descendre.py : la liste « ne plus contacter » et les corrections ramenees en
#                  local -- un effacement demande dans l'app est applique a la base locale LE JOUR MEME, pas
#                  deux mois plus tard (derriere RECRUTEMENT_DESCENTE, comme dans le run)
#   Un battement « recrutement.sauvegarde_quotidienne » (28 h) dit a la surveillance qu'elle a tourne.
#
# ELLE NE FAIT RIEN (sortie 0, en le disant) :
#   - tant que l'interrupteur RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE n'est pas a 1 (recrutement_donnees\interrupteurs.env) ;
#   - pendant que le run de deux mois tourne (verrou run.lock) : il fait lui-meme sa descente et sa sauvegarde.
# Elle prend le MEME verrou pendant ses quelques secondes : le run ne peut pas demarrer au milieu de sa descente.
#
# CE QU'ELLE NE TOUCHE JAMAIS : Hektor, le worker, le run de nuit, phase2.sqlite, les tables de l'app (schema
#   public). Elle ne lit aucun site. Le journal ne porte que des COMPTES, jamais un nom.
# LES CODES : 0 = fait (ou rien a faire) ; 1 = la sauvegarde ou la descente a echoue -- un 1 se VOIT au
#   Planificateur et a l'ecran Sante (« warning »).
#
#   .\scheduled\run_recrutement_sauvegarde.ps1            <- comme la tache
#   .\scheduled\run_recrutement_sauvegarde.ps1 -Essai     <- lit et compte, n'ecrit rien (ni copie, ni descente, ni battement)

param(
    [switch]$Essai
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$root = "C:\Hektor\Projet"
$donnees = if ($env:RECRUTEMENT_DONNEES) { $env:RECRUTEMENT_DONNEES } else { "C:\Hektor\recrutement_donnees" }
$py = Join-Path $root ".venv\Scripts\python.exe"
# Le robot parle a la base par psycopg2 : le Python SYSTEME, avec SON dossier de paquets et -s (sans dossier
# personnel). Meme regle que run_recrutement.ps1 (24/11 : l'app Claude est un paquet MSIX, ce qu'elle installe
# sous AppData n'est vu ni des taches ni des services).
$pyBase = if ($env:RECRUTEMENT_PYTHON_BASE) { $env:RECRUTEMENT_PYTHON_BASE } else { "C:\Python314\python.exe" }
$paquetsRobot = if ($env:RECRUTEMENT_PAQUETS_PYTHON) { $env:RECRUTEMENT_PAQUETS_PYTHON } else { Join-Path $donnees "python_paquets" }
function Invoke-PythonRobot {
    $ancien = $env:PYTHONPATH
    $env:PYTHONPATH = $paquetsRobot
    try { & $pyBase -s @args 2>&1 }
    finally { if ($null -eq $ancien) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $ancien } }
}
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "recrutement_sauvegarde_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null

function Read-Interrupteurs {
    $valeurs = @{ RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE = "0"; RECRUTEMENT_DESCENTE = "0"; RECRUTEMENT_BATTEMENTS = "0" }
    $fichier = Join-Path $donnees "interrupteurs.env"
    if (Test-Path -LiteralPath $fichier) {
        foreach ($ligne in Get-Content -LiteralPath $fichier) {
            if ($ligne -match '^\s*(RECRUTEMENT_[A-Z_]+)\s*=\s*([01])\s*$') { $valeurs[$Matches[1]] = $Matches[2] }
        }
    }
    return $valeurs
}

function Send-Battement {
    param([string]$Statut, [string]$Erreur = "")
    if (-not $script:battements) { return }
    $arguments = @((Join-Path $root "monitoring\heartbeat.py"), "--worker", "recrutement.sauvegarde_quotidienne", "--status", $Statut)
    if ($Erreur) { $arguments += @("--error", $Erreur) }
    & $py @arguments 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host "    ⚠ le battement n'est pas parti (code $LASTEXITCODE)" }
}

$runFailed = $false
$rienAFaire = $false
$verrou = Join-Path $donnees "run.lock"
$verrouPris = $false
try {
    Write-Output "=== Sauvegarde quotidienne du recrutement demarree $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')$(if ($Essai) { ' (ESSAI : rien n''est ecrit)' }) ==="
    $inter = Read-Interrupteurs
    $script:battements = ($inter.RECRUTEMENT_BATTEMENTS -eq "1") -and -not $Essai
    Write-Output "    interrupteurs : sauvegarde_quotidienne=$($inter.RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE) descente=$($inter.RECRUTEMENT_DESCENTE) battements=$($inter.RECRUTEMENT_BATTEMENTS)"

    if ($inter.RECRUTEMENT_SAUVEGARDE_QUOTIDIENNE -ne "1" -and -not $Essai) {
        Write-Output "    interrupteur eteint : rien a faire aujourd'hui"
        $rienAFaire = $true
    }
    elseif (Test-Path -LiteralPath $verrou) {
        $autre = [int](Get-Content -LiteralPath $verrou -TotalCount 1)
        if (Get-Process -Id $autre -ErrorAction SilentlyContinue) {
            Write-Output "    le run du recrutement tourne (processus $autre) : il fait lui-meme sa descente et sa sauvegarde -- rien aujourd'hui"
            $rienAFaire = $true
        }
        else { Write-Output "    verrou orphelin (processus $autre absent) : on le reprend" }
    }

    if (-not $rienAFaire) {
        if (-not $Essai) { Set-Content -LiteralPath $verrou -Value $PID -Encoding ascii; $verrouPris = $true }
        if (-not (Test-Path -LiteralPath $pyBase)) { throw "le Python systeme est absent : $pyBase" }
        if (-not (Test-Path -LiteralPath $paquetsRobot)) { throw "le dossier des paquets du robot est absent ($paquetsRobot) : voir run_recrutement.ps1" }

        # 1. LA SAUVEGARDE (la base est la seule source : elle passe AVANT la descente)
        $argsSauvegarde = @("-X", "utf8", (Join-Path $root "recrutement\sauvegarder_app.py"))
        if ($Essai) { $argsSauvegarde += "--essai" }
        Invoke-PythonRobot @argsSauvegarde | ForEach-Object { Write-Output "[sauvegarde] $_" }
        $codeSauvegarde = $LASTEXITCODE
        if ($codeSauvegarde -ne 0) { $runFailed = $true; Write-Output "    ⛔ sauvegarde en echec (code $codeSauvegarde)" }

        # 2. LA DESCENTE (meme interrupteur que dans le run)
        if ($inter.RECRUTEMENT_DESCENTE -eq "1") {
            $argsDescente = @("-X", "utf8", (Join-Path $root "recrutement\descendre.py"))
            if ($Essai) { $argsDescente += "--essai" }
            Invoke-PythonRobot @argsDescente | ForEach-Object { Write-Output "[descente] $_" }
            $codeDescente = $LASTEXITCODE
            if ($codeDescente -ne 0) { $runFailed = $true; Write-Output "    ⛔ descente en echec (code $codeDescente)" }
        }
        else { Write-Output "    descente eteinte (RECRUTEMENT_DESCENTE=0)" }

        if ($runFailed) { Send-Battement -Statut "error" -Erreur "sauvegarde code $codeSauvegarde ; descente code $codeDescente" }
        else { Send-Battement -Statut "ok" }
    }
}
catch {
    $runFailed = $true
    Write-Output "=== ERREUR sauvegarde quotidienne du recrutement : $_ ==="
    Send-Battement -Statut "error" -Erreur "$_"
}
finally {
    # on ne retire le verrou que s'il est a NOUS (jamais celui du run)
    if ($verrouPris -and (Test-Path -LiteralPath $verrou) -and ((Get-Content -LiteralPath $verrou -TotalCount 1) -eq "$PID")) {
        Remove-Item -LiteralPath $verrou -Force
    }
    Write-Output "=== Fin $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- $(if ($runFailed) { 'QUELQUE CHOSE A VOIR (sortie 1)' } elseif ($rienAFaire) { 'rien a faire (sortie 0)' } else { 'tout vert (sortie 0)' }) ==="
    Stop-Transcript | Out-Null
}
if ($runFailed) { exit 1 }
exit 0
