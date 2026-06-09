param(
  [ValidateSet("all", "active", "archived")]
  [string]$Scope = "all",
  [int]$Limit = 50000,
  [int]$BatchSize = 1000,
  [int]$BatchPauseSeconds = 60,
  [double]$RequestDelaySeconds = 0.1,
  [ValidateSet("missing_only", "missing_or_stale")]
  [string]$SelectionMode = "missing_only",
  [switch]$DryRun,
  [switch]$ForceFull,
  [switch]$IncludeStale,
  [switch]$RefreshListing,
  [switch]$FullListingRefresh,
  [int]$ListingMaxPages = 5,
  [switch]$NoNormalize,
  [int]$MaxAttempts = 1,
  [int]$RetryDelaySeconds = 600,
  [int]$MinRunIntervalMinutes = 60,
  [switch]$ForceRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

if (-not $DryRun -and -not $ForceRun) {
  if ($Limit -le 0) {
    throw "Safety stop: Limit=0 is not allowed for annonce backfill without -ForceRun."
  }
  if ($Limit -gt 50000) {
    throw "Safety stop: Limit above 50000 is not allowed for annonce backfill without -ForceRun."
  }
  if ($ForceFull) {
    throw "Safety stop: ForceFull is not allowed for annonce backfill without -ForceRun."
  }
  if ($RefreshListing -or $FullListingRefresh) {
    throw "Safety stop: listing refresh is not allowed for annonce backfill without -ForceRun."
  }
}

$stateDir = Join-Path $projectRoot ".tmp"
$lastRunFile = Join-Path $stateDir "annonce_details_backfill_last_run.txt"
$lastSuccessFile = Join-Path $stateDir "annonce_details_backfill_last_success.txt"
if (-not $DryRun) {
  New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
  $lastIntervalFile = if (Test-Path -LiteralPath $lastRunFile) { $lastRunFile } else { $lastSuccessFile }
  if (-not $ForceRun -and (Test-Path -LiteralPath $lastIntervalFile)) {
    $lastRunRaw = (Get-Content -LiteralPath $lastIntervalFile -Raw).Trim()
    if ($lastRunRaw) {
      try {
        $lastRun = [DateTimeOffset]::Parse($lastRunRaw)
        $elapsedMinutes = ([DateTimeOffset]::UtcNow - $lastRun.ToUniversalTime()).TotalMinutes
        if ($elapsedMinutes -lt $MinRunIntervalMinutes) {
          $remaining = [Math]::Ceiling($MinRunIntervalMinutes - $elapsedMinutes)
          Write-Warning ("Safety stop: last annonce backfill attempt was {0:N0} minute(s) ago. Wait about {1:N0} minute(s), or use -ForceRun intentionally." -f $elapsedMinutes, $remaining)
          exit 0
        }
      }
      catch {
        Write-Warning "Could not parse last annonce backfill timestamp; continuing with safety defaults."
      }
    }
  }
}

$effectiveSelectionMode = $SelectionMode
if ($IncludeStale) {
  $effectiveSelectionMode = "missing_or_stale"
}

$requestDelayArg = $RequestDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)

$argsList = @(
  "sync_annonce_details_backfill.py",
  "--scope", $Scope,
  "--limit", $Limit,
  "--batch-size", $BatchSize,
  "--batch-pause-seconds", $BatchPauseSeconds,
  "--request-delay-seconds", $requestDelayArg,
  "--selection-mode", $effectiveSelectionMode,
  "--listing-max-pages", $ListingMaxPages
)

if ($DryRun) { $argsList += "--dry-run" }
if ($ForceFull) { $argsList += "--force-full" }
if ($RefreshListing -or $FullListingRefresh) { $argsList += "--refresh-listing" }
if ($FullListingRefresh) { $argsList += "--full-listing-refresh" }
if ($NoNormalize) { $argsList += "--no-normalize" }

for ($attempt = 1; $attempt -le [Math]::Max(1, $MaxAttempts); $attempt++) {
  Write-Host ("Annonce detail extraction attempt {0}/{1}" -f $attempt, [Math]::Max(1, $MaxAttempts))
  Write-Host ("Annonce detail safety: scope={0} limit={1} batch_size={2} request_delay_seconds={3} batch_pause_seconds={4} selection_mode={5}" -f $Scope, $Limit, $BatchSize, $requestDelayArg, $BatchPauseSeconds, $effectiveSelectionMode)
  if (-not $DryRun) {
    Set-Content -LiteralPath $lastRunFile -Value ([DateTimeOffset]::UtcNow.ToString("o"))
  }
  & $python $argsList
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 0) {
    if (-not $DryRun) {
      $finishedAt = [DateTimeOffset]::UtcNow.ToString("o")
      Set-Content -LiteralPath $lastRunFile -Value $finishedAt
      Set-Content -LiteralPath $lastSuccessFile -Value $finishedAt
    }
    exit 0
  }
  if (-not $DryRun) {
    Set-Content -LiteralPath $lastRunFile -Value ([DateTimeOffset]::UtcNow.ToString("o"))
  }
  if ($attempt -ge [Math]::Max(1, $MaxAttempts)) {
    exit $exitCode
  }
  Write-Warning ("Annonce detail extraction failed with exit code {0}. Retry in {1} seconds." -f $exitCode, $RetryDelaySeconds)
  Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
}
