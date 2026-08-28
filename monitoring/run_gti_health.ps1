param(
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Python = $env:GTI_MONITOR_PYTHON
if (-not $Python) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $Python = $PythonCommand.Source
    } else {
        $Python = "python.exe"
    }
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDir "check_gti_health_$Timestamp.log"
$ScriptPath = Join-Path $PSScriptRoot "check_gti_health.py"

# C.17 (27/08/2026) -- L'EN-TETE QUI MANQUAIT.
# Les 25, 26 et 27/08, des passages ont laisse un journal de 0 OCTET avec exit 1. Or le
# script Python ne rend JAMAIS 1 (son main() rend 0 ou 2) : un fichier totalement vide
# signifie donc que le processus n'a pas demarre, ou qu'il a ete tue de l'exterieur --
# deux causes qu'on ne pouvait pas distinguer, faute de la moindre trace.
#
# On ecrit donc l'en-tete AVANT d'invoquer Python, et le pied APRES. La prochaine fois :
#   fichier vide          -> la redirection elle-meme a echoue
#   en-tete seul          -> Python n'a pas demarre, ou a ete tue
#   en-tete + pied        -> le script est alle au bout, lire son contenu
$Entete = @(
    "=== check_gti_health -- debut $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===",
    "interpreteur : $Python",
    "script       : $ScriptPath",
    ""
)
# L'ENCODAGE DOIT ETRE CELUI DE LA REDIRECTION. `*>>` ecrit en UTF-16 sous Windows
# PowerShell : un en-tete en UTF-8 donnait un journal a deux encodages depuis le
# 27/08 -- lisible de justesse, mais bancal. On aligne les trois ecritures.
Set-Content -Path $LogPath -Value $Entete -Encoding unicode

# C.17-bis (28/08/2026) -- LE VEILLEUR NE DOIT PAS MOURIR EN PARLANT.
#
# CE QUI S'EST PASSE. Passages de 05:48 et 07:48 le 28/08 : journal de 164 octets --
# l'en-tete seul, sans le pied -- et code de sortie 1. Relance a la main, le moniteur
# rend pourtant son rapport complet et juste.
#
# LA CAUSE. Deux choses inoffensives separement, mortelles ensemble :
#   1. $ErrorActionPreference = "Stop" en tete de ce fichier (d'origine) ;
#   2. la redirection `*>>`, qui recopie AUSSI la sortie d'erreur de Python.
# Sous Windows PowerShell, recopier la sortie d'erreur d'un programme externe emballe
# CHAQUE LIGNE dans une erreur ; avec "Stop", la premiere devient terminante. Le script
# meurt donc a l'instant ou le moniteur signale quelque chose -- AVANT d'avoir ecrit la
# ligne qui l'explique, et avant le pied de page.
#
# L'IRONIE, ET LE DANGER. Tant que tout va bien le moniteur ne dit rien, donc rien ne le
# tue et son rapport s'ecrit (01:49 et 03:49 : 55 Ko chacun). Il ne se taisait QUE quand
# il avait quelque chose a dire. Une sentinelle qui ne sait rapporter que le beau temps
# ne sert a rien -- c'est deja la lecon de C.17.
#
# LE REMEDE. On leve la consigne "arrete tout" AUTOUR DE CE SEUL GESTE, et on la remet
# aussitot. Tout le reste du script garde sa prudence.
$PrudenceHabituelle = $ErrorActionPreference
$ExitCode = $null
Push-Location $ProjectRoot
try {
    $ErrorActionPreference = "Continue"
    & $Python $ScriptPath --json *>> $LogPath
    $ExitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $PrudenceHabituelle
    Pop-Location
}

# Python n'a pas rendu de code : il n'a pas demarre. On ne rend SURTOUT pas 0 --
# un echec silencieux serait pire que l'echec bruyant qu'on vient de corriger.
if ($null -eq $ExitCode) { $ExitCode = 1 }

Add-Content -Path $LogPath -Encoding unicode -Value @(
    "",
    "=== fin $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- code de sortie $ExitCode ==="
)

$RetentionLimit = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $LogDir -Filter "check_gti_health_*.log" -File |
    Where-Object { $_.LastWriteTime -lt $RetentionLimit } |
    Remove-Item -Force

exit $ExitCode
