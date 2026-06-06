param(
  [ValidateSet("Install", "Uninstall", "Start", "Stop", "Restart", "Status")]
  [string]$Action = "Install",
  [ValidateSet("actions", "documents", "admin", "sync_light", "all")]
  [string]$WorkerKind = "all",
  [switch]$KeepScheduledTasks
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serviceDir = Join-Path $scriptDir "service"
$sourcePath = Join-Path $serviceDir "HektorConsoleWorkerService.cs"
$exePath = Join-Path $serviceDir "HektorConsoleWorkerService.exe"
$cscPath = "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$nodeCandidates = @(
  $env:CONSOLE_NODE_EXE,
  "C:\Program Files\nodejs\node.exe",
  "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$nodeExe = if ($nodeCandidates.Count -gt 0) { $nodeCandidates[0] } else { "node.exe" }
$userProfileDir = $env:USERPROFILE

$workerKinds = if ($WorkerKind -eq "all") {
  @("actions", "admin", "documents", "sync_light")
} else {
  @($WorkerKind)
}

$serviceNames = @{
  actions = "HektorConsoleWorkerActions"
  admin = "HektorConsoleWorkerAdmin"
  documents = "HektorConsoleWorkerDocuments"
  sync_light = "HektorConsoleWorkerSyncLight"
}

$scheduledTaskNames = @{
  actions = "Hektor Console Worker"
  admin = "Hektor Console Worker admin"
  documents = "Hektor Console Worker documents"
  sync_light = "Hektor Console Worker sync_light"
}

function Assert-Admin {
  $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = [Security.Principal.WindowsPrincipal]::new($identity)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Lance PowerShell en administrateur pour gerer les services Windows."
  }
}

function Build-ServiceExe {
  if (-not (Test-Path -LiteralPath $cscPath)) {
    throw "Compilateur C# introuvable: $cscPath"
  }
  if (-not (Test-Path -LiteralPath $sourcePath)) {
    throw "Source service introuvable: $sourcePath"
  }
  $needsBuild = -not (Test-Path -LiteralPath $exePath)
  if (-not $needsBuild) {
    $needsBuild = (Get-Item -LiteralPath $sourcePath).LastWriteTimeUtc -gt (Get-Item -LiteralPath $exePath).LastWriteTimeUtc
  }
  if ($needsBuild) {
    New-Item -ItemType Directory -Force -Path $serviceDir | Out-Null
    & $cscPath /nologo /target:exe /optimize+ /out:$exePath /reference:System.ServiceProcess.dll /reference:System.Management.dll $sourcePath
    if ($LASTEXITCODE -ne 0) {
      throw "Compilation du service echouee."
    }
  }
}

function Get-ServiceConfigPath {
  param([string]$Kind)
  $name = $serviceNames[$Kind]
  $parts = @(
    "`"$exePath`"",
    "--service-name `"$name`"",
    "--worker-kind `"$Kind`"",
    "--console-dir `"$scriptDir`"",
    "--node-exe `"$nodeExe`""
  )
  if ($userProfileDir) {
    $parts += "--user-profile-dir `"$userProfileDir`""
  }
  return ($parts -join " ")
}

function Install-OneService {
  param([string]$Kind)
  $name = $serviceNames[$Kind]
  $displayName = "Hektor Console Worker $Kind"
  $binaryPath = Get-ServiceConfigPath -Kind $Kind
  $existing = Get-Service -Name $name -ErrorAction SilentlyContinue
  if ($existing) {
    if ($existing.Status -ne "Stopped") {
      Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
      $existing.WaitForStatus("Stopped", "00:00:30")
    }
    sc.exe delete $name | Out-Null
    Start-Sleep -Seconds 2
  }

  New-Service -Name $name -BinaryPathName $binaryPath -DisplayName $displayName -StartupType Automatic -Description "Worker local Hektor Console ($Kind) gere comme service Windows." | Out-Null
  sc.exe config $name start= delayed-auto | Out-Null
  sc.exe failure $name reset= 60 actions= restart/60000/restart/60000/restart/300000 | Out-Null
  Write-Host "Service installe: $name"
}

function Disable-ScheduledWorkers {
  foreach ($kind in $workerKinds) {
    $taskName = $scheduledTaskNames[$kind]
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
      if ($task.State -eq "Running") {
        Stop-ScheduledTask -TaskName $taskName
      }
      Disable-ScheduledTask -TaskName $taskName | Out-Null
      Write-Host "Tache planifiee desactivee: $taskName"
    }
  }
}

function Enable-ScheduledWorkers {
  foreach ($kind in $workerKinds) {
    $taskName = $scheduledTaskNames[$kind]
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
      Enable-ScheduledTask -TaskName $taskName | Out-Null
      Write-Host "Tache planifiee reactivee: $taskName"
    }
  }
}

function Start-OneService {
  param([string]$Kind)
  $name = $serviceNames[$Kind]
  Start-Service -Name $name
  (Get-Service -Name $name).WaitForStatus("Running", "00:00:30")
  Write-Host "Service demarre: $name"
}

function Stop-OneService {
  param([string]$Kind)
  $name = $serviceNames[$Kind]
  $service = Get-Service -Name $name -ErrorAction SilentlyContinue
  if ($service -and $service.Status -ne "Stopped") {
    Stop-Service -Name $name -Force
    (Get-Service -Name $name).WaitForStatus("Stopped", "00:00:30")
    Write-Host "Service arrete: $name"
  }
}

function Remove-OneService {
  param([string]$Kind)
  $name = $serviceNames[$Kind]
  Stop-OneService -Kind $Kind
  if (Get-Service -Name $name -ErrorAction SilentlyContinue) {
    sc.exe delete $name | Out-Null
    Write-Host "Service supprime: $name"
  }
}

function Show-Status {
  $rows = @()
  foreach ($kind in $workerKinds) {
    $name = $serviceNames[$kind]
    $service = Get-Service -Name $name -ErrorAction SilentlyContinue
    $taskName = $scheduledTaskNames[$kind]
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    $rows += [PSCustomObject]@{
      Worker = $kind
      ServiceName = $name
      ServiceStatus = if ($service) { $service.Status } else { "Absent" }
      ServiceStartType = if ($service) { $service.StartType } else { "" }
      ScheduledTask = $taskName
      ScheduledTaskState = if ($task) { $task.State } else { "Absent" }
    }
  }
  $rows | Format-Table -AutoSize
}

Assert-Admin

switch ($Action) {
  "Install" {
    Build-ServiceExe
    foreach ($kind in $workerKinds) {
      Install-OneService -Kind $kind
    }
    if (-not $KeepScheduledTasks) {
      Disable-ScheduledWorkers
    }
    foreach ($kind in $workerKinds) {
      Start-OneService -Kind $kind
    }
    Show-Status
  }
  "Uninstall" {
    foreach ($kind in $workerKinds) {
      Remove-OneService -Kind $kind
    }
    if (-not $KeepScheduledTasks) {
      Enable-ScheduledWorkers
    }
    Show-Status
  }
  "Start" {
    foreach ($kind in $workerKinds) {
      Start-OneService -Kind $kind
    }
    Show-Status
  }
  "Stop" {
    foreach ($kind in $workerKinds) {
      Stop-OneService -Kind $kind
    }
    Show-Status
  }
  "Restart" {
    foreach ($kind in $workerKinds) {
      Stop-OneService -Kind $kind
      Start-OneService -Kind $kind
    }
    Show-Status
  }
  "Status" {
    Show-Status
  }
}
