param(
  [int]$Limit = 0,
  [int]$BatchSize = 100,
  [switch]$DryRun,
  [switch]$ForceFull,
  [switch]$SkipListingRefresh,
  [switch]$FullListingRefresh,
  [int]$ListingMaxPages = 5,
  [ValidateSet("active", "archived", "both")]
  [string]$ContactScope = "both",
  [switch]$MissingOnly,
  [switch]$Retry404,
  [switch]$NoNormalize,
  [int]$MaxAttempts = 6,
  [int]$RetryDelaySeconds = 120
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

$argsList = @(
  "phase2\sync\sync_contact_details.py",
  "--limit", $Limit,
  "--batch-size", $BatchSize,
  "--listing-max-pages", $ListingMaxPages,
  "--contact-scope", $ContactScope
)

if ($DryRun) { $argsList += "--dry-run" }
if ($ForceFull) { $argsList += "--force-full" }
if ($SkipListingRefresh) { $argsList += "--skip-listing-refresh" }
if ($FullListingRefresh) { $argsList += "--full-listing-refresh" }
if ($MissingOnly) { $argsList += "--missing-only" }
if ($Retry404) { $argsList += "--retry-404" }
if ($NoNormalize) { $argsList += "--no-normalize" }

for ($attempt = 1; $attempt -le [Math]::Max(1, $MaxAttempts); $attempt++) {
  Write-Host ("Contact detail extraction attempt {0}/{1}" -f $attempt, [Math]::Max(1, $MaxAttempts))
  & $python $argsList
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 0) {
    exit 0
  }
  if ($attempt -ge [Math]::Max(1, $MaxAttempts)) {
    exit $exitCode
  }
  Write-Warning ("Contact detail extraction failed with exit code {0}. Retry in {1} seconds." -f $exitCode, $RetryDelaySeconds)
  Start-Sleep -Seconds ([Math]::Max(1, $RetryDelaySeconds))
}
