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
Set-Content -Path $LogPath -Value $Entete -Encoding utf8

Push-Location $ProjectRoot
try {
    & $Python $ScriptPath --json *>> $LogPath
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

Add-Content -Path $LogPath -Encoding utf8 -Value @(
    "",
    "=== fin $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') -- code de sortie $ExitCode ==="
)

$RetentionLimit = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $LogDir -Filter "check_gti_health_*.log" -File |
    Where-Object { $_.LastWriteTime -lt $RetentionLimit } |
    Remove-Item -Force

exit $ExitCode
