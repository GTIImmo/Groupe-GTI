param(
  [int]$Limit = 0,
  [int]$BatchSize = 100,
  [switch]$DryRun,
  [switch]$ForceFull,
  [switch]$SkipListingRefresh,
  [switch]$FullListingRefresh,
  [int]$ListingMaxPages = 5,
  [switch]$NoNormalize
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
  $python = "python"
}

$argsList = @(
  "sync_archived_annonce_details.py",
  "--limit", $Limit,
  "--batch-size", $BatchSize,
  "--listing-max-pages", $ListingMaxPages
)

if ($DryRun) { $argsList += "--dry-run" }
if ($ForceFull) { $argsList += "--force-full" }
if ($SkipListingRefresh) { $argsList += "--skip-listing-refresh" }
if ($FullListingRefresh) { $argsList += "--full-listing-refresh" }
if ($NoNormalize) { $argsList += "--no-normalize" }

& $python $argsList
