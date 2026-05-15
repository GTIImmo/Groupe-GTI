param(
  [switch]$Once,
  [switch]$DisableHektorActions,
  [ValidateSet("actions", "sync", "all")]
  [string]$WorkerKind = "actions",
  [switch]$SyncWorker
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$logDir = Join-Path $scriptDir "logs"
if (-not (Test-Path -LiteralPath $logDir)) {
  New-Item -ItemType Directory -Path $logDir | Out-Null
}

$env:CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS = if ($DisableHektorActions) { "false" } else { "true" }
if ($SyncWorker) {
  $WorkerKind = "sync"
}
$env:CONSOLE_WORKER_KIND = $WorkerKind
$env:CONSOLE_WORKER_ID = "$($env:COMPUTERNAME):$($WorkerKind):scheduled"
if (-not $env:CONSOLE_WORKER_POLL_INTERVAL_MS) {
  $env:CONSOLE_WORKER_POLL_INTERVAL_MS = if ($WorkerKind -eq "sync") { "60000" } else { "5000" }
}
if (-not $env:CONSOLE_HEKTOR_SESSION_REFRESH_MS) {
  $env:CONSOLE_HEKTOR_SESSION_REFRESH_MS = "7200000"
}
if (-not $env:CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT) {
  $env:CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT = "true"
}
if (-not $env:CONSOLE_LOCAL_ARCHIVE_ROOT) {
  $env:CONSOLE_LOCAL_ARCHIVE_ROOT = "C:\HektorConsoleDocuments"
}

$nodeCandidates = @(
  $env:CONSOLE_NODE_EXE,
  "C:\Program Files\nodejs\node.exe",
  "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$nodeExe = if ($nodeCandidates.Count -gt 0) { $nodeCandidates[0] } else { "node.exe" }

$storageStatePath = Join-Path $scriptDir "storage_state.json"
if (-not (Test-Path -LiteralPath $storageStatePath)) {
  Write-Host "Session Hektor absente, lancement du login Playwright..."
  & $nodeExe playwright_login.js
}

$arguments = @("console_job_worker.js")
if ($Once) {
  $arguments += "--once"
}

Write-Host "Demarrage worker Console Hektor..."
Write-Host "Type worker: $env:CONSOLE_WORKER_KIND"
Write-Host "Polling: $env:CONSOLE_WORKER_POLL_INTERVAL_MS ms"
Write-Host "Actions Hektor: $env:CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS"
Write-Host "Archive locale: $env:CONSOLE_LOCAL_ARCHIVE_ROOT"
$logPath = Join-Path $logDir ("console_worker_{0}_{1}.log" -f $WorkerKind, $PID)
& $nodeExe $arguments 2>&1 | Tee-Object -FilePath $logPath -Append
