param(
  [int]$Limit = 50000,
  [int]$BatchSize = 1000,
  [switch]$DryRun,
  [switch]$ForceFull,
  [switch]$SkipListingRefresh,
  [switch]$RefreshListing,
  [switch]$FullListingRefresh,
  [int]$ListingMaxPages = 5,
  [ValidateSet("active", "archived", "both")]
  [string]$ContactScope = "both",
  [switch]$MissingOnly,
  [switch]$Retry404,
  [switch]$NoNormalize,
  [double]$RequestDelaySeconds = 0.1,
  [int]$BatchPauseSeconds = 60,
  [int]$MaxHardErrors = 1,
  [int]$MaxConsecutiveHardErrors = 1,
  [int]$Max404Errors = 0,
  [int]$MaxConsecutive404Errors = 0,
  [int]$ClientMaxRetries = 1,
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
    throw "Safety stop: Limit=0 is not allowed for contact backfill without -ForceRun."
  }
  if ($Limit -gt 50000) {
    throw "Safety stop: Limit above 50000 is not allowed for contact backfill without -ForceRun."
  }
  if ($ForceFull) {
    throw "Safety stop: ForceFull is not allowed for contact backfill without -ForceRun."
  }
  if ($RefreshListing -or $FullListingRefresh) {
    throw "Safety stop: listing refresh is not allowed for contact backfill without -ForceRun."
  }
}

$stateDir = Join-Path $projectRoot ".tmp"
$lastRunFile = Join-Path $stateDir "contact_details_backfill_last_run.txt"
$lastSuccessFile = Join-Path $stateDir "contact_details_backfill_last_success.txt"
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
          Write-Warning ("Safety stop: last contact backfill attempt was {0:N0} minute(s) ago. Wait about {1:N0} minute(s), or use -ForceRun intentionally." -f $elapsedMinutes, $remaining)
          exit 0
        }
      }
      catch {
        Write-Warning "Could not parse last contact backfill timestamp; continuing with safety defaults."
      }
    }
  }
}

$requestDelayArg = $RequestDelaySeconds.ToString([System.Globalization.CultureInfo]::InvariantCulture)

$argsList = @(
  "phase2\sync\sync_contact_details.py",
  "--limit", $Limit,
  "--batch-size", $BatchSize,
  "--listing-max-pages", $ListingMaxPages,
  "--contact-scope", $ContactScope,
  "--request-delay-seconds", $requestDelayArg,
  "--batch-pause-seconds", $BatchPauseSeconds,
  "--max-hard-errors", $MaxHardErrors,
  "--max-consecutive-hard-errors", $MaxConsecutiveHardErrors,
  "--max-404-errors", $Max404Errors,
  "--max-consecutive-404-errors", $MaxConsecutive404Errors,
  "--client-max-retries", $ClientMaxRetries
)

if ($DryRun) { $argsList += "--dry-run" }
if ($ForceFull) { $argsList += "--force-full" }
if ($SkipListingRefresh -or (-not $RefreshListing -and -not $FullListingRefresh)) { $argsList += "--skip-listing-refresh" }
if ($FullListingRefresh) { $argsList += "--full-listing-refresh" }
if ($MissingOnly -or -not $ForceFull) { $argsList += "--missing-only" }
if ($Retry404) { $argsList += "--retry-404" }
if ($NoNormalize) { $argsList += "--no-normalize" }

for ($attempt = 1; $attempt -le [Math]::Max(1, $MaxAttempts); $attempt++) {
  Write-Host ("Contact detail extraction attempt {0}/{1}" -f $attempt, [Math]::Max(1, $MaxAttempts))
  Write-Host ("Contact detail safety: limit={0} batch_size={1} request_delay_seconds={2} batch_pause_seconds={3} max_hard_errors={4}/{5}" -f $Limit, $BatchSize, $requestDelayArg, $BatchPauseSeconds, $MaxHardErrors, $MaxConsecutiveHardErrors)
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
  Write-Warning ("Contact detail extraction failed with exit code {0}. Retry in {1} seconds." -f $exitCode, $RetryDelaySeconds)
  Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
}
