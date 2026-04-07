$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$workerScript = Join-Path $projectRoot "run_phase1_safe_worker.ps1"
$logDir = Join-Path $projectRoot ".tmp"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

if (-not (Test-Path $workerScript)) {
    throw "Worker script not found at $workerScript"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stdoutLog = Join-Path $logDir "phase1_safe_$timestamp.log"
$stderrLog = Join-Path $logDir "phase1_safe_$timestamp.err.log"

$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", $workerScript
    ) `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -WindowStyle Hidden `
    -PassThru

Write-Output "Phase 1 worker started."
Write-Output "PID: $($process.Id)"
Write-Output "Stdout log: $stdoutLog"
Write-Output "Stderr log: $stderrLog"
Write-Output "Check progress with: Get-Content `"$stdoutLog`" -Wait"
Write-Output "Live DB progress: .\.venv\Scripts\python.exe sync_progress.py --watch 5"
