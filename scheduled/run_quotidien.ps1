# Tache planifiee : RUN QUOTIDIEN complet (05:30).
# Invocation identique a la commande manuelle de reference :
#   run_full_pipeline.ps1 -PushContactsToSupabase -ContactsEligibleOnly
# (annonces + mandats + contacts eligibles + chauffage + Matterport + Android ;
#  photos/documents Console NON traites = opt-in non activé).
$ErrorActionPreference = "Continue"
$root = "C:\Hektor\Projet"
$logDir = Join-Path $root "logs\scheduled"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$log = Join-Path $logDir "quotidien_$stamp.log"
Start-Transcript -Path $log -Append | Out-Null
try {
    Write-Output "=== Run quotidien demarre $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="
    & "$root\run_full_pipeline.ps1" -PushContactsToSupabase -ContactsEligibleOnly -AllowStaleSupabaseDeletes
    Write-Output "=== Run quotidien termine $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (exit $LASTEXITCODE) ==="
} catch {
    Write-Output "=== ERREUR run quotidien : $_ ==="
} finally {
    Stop-Transcript | Out-Null
    Get-ChildItem $logDir -Filter "quotidien_*.log" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}
