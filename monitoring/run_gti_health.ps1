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

Push-Location $ProjectRoot
try {
    & $Python $ScriptPath --json *> $LogPath
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$RetentionLimit = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $LogDir -Filter "check_gti_health_*.log" -File |
    Where-Object { $_.LastWriteTime -lt $RetentionLimit } |
    Remove-Item -Force

exit $ExitCode
