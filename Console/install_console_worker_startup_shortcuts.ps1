param(
  [switch]$Remove
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupDir = [Environment]::GetFolderPath("Startup")
$powerShellPath = "$env:WINDIR\System32\WindowsPowerShell\v1.0\powershell.exe"

$shortcuts = @(
  @{
    Name = "Hektor Console Worker Actions.lnk"
    WorkerKind = "actions"
  },
  @{
    Name = "Hektor Console Worker Sync.lnk"
    WorkerKind = "sync"
  }
)

foreach ($item in $shortcuts) {
  $shortcutPath = Join-Path $startupDir $item.Name
  if ($Remove) {
    if (Test-Path -LiteralPath $shortcutPath) {
      Remove-Item -LiteralPath $shortcutPath -Force
      Write-Host "Raccourci supprime: $shortcutPath"
    }
    continue
  }

  $shell = New-Object -ComObject WScript.Shell
  $shortcut = $shell.CreateShortcut($shortcutPath)
  $shortcut.TargetPath = $powerShellPath
  $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptDir\run_console_worker.ps1`" -WorkerKind $($item.WorkerKind)"
  $shortcut.WorkingDirectory = $scriptDir
  $shortcut.WindowStyle = 7
  $shortcut.Description = "Worker local Hektor Console $($item.WorkerKind)"
  $shortcut.Save()
  Write-Host "Raccourci cree: $shortcutPath"
}
