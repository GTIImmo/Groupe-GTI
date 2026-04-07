$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "[$timestamp] START $Label"
    & $pythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Step failed: $Label (exit code $LASTEXITCODE)"
    }
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "[$timestamp] DONE  $Label"
}

Set-Location $projectRoot

Invoke-Step -Label "sync_raw annonces" -Arguments @(
    "sync_raw.py",
    "--resources", "annonces",
    "--max-pages", "0",
    "--detail-limit", "0"
)

Invoke-Step -Label "sync_raw complementary resources" -Arguments @(
    "sync_raw.py",
    "--resources", "agences", "negos", "contacts", "mandats", "offres", "compromis", "ventes", "broadcasts",
    "--max-pages", "0",
    "--detail-limit", "0",
    "--no-with-offer-status",
    "--no-with-compromis-status",
    "--mandat-date-start", "2010-01-01",
    "--mandat-date-end", "2030-12-31",
    "--vente-date-start", "2010-01-01",
    "--vente-date-end", "2030-12-31"
)

Invoke-Step -Label "normalize_source" -Arguments @(
    "normalize_source.py"
)

Invoke-Step -Label "build_case_index" -Arguments @(
    "build_case_index.py"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Output "[$timestamp] Phase 1 safe run finished"
