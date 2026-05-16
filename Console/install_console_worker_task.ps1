param(
  [string]$TaskName = "",
  [ValidateSet("actions", "documents", "admin", "sync_light", "sync_full", "sync", "all")]
  [string]$WorkerKind = "actions",
  [switch]$SyncWorker,
  [switch]$AtStartup,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptDir "run_console_worker.ps1"
if ($SyncWorker) {
  $WorkerKind = "sync_light"
}
if (-not $TaskName) {
  $TaskName = "Hektor Console Worker $WorkerKind"
  if ($WorkerKind -eq "actions") {
    $TaskName = "Hektor Console Worker"
  }
}

if (-not (Test-Path -LiteralPath $runnerPath)) {
  throw "Runner introuvable: $runnerPath"
}

$powerShellPath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"
$taskArguments = "-NoProfile -ExecutionPolicy Bypass -File `"$runnerPath`" -WorkerKind $WorkerKind"

if ($WhatIf) {
  Write-Host "Tache planifiee non creee (WhatIf)."
  Write-Host "Nom: $TaskName"
  Write-Host "Type worker: $WorkerKind"
  Write-Host "Declencheur: $(if ($AtStartup) { 'Au demarrage Windows' } else { 'A la connexion utilisateur' })"
  Write-Host "Commande: $powerShellPath $taskArguments"
  exit 0
}

$action = New-ScheduledTaskAction -Execute $powerShellPath -Argument $taskArguments -WorkingDirectory $scriptDir
$trigger = if ($AtStartup) {
  New-ScheduledTaskTrigger -AtStartup
} else {
  New-ScheduledTaskTrigger -AtLogOn
}
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit (New-TimeSpan -Days 7) `
  -MultipleInstances IgnoreNew `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -Description "Worker local qui traite les jobs Supabase pour Hektor Console." `
  -Force | Out-Null

Write-Host "Tache planifiee creee: $TaskName"
Write-Host "Type worker: $WorkerKind"
Write-Host "Le worker demarrera $(if ($AtStartup) { 'au demarrage Windows' } else { 'a la connexion utilisateur' })."
