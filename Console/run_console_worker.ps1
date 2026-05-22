param(
  [switch]$Once,
  [switch]$DisableHektorActions,
  [switch]$DisableMatterportActions,
  [ValidateSet("actions", "documents", "admin", "matterport", "sync_light", "sync_full", "sync", "all")]
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
$env:CONSOLE_WORKER_ENABLE_MATTERPORT_ACTIONS = if ($DisableMatterportActions) { "false" } else { "true" }
if ($SyncWorker) {
  $WorkerKind = "sync_light"
}
$env:CONSOLE_WORKER_KIND = $WorkerKind
$env:CONSOLE_WORKER_GENERATION = "v7"
$env:CONSOLE_WORKER_ID = "$($env:COMPUTERNAME):$($WorkerKind):scheduled:$($env:CONSOLE_WORKER_GENERATION)"
if (-not $env:CONSOLE_WORKER_POLL_INTERVAL_MS) {
  $env:CONSOLE_WORKER_POLL_INTERVAL_MS = if ($WorkerKind -in @("sync", "sync_full")) { "60000" } elseif ($WorkerKind -eq "sync_light") { "10000" } else { "5000" }
}
if (-not $env:CONSOLE_HEKTOR_SESSION_REFRESH_MS) {
  $env:CONSOLE_HEKTOR_SESSION_REFRESH_MS = "7200000"
}
if (-not $env:CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT) {
  $env:CONSOLE_HEKTOR_CONTEXT_SWITCH_FALLBACK_PLAYWRIGHT = "true"
}
if (-not $env:CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT) {
  $env:CONSOLE_HEKTOR_ALLOW_UNVERIFIED_CONTEXT = "true"
}
if (-not $env:CONSOLE_LOCAL_ARCHIVE_ROOT) {
  $env:CONSOLE_LOCAL_ARCHIVE_ROOT = "C:\Hektor\HektorConsoleDocuments"
}

$sessionDir = Join-Path $scriptDir "sessions"
if (-not (Test-Path -LiteralPath $sessionDir)) {
  New-Item -ItemType Directory -Path $sessionDir | Out-Null
}
if (-not $env:CONSOLE_STORAGE_STATE_PATH) {
  $env:CONSOLE_STORAGE_STATE_PATH = Join-Path $sessionDir ("storage_state_{0}.json" -f $WorkerKind)
}

$nodeCandidates = @(
  $env:CONSOLE_NODE_EXE,
  "C:\Program Files\nodejs\node.exe",
  "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$nodeExe = if ($nodeCandidates.Count -gt 0) { $nodeCandidates[0] } else { "node.exe" }

$storageStatePath = $env:CONSOLE_STORAGE_STATE_PATH
$legacyStorageStatePath = Join-Path $scriptDir "storage_state.json"
if (-not (Test-Path -LiteralPath $storageStatePath) -and (Test-Path -LiteralPath $legacyStorageStatePath)) {
  Copy-Item -LiteralPath $legacyStorageStatePath -Destination $storageStatePath -Force
}
if ($WorkerKind -ne "matterport" -and -not (Test-Path -LiteralPath $storageStatePath)) {
  Write-Host "Session Hektor absente, lancement du login Playwright..."
  & $nodeExe playwright_login.js
}

if ($WorkerKind -eq "matterport") {
  if (-not $env:MATTERPORT_STORAGE_STATE_PATH) {
    $env:MATTERPORT_STORAGE_STATE_PATH = Join-Path $scriptDir "matterport_storage_state.json"
  }
  if (-not (Test-Path -LiteralPath $env:MATTERPORT_STORAGE_STATE_PATH)) {
    Write-Host "Session Matterport absente, lancement du login Playwright..."
    & $nodeExe matterport_playwright_login.js
  }
}

$arguments = @("console_job_worker.js")
if ($Once) {
  $arguments += "--once"
}

Write-Host "Demarrage worker Console..."
Write-Host "Type worker: $env:CONSOLE_WORKER_KIND"
Write-Host "Polling: $env:CONSOLE_WORKER_POLL_INTERVAL_MS ms"
if ($WorkerKind -eq "matterport") {
  Write-Host "Session Matterport: $env:MATTERPORT_STORAGE_STATE_PATH"
} else {
  Write-Host "Session Hektor: $env:CONSOLE_STORAGE_STATE_PATH"
}
Write-Host "Actions Hektor: $env:CONSOLE_WORKER_ENABLE_HEKTOR_ACTIONS"
Write-Host "Actions Matterport: $env:CONSOLE_WORKER_ENABLE_MATTERPORT_ACTIONS"
Write-Host "Archive locale: $env:CONSOLE_LOCAL_ARCHIVE_ROOT"
$logPath = Join-Path $logDir ("console_worker_{0}_{1}.log" -f $WorkerKind, $PID)
& $nodeExe $arguments 2>&1 | Tee-Object -FilePath $logPath -Append
